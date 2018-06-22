from __future__ import (unicode_literals, division, absolute_import,
                        print_function)
import django
django.setup()

from pdata_app.models import __all__ as all_class_names

classes = [eval(cls_name) for cls_name in all_class_names]
 
for cls in classes:
    print(cls.__name__)
    cls.objects.all().delete()

print("Deleted all!")
