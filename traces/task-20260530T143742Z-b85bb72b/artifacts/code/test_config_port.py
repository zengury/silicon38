"""
Unit tests for ports.config — ConfigPort ABC and DictConfigAdapter.
"""

import pytest
from ports.config import ConfigPort

# Use the actual adapter from config/app_config.py
from config.app_config import DictConfigAdapter
from common.errors import ConfigurationError


class TestDictConfigAdapter:
    """Verify the in-memory config adapter — used by tests everywhere."""

    def test_get_with_value(self):
        adapter = DictConfigAdapter({"KEY": "value"})
        assert adapter.get("KEY") == "value"

    def test_get_with_default(self):
        adapter = DictConfigAdapter({})
        assert adapter.get("MISSING", "fallback") == "fallback"

    def test_get_required_success(self):
        adapter = DictConfigAdapter({"KEY": "v"})
        assert adapter.get_required("KEY") == "v"

    def test_get_required_raises(self):
        adapter = DictConfigAdapter({})
        with pytest.raises(ConfigurationError):
            adapter.get_required("MISSING")

    def test_get_int(self):
        adapter = DictConfigAdapter({"PORT": "8080"})
        assert adapter.get_int("PORT") == 8080

    def test_get_int_default(self):
        adapter = DictConfigAdapter({})
        assert adapter.get_int("PORT", 3000) == 3000

    def test_get_bool_true(self):
        adapter = DictConfigAdapter({"DEBUG": "true"})
        assert adapter.get_bool("DEBUG") is True

    def test_get_bool_false(self):
        adapter = DictConfigAdapter({"DEBUG": "false"})
        assert adapter.get_bool("DEBUG") is False

    def test_get_float(self):
        adapter = DictConfigAdapter({"RATE": "0.75"})
        assert adapter.get_float("RATE") == 0.75

    def test_all_returns_copy(self):
        adapter = DictConfigAdapter({"A": "1"})
        d = adapter.all()
        assert d == {"A": "1"}

    def test_set_overrides(self):
        adapter = DictConfigAdapter({"A": "1"})
        adapter.set("A", "2")
        assert adapter.get("A") == "2"
