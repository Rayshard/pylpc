from pylpc.parsers import *
from pylpc.lexer import *

if __name__ == '__main__':
    input = StringStream("Hello letWorld!wassup", "MyStream")

    lexer = Lexer([
        Pattern("WS", Regex("[\\s]+")),
        Pattern("LET", Regex("let")),
        Pattern("ID", Regex("[a-zA-Z_]+")),
    ])

    while True:
         
        try:
            result = lexer.parse(input)
            Digits().parse(input)
            print(result)
            if result.value.id == EOS_PATTERN_ID():
                break

        except ParseError as e:
            print(e.get_message_with_trace())
            break

    # print(letters().parse(input))
    # print(regex_lexeme(Regex(" ")).parse(input))
    # print(letters().parse(input))
