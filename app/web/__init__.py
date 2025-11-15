"""Web route package for ComplyEur."""

from .base import main_bp

# Import route modules for side-effects (they attach to main_bp)
from . import dashboard  # noqa: E402,F401
from . import employees  # noqa: E402,F401
from . import trips  # noqa: E402,F401
from . import admin  # noqa: E402,F401
from . import exports  # noqa: E402,F401
from . import privacy  # noqa: E402,F401
from . import auth  # noqa: E402,F401
from . import calendar  # noqa: E402,F401
from . import pages  # noqa: E402,F401
from . import health  # noqa: E402,F401

__all__ = ['main_bp']
