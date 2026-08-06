from importlib.metadata import version

from openpyxl import load_workbook


def test_approved_tabular_stack_is_available() -> None:
    assert version("openpyxl").startswith("3.")
    assert callable(load_workbook)
