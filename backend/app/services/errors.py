"""Application failures translated into HTTP responses at the API boundary."""

from collections.abc import Collection
from uuid import UUID


class NotFoundError(Exception):
    pass


class ConflictError(Exception):
    pass


class ReferenceValidationError(Exception):
    def __init__(self, field: str, identifiers: Collection[UUID]):
        self.field = field
        super().__init__(f"Unknown {field}: {', '.join(sorted(map(str, identifiers)))}")
