from collections.abc import Sequence
from dataclasses import dataclass
from typing import Generic, TypeVar


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

    def __or__(self, other: object) -> 'RangeOptionGroup':
        if not isinstance(other, RangeOptionGroup):
            return NotImplemented

        return RangeOptionGroup([*self.ranges, *other.ranges])
