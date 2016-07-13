import shutil
import time

from pdatalib.controllers.base_controller import BaseController
from pdata_app.utils.dbapi import *
from pdata_app.utils.common import *
from pdata_app.pdata_exceptions import PdataQCError, PdataNotifyError
from config import get_dir_from_scheme


class QCController(BaseController):
    """
      - get pending datasets from db
      - check files are in: incoming dir
      - do: quality control on files: needs content to match file name
      - undo: do nothing
    """
    name = "QCController"
    purpose = "Runs QC code on the contents of each data file."

    def _run_qc(self, fpath):
        expected_var_id = os.path.basename(fpath).split("_")[0]
        with open(fpath) as f:
            if f.read() != expected_var_id:
                raise PdataQCError("File: %s failed QC with contents error." % fpath)

    def _run_do(self, task):
        ds = task.dataset
        incoming_dir = get_dir_from_scheme(ds.chain.name, "incoming_dir")
        files = get_dataset_files(ds)

        # check all files are in: incoming dir
        missing_files = get_missing_file_list(incoming_dir, files)
        if missing_files:
            raise Exception("%d files are missing from the incoming directory for dataset: %s" % \
                            (len(missing_files), ds.name))

        # do: quality control on files: needs content to match file name
        qc_failures = []
        fpaths = [os_path_join(incoming_dir, f.name) for f in files]

        for fpath in fpaths:
            try:
                self._run_qc(fpath)
            except PdataQCError, err:
                qc_failures.append(err)
            # Does not catch other exceptions

        if qc_failures:
            set_dataset_status(ds, self.name, STATUS_VALUES.FAILED)
            raise PdataQCError("%d files failed QC for dataset: %s" % (len(qc_failures), ds.name))

        self.log.info("QC completed for: %s" % ds.name)

    def _run_undo(self, task):
        # undo: do nothing
        self.log.warn("No UNDO actions required for controller: %s" % self.name)


class IngestController(BaseController):
    """
      - get pending datasets from db
      - check all files are in: incoming dir
      - do: move files to: archive dir
      - undo: if undo is required: move files back to: incoming dir
    """
    name = "IngestController"
    purpose = "Finds data in incoming; moves it to archive directory"

    def _move_file(self, source_path, target_path):
        if os.path.isfile(target_path): os.remove(target_path)
        os.rename(source_path, target_path)

    def _run_do(self, task):
        ds = task.dataset
        incoming_dir = get_dir_from_scheme(ds.chain.name, "incoming_dir")
        files = get_dataset_files(ds)

## TODO - could use a decorator for this task - might be useful for common sub-tasks!!!
        # check all files are in: incoming dir
        missing_files = get_missing_file_list(incoming_dir, files)
        if missing_files:
            raise Exception("%d files are missing from the incoming directory for dataset: %s" % \
                            (len(missing_files), ds.name))

        # do: move files to: archive dir
        archive_dir = get_dir_from_scheme(ds.chain.name, "archive_dir")
        move_actions = []

        for f in files:
            fpath = os_path_join(incoming_dir, f.name)
            target = os_path_join(archive_dir, os.path.basename(fpath))

            try:
                self.log.info("Trying to move: %s" % fpath)
                # Set special error to raise on particular file (test 3)
                if f.name == "tasmax_day_IPSL-CM5A-LR_amip4K_r1i1p1_18600101-18601230.nc":
                    raise IOError("Cannot move file: %s" % fpath)
                elif f.name == "rsds_cfDay_IPSL-CM5A-LR_abrupt4xCO2_r1i1p1_19920101-19921230.nc":
                    # Wait here so that we can simulate the controller being switched off in test workflow
                    time.sleep(5)

                self._move_file(fpath, target)
                move_actions.append((fpath, target))
            except Exception, err:
                try:
                    self._clean_up_failed_move(f, fpath, target)
                except:
                    raise PdataNotifyError("Cannot move or clean up file move actions: %s -> %s for dataset: %s" % \
                                           (fpath, target, ds.name))
                try:
                    self._rollback_successful_move_actions(move_actions)
                except:
                    raise PdataNotifyError("Cannot rollback move actions for: %s." % ds.name)

        files.update(directory=archive_dir)
        self.log.info("DO: Ingestion completed for: %s" % ds.name)

    def _clean_up_failed_move(self, f, source, target):
        if os.path.isfile(source) and md5(source) == get_checksum(f, "MD5"):
            if os.path.isfile(target): os.remove(target)
        else:
            self._move_file(target, source)

    def _rollback_successful_move_actions(self, move_actions):
        "Move files back that have been successfully moved to the ."
        for source, target in move_actions:
            self._move_file(target, source)

    def _run_undo(self, task):
        """Does undo but is also used for clean-up after re-start of the controller.
        Hence the design needs to account for the fact that we only care about the
        outcome and not how we got there. If we discover things are in order without
        fully running the undo actions then we accept that.
        """
        # undo: if nextController.status is empty: delete files in: archive dir
        ds = task.dataset
        incoming_dir = get_dir_from_scheme(ds.chain.name, "incoming_dir")
        files = get_dataset_files(ds)

        # undo: move files back to: incoming dir
        archive_dir = get_dir_from_scheme(ds.chain.name, "archive_dir")
