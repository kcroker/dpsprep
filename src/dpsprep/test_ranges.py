import pytest

from dpsprep.exceptions import DpsPrepConfigError
from dpsprep.ranges import RangeOption, parse_str_range_option


class TestParseStrRangeArgument:
    def test_without_range(self) -> None:
        assert parse_str_range_option('value') == RangeOption('value')

    def test_empty_range(self) -> None:
        with pytest.raises(DpsPrepConfigError):
            assert parse_str_range_option('value[]')

    def test_malformed_range(self) -> None:
        with pytest.raises(DpsPrepConfigError):
            assert parse_str_range_option('value[1-]')

    def test_range_with_only_start(self) -> None:
        assert parse_str_range_option('value[1]') == RangeOption('value', 1, 1)

    def test_unbounded_from_above_range(self) -> None:
        assert parse_str_range_option('value[1-end]') == RangeOption('value', 1)

    def test_bounded_range(self) -> None:
        assert parse_str_range_option('value[1-2]') == RangeOption('value', 1, 2)

    def test_tail(self) -> None:
        with pytest.raises(DpsPrepConfigError):
            assert parse_str_range_option('value[1-2]tail')
