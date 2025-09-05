"""
Core package for shared functionality and base classes.
Contains common utilities used across the application.
"""

from .base_handler import BaseHandler
from .response_manager import ResponseManager
from .confirmation_handler import ConfirmationHandler
from .error_handler import ErrorHandler

__all__ = [
    'BaseHandler',
    'ResponseManager',
    'ConfirmationHandler',
    'ErrorHandler'
]
