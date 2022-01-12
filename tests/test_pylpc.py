from pylpc import __version__
from pylpc.parsers import AlphaNums, Char, Chars, Count, Digits, FirstSuccess, Letter, Letters, Longest, Map, Maybe, Reference, Seq, Try, Value, Whitespaces
from pylpc.pylpc import Location, ParseError, ParseResult, Parser, char, Position, StringStream

def test_version():
    assert __version__ == '0.1.0'

def test_StringStream():
    ss = StringStream("this\nis \n s\n\nstring  !")

    assert ss.get_position() == Position(1, 1)
    assert ss.get_offset() == 0
    assert ss.get() == 't'
    assert ss.get_position() == Position(1, 2)
    assert ss.get_offset() == 1
    assert ss.get() == 'h'
    assert ss.get_position() == Position(1, 3)
    assert ss.get_offset() == 2
    assert not ss.is_eos()

    peek : char = ss.peek()
    assert peek == ss.get()
    assert ss.get_position() == Position(1, 4)
    assert ss.get_offset() == 3
    assert not ss.is_eos()

    ss.ignore(4)
    assert ss.get_position() == Position(2, 3)
    assert ss.get_offset() == 7
    assert ss.get() == ' '
    assert ss.get_position() == Position(2, 4)
    assert ss.get_offset() == 8
    assert not ss.is_eos()

    ss.set_offset(12)
    assert ss.get_offset() == 12
    assert ss.get_position() == Position(4, 1)
    assert not ss.is_eos()

    ss.set_position(Position(5, 3))
    assert ss.get_offset() == 15
    assert ss.get() == 'r'
    assert ss.get_offset() == 16
    assert not ss.is_eos()

    assert ss.get_offset_from_pos(Position(1, 1)) == 0
    assert ss.get_offset_from_pos(Position(1, 2)) == 1
    assert ss.get_offset_from_pos(Position(2, 1)) == 5
    assert ss.get_offset_from_pos(Position(5, 10)) == 22

    assert ss.get_data() == "this\nis \n s\n\nstring  !"
    assert ss.get_data(ss.get_offset()) == "ing  !"
    assert ss.get_data(3, 7) == "s\nis \n "

    ss.ignore(100)
    assert ss.get_offset() == len(ss.get_data(0, None))
    assert ss.is_eos()

    assert False # get_name
    assert False # get_token
    assert False # peek_token
    assert False # set_token
    assert False # clear_tokens

def test_Lexer():
    assert False

def test_Map():
    assert Map(Value(5), lambda input: 6).parse("").value == 6

def test_Reference():
    reference = Reference[char]()
    function = Parser(lambda loc, stream: Parser(reference).parse(stream))

    reference.set(Value('b'))
    assert function.parse("a").value == 'b'

    other = reference
    
    def other_func(loc: Location, stream: StringStream) -> ParseResult[char]:
        raise ParseError(loc, "Hiya")

    other.set(Parser(other_func))

    try:
        function.parse("a")
        assert False
    except ParseError as e:
        pass

def test_Try():
    expected_error = ParseError(Location("", Position(100, 250)), "The error!")

    def func(loc: Location, stream: StringStream) -> ParseResult[int]:
        if stream.peek() != 'q':
            raise expected_error

        return ParseResult(loc, 123)

    parser = Try(Parser(func))

    success = parser.parse("q").value
    assert success.IsSuccess() and success.ExtractSuccess() == 123

    error = parser.parse("a").value
    assert error.IsError() and error.ExtractError() == expected_error

def test_Count():
    def func(loc: Location, stream: StringStream) -> ParseResult[char]:
        if not stream.peek().isalpha():
            raise ParseError.expectation("a letter", f"'{stream.peek()}'", loc)

        return ParseResult(loc, stream.get())

    parser = Count(Parser(func), 1, 3)
    stream = StringStream("abcef g ")

    try:
        value = parser.parse(stream).value
        assert len(value) == 3
        assert value[0].location.position == Position(1, 1) and value[0].value == 'a'
        assert value[1].location.position == Position(1, 2) and value[1].value == 'b'
        assert value[2].location.position == Position(1, 3) and value[2].value == 'c'

        value = parser.parse(stream).value
        assert len(value) == 2
        assert value[0].location.position == Position(1, 4) and value[0].value == 'e'
        assert value[1].location.position == Position(1, 5) and value[1].value == 'f'

        try:
            parser.parse(stream)
            assert False
        except ParseError as e:
            stream.ignore(1)

        value = parser.parse(stream).value
        assert len(value) == 1
        assert value[0].location.position == Position(1, 7) and value[0].value == 'g'
    except ParseError as e:
        assert False

