"""
Base class for code_lists.

code lists are ordered dictionaries with attribute access.

"""


try:
    from collections import OrderedDict
except ImportError:
    try:
        from ordereddict import OrderedDict
    except ImportError:
        raise ImportError('No implementation of OrderedDict found.  '
                          'In Python<2.7 install the ordereddict package')

class CodeList(OrderedDict):
    """
    At the moment CodeLists simply map keys to descriptions and
    allow attribute access for easy lookup.  In the future there may be
    more features like short_description, long_description and the
    internal code may differ from the attribute.

    The main features to retain are:
     1. Ordered dict
     2. self.items() should return an iterable suitable for sending to django's
        Field.choices argument.
     3. Code can refer to codeList.codename and get back the internal code.
    """
    def __getattr__(self, attr):
        if attr in self:
            return attr
        else:
            raise AttributeError('No code for %s' % attr)
