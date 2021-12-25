from .pylpc import *

def lexer_lexeme(lexer: Lexer, id: Lexer.PatternID, ignores: Optional[Set[Lexer.PatternID]] = None, value: Optional[str] = None) -> Parser[str]:
    raise NotADirectoryError()

def regex_lexeme(regex: Regex, value: Optional[str] = None) -> Parser[str]:
    def function(pos: Position, stream: StringStream) -> ParseResult[str]:
        regex_match : Optional[re.Match] = regex.match(stream.get_data(stream.get_offset()))

        if regex_match is None:
            raise ParseError(pos, f"No match found for regular expression: {regex.get_pattern()}")
                
        string = regex_match[0]

        if value is not None and string != value:
            raise ParseError.expectation(f"'{value}'", f"'{string}'", pos)

        stream.ignore_chars(len(string))
        return ParseResult[str](pos, string)

    return Parser[str](function)

def character(value: Optional[char] = None) -> Parser[char]:
    return regex_lexeme(Regex("[\\S\\s]"), value)

def characters(value: Optional[str] = None) -> Parser[str]:
    return regex_lexeme(Regex("[\\S\\s]+"), value)

def letter(value: Optional[char] = None) -> Parser[char]:
    return regex_lexeme(Regex("[a-zA-Z]"), value)

def letters(value: Optional[str] = None) -> Parser[str]:
    return regex_lexeme(Regex("[a-zA-Z]+"), value)

def digit(value: Optional[char] = None) -> Parser[char]:
    return regex_lexeme(Regex("[0-9]"), value)

def digits(value: Optional[str] = None) -> Parser[str]:
    return regex_lexeme(Regex("[0-9]+"), value)

def alpha_num(value: Optional[char] = None) -> Parser[char]:
    return regex_lexeme(Regex("[a-zA-Z]"), value)

def alpha_nums(value: Optional[str] = None) -> Parser[str]:
    return regex_lexeme(Regex("[a-zA-Z]+"), value)

def whitespace(value: Optional[char] = None) -> Parser[char]:
    return regex_lexeme(Regex("[\\s]"), value)

def whitespaces(value: Optional[str] = None) -> Parser[str]:
    return regex_lexeme(Regex("[\\s]+"), value)

def eos() -> Parser[None]:
    def function(pos: Position, stream: StringStream) -> ParseResult[None]:
        if stream.is_eos():
            raise ParseError.expectation(f"'{Lexer.EOS_PATTERN_ID()}'", f"'{stream.peek()}'", pos)

        return ParseResult[None](pos, None)

    return Parser[None](function)

def error(message: str) -> Parser[None]:
    def function(pos: Position, stream: StringStream) -> ParseResult[None]:
        raise ParseError(pos, message)

    return Parser[None](function)