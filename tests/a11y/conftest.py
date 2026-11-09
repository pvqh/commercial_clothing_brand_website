"""Accessibility checks (constitution Principle II): axe-core through Playwright."""

import pytest
from axe_playwright_python.sync_playwright import Axe
from playwright.sync_api import Page

BLOCKING_IMPACTS = {"serious", "critical"}
_axe = Axe()


def assert_no_serious_axe_violations(page: Page) -> None:
    results = _axe.run(page)
    blocking = [
        violation
        for violation in results.response["violations"]
        if violation.get("impact") in BLOCKING_IMPACTS
    ]
    assert not blocking, describe_violations(blocking)


def describe_violations(violations: list[dict]) -> str:
    lines = [f"{len(violations)} serious or critical axe violation(s):"]
    for violation in violations:
        targets = ", ".join(str(node["target"]) for node in violation["nodes"][:3])
        lines.append(
            f"- {violation['id']} ({violation['impact']}): {violation['help']} — {targets}"
        )
    return "\n".join(lines)


@pytest.fixture
def axe_check():
    return assert_no_serious_axe_violations
