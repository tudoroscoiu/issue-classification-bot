"""Represents a model for the application."""

from typing import Protocol

class Model(Protocol):

    def label(self, issue):
        """Labels an issue"""

    