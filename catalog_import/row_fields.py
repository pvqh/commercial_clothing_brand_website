"""Typed reading of one workbook row; each bad value is reported to the problem log."""

import re
from decimal import Decimal, InvalidOperation
from typing import Any

from django.utils.translation import gettext as _

from .problems import ImportProblem, ProblemLog
from .workbook_reader import SheetRow

WHOLE_NUMBER = re.compile(r"-?\d+")


class RowFields:
    def __init__(self, sheet: str, row: SheetRow, log: ProblemLog):
        self.sheet = sheet
        self.row = row
        self.log = log
        self.problem_count = 0

    @property
    def is_valid(self) -> bool:
        return self.problem_count == 0

    def report(self, column: str, message: str) -> None:
        self.problem_count += 1
        self.log.report(ImportProblem(self.sheet, self.row.number, column, message))

    def raw(self, column: str) -> Any:
        return self.row.values.get(column)

    def text(self, column: str, required: bool = False, max_length: int | None = None) -> str:
        value = self.raw(column)
        text = "" if value is None else str(value).strip()
        if required and not text:
            self.report(column, _("Required field is empty."))
        elif max_length and len(text) > max_length:
            message = _("The text is too long: at most %(limit)s characters.")
            self.report(column, message % {"limit": max_length})
        return text

    def whole_number(self, column: str, minimum: int, message: str) -> int | None:
        number = parse_whole_number(self.raw(column))
        if number is None or number < minimum:
            self.report(column, message)
            return None
        return number

    def position(self, column: str = "position") -> int | None:
        return self.whole_number(
            column, 0, _("The position must be a whole number not less than zero.")
        )

    def measurement(self, column: str) -> Decimal | None:
        number = parse_decimal(self.raw(column))
        if number is None or number <= 0:
            self.report(column, _("The measurement must be a number greater than zero."))
            return None
        return number.quantize(Decimal("0.1"))

    def choice(self, column: str, choices: dict[str, Any], message: str) -> Any:
        code = self.text(column).lower()
        if code not in choices:
            self.report(column, message % {"value": code})
            return None
        return choices[code]


def parse_whole_number(value: Any) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value) if value.is_integer() else None
    text = str(value).strip()
    return int(text) if WHOLE_NUMBER.fullmatch(text) else None


def parse_decimal(value: Any) -> Decimal | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        return Decimal(str(value).strip().replace(",", "."))
    except InvalidOperation:
        return None
