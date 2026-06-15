import enum
import sys
from collections.abc import Iterable
from typing import Generic, TypeVar


if sys.version_info < (3, 12):
    from typing_extensions import override
else:
    from typing import override

from dpsprep.exceptions import DpsPrepParseError

from .range_option import RangeOption, RangeOptionGroup


T = TypeVar('T')
EnumT = TypeVar('EnumT', bound=enum.Enum)


class RangeOptionParser(Generic[T]):
    def __init__(self, source: str) -> None:
        self.source = source
        self.index = 0

    def peek(self) -> str | None:
        try:
            return self.source[self.index]
        except IndexError:
            return None

    def peek_multiple(self, count: int) -> str:
        return self.source[self.index: self.index + count]

    def advance(self, count: int = 1) -> None:
        self.index += count

    def get_position_message(self) -> str:
        if self.index == 0:
            return 'at position 0'

        return f'after {self.source[:self.index]!r}'


    def create_unexpected_end_error(self) -> DpsPrepParseError:
        if self.source == '':
            return DpsPrepParseError('Empty input')

        return DpsPrepParseError(f'Unexpected end of input {self.get_position_message()}')

    def parse_option(self) -> T:
        raise NotImplementedError

    def parse_int(self) -> int:
        head = self.peek()

        if head is None:
            raise self.create_unexpected_end_error()

        if not head.isdigit():
            raise DpsPrepParseError(f'Expected an integer {self.get_position_message()}')

        i_match_start = self.index

        while (head := self.peek()) and head.isdigit():
            self.advance()

        return int(self.source[i_match_start:self.index])

    def iter_range_options(self) -> Iterable[RangeOption[T]]:
        """Iterate RangeOption instances from opt[...]."""
        option = self.parse_option()

        if self.peek() != '[':
            yield RangeOption(option)
            return

        self.advance()

        if self.peek() is None:
            raise self.create_unexpected_end_error()

        while self.peek():
            start = self.parse_int()
            end: int | None = start

            head = self.peek()

            if head == '-':
                self.advance()
                if self.peek_multiple(3) == 'end':
                    self.advance(3)
                    end = None
                else:
                    end = self.parse_int()

            match head := self.peek():
                case ',':
                    self.advance()
                    yield RangeOption(option, start, end)

                case ']':
                    self.advance()
                    yield RangeOption(option, start, end)
                    return

                case None:
                    raise self.create_unexpected_end_error()

                case _:
                    raise DpsPrepParseError(f'Unexpected symbol {head!r} {self.get_position_message()}')

    def iter_range_option_group(self) -> Iterable[RangeOption[T]]:
        """Iterate RangeOption instances from opt[...],opt[...]."""
        if not self.peek():
            raise self.create_unexpected_end_error()

        while self.peek():
            yield from self.iter_range_options()

            match head := self.peek():
                case ',':
                    self.advance()

                case None:
                    return

                case _:
                    raise DpsPrepParseError(f'Unexpected symbol {head!r} {self.get_position_message()}')

    def parse_range_option_group(self) -> RangeOptionGroup[T]:
        range_options = list(self.iter_range_option_group())

        if head := self.peek():
            raise self.create_unexpected_end_error()
            raise DpsPrepParseError(f'Unexpected symbol {head!r} {self.get_position_message()}')

        return RangeOptionGroup(range_options)


class EnumRangeOptionParser(RangeOptionParser[EnumT]):
    enum: type[EnumT]

    def __init__(self, source: str, enum: type[EnumT]) -> None:
        self.enum = enum
        super().__init__(source)

    @override
    def parse_option(self) -> EnumT:
        head = self.peek()

        if head is None:
            raise self.create_unexpected_end_error()

        for member in self.enum:
            if self.source.startswith(member.value, self.index):
                self.advance(len(member.value))
                return member

        raise DpsPrepParseError(f'Expected a supported option {self.get_position_message()}')


def parse_enum_range_group(string: str, enum: type[EnumT]) -> RangeOptionGroup[EnumT]:
    return EnumRangeOptionParser(string, enum).parse_range_option_group()


class IntRangeOptionParser(RangeOptionParser[int]):
    @override
    def parse_option(self) -> int:
        return self.parse_int()


def parse_int_range_group(string: str) -> RangeOptionGroup[int]:
    return IntRangeOptionParser(string).parse_range_option_group()
