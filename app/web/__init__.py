"""Web route package for ComplyEur."""

from .base import main_bp

# Load implemented route groups
from . import pages  # noqa: E402,F401
from . import privacy  # noqa: E402,F401
from . import dashboard  # noqa: E402,F401
from . import employees  # noqa: E402,F401
from . import trips  # noqa: E402,F401
from . import exports  # noqa: E402,F401

__all__ = ['main_bp']
