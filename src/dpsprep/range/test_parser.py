import enum
import re

import pytest

from dpsprep.exceptions import DpsPrepParseError
from dpsprep.range import RangeOption, RangeOptionGroup, parse_enum_range_group


class AbcEnum(enum.StrEnum):
    A = 'a'
    B = 'b'
    C = 'c'


class TestParseLiteralRangeOption:
    def test_without_range(self) -> None:
        assert parse_enum_range_group('a', AbcEnum).ranges == [RangeOption(AbcEnum.A)]

    def test_empty_range(self) -> None:
        with pytest.raises(DpsPrepParseError, match=re.escape("Expected an integer after 'a['")):
            parse_enum_range_group('a[]', AbcEnum)

    def test_malformed_range(self) -> None:
        with pytest.raises(DpsPrepParseError, match=re.escape("Expected an integer after 'a[1-'")):
            parse_enum_range_group('a[1-]', AbcEnum)

    def test_invalid_option(self) -> None:
        with pytest.raises(DpsPrepParseError, match=re.escape('Expected a supported option at position 0')):
            parse_enum_range_group('d[1-]', AbcEnum)

    def test_range_with_only_start(self) -> None:
        assert parse_enum_range_group('a[1]', AbcEnum).ranges == [RangeOption(AbcEnum.A, 1, 1)]

    def test_unbounded_from_above_range(self) -> None:
        assert parse_enum_range_group('a[1-end]', AbcEnum).ranges == [RangeOption(AbcEnum.A, 1)]

    def test_bounded_range(self) -> None:
        assert parse_enum_range_group('a[1-2]', AbcEnum).ranges == [RangeOption(AbcEnum.A, 1, 2)]

    def test_tail(self) -> None:
        with pytest.raises(DpsPrepParseError, match=re.escape("Unexpected symbol 't' after 'a[1-2]'")):
            parse_enum_range_group('a[1-2]tail', AbcEnum)

    def test_multiple_start_values(self) -> None:
        assert parse_enum_range_group('a[1,2]', AbcEnum).ranges == [RangeOption(AbcEnum.A, 1, 1), RangeOption(AbcEnum.A, 2, 2)]


class TestRangeOptionGroup:
    def test_empty_group(self) -> None:
        group = RangeOptionGroup[str]([])
        assert group.get_value_for_one_based_page(3) is None
        assert group.get_global_value() is None

    def test_single_option(self) -> None:
        group = parse_enum_range_group('a', AbcEnum)
        assert group.get_value_for_one_based_page(3) == 'a'
        assert group.get_global_value() == 'a'

    def test_single_option_with_index(self) -> None:
        group = parse_enum_range_group('a[3]', AbcEnum)
        assert group.get_value_for_one_based_page(2) is None
        assert group.get_value_for_one_based_page(3) == 'a'
        assert group.get_global_value() is None

    def test_single_option_with_bounded_range(self) -> None:
        group = parse_enum_range_group('a[3-4]', AbcEnum)
        assert group.get_value_for_one_based_page(2) is None
        assert group.get_value_for_one_based_page(3) == 'a'
        assert group.get_value_for_one_based_page(5) is None
        assert group.get_global_value() is None

    def test_single_option_with_unbounded_range(self) -> None:
        group = parse_enum_range_group('a[3-end]', AbcEnum)
        assert group.get_value_for_one_based_page(2) is None
        assert group.get_value_for_one_based_page(3) == 'a'
        assert group.get_value_for_one_based_page(5) == 'a'
        assert group.get_global_value() is None

    def test_two_options(self) -> None:
        group = parse_enum_range_group('a[1]', AbcEnum) | parse_enum_range_group('b[3-4]', AbcEnum)
        assert group.get_value_for_one_based_page(1) == 'a'
        assert group.get_value_for_one_based_page(2) is None
        assert group.get_value_for_one_based_page(3) == 'b'
        assert group.get_value_for_one_based_page(4) == 'b'
        assert group.get_value_for_one_based_page(5) is None
        assert group.get_global_value() is None
