"""Shared error handlers for the ComplyEur web blueprint."""

from flask import render_template

from .base import logger, main_bp


@main_bp.errorhandler(403)
def forbidden_error(error):
    logger.warning("403 error: %s", error)
    return render_template('403.html'), 403


@main_bp.errorhandler(404)
def not_found_error(error):
    logger.warning("404 error: %s", error)
    return render_template('404.html'), 404


@main_bp.errorhandler(500)
def internal_error(error):
    import traceback

    logger.error("500 Internal Server Error: %s", error)
    logger.error(traceback.format_exc())
    return render_template('500.html'), 500


@main_bp.errorhandler(Exception)
def handle_exception(exc):
    import traceback

    logger.error("Unhandled exception: %s", exc)
    logger.error(traceback.format_exc())
    return render_template('500.html'), 500
