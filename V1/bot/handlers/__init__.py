from .analysis import register_analysis_handlers
from .webapp import register_webapp_handlers


def register_handlers(application):
    """Register all handlers"""
    register_analysis_handlers(application)
    register_webapp_handlers(application)
