#  Copyright 2008-2015 Nokia Networks
#  Copyright 2016-     Robot Framework Foundation
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

try:
    from collections import MutableMapping
except ImportError:
    from collections.abc import MutableMapping  # Python 3.10

from .platform import PY3
from .robottypes import is_dict_like, is_unicode


def normalize(string, ignore=(), caseless=True, spaceless=True, suffixless=False):
    """Normalizes given string according to given spec.

    By default, string is turned to lower case and all whitespace is removed.
    Additional characters can be removed by giving them in ``ignore`` list.
    :param
      suffixless: the end char is removed if is a symbol
    """
    if not string or string == '':
        return ''
    empty = u'' if is_unicode(string) else b''
    if PY3 and isinstance(ignore, bytes):
        # Iterating bytes in Python3 yields integers.
        ignore = [bytes([i]) for i in ignore]
    if spaceless:
        string = empty.join(string.split())
    if caseless:
        string = lower(string)
        ignore = [lower(i) for i in ignore]
    # both if statements below enhance performance a little
    if ignore:
        for ign in ignore:
            if ign in string:
                string = string.replace(ign, empty)
    if suffixless:
        while len(string) > 1 and string[-1] in "=}])":
            string = string[:-1]
    return string


def lower(string):
    return string.lower()


def _normalize(name, ignore=(), caseless=True, spaceless=True):
    return normalize(name, ignore, caseless, spaceless)


def normalized_headers(table: dict):
    """
    Returns the normalized keys from the dictionary
    :param table: the dict to get headers normalized
    :return: normalized keys from table
    """
    result = []
    for name in table.keys():
        result.append(normalize(name))
    return result


class NormalizedDict(MutableMapping):
    """Custom dictionary implementation automatically normalizing keys."""

    def __init__(self, initial=None, ignore=(), caseless=True, spaceless=True):
        """Initialized with possible initial value and normalizing spec.

        Initial values can be either a dictionary or an iterable of name/value
        pairs. In the latter case items are added in the given order.

        Normalizing spec has exact same semantics as with the :func:`normalize`
        function.
        """
        self._data = {}
        self._keys = {}
        self._ignore = ignore
        self._caseless = caseless
        self._spaceless = spaceless
        if initial:
            self._add_initial(initial)

    def _add_initial(self, initial):
        items = initial.items() if hasattr(initial, 'items') else initial
        for key, value in items:
            self[key] = value

    def __getitem__(self, key):
        return self._data[_normalize(key, ignore=self._ignore, caseless=self._caseless, spaceless=self._spaceless)]

    def __setitem__(self, key, value):
        norm_key = _normalize(key, ignore=self._ignore, caseless=self._caseless, spaceless=self._spaceless)
        self._data[norm_key] = value
        self._keys.setdefault(norm_key, key)

    def __delitem__(self, key):
        norm_key = _normalize(key, ignore=self._ignore, caseless=self._caseless, spaceless=self._spaceless)
        del self._data[norm_key]
        del self._keys[norm_key]

    def __iter__(self):
        return (self._keys[norm_key] for norm_key in sorted(self._keys))

    def __len__(self):
        return len(self._data)

    def __str__(self):
        return '{%s}' % ', '.join('%r: %r' % (key, self[key]) for key in self)

    def __eq__(self, other):
        if not is_dict_like(other):
            return False
        if not isinstance(other, NormalizedDict):
            other = NormalizedDict(other, caseless=self._caseless)
        return self._data == other._data

    def __ne__(self, other):
        return not self == other

    def copy(self):
        copy = NormalizedDict()
        copy._data = self._data.copy()
        copy._keys = self._keys.copy()
        copy._normalize = _normalize
        return copy

    # Speed-ups. Following methods are faster than default implementations.

    def __contains__(self, key):
        return _normalize(key, ignore=self._ignore, caseless=self._caseless, spaceless=self._spaceless) in self._data

    def clear(self):
        self._data.clear()
        self._keys.clear()
