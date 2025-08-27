"""
Operations package for handling different types of calendar operations.
Provides unified interface for create, update, delete, and query operations.
"""

from .base_operation import BaseOperation
from .create_operation import CreateOperation
from .update_operation import UpdateOperation
from .delete_operation import DeleteOperation
from .query_operation import QueryOperation
from .operation_factory import OperationFactory

__all__ = [
    'BaseOperation',
    'CreateOperation',
    'UpdateOperation',
    'DeleteOperation',
    'QueryOperation',
    'OperationFactory'
]
