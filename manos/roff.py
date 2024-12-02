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

from typing import List, Union, Optional

import lxml
import lxml.etree
import math

from .ordered_set import OrderedSet
from .sentence import segment

class Text:
    def __init__(self, content: str) -> None:
        self.content = content

# This is identical to 'Text' except it is output as-is without any special processing.
# It is intended for literal blocks, like code examples.
class CodeLine:
    def __init__(self, source: str) -> None:
        assert source.find("\n") == -1, "code line cannot contain a new line character"
        self.source = source

class Macro:
    def __init__(self, name: str) -> None:
        self.name = name

RoffElements = Union[Text, Macro, CodeLine]

class Roff:
    def __init__(self) -> None:
        self.entries: List[RoffElements] = []

    def is_text(self) -> bool:
        for entry in self.entries:
            if not isinstance(entry, Text):
                return False
        return True

    def append_roff(self, other: 'Roff') -> None:
        self.entries += other.entries

    def append_text(self, other: str) -> None:
        # Special case: if the previous entry is a macro and the text being added begins
        # with a dot, then the implementation will place said new text on its own line.
        # This is a problem because that new line begins with dot and therefore Roff
        # will interpret it as the beginning of a macro. If this situtation happens
        # then escape the dot so Roff treats it as text.
        if other.startswith("."):
            if len(self.entries) > 0:
                if isinstance(self.entries[-1], Macro):
                    other = r"\[char46]" + other[1:]  # Escape the first dot.
        self.entries.append(Text(other))

    def append_source(self, other: str) -> None:
        self.entries.append(CodeLine(other))

    def append_macro(self, other: str) -> None:
        roff = Roff()
        roff.entries.append(Macro(other))
        self.append_roff(roff)

    def copy(self) -> 'Roff':
        copy = Roff()
        copy.entries = self.entries.copy()
        return copy

    def filter(self) -> List[RoffElements]:
        keep: List[RoffElements] = []
        prev: Optional[RoffElements] = None
        for curr in self.entries:
            if isinstance(curr, Text):
                # Only keep non-blank text lines.
                if len(curr.content.strip()) > 0:
                    keep.append(curr)
                    prev = curr
            elif isinstance(curr, CodeLine):
                keep.append(curr)
                prev = curr
            elif isinstance(curr, Macro):
                # If the first commands are .PP commands (indicating a new paragraph), then
                # remove them as this is implied.
                if prev is None and curr.name == ".PP":
                    continue
                # Do not add duplicate .PP commands in a row.
                elif not (isinstance(prev, Macro) and prev.name == curr.name and prev.name == ".PP"):
                    keep.append(curr)
                    prev = curr
        # Remove trailing paragraph breaks.
        while len(keep) > 0 and isinstance(keep[-1], Macro) and keep[-1].name == ".PP":
            keep.pop()
        return keep
    
    def simplify(self) -> 'Roff':
        copy = self.copy()
        copy.entries = copy.filter()
        return copy
    
    def has_command(self, index: int, command: str) -> bool:
        entry = self.entries[index]
        if isinstance(entry, Macro) and entry.name == command:
            return True
        return False
    
    def pop(self, index: int) -> RoffElements:
        return self.entries.pop(index)

    def __len__(self) -> int:
        return len(self.entries)

    def __str__(self) -> str:
        # Coalesce neighboring Text blocks into a single text block.
        # This is needed so sentence segmentation is performed on the entire string.
        entries: List[RoffElements] = []
        textblob = ""
        for curr in self.filter():
            if isinstance(curr, Text):
                textblob += curr.content
            else:
                if len(textblob) > 0:
                    entries.append(Text(textblob))
                    textblob = ""
                entries.append(curr)
        if len(textblob) > 0:
            entries.append(Text(textblob))

        # Concatenate all macros and text blocks.
        text = ""
        prev: Optional[RoffElements] = None
        for curr in entries:
            # Put roff macros on their own lines.
            if isinstance(curr, Macro):
                # Add a new line unless were at the beginning of the string.
                # Thie ensures macros are always on their own line.
                if len(text) > 0:
                    text += "\n"
                text += curr.name
            elif isinstance(curr, CodeLine):
                # If the previous entry was a macro, then add a new line after it.
                if isinstance(prev, Macro):
                    text += "\n"
                # If the previous entry was code, then append a new line.
                # This ensures each line of code is seperated onto their own line.
                elif isinstance(prev, CodeLine):
                    text += "\n"
                text += curr.source
            elif isinstance(curr, Text):
                # If the previous entry was a macro or source code, then add a new line after it.
                # This deliminates code/macros from paragraph text.
                if isinstance(prev, Macro) or isinstance(prev, CodeLine):
                    text += "\n"
                text += "\n".join(segment(curr.content))
            prev = curr
        return text
