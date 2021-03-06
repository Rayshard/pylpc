import re
from typing import Any, Callable, Generic, List, Optional, Tuple, TypeVar, Union, cast

from pylpc.pylpc import T, Location, char, ParseError, ParseResult, Parser, Regex, StringStream

T1 = TypeVar("T1")
T2 = TypeVar("T2")
T3 = TypeVar("T3")
T4 = TypeVar("T4")
T5 = TypeVar("T5")

def Map(parser: Parser[T], func: Callable[[ParseResult[T]], T1]) -> Parser[T1]:
    def function(loc: Location, stream: StringStream) -> ParseResult[T1]:
        result = parser.parse(stream)
        location = result.location

        return ParseResult[T1](location, func(result))

    return Parser[T1](function)

class Reference(Generic[T]):
    def __init__(self) -> None:
        self.__reference : List[List[Parser[T]]] = [[]]

    def set(self, parser: Parser[T]) -> None:
        self.__reference[0] = [parser]

    def __call__(self, loc: Location, stream: StringStream) -> ParseResult[T]:
        return self.__reference[0][0].parse(stream)

class TryValue(Generic[T]):
    def __init__(self, variant: Union[T, ParseError], is_success: bool) -> None:
        super().__init__()

        self.__variant = variant
        self.__is_success = is_success

    def IsSuccess(self) -> bool:
        return self.__is_success

    def IsError(self) -> bool:
        return not self.__is_success

    def ExtractSuccess(self) -> T:
        return cast(T, self.__variant)

    def ExtractError(self) -> ParseError:
        return cast(ParseError, self.__variant)

    @staticmethod
    def CreateSuccess(value: T) -> 'TryValue[T]':
        return TryValue[T](value, True)

    @staticmethod
    def CreateError(e: ParseError) -> 'TryValue[T]':
        return TryValue[T](e, False)

TryResult = ParseResult[TryValue[T]]    
TryParser = Parser[TryValue[T]]

def Try(parser: Parser[T]) -> TryParser[T]:
    def function(loc: Location, stream: StringStream) -> TryResult[T]:
        try:
            result = parser.parse(stream)
            return TryResult(result.location, TryValue.CreateSuccess(result.value))
        except ParseError as e:
            return TryResult(e.get_location(), TryValue.CreateError(e))

    return TryParser[T](function)

CountValue = list[ParseResult[T]]
CountResult = ParseResult[CountValue[T]]    
CountParser = Parser[CountValue[T]]

def Count(parser: Parser[T], min: int, max: Optional[int]) -> CountParser[T]:
    if min < 0:
        raise ValueError("min must be non-negative")
    elif max is not None:
        if max < 0:
            raise ValueError("max must be non-negative")
        if max < min:
            raise ValueError(f"max must be at least min: {max} < {min}")

    def function(loc: Location, stream: StringStream) -> CountResult[T]:
        results = CountValue[T]()

        while max is None or len(results) < max:
            try:
                results.append(parser.parse(stream))
            except ParseError as e:
                if len(results) >= min:
                    break

                error = ParseError.expectation(f"at least {min}", f"only {len(results)}", Location(stream.get_name(), stream.get_position()))
                raise ParseError.combine(e, error)

        return CountResult[T](loc if len(results) == 0 else results[0].location, results)

    return CountParser[T](function)

def ManyOrOne(parser: Parser[T]) -> CountParser[T]:
    return Count(parser, 1, None)

def ZeroOrOne(parser: Parser[T]) -> CountParser[T]:
    return Count(parser, 0, 1)

def ZeroOrMore(parser: Parser[T]) -> CountParser[T]:
    return Count(parser, 0, None)

def Exactly(parser: Parser[T], n: int) -> CountParser[T]:
    return Count(parser, n, n)

SeqValue = tuple[ParseResult[Any], ...]
SeqResult = ParseResult[SeqValue]    
SeqParser = Parser[SeqValue]

def Seq(*parsers: Parser[Any]) -> SeqParser:
    def function(loc: Location, stream: StringStream) -> SeqResult:
        results = SeqValue([parser.parse(stream) for parser in parsers])
        return SeqResult(loc if len(results) == 0 else results[0].location, results)

    return SeqParser(function)

Seq2Parser = Parser[Tuple[ParseResult[T1], ParseResult[T2]]]
def Seq2(p1: Parser[T1], p2: Parser[T2]) -> Seq2Parser[T1, T2]:
    return cast(Seq2Parser, Seq(p1, p2))

