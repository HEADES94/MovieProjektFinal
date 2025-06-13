"""
__init__.py - Initialisierung des Datamanager-Pakets
"""
from .data_manager_interface import DataManagerInterface
from .sqlite_data_manager import SQliteDataManager

__all__ = ['DataManagerInterface', 'SQliteDataManager']
