"""Коннекторы к внешним системам."""

from app.pkg.connectors.base import BaseConnector
from app.pkg.connectors.postgres import PostgresConnector

__all__ = ["BaseConnector", "PostgresConnector"]
