"""Problems found in the workbook, reported by sheet, row and column (SC-008)."""

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class ImportProblem:
    sheet: str
    row: int
    column: str
    message: str
    rejects_row: bool = True

    def as_dict(self) -> dict:
        return {key: value for key, value in asdict(self).items() if key != "rejects_row"}


class ProblemLog:
    def __init__(self) -> None:
        self.problems: list[ImportProblem] = []

    def report(self, problem: ImportProblem) -> None:
        self.problems.append(problem)

    def rejected_row_count(self) -> int:
        return len({(p.sheet, p.row) for p in self.problems if p.rejects_row})
