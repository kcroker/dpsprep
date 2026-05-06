import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

from dpsprep.exceptions import DpsPrepConfigError


T = TypeVar('T')


@dataclass(frozen=True)
class RangeOption(Generic[T]):
    """A value with a range of one-based pages attached.

    Args:
        value: The value of the range.
        start: Either a positive integer or None.

            The special value None indicates that the range is unbounded from below.

        end: Either a positive integer or None.

            The special value None indicates that the range is unbounded from above.

    """
    value: T
    start: int | None = None
    end: int | None = None

    def matches_one_based_page(self, page_number: int) -> bool:
        if self.start is not None and self.end is not None:
            return self.start <= page_number <= self.end

        if self.start is not None:
            return page_number >= self.start

        if self.end is not None:
            return page_number <= self.end

        return True


@dataclass(frozen=True)
class RangeOptionGroup(Generic[T]):
    ranges: Sequence[RangeOption[T]]

    def get_value_for_one_based_page(self, page_number: int) -> T | None:
        for range_ in self.ranges:
            if range_.matches_one_based_page(page_number):
                return range_.value

        return None

    def get_value_for_zero_based_page(self, i: int) -> T | None:
        return self.get_value_for_one_based_page(i + 1)

    def get_global_value(self) -> T | None:
        if len(self.ranges) == 1 and self.ranges[0].start == self.ranges[0].end is None:
            return self.ranges[0].value

        return None


def parse_str_range_option(string: str) -> RangeOption[str]:
    match = re.match(r'(?P<value>[^\[]+)\[(?P<start>\d+)(-(?P<end>(\d+|end)))?\](?P<tail>.+)?', string)

    if match is None:
        if '[' in string:
            raise DpsPrepConfigError(f'Incomplete range option {string}')

        return RangeOption(string)

    groups = match.groupdict()

    if groups.get('tail'):
        raise DpsPrepConfigError(f'Unexpected content after range in option {string}')

    value: Any

    value = groups['value']
    start = int(groups['start']) if groups.get('start') else None

    if end_str := groups.get('end'):
        try:
            end = int(end_str)
        except ValueError:
            end = None
    else:
        end = start

    if start is None and end is None:
        return RangeOption(value)

    return RangeOption(value, start, end)


def parse_int_range_option(string: str) -> RangeOption[int]:
    str_range = parse_str_range_option(string)

    try:
        return RangeOption[int](int(str_range.value), str_range.start, str_range.end)
    except ValueError:
        raise DpsPrepConfigError(f'Expected the value of the range option {string} to be an integer') from None

