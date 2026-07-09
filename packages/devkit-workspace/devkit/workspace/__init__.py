from importlib.metadata import PackageNotFoundError, version as _v

try:
    __version__ = _v('devkit-workspace')
except PackageNotFoundError:
    __version__ = '0.0.0.dev0'

__all__ = ['__version__']