Seq3Parser = Parser[Tuple[ParseResult[T1], ParseResult[T2], ParseResult[T3]]]
def Seq3(p1: Parser[T1], p2: Parser[T2], p3: Parser[T3]) -> Seq3Parser[T1, T2, T3]:
    return cast(Seq3Parser, Seq(p1, p2, p3))

Seq4Parser = Parser[Tuple[ParseResult[T1], ParseResult[T2], ParseResult[T3], ParseResult[T4]]]
def Seq4(p1: Parser[T1], p2: Parser[T2], p3: Parser[T3], p4: Parser[T4]) -> Seq4Parser[T1, T2, T3, T4]:
    return cast(Seq4Parser, Seq(p1, p2, p3, p4))

Seq5Parser = Parser[Tuple[ParseResult[T1], ParseResult[T2], ParseResult[T3], ParseResult[T4], ParseResult[T5]]]
def Seq5(p1: Parser[T1], p2: Parser[T2], p3: Parser[T3], p4: Parser[T4], p5: Parser[T5]) -> Seq5Parser[T1, T2, T3, T4, T5]:
    return cast(Seq5Parser, Seq(p1, p2, p3, p4, p5))

class MaybeValue(Generic[T]):
    def __init__(self, variant: Optional[T], is_success: bool) -> None:
        super().__init__()

        self.__variant = variant
        self.__is_success = is_success

    def IsSuccess(self) -> bool:
        return self.__is_success

    def ExtractSuccess(self) -> T:
        return cast(T, self.__variant)

    @staticmethod
    def CreateSome(value: T) -> 'MaybeValue[T]':
        return MaybeValue[T](value, True)

    @staticmethod
    def CreateNone() -> 'MaybeValue[T]':
        return MaybeValue[T](None, False)

MaybeResult = ParseResult[MaybeValue[T]]    
MaybeParser = Parser[MaybeValue[T]]

def Maybe(parser: Parser[T]) -> MaybeParser[T]:
    def function(loc: Location, stream: StringStream) -> MaybeResult[T]:
        try:
            result = parser.parse(stream)
            return MaybeResult(result.location, MaybeValue.CreateSome(result.value))
        except ParseError as e:
            return MaybeResult(e.get_location(), MaybeValue.CreateNone())

    return MaybeParser[T](function)

def Longest(parsers: List[Parser[T]]) -> Parser[T]:
    def function(loc: Location, stream: StringStream) -> ParseResult[T]:
        stream_start, greatest_length = stream.get_offset(), 0
        result : Optional[ParseResult[T]] = None
        errors : List[ParseError] = []

        for parser in parsers:
            try:
                parse_result = parser.parse(stream)
                length = stream.get_offset() - stream_start

                if result is None or length > greatest_length:
                    result = parse_result
                    greatest_length = length
                    errors.clear() # We put this here to save memory
            except ParseError as e:
                if result is None:
                    e_length = stream.get_offset_from_pos(e.get_location().position)
                    errors_length = 0 if len(errors) == 0 else stream.get_offset_from_pos(errors[0].get_location().position)

                    if e_length == errors_length:
                        errors.append(e)
                    elif e_length > errors_length:
                        errors = [e]

            stream.set_offset(stream_start)

        if result is None:
            raise errors.pop() if len(errors) == 1 else ParseError(loc, "No option parsed!", errors)

        stream.set_offset(stream_start + greatest_length)
        return result

    return Parser(function)

def FirstSuccess(parsers: List[Parser[T]]) -> Parser[T]:
    def function(loc: Location, stream: StringStream) -> ParseResult[T]:
        stream_start, greatest_length = stream.get_offset(), 0
        errors : List[ParseError] = []

        for parser in parsers:
            try:
                return parser.parse(stream)
            except ParseError as e:
                e_length = stream.get_offset_from_pos(e.get_location().position)
                errors_length = 0 if len(errors) == 0 else stream.get_offset_from_pos(errors[0].get_location().position)

                if e_length == errors_length:
                    errors.append(e)
                elif e_length > errors_length:
                    errors = [e]

            stream.set_offset(stream_start)

        raise errors.pop() if len(errors) == 1 else ParseError(loc, "No option parsed!", errors)

    return Parser(function)

def Named(name: str, parser: Parser[T]) -> Parser[T]:
    def function(loc: Location, stream: StringStream) -> ParseResult[T]:
        try:
            return parser.parse(stream)
        except ParseError as e:
            raise ParseError.combine(ParseError(e.get_location(), f"Unable to parse {name}"), e)

    return Parser(function)

