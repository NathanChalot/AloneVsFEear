"""The shape of the town (E3): sheets, neighbours and distance. Pure geometry, no state.

The town is one grid of boxes; a sheet is a 5-column, 6-row block of it (design/town-map.md).
A `Position` is a box's (column, row) in the grid; a sheet is named by its own (column, row) in
the grid of sheets, so the first sheet is (0, 0) and the one to its right is (1, 0).
"""

from __future__ import annotations

from collections.abc import Collection

from .state import Position

SHEET_COLUMNS = 5
SHEET_ROWS = 6


def sheet_of(position: Position) -> Position:
    """The sheet a box belongs to."""
    return Position(position.column // SHEET_COLUMNS, position.row // SHEET_ROWS)


def boxes_of(sheet: Position) -> list[Position]:
    """The 30 boxes of a sheet."""
    return [
        Position(sheet.column * SHEET_COLUMNS + column, sheet.row * SHEET_ROWS + row)
        for row in range(SHEET_ROWS)
        for column in range(SHEET_COLUMNS)
    ]


def sheet_neighbours(sheet: Position) -> set[Position]:
    """The sheets that share a side with `sheet`."""
    return {
        Position(sheet.column + 1, sheet.row),
        Position(sheet.column - 1, sheet.row),
        Position(sheet.column, sheet.row + 1),
        Position(sheet.column, sheet.row - 1),
    }


def neighbours(position: Position, sheets: Collection[Position]) -> set[Position]:
    """The boxes around `position`, diagonals included, that lie on a sheet in `sheets`."""
    around = {
        Position(position.column + dc, position.row + dr)
        for dc in (-1, 0, 1)
        for dr in (-1, 0, 1)
        if (dc, dr) != (0, 0)
    }
    return {box for box in around if sheet_of(box) in sheets}


def distance(a: Position, b: Position) -> int:
    """The fewest moves between two boxes, a diagonal step counting as 1."""
    return max(abs(a.column - b.column), abs(a.row - b.row))
