"""
test_validate_data_submission.py - unit tests for validate_data_submission.py
"""
from django.contrib.auth.models import User
from django.test import tag, TestCase
import mock

try:
    import iris
except ImportError:
    pass
else:
    # Only import the validations if Iris is available
    from scripts.validate_data_submission import update_database_submission
from pdata_app.models import DataSubmission
from pdata_app.utils.dbapi import get_or_create
from vocabs.vocabs import STATUS_VALUES


@tag('validation')
class TestUpdateDatabaseSubmission(TestCase):
    @mock.patch('scripts.validate_data_submission.create_database_file_object')
    def setUp(self, mock_create_file):
        self.mock_create_file = mock_create_file
        user = get_or_create(User, username='fred')
        self.ds = get_or_create(DataSubmission, incoming_directory='/dir',
                                directory='/dir', user=user,
                                status=STATUS_VALUES['PENDING_PROCESSING'])
        self.metadata = [{'file': 'file1'}, ]
        update_database_submission(self.metadata, self.ds)

    def test_submission_status(self):
        self.ds.refresh_from_db()
        self.assertEqual(self.ds.status, 'VALIDATED')

    def test_create_db_file_called(self):
        self.mock_create_file.assert_called_once_with(self.metadata[0],
                                                      self.ds, True, None)