def Prefixed(prefix: Parser[T1], parser: Parser[T2]) -> Parser[T2]:
    return prefix >> parser

def Suffixed(parser: Parser[T1], suffix: Parser[T2]) -> Parser[T1]:
    return parser << suffix

def Between(prefix: Parser[T1], parser: Parser[T], suffix: Parser[T2]) -> Parser[T]:
    return Suffixed(Prefixed(prefix, parser), suffix)

def Value(value: T) -> Parser[T]:
    def function(loc: Location, stream: StringStream) -> ParseResult[T]:
        return ParseResult(loc, value)

    return Parser(function)

def Separate() -> Parser[T]:
    raise NotImplementedError()

def Fold() -> Parser[T]:
    raise NotImplementedError()

def LookAhead() -> Parser[T]:
    raise NotImplementedError()

def Chain() -> Parser[T]:
    raise NotImplementedError()

def Satisfy(parser: Parser[T], predicate: Callable[[ParseResult[T]], bool]) -> Parser[T]:
    def function(loc: Location, stream: StringStream) -> ParseResult[T]:
        result = parser.parse(stream)

        if predicate(result):
            return result
        else:
            raise ParseError(result.location, "Predicate not satisfied!")

    return Parser(function)

def Success(parser: Parser, default: T) -> Parser[T]:
    def function(loc: Location, stream: StringStream) -> ParseResult[T]:
        try:
            return parser.parse(stream)
        except ParseError as e:
            return ParseResult(loc, default)

    return Parser(function)

def Failure(parser: Parser[T]) -> Parser[ParseError]:
    def function(loc: Location, stream: StringStream) -> ParseResult[ParseError]:
        error : Optional[ParseError] = None

        try:
            parser.parse(stream)
        except ParseError as e:
            error = e

        if error is None:
            raise ParseError(loc, "Unexpected Success")

        return ParseResult(loc, error)

    return Parser(function)

def Callback(parser: Parser[T], func: Callable[[ParseResult[T]], None]) -> Parser[T]:
    def function(loc: Location, stream: StringStream) -> ParseResult[T]:
        result = parser.parse(stream)
        
        func(result)
        return result

    return Parser(function)

def Terminal(regex: Regex, value: Optional[str] = None) -> Parser[str]:
    def function(loc: Location, stream: StringStream) -> ParseResult[str]:
        regex_match : Optional[re.Match] = regex.match(stream.get_data(stream.get_offset()))

        if regex_match is None:
            raise ParseError(loc, f"No match found for regular expression: {regex.get_pattern()}")
                
        string = regex_match[0]

        if value is not None and string != value:
            raise ParseError.expectation(f"'{value}'", f"'{string}'", loc)

        stream.ignore(len(string))
        return ParseResult(loc, string)

    return Parser(function)

def Char(value: Optional[char] = None) -> Parser[char]:
    return Terminal(Regex("[\\S\\s]"), value)

def Chars(value: Optional[str] = None) -> Parser[str]:
    return Terminal(Regex("[\\S\\s]+"), value)

def Letter(value: Optional[char] = None) -> Parser[char]:
    return Terminal(Regex("[a-zA-Z]"), value)

def Letters(value: Optional[str] = None) -> Parser[str]:
    return Terminal(Regex("[a-zA-Z]+"), value)

def Digit(value: Optional[char] = None) -> Parser[char]:
    return Terminal(Regex("[0-9]"), value)

def Digits(value: Optional[str] = None) -> Parser[str]:
    return Terminal(Regex("[0-9]+"), value)

def AlphaNum(value: Optional[char] = None) -> Parser[char]:
    return Terminal(Regex("[a-zA-Z0-9]"), value)

def AlphaNums(value: Optional[str] = None) -> Parser[str]:
    return Terminal(Regex("[a-zA-Z0-9]+"), value)

def Whitespace(value: Optional[char] = None) -> Parser[char]:
    return Terminal(Regex("[\\s]"), value)

def Whitespaces(value: Optional[str] = None) -> Parser[str]:
    return Terminal(Regex("[\\s]+"), value)

def EOS() -> Parser[None]:
    def function(loc: Location, stream: StringStream) -> ParseResult[None]:
        if not stream.is_eos():
            raise ParseError.expectation(f"EOS", f"'{stream.peek()}'", loc)

        return ParseResult(loc, None)

    return Parser(function)

def Error(message: str) -> Parser[None]:
    def function(loc: Location, stream: StringStream) -> ParseResult[None]:
        raise ParseError(loc, message)

    return Parser(function)
