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

from typing import List

import re

# The FreeBSD manual page guidelines recommend placing sentences on their own lines.
# The Linux manual page guidelines agree but go further suggesting to use "semantic newlines" for long lines.
# Semantic newlines means splitting long lines at clause breaks (commas, semicolons, colons, and so on).
# The following function uses the Linux guidelines. The algorithm for detecting new lines is uses a
# heuristic based on the sentence break algorithm specified by Unicode® Technical Report #14.
def segment(text: str) -> List[str]:
    # Do not break on recognized acronyms.
    # The following list of acronyms is adapted from Unicode CLDR:
    # https://github.com/unicode-org/cldr/blob/e09d3737bd2aa9b441801cc3de00adb084226058/common/segments/en.xml
    def suppress(segment: str) -> bool:
        segment = segment.rstrip() # There might be trailing whitespace, e.g. "Mr. " instead of "Mr."
        SUPPRESSIONS = ["L.P.", "Alt.", "Approx.", "E.G.", "O.", "Maj.", "Misc.", "P.O.", "J.D.",
                        "Jam.", "Card.", "Dec.", "Sept.", "MR.", "Long.", "Hat.", "G.", "Link.",
                        "DC.", "D.C.", "M.T.", "Hz.", "Mrs.", "By.", "Act.", "Var.", "N.V.", "Aug.",
                        "B.", "S.A.", "Up.", "Job.", "Num.", "M.I.T.", "Ok.", "Org.", "Ex.", "Cont.",
                        "U.", "Mart.", "Fn.", "Abs.", "Lt.", "OK.", "Z.", "E.", "Kb.", "Est.", "A.M.",
                        "L.A.", "Prof.", "U.S.", "Nov.", "Ph.D.", "Mar.", "I.T.", "exec.", "Jan.", "N.Y.",
                        "X.", "Md.", "Op.", "vs.", "D.A.", "A.D.", "R.L.", "P.M.", "Or.", "M.R.", "Cap.",
                        "PC.", "Feb.", "Exec.", "I.e.", "Sep.", "Gb.", "K.", "U.S.C.", "Mt.", "S.", "A.S.",
                        "C.O.D.", "Capt.", "Col.", "In.", "C.F.", "Adj.", "AD.", "I.D.", "Mgr.", "R.T.",
                        "B.V.", "M.", "Conn.", "Yr.", "Rev.", "Phys.", "pp.", "Ms.", "To.", "Sgt.", "J.K.",
                        "Nr.", "Jun.", "Fri.", "S.A.R.", "Lev.", "Lt.Cdr.", "Def.", "F.", "Do.", "Joe.",
                        "Id.", "Mr.", "Dept.", "Is.", "Pvt.", "Diff.", "Hon.B.A.", "Q.", "Mb.", "On.",
                        "Min.", "J.B.", "Ed.", "AB.", "A.", "S.p.A.", "I.", "a.m.", "Comm.", "Go.", "VS.",
                        "L.", "All.", "PP.", "P.V.", "T.", "K.R.", "Etc.", "D.", "Adv.", "Lib.", "E.g.", "Pro.",
                        "U.S.A.", "S.E.", "AA.", "Rep.", "Sq.", "As.", "LLC.", "LTD.", "i.e.", "e.g" ]
        for sup in SUPPRESSIONS:
            if segment.endswith(sup):
                return True
        return False

    sentences: List[str] = []
    split = re.split(r"([\.\!\?]+['\"]*\s+)", text) # Break after sentence seperators, but include closing punctuation.
    prefix = ""
    while len(split) > 0:
        segment = split.pop(0)
        if len(split) > 0: # Check for a terminator.
            segment += split.pop(0) # Append the terminator.
        if suppress(segment):
            prefix += segment
            continue
        if len(segment) > 0:
            sentences.append(prefix + segment)
            prefix = ""

    # There might be some text leftover.
    if len(prefix) > 0:
        sentences.append(prefix)

    # Trim all leading and trailing spaces.
    sentences = [s.strip() for s in sentences]
    return sentences
