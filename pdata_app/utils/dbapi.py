"""
Various utility functions that work with pdata_app data objects
"""
from __future__ import unicode_literals, division, absolute_import

from django.core.exceptions import ObjectDoesNotExist

from pdata_app.models import Settings


def insert(cls, **props):
    """
    Create a object in the database and return the corresponding object. If the
    object already exists in the database that must be unique then
    django.db.utils.IntegrityError will be raised.
    """
    obj = cls(**props)
    obj.save()
    return obj


def match_one(cls, **props):
    """
    Return an object corresponding to an existing object in the database. If
    more than one object or no object is found then return None.
    """
    match = cls.objects.filter(**props)
    if match.count() == 1:
        return match.first()
    return None


def get_or_create(cls, **props):
    """
    If an object already exists then this is returned, otherwise a new object
    is created and retruned.
    """
    obj, created = cls.objects.get_or_create(**props)
    return obj


def exists(cls, **props):
    """
    If an object already exists then return True, else return False.
    """
    if cls.objects.filter(**props):
        return True
    else:
        return False


def get_checksum(data_file, checksum_type="MD5"):
    """
    Return a data file's checksum
    """
    return data_file.checksum_set.get(checksum_type=checksum_type).checksum_value


def count(cls):
    """
    Return the number of objects of this type that exist in the database
    """
    return cls.objects.count()


def is_paused():
    """
    Return True if is_paused is set in the global settings table of the database.
    """
    try:
        is_paused_val = Settings.objects.get().is_paused
    except ObjectDoesNotExist:
        is_paused_val = False

    return is_paused_val
