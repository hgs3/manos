#  Manos
#  Copyright (C) 2023-2024, Henry Stratmann III
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License version 3 as
#  published by the Free Software Foundation.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.

from manos.sentence import segment

def test_suppressions_through_string() -> None:
    assert segment('Tall Mr. Thomspon was from the U.S.A. specifically N.Y. City.') == [
        'Tall Mr. Thomspon was from the U.S.A. specifically N.Y. City.',
    ]

def test_suppression_at_end() -> None:
    assert segment('Good day Mr.') == [
        'Good day Mr.',
    ]

def test_suppressions_back_to_back() -> None:
    assert segment('Their title is Hon.B.A. Ph.D. Lt.Cdr. Maximilian the third.') == [
        'Their title is Hon.B.A. Ph.D. Lt.Cdr. Maximilian the third.',
    ]

def test_suppression_at_beginning() -> None:
    assert segment("Jan. is gone, but Mar. is close by!") == [
        "Jan. is gone, but Mar. is close by!",
    ]

def test_suppresions_are_case_sensative() -> None:
    assert segment("JAN. is gone, but MAR. is close by!") == [
        "JAN.",
        "is gone, but MAR.",
        "is close by!",
    ]

def test_double_quotes_after_terminator() -> None:
    assert segment('The quick brown. "Fox jumps over?" The lazy dog!') == [
        'The quick brown.',
        '"Fox jumps over?"',
        'The lazy dog!',
    ]

def test_line_quotes_after_terminator() -> None:
    assert segment("I can't enter.' Dairy day.") == [
        "I can't enter.'",
        'Dairy day.',
    ]

def test_multiple_double_quotes_after_terminator() -> None:
    assert segment('"""The roaring fire.""" Remains bright.') == [
        '"""The roaring fire."""',
        'Remains bright.',
    ]

def test_ellipsis_and_clause() -> None:
    assert segment('Nothing remained...but to go home.') == [
        'Nothing remained...but to go home.',
    ]

def test_ellipsis_and_space_and_clause() -> None:
    assert segment('Nothing remained... but to go home.') == [
        'Nothing remained...',
        'but to go home.',
    ]

def test_ellipsis_and_capital_clause() -> None:
    assert segment('Nothing remained...But to go home.') == [
        'Nothing remained...But to go home.',
    ]

def test_ellipsis_and_space_and_capital_clause() -> None:
    assert segment('Nothing remained... But to go home.') == [
        'Nothing remained...',
        'But to go home.',
    ]
