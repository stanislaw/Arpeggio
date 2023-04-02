from arpeggio import ZeroOrMore, RegExMatch, StrMatch, EOF
from arpeggio import ParserPython


def test_suppressed_match_in_zero_or_more():
    """
    See: https://github.com/textX/Arpeggio/issues/98
    """

    class SuppressStrMatch(StrMatch):
        suppress = True

    newline = SuppressStrMatch('\n')

    def line():
        return RegExMatch(r'^.*$'), newline

    def grammar():
        return ZeroOrMore(line), EOF

    parser = ParserPython(grammar, skipws=False)
    result = parser.parse('one\nthree\nfour\n')
    # WIP: Cannot figure out yet why two newlines do not work.
    # result = parser.parse('one\n\nthree\nfour\n')

    assert result
