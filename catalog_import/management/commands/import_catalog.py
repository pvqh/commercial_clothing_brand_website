import csv
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.utils import translation

from catalog_import.importer import CatalogImporter, ImportRefused, ImportSummary
from catalog_import.workbook_reader import ImportFormatError


class Command(BaseCommand):
    help = (
        "Loads the launch catalog from the staff workbook (see catalog_import/WORKBOOK_FORMAT.md)."
    )

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("workbook", type=Path, help="The .xlsx workbook")
        parser.add_argument("--photos", type=Path, required=True, help="Folder with every photo")
        parser.add_argument("--run-by", required=True, help="Username of the admin running it")
        parser.add_argument("--dry-run", action="store_true", help="Check only; write nothing")

    def handle(self, *args, **options) -> None:
        with translation.override("ru"):
            importer = CatalogImporter(options["workbook"], options["photos"], admin(options))
            summary = run(importer, dry_run=options["dry_run"])
            report = write_report(options["workbook"], summary)
            self.print_summary(summary, report, dry_run=options["dry_run"])

    def print_summary(self, summary: ImportSummary, report: Path, dry_run: bool) -> None:
        heading = "Проверка завершена (ничего не записано)" if dry_run else "Загрузка завершена"
        self.stdout.write(self.style.SUCCESS(heading))
        self.stdout.write(f"Опубликовано товаров: {summary.products_published}")
        self.stdout.write(f"Сохранено черновиков: {summary.products_draft}")
        self.stdout.write(f"Отклонено строк: {summary.rows_rejected}")
        self.stdout.write(f"Отчёт: {report}")


def admin(options: dict):
    user = get_user_model().objects.filter(username=options["run_by"], is_superuser=True).first()
    if user is None:
        raise CommandError(f"Администратор «{options['run_by']}» не найден.")
    return user


def run(importer: CatalogImporter, dry_run: bool) -> ImportSummary:
    try:
        return importer.check() if dry_run else importer.run()
    except (ImportFormatError, ImportRefused) as refusal:
        raise CommandError(str(refusal)) from refusal
    except Exception as failure:
        message = f"Загрузка прервана, изменения отменены: {failure}"
        raise CommandError(message) from failure


def write_report(workbook: Path, summary: ImportSummary) -> Path:
    report = workbook.with_name(f"{workbook.stem}-report.csv")
    with report.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["sheet", "row", "column", "problem"])
        for problem in summary.problems:
            writer.writerow([problem.sheet, problem.row, problem.column, problem.message])
    return report
