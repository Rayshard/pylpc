from dataclasses import dataclass
from typing import Callable, Dict, Generic, List, Optional, TypeAlias, TypeVar
import re

char = str
EOF : char = ''

@dataclass
class Position:
    line : int
    column : int

    def __str__(self) -> str:
        return f"({self.line}, {self.column})"

class Regex:
    def __init__(self, pattern: str = "") -> None:
        self.__pattern : str = pattern
        self.__regex : re.Pattern = re.compile(f"^({self.__pattern})")

    def match(self, string: str) -> Optional[re.Match]:
        return self.__regex.search(string)

    def get_pattern(self) -> str:
        return self.__pattern

class StringStream:
    TokenID : TypeAlias = int

    @dataclass(frozen=True)
    class Token:
        id : 'StringStream.TokenID'
        position : Position  
        value : str

    def __init__(self, data: str, name: Optional[str] = None) -> None:
        self.__name : str = "" if name is None else name
        self.__data : str = data
        self.__offset : int = 0
        self.__tokens : Dict[int, StringStream.Token] = {}
        self.__line_starts : List[int] = [0]

        for i, c in enumerate(data):
            if c == '\n':
                self.__line_starts.append(i + 1)

    def get(self) -> char:
        if self.is_eos():
            return EOF
        else:
            c : char = self.__data[self.__offset]
            self.__offset += 1
            return c

    def peek(self) -> char:
        init_offset : int = self.__offset
        peeked : char = self.get()
        self.__offset = init_offset
        return peeked

    def ignore(self, amt: int) -> None:
        assert amt >= 0
        self.__offset = min(len(self.__data), self.__offset + amt)

    def get_token(self) -> Optional[Token]:
        token = self.__tokens.get(self.__offset)
        
        if token is not None:
            self.ignore(len(token.value))

        return token

    def peek_token(self) -> Optional[Token]:
        return self.__tokens.get(self.__offset)

    def set_token(self, position: Position, length: int, id: TokenID) -> Token:
        offset = self.get_offset_from_pos(position)
        token = StringStream.Token(id, position, self.get_data(offset, length))

        self.__tokens[offset] = token
        return token

    def clear_tokens(self) -> None:
        self.__tokens.clear()

    def get_name(self) -> str:
        return self.__name

    def get_offset(self) -> int:
        return self.__offset

    def get_offset_from_pos(self, pos: Position) -> int:
        assert pos.line >= 1 and pos.column >= 1

        if pos.line > len(self.__line_starts) or pos.line == 0 or pos.column == 0:
            raise Exception("Invalid position: " + str(pos))

        line_start : int = self.__line_starts[pos.line - 1]
        line_width : int = (len(self.__data) if pos.line == len(self.__line_starts) else self.__line_starts[pos.line]) - line_start

        if pos.column - 1 > line_width:
            raise Exception("Invalid position: " + str(pos))

        return line_start + pos.column - 1

    def get_position(self) -> Position:
        return self.get_position_from_offset(self.__offset)

    def get_position_from_offset(self, offset: int) -> Position:
        assert offset >= 0

        if offset > len(self.__data):
            raise Exception("Offset is out of range of data!")

        line : int = 0
        closest_line_start : int = 0

        for line_start in self.__line_starts:
            if line_start > offset:
                break

            closest_line_start = line_start
            line += 1

        return Position(line, offset - closest_line_start + 1)

    def set_offset(self, offset: int) -> None:
        assert offset >= 0
        self.__offset = min(offset, len(self.__data))

    def set_position(self, pos: Position) -> None:
        assert pos.line >= 1 and pos.column >= 1
        self.set_offset(self.get_offset_from_pos(pos))

    def get_data(self, start: int = 0, length: Optional[int] = None) -> str:
        assert start >= 0 and (length is None or length >= 0)
        
        if length is None:
            length = len(self.__data) - start

        if start + length > len(self.__data):
            raise Exception("Parameters out of range of data!")

        return self.__data[start:start + length]

    def is_eos(self) -> bool:
        return self.__offset >= len(self.__data)

class ParseError(Exception):
    def __init__(self, pos: Position = Position(1, 1), msg: str = "", trace: Optional[List['ParseError']] = None) -> None:
        super().__init__(f"Error @ {pos}: {msg}")
        
        self.__position : Position = pos
        self.__message : str = msg
        self.__trace : List[ParseError] = [] if trace is None else list(trace)
        
    def get_position(self) -> Position:
        return self.__position

    def get_message(self) -> str:
        return self.__message

    def get_trace(self) -> List['ParseError']:
        return self.__trace

    def get_message_with_trace(self) -> str:
        trace_message : str = ""

        for e in self.__trace:
            trace_message += "\n\t" + e.get_message_with_trace().replace("\n", "\n\t")

        return str(self) + trace_message

    @staticmethod
    def create(e1: 'ParseError', e2: 'ParseError') -> 'ParseError':
        return ParseError(e1.__position, e1.__message, e1.__trace + [e2])

    @staticmethod
    def expectation(expected: str, found: str, pos: Position) -> 'ParseError':
        return ParseError()

T = TypeVar('T')

@dataclass
class ParseResult(Generic[T]):
    position : Position
    value : T

class Parser(Generic[T]):
    def __init__(self, parsable: Callable[[Position, StringStream], ParseResult[T]]) -> None:
        super().__init__()

        self.__function : Callable[[Position, StringStream], ParseResult[T]] = lambda position, stream: parsable(position, stream)

    def parse(self, input: StringStream | str) -> ParseResult[T]:
        stream = input if isinstance(input, StringStream) else StringStream(input)
        stream_start : int = stream.get_offset()

        try:
            return self.__function(stream.get_position(), stream)
        except ParseError as e:
            stream.set_offset(stream_start)
            raise e
