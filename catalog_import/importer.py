"""The one-time launch import (User Story 5, FR-030–FR-032, research R14)."""

from dataclasses import dataclass
from pathlib import Path

from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext as _

from catalog.models import Product
from catalog.services.publishing import PublishRuleError, publish

from .catalog_writer import CatalogWriter
from .models import CatalogImport
from .problems import ImportProblem
from .row_validation import validate_catalog
from .validated_rows import ProductRow, ValidatedCatalog
from .workbook_reader import read_workbook


class ImportRefused(Exception):
    """A completed import already exists, so the catalog may not be loaded again (FR-032)."""


@dataclass(frozen=True)
class ImportSummary:
    products_published: int
    products_draft: int
    rows_rejected: int
    problems: list[ImportProblem]


class CatalogImporter:
    def __init__(self, workbook: Path, photos_dir: Path, run_by: User):
        self.workbook = workbook
        self.photos_dir = photos_dir
        self.run_by = run_by

    def check(self) -> ImportSummary:
        """Validates everything and reports what would happen, writing nothing (`--dry-run`)."""
        refuse_if_already_imported()
        catalog = self.validated()
        will_publish = [row for row in catalog.products.values() if is_ready(row)]
        drafts = len(catalog.products) - len(will_publish)
        return ImportSummary(
            len(will_publish), drafts, catalog.rejected_row_count, catalog.problems
        )

    def run(self) -> ImportSummary:
        refuse_if_already_imported()
        catalog = self.validated()
        record = CatalogImport.objects.create(
            source_filename=self.workbook.name, run_by=self.run_by
        )
        try:
            with transaction.atomic():
                summary = load_catalog(catalog)
        except Exception:
            finish(record, CatalogImport.Status.FAILED)
            raise
        finish(record, CatalogImport.Status.COMPLETED, summary)
        return summary

    def validated(self) -> ValidatedCatalog:
        return validate_catalog(read_workbook(self.workbook), self.photos_dir)


def refuse_if_already_imported() -> None:
    if CatalogImport.objects.filter(status=CatalogImport.Status.COMPLETED).exists():
        raise ImportRefused(_("The launch catalog has already been imported."))


def is_ready(row: ProductRow) -> bool:
    return row.publish and not row.has_problems


def load_catalog(catalog: ValidatedCatalog) -> ImportSummary:
    products = CatalogWriter(catalog).write()
    problems = list(catalog.problems)
    published = 0
    for key, row in catalog.products.items():
        if is_ready(row):
            failure = try_to_publish(products[key], row)
            published += failure is None
            problems += [failure] if failure else []
    drafts = len(products) - published
    return ImportSummary(published, drafts, catalog.rejected_row_count, problems)


def try_to_publish(product: Product, row: ProductRow) -> ImportProblem | None:
    try:
        publish(product)
    except PublishRuleError as refusal:
        return ImportProblem(
            "Products", row.row_number, "publish", " ".join(refusal.failures), rejects_row=False
        )
    return None


def finish(record: CatalogImport, status: str, summary: ImportSummary | None = None) -> None:
    record.status = status
    record.finished_at = timezone.now()
    if summary is not None:
        record.products_published = summary.products_published
        record.products_draft = summary.products_draft
        record.rows_rejected = summary.rows_rejected
        record.problems = [problem.as_dict() for problem in summary.problems]
    record.save()
