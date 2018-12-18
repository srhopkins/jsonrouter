# This is to get around bumpversion issue and still use a tuple of int
# https://github.com/peritus/bumpversion/issues/25
VERSION = tuple(int(i) for i in '0.4.0'.split('.'))

__version_info__ = VERSION
__version__ = '.'.join(map(str, VERSION))
