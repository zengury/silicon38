"""
Unit tests for application.dto — PageResult DTO.
"""

from application.dto import PageResult


class TestPageResult:
    """Verify PageResult construction and defaults."""

    def test_defaults(self):
        pr = PageResult()
        assert pr.total == 0
        assert pr.items == []

    def test_with_data(self):
        items = [{"id": 1}, {"id": 2}]
        pr = PageResult(total=2, items=items)
        assert pr.total == 2
        assert len(pr.items) == 2
        assert pr.items[0]["id"] == 1

    def test_empty_items_list(self):
        pr = PageResult(total=0, items=[])
        assert pr.total == 0
        assert pr.items == []

    def test_items_none(self):
        pr = PageResult(total=5)
        assert pr.total == 5
        assert pr.items == []
