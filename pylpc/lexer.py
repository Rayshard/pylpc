from dataclasses import dataclass
from typing import List, OrderedDict
from pylpc.parsers import Char, Longest, Map, Satisfy, Terminal
from pylpc.pylpc import ParseError, ParseResult, Parser, Location, Regex, StringStream

def EOS_PATTERN_ID():
    return "<EOS>"

def UNKNOWN_PATTERN_ID():
    return "<UNKNOWN>"

@dataclass(frozen=True)
class Pattern:
    id : str
    regex : Regex

@dataclass(frozen=True)
class Token:
    id : str
    text : str

def Lexer(patterns: List[Pattern]) -> Parser[Token]:
    parsers = OrderedDict[str, Parser[Token]]()
    
    def eos_function(loc: Location, stream: StringStream) -> ParseResult[Token]:
        if stream.is_eos():
            return ParseResult(loc, Token(EOS_PATTERN_ID(), ""))

        raise ParseError.expectation(f"'{EOS_PATTERN_ID()}'", f"'{stream.peek()}'", loc)

    parsers[EOS_PATTERN_ID()] = Parser(eos_function)

    for pattern in patterns:
        if pattern.id in parsers:
            raise ValueError(f"Pattern already exists with id: {pattern.id}")

        def pattern_parser(pattern: Pattern) -> Parser[Token]:
            return Map(Terminal(pattern.regex), lambda result: Token(pattern.id, result.value))

        parsers[pattern.id] = pattern_parser(pattern)

    parsers[UNKNOWN_PATTERN_ID()] = Map(Char(), lambda result: Token(UNKNOWN_PATTERN_ID(), result.value)) 

    longest = Longest(list(parsers.values()))
    pattern_ids = {idx: id for idx, id in enumerate(parsers)}
    token_idxs = {id: idx for idx, id in pattern_ids.items()}

    def function(loc: Location, stream: StringStream) -> ParseResult[Token]:
        token = stream.get_token()
            
        if token is None:
            result = longest.parse(stream)
            token = stream.set_token(result.location.position, len(result.value.text), token_idxs[result.value.id])
        
        return ParseResult(token.location, Token(pattern_ids[token.id], token.value))

    return Parser(function)

def Lexeme(lexer: Parser[Token], id: str) -> Parser[str]:
    def predicate(result: ParseResult[Token]) -> bool:
        return result.value.id == id

    def on_fail(result: ParseResult[Token]) -> ParseError:
        return ParseError.expectation(f"'{id}'", f"'{result.value.id}" + (f": {result.value.text}" if len(result.value.text) != 0 else "") + "'", result.location)

    return Map(Satisfy(lexer, predicate, on_fail), lambda result: result.value.text)

def EOSLexeme(lexer) -> Parser[str]:
    return Lexeme(lexer, EOS_PATTERN_ID())

def UnknownLexeme(lexer) -> Parser[str]:
    return Lexeme(lexer, UNKNOWN_PATTERN_ID())