# -*- coding: utf-8 -*-
#######################################################################
# Name: test_error_reporting
# Purpose: Test error reporting for various cases.
# Author: Igor R. Dejanović <igor DOT dejanovic AT gmail DOT com>
# Copyright: (c) 2015 Igor R. Dejanović <igor DOT dejanovic AT gmail DOT com>
# License: MIT License
#######################################################################
from __future__ import unicode_literals
import pytest

from arpeggio import Optional, Not, ParserPython, NoMatch, EOF
from arpeggio import RegExMatch as _


def test_minimal_error():
    """
    Most basic test to ensure that an unmatched string is reported.
    """
    def grammar():
        return 'abc'

    parser = ParserPython(grammar)

    with pytest.raises(NoMatch) as e:
        parser.parse('xyz')
    assert "Expected 'abc' at position (1, 1) => '*xyz'." == str(e.value)
    assert (e.value.line, e.value.col) == (1, 1)


def test_non_optional_precedence_1():
    """
    Test that all tried match at position are reported.
    """
    def grammar():
        return Optional('a'), 'b'

    parser = ParserPython(grammar)

    with pytest.raises(NoMatch) as e:
        parser.parse('c')
    assert "'a' or 'b' at position (1, 1)" in str(e.value)
    assert (e.value.line, e.value.col) == (1, 1)


def test_non_optional_precedence_2():
    """
    Test that all tried match at position are reported.
    """

    def grammar():
        return ['b', Optional('a')]

    parser = ParserPython(grammar)

    with pytest.raises(NoMatch) as e:
        parser.parse('c')

    assert "Expected 'b' or 'a' at position (1, 1)" in str(e.value)
    assert (e.value.line, e.value.col) == (1, 1)


def test_optional_with_better_match():
    """
    Test that optional match that has gone further in the input stream
    has precedence over non-optional.
    """

    def grammar():  return [first, Optional(second)]
    def first():    return 'one', 'two', 'three', '4'
    def second():   return 'one', 'two', 'three', 'four', 'five'

    parser = ParserPython(grammar)

    with pytest.raises(NoMatch) as e:
        parser.parse('one two three four 5')

    # The reporting capability has degraded because we are printing the whole
    # failed expression but an optimization is possible within the parsing code
    # of Sequence.
    #     assert "Expected 'five'" in str(e.value)
    #     assert (e.value.line, e.value.col) == (1, 20)
    # WIP: TODO: FULL STRING MATCH
    assert (
       "Expected '4' at position (1, 15)"
       " or "
       "'five' at position (1, 20)" in str(e.value)
    )
    assert (e.value.line, e.value.col) == (1, 15)


def test_alternative_added():
    """
    Test that matches from alternative branches at the same positiona are
    reported.
    """

    def grammar():
        return ['one', 'two'], _(r'\w+')

    parser = ParserPython(grammar)

    with pytest.raises(NoMatch) as e:
        parser.parse('   three ident')
    assert "Expected 'one' or 'two'" in str(e.value)

    assert (e.value.line, e.value.col) == (1, 4)


def test_file_name_reporting():
    """
    Test that if parser has file name set it will be reported.
    """

    def grammar():      return Optional('a'), 'b', EOF

    parser = ParserPython(grammar)

    with pytest.raises(NoMatch) as e:
        parser.parse("\n\n   a c", file_name="test_file.peg")
    # WIP: Repetition of "at position"
    assert "Expected 'b' at position (3, 6) at position test_file.peg:(3, 6)" in str(e.value)
    assert (e.value.line, e.value.col) == (3, 6)


def test_comment_matching_not_reported():
    """
    Test that matching of comments is not reported.
    """

    def grammar():      return Optional('a'), 'b', EOF
    def comments():     return _(r'//.*$')

    parser = ParserPython(grammar, comments)

    with pytest.raises(NoMatch) as e:
        parser.parse('\n\n a // This is a comment \n c')
    assert "Expected 'b' at position (4, 2) at position (4, 2)" in str(e.value)
    assert (e.value.line, e.value.col) == (4, 2)


def test_not_basic_match():
    def grammar():
        return Not("bar"), "foo"

    parser = ParserPython(grammar, skipws=False)

    with pytest.raises(NoMatch) as e:
        _ = parser.parse('bar')

    assert "Expected not('bar') at position (1, 1)" in str(e.value)


def test_not_match_at_beginning():
    """
    Test that matching of Not ParsingExpression is not reported in the
    error message.
    """

    def grammar():
        return Not('one'), _(r'\w+')

    parser = ParserPython(grammar)

    with pytest.raises(NoMatch) as e:
        parser.parse('   one ident')
    assert (
        "Expected not('one') at position (1, 4) at position (1, 4)"
        in str(e.value)
    )


def test_not_match_as_alternative():
    """
    # ##########################################################################
    # WIP: We have doubts about this behavior. To our understanding,
    # the parsing of OrderedChoice should not throw.
    # ##########################################################################
    Test that Not is not reported if a part of OrderedChoice.
    """

    def grammar():
        return ['one', Not('two')], _(r'\w+')

    parser = ParserPython(grammar)

    with pytest.raises(NoMatch) as e:
        parser.parse('   three ident')
    assert "Expected 'one' at position (1, 4) at position (1, 4)" in str(e.value)


def test_sequence_of_nots():
    """
    Test that sequence of Not rules is handled properly.
    """

    def grammar():
        return Not('one'), Not('two'), _(r'\w+')

    parser = ParserPython(grammar)

    with pytest.raises(NoMatch) as e:
        parser.parse('   two ident')
    assert "Expected not('two') at position (1, 4) at position (1, 4)" in str(e.value)


def test_compound_not_match():
    """
    Test a more complex Not match error reporting.
    """
    def grammar():
        return [Not(['two', 'three']), 'one', 'two'], _(r'\w+')

    parser = ParserPython(grammar)

    with pytest.raises(NoMatch) as e:
        parser.parse('   three ident')
    assert (
        "Expected not(('two' OR 'three')) or 'one' or 'two' "
        "at position (1, 4) at position (1, 4)"
    ) in str(e.value)

    with pytest.raises(NoMatch) as e:
        parser.parse('   four ident')
    assert "Expected 'one' or 'two' at position (1, 4) at position (1, 4)" in str(e.value)
