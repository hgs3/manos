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

from typing import List, Dict, Any, Union, Optional
from .sentence import segment

class Text:
    def __init__(self, content: str) -> None:
        self.content = content

# This is identical to 'Text' except it is output as-is without any special processing.
# It is intended for literal blocks, like code examples.
class LiteralText:
    def __init__(self, content: str, standalone: bool = False) -> None:
        self.content = content
        self.standalone = standalone

class Macro:
    def __init__(self, name: str, argument: Optional[str]) -> None:
        assert name[0] != ".", "You should omit the dot when appending a macro."
        self.command = name
        self.argument = argument

RoffElements = Union[Text, Macro, LiteralText]

class Roff:
    def __init__(self) -> None:
        self.entries: List[RoffElements] = []

    def is_text(self) -> bool:
        for entry in self.entries:
            if not isinstance(entry, Text):
                return False
        return True

    # While groff can handle a vast range of Unicode characters, for maximum compatibility and ease of use,
    # it's best practice to primarily use basic Latin (US-ASCII) characters for the core content of man pages.
    def escape(self, other: str) -> str:
        unicode_escapes = {
            '\u201C': r'"',
            '\u201D': r'"',
            '\u2018': r"'",
            '\u2019': r"'",
        }
        return ''.join(unicode_escapes.get(char, char) for char in other)

    def append_roff(self, other: 'Roff') -> None:
        self.entries += other.entries

    def append_text(self, other: str) -> None:
        self.entries.append(Text(self.escape(other)))

    def append_source(self, other: str) -> None:
        self.entries.append(LiteralText(self.escape(other), True))

    def append_macro(self, name: str, argument: Optional[str] = None) -> None:
        self.entries.append(Macro(name, argument))

    def append(self, elem: RoffElements) -> None:
        self.entries.append(elem)

    def __deepcopy__(self, memo: Dict[int, Any]) -> 'Roff':
        copy = Roff()
        for entry in self.entries:
            if isinstance(entry, Macro):
                copy.append_macro(entry.command, entry.argument)
            elif isinstance(entry, Text):
                copy.append_text(entry.content)
            elif isinstance(entry, LiteralText):
                copy.append(LiteralText(entry.content, entry.standalone))
        return copy
    
    def simplify(self) -> 'Roff':
        copy = Roff()
        copy.entries = self._simplify()
        return copy
    
    def has_command(self, index: int, command: str) -> bool:
        entry = self.entries[index]
        if isinstance(entry, Macro) and entry.command == command:
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
        for curr in self._simplify():
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
                text += f".{curr.command}"
                if curr.argument is not None:
                    text += f" {curr.argument}"
            elif isinstance(curr, LiteralText) or isinstance(curr, Text):
                content = curr.content
                # Special case: if the previous entry is a macro and the text being added begins
                # with a dot, then the implementation will place said new text on its own line.
                # This is a problem because that new line begins with dot and therefore Roff
                # will interpret it as the beginning of a macro. If this situtation happens
                # then escape the dot so Roff treats it as text.
                if content.startswith("."):
                    if len(self.entries) > 0:
                        if prev is None or isinstance(prev, Macro):
                            content = r"\[char46]" + content[1:]  # Escape the first dot.
                # Same story for single quotes which joins the previous and current line.
                if content.startswith("'"):
                    if len(self.entries) > 0:
                        if prev is None or isinstance(prev, Macro):
                            content = r"\[char39]" + content[1:]  # Escape the first single quote.
                # Emit the text.
                if isinstance(curr, LiteralText):
                    # Escape the backslash character in literal text because otherwise it
                    # won't show up in the output.
                    content = content.replace("\\", "\\\\")
                    # If the previous entry was a macro, then add a new line after it.
                    if isinstance(prev, Macro):
                        text += "\n"
                    # If the previous entry was code, then append a new line.
                    # This ensures each line of code is seperated onto their own line.
                    elif isinstance(prev, LiteralText):
                        text += "\n"
                    text += content
                elif isinstance(curr, Text):
                    # If the previous entry was a macro or source code, then add a new line after it.
                    # This deliminates code/macros from paragraph text.
                    if isinstance(prev, Macro) or (isinstance(prev, LiteralText) and prev.standalone):
                        text += "\n"
                    text += "\n".join(segment(content))
            prev = curr
        return text

    def _simplify(self) -> List[RoffElements]:
        keep: List[RoffElements] = []
        prev: Optional[RoffElements] = None

        # Keep only non-blank text lines.
        for curr in self.entries:
            if isinstance(curr, Text):
                if len(curr.content.strip()) > 0:
                    keep.append(curr)
                    prev = curr
            elif isinstance(curr, LiteralText):
                keep.append(curr)
                prev = curr
            elif isinstance(curr, Macro):
                # If the first commands are .PP commands (indicating a new paragraph), then
                # remove them as this is implied.
                if prev is None and curr.command == "PP":
                    continue
                # Do not add duplicate .PP commands in a row.
                elif not (isinstance(prev, Macro) and prev.command == curr.command and prev.command == "PP"):
                    keep.append(curr)
                    prev = curr

        # Special case: if the previous entry was a .UE (end URL) macro and the text
        # being added is a sentence ending punctuator, then there should be no space
        # between the URL link and the punctuator. Unfortunatly, if we add the punctuator
        # to a new line (which is what would happen without this special logic), then the
        # punctuator will be sperated by a space.
        for curr in keep:
            if isinstance(curr, Text) or isinstance(curr, LiteralText):
                # We still check for blank lines because literal text might still start with it.
                if isinstance(prev, Macro) and prev.command == "UE":
                    while len(curr.content) > 0 and curr.content[0] in (".", "!", "?", ","):                        
                        if prev.argument is None:
                            prev.argument = "" # Avoid appending onto None.
                        prev.argument += curr.content[0] # Move the punctuation to the macro.
                        curr.content = curr.content[1:] # Trim the punctuator form the text.
            prev = curr

        # Remove trailing paragraph breaks.
        while len(keep) > 0 and isinstance(keep[-1], Macro) and keep[-1].command == "PP":
            keep.pop()
        return keep
