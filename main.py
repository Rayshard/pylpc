from pylpc.parsers import *

if __name__ == '__main__':
    input = StringStream("Hello World!wassup")

    print(letters().parse(input))
    print(regex_lexeme(Regex(" ")).parse(input))
    print(letters().parse(input))
