from pylpc import __version__
from pylpc.pylpc import *

def test_version():
    assert __version__ == '0.1.0'

def test_StringStream():
    ss : StringStream = StringStream("this\nis \n s\n\nstring  !")

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

    ss.ignore_chars(4)
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

    ss.ignore_chars(100)
    assert ss.get_offset() == len(ss.get_data(0, None))
    assert ss.is_eos()