def test_ManyOrOne():
    pass #Derivateive of Count

def test_ZeroOrOne():
    pass #Derivateive of Count

def test_ZeroOrMore():
    pass #Derivateive of Count

def test_Exactly():
    pass #Derivateive of Count

def test_Seq():
    input = StringStream("abcde")
    r1, r2, r3, r4, r5 = Seq(Char('a'), Char('b'), Char('c'), Char('d'), Char('e')).parse(input).value

    assert r1.value == 'a'
    assert r2.value == 'b'
    assert r3.value == 'c'
    assert r4.value == 'd'
    assert r5.value == 'e'
    assert input.get_offset() == 5

def test_Maybe():
    input = StringStream("123abc abc 123abc")
    parser = Maybe(Digits())

    value = parser.parse(input).value
    assert value.IsSuccess() and value.ExtractSuccess() == "123"

    value = parser.parse(input).value
    assert not value.IsSuccess()

    assert input.get_offset() == 3

def test_Variant():
    assert False

def test_Longest():
    input = StringStream("123 abc 123abc")
    parser = Longest([Digits(), Letters(), Chars("123abc")])

    assert parser.parse(input).value == "123"
    input.ignore(1)
    assert parser.parse(input).value == "abc"
    input.ignore(1)
    assert parser.parse(input).value == "123abc"

def test_FirstSuccess():
    input = StringStream("123abc abc 123abc")

    assert FirstSuccess([Letters(), Digits(), AlphaNums()]).parse("123abc").value == "123"
    assert FirstSuccess([Letters(), AlphaNums(), Digits()]).parse("123abc").value == "123abc"
    assert FirstSuccess([Letters(), AlphaNums(), Digits()]).parse("qwe123abc").value == "qwe"

def test_Named():
    assert False

def test_ParserLShift():
    assert False

def test_ParserRShift():
    assert False

def test_Prefixed():
    pass # Derivative of ParserRShift

def test_Suffixed():
    pass # Derivative of ParserLShift

def test_Value():
    assert False

def test_Separate():
    assert False

def test_Fold():
    assert False

def test_LookAhead():
    assert False

def test_Between():
    assert False

def test_Chain():
    assert False

def test_BinopChain():
    assert False

def test_Satisfy():
    assert False

def test_Success():
    assert False

def test_Failure():
    assert False

def test_Callback():
    assert False

def test_Terminal():
    assert False

def test_Char():
    assert Char().parse("!&^").value == '!'

    try:
        Char('-').parse("!&^")
        assert False
    except ParseError as e:
        pass

def test_Chars():
    assert Chars().parse("!&^").value == '!&^'
    assert Chars("!&^").parse("!&^").value == '!&^'

    try:
        Char('!&^123abc').parse("!&^")
        assert False
    except ParseError as e:
        pass

def test_Letter():
    assert Letter().parse("test").value == 't'

    try:
        Letter().parse("123")
        assert False
    except ParseError as e:
        pass

    try:
        Letter('l').parse("test")
        assert False
    except ParseError as e:
        pass

def test_Letters():
    assert Letters().parse("abc123").value == 'abc'
    assert Letters("abc").parse("abc123").value == 'abc'

    try:
        Letters().parse("123")
        assert False
    except ParseError as e:
        pass

    try:
        Letters('cba').parse("abc")
        assert False
    except ParseError as e:
        pass

def test_Digit():
    assert False

def test_Digits():
    assert False

def test_AlphaNum():
    assert False

def test_AlphaNums():
    assert False

def test_Whitespace():
    assert False

def test_Whitespaces():
    assert False

def test_EOS():
    assert False

def test_Error():
    assert False