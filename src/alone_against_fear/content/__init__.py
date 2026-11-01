"""The rules text, copied from the book into the YAML files of this package.

See docs/content.md for the file layout, the ID scheme and the shape of a table.
"""

from .loader import CONTENT_DIR, load_content
from .model import (
    KINDS,
    CatalogueEvent,
    CatalogueTable,
    Content,
    ContentError,
    Entry,
    Roll,
    Table,
    coverage_problems,
    note_problems,
    reference_problems,
)

__all__ = [
    "CONTENT_DIR",
    "KINDS",
    "CatalogueEvent",
    "CatalogueTable",
    "Content",
    "ContentError",
    "Entry",
    "Roll",
    "Table",
    "coverage_problems",
    "load_content",
    "note_problems",
    "reference_problems",
]