#        move_actions = []

        for f in files:
            fpath = os_path_join(archive_dir, f.name)
            if 1: #try:
                target = os_path_join(incoming_dir, os.path.basename(fpath))

                # This is an undo so do not care if target already exists and
                # the source doesn't exist.
                if os.path.isfile(fpath):
                    self._move_file(fpath, target)

                # Now test that target exists and raise Exception if not
                if not os.path.isfile(target):
                    raise Exception
#                move_actions.append((fpath, target))
            else: #except Exception, err:
                raise PdataNotifyError("Cannot complete UNDO move actions for: %s." % ds.name)

        files.update(directory=incoming_dir)
        self.log.warn("UNDO: Files removed from archive for controller: %s" % self.name)
        self.log.warn("Archive contains:" + str(os.listdir(archive_dir)))
        self.log.warn("Incoming contains:" + str(os.listdir(incoming_dir)))


class PublishController(BaseController):
    """
      - get pending datasets from db
      - assert files are in: archive dir
      - do: copy files to: esgf dir
      - undo: if undo is required: delete files in: esgf dir
    """
    name = "PublishController"
    purpose = "Finds data in archive dir; copies it to esgf dir"

    def _copy_file(self, source_path, target_dir):
        shutil.copy(source_path, target_dir)

    def _run_do(self, task):
        ds = task.dataset
        archive_dir = get_dir_from_scheme(ds.chain.name, "archive_dir")
        files = get_dataset_files(ds)

        # check all files are in: archive dir
        missing_files = get_missing_file_list(archive_dir, files)
        if missing_files:
            raise Exception("%d files are missing from the archive directory for dataset: %s" % \
                            (len(missing_files), ds.name))

        # do: copy files to: esgf dir
        esgf_dir = get_dir_from_scheme(ds.chain.name, "esgf_dir")
        copy_actions = []

        for f in files:
            fpath = os_path_join(archive_dir, f.name)

            try:
                self._copy_file(fpath, esgf_dir)
                copy_actions.append((fpath, esgf_dir))
            except Exception, err:
                try:
                    self._remove_if_exists(os_path_join(esgf_dir, os.path.basename(fpath)))
                except:
                    raise PdataNotifyError("Cannot move or clean up file copy actions: %s -> %s for dataset: %s" % \
                                           (fpath, esgf_dir, ds.name))
                try:
                    self._rollback_successful_copy_action(copy_actions)
                except:
                    raise PdataNotifyError("Cannot rollback copy actions for: %s." % ds.name)

        self.log.info("DO: Publishing completed for: %s" % ds.name)

    def _move_file(self, source_path, target_path):
        os.rename(source_path, target_path)

    def _remove_if_exists(self, fpath):
        if os.path.isfile(fpath):
            os.remove(fpath)

    def _rollback_successful_copy_action(self, copy_actions):
        "Move files back that have been successfully moved to the archive."
        for source_path, target_dir in copy_actions:
            fpath = os_path_join(target_dir, os.path.basename(source_path))
            self._remove_if_exists(fpath)

    def _run_undo(self, task):
        # undo: if undo is required: delete files in: esgf dir
        ds = task.dataset
        esgf_dir = get_dir_from_scheme(ds.chain.name, "esgf_dir")
        files = get_dataset_files(ds)

        # undo: delete files in: esgf dir
        for f in files:
            fpath = os_path_join(esgf_dir, f.name)
            try:
                self._remove_if_exists(fpath)
            except Exception, err:
                raise PdataNotifyError("Cannot complete UNDO copy actions for: %s." % ds.name)

        self.log.warn("UNDO: Files removed from esgf dir for controller: %s" % self.name)