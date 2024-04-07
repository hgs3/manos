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

from typing import List, Set, Dict, Tuple, Union, Optional, TextIO, TypeAlias, cast
from io import TextIOWrapper

import lxml
import lxml.etree
import os
import sys
import subprocess
import glob
import shutil
import argparse
import math
import datetime
import re

from .ordered_set import OrderedSet
from .sentence import segment

class Arguments(argparse.Namespace):
    def __init__(self) -> None:
        self.doxyfile = ""
        self.output = "man"
        self._synopsis: List[List[str]] = []
        self.synopsis: Set[str] = set()
        self.function_parameters = False
        self.macro_parameters = False
        self.composite_fields = False
        self.topic: Optional[str] = None
        self.section = 3
        self.include_path = "short"
        self.footer_middle: Optional[str] = None
        self.footer_inside: Optional[str] = None
        self.header_middle: Optional[str] = None
        self.autofill = False
        self.preamble_file: Optional[str] = None
        self.epilogue_file: Optional[str] = None
        self.preamble: Optional[str] = None
        self.epilogue: Optional[str] = None
        self.pattern: Optional[str] = None
        self.suppress_output = False
        self.stdout: TextIO = sys.stdout
        self.stderr: TextIO = sys.stderr
        self.doxygen_settings: List[Tuple[str,str]] = []

    def finish(self) -> None:
        for sublist in self._synopsis:
            for item in sublist:
                self.synopsis.add(item)
        if self.suppress_output:
            self.stdout = open(os.devnull, 'w')
            self.stderr = open(os.devnull, 'w')

class Field:
    def __init__(self) -> None:
        self.type = "void"
        self.name = "unnamed"
        self.argstring = ""
        self.brief = ""
        self.description = Roff()

class CompositeType:
    def __init__(self, is_struct: bool, name: str, element: lxml.etree._Element) -> None:
        self.is_struct = is_struct
        self.element: Optional[lxml.etree._Element] = element
        self.name = name
        self.brief = ""
        self.description = Roff()
        self.fields: List[Field] = []

    @property
    def is_union(self) -> bool:
        return not self.is_struct

class Function:
    def __init__(self, name: str, group_id: Optional[str] = None) -> None:
        self.name = name
        self.params: Set[str] = set()
        self.group_id = group_id

class Enum:
    def __init__(self, name: str) -> None:
        self.name = name

class EnumElement:
    def __init__(self, name: str) -> None:
        self.name = name

class Typedef:
    def __init__(self, name: str) -> None:
        self.name = name

class Define:
    def __init__(self, name: str) -> None:
        self.name = name

# Doxygen group XML.
class Group:
    def __init__(self, id: str) -> None:
        self.id = id
        self.functions: OrderedSet[str] = OrderedSet()

# Doxygen example XML.
class Example:
    def __init__(self, description: lxml.etree._Element) -> None:
        self.description = description

Compound: TypeAlias = Union[CompositeType, Group, Enum, Function, Typedef, EnumElement, Define]

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

class State:
    def __init__(self) -> None:
        self.project_name: Optional[str] = None
        self.project_brief: Optional[str] = None
        self.project_version: Optional[str] = None
        self.examples: Dict[str, List[Example]] = {}
        self.compounds: Dict[str, Compound] = {}

state = State()
args = Arguments()

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

class Context:
    def __init__(self, ignore_refs: bool = False) -> None:
        self.ignore_refs = ignore_refs
        self.referenced_functions: OrderedSet[str] = OrderedSet()
        self.authors: List[Roff] = []
        self.bugs: List[Roff] = []
        self.examples: List[Roff] = []
        self.deprecated: List[Roff] = []
        self.return_type: Optional[Roff] = None
        self.function_params: Optional[Roff] = None
        self.active_function: Optional[Function] = None

    def clear_signature(self) -> None:
        self.return_type = None
        self.function_params = None

def process_children(ctx: Context, elem: lxml.etree._Element) -> Roff:
    # Compute the text for this node.
    content = Roff()
    if elem.text:
        content.append_text(elem.text)
    for child in elem:
        content.append_roff(process_as_roff(ctx, child))
        if child.tail:
            content.append_text(child.tail)
    return content

def process_as_roff(ctx: Context, elem: Optional[lxml.etree._Element]) -> Roff:
    if elem is None:
        return Roff()

    # Space element.
    if elem.tag == "sp":
        roff = Roff()
        roff.append_text(" ")
        return roff

    # Bold.
    if elem.tag == "bold":
        content = process_children(ctx, elem)
        roff = Roff()
        roff.append_text(f"\\f[B]{content}\\f[R]")
        return roff

    # Italic.
    if elem.tag == "emphasis":
        content = process_children(ctx, elem)
        roff = Roff()
        roff.append_text(f"\\f[I]{content}\\f[R]")
        return roff

    # Strikethrough
    if elem.tag == "strike":
        print("warning: ignoring \\strike command", file=args.stdout)
        return process_children(ctx, elem)

    # Styling when using inline code experts, i.e. "\c foobar" or "`foobar`" in markdown syntax.
    if elem.tag == "computeroutput":
        ctx.ignore_refs = True # Ignore to prevent unwanted styling of recognized types and functions.
        content = process_children(ctx, elem)
        ctx.ignore_refs = False
        if content.is_text():
            raw_text = str(content)
            # Doxygen represents function parameters identically to inline code snippets in its generated XML.
            # To deduce which is which, check if the XML for a function is being processed and if so, then
            # check if what is being processed matches a function parameter.
            if ctx.active_function is not None and raw_text in ctx.active_function.params:
                roff = Roff()
                roff.append_text(f'\\f[I]{raw_text}\\f[R]')
                return roff
            else:
                roff = Roff()
                roff.append_text(f'\\f[V]{raw_text}\\f[R]')
                return roff
        return content

    # Paramter name styling.
    if elem.tag == "parametername":
        content = process_children(ctx, elem)
        roff = Roff()
        roff.append_text(f"\\f[I]{content}\\f[R]")
        return roff

    # Paragraph elements: Doxygen likes to wrap <para> elements around everything.
    # This implementation strips the unneccessary <para> elements when processing the parent element.
    if elem.tag == "para":
        roff = Roff()
        roff.append_macro(".PP")
        roff.append_roff(process_children(ctx, elem))
        return roff

    # Special case: paramter list.
    if elem.tag == "parameterlist":
        kind = elem.get("kind")
        if kind == "param":
            content = Roff()
            for parameteritem in elem.findall("parameteritem"):
                params: List[str] = []
                for parameternamelist in parameteritem.findall("parameternamelist"):
                    for parametername in parameternamelist.findall("parametername"):
                        params.append(process_text(parametername))
                content.append_macro(".TP")
                content.append_text(", ".join(params) + "\n")
                content.append_text(process_description(ctx, parameteritem.find("parameterdescription")))
            ctx.function_params = content
        elif kind == "retval":
            content = Roff()
            for parameteritem in elem.findall("parameteritem"):
                retvals: List[str] = []
                for parameternamelist in parameteritem.findall("parameternamelist"):
                    for parametername in parameternamelist.findall("parametername"):
                        retvals.append(process_text(parametername))
                content.append_macro(".TP")
                content.append_text(", ".join(retvals) + "\n")
                content.append_text(process_description(ctx, parameteritem.find("parameterdescription")))
            ctx.return_type = content
        return Roff()

    # Anchor tags are meant to be linked to but have no usage in man pages.
    if elem.tag == "anchor":
        return process_children(ctx, elem)

    # Check for internal references, i.e. a reference to a C function or struct.
    if elem.tag == "ref":
        # If this is a reference to a C function defined by the API, then emit it
        # as a man page reference, i.e. the function "foobar" should appear as
        # the bolded text "foobar (3)" in the man page.
        content = process_children(ctx, elem)
        if not ctx.ignore_refs and content.is_text():
            refid_xml = elem.get("refid")
            if refid_xml is not None and refid_xml in state.compounds:
                compound = state.compounds[refid_xml]
                if isinstance(compound, Function):
                    roff = Roff()
                    roff.append_text(f"\\f[B]{compound.name}\\f[R](3)")
                    ctx.referenced_functions.add(compound.name)
                    return roff
                elif isinstance(compound, CompositeType):
                    roff = Roff()
                    if compound.is_struct:
                        roff.append_text(f"\\f[I]struct {compound.name}\\f[R]")
                    else:
                        roff.append_text(f"\\f[I]union {compound.name}\\f[R]")
                    return roff
                elif isinstance(compound, Enum):
                    roff = Roff()
                    roff.append_text(f"\\f[I]enum {compound.name}\\f[R]")
                    return roff
                elif isinstance(compound, EnumElement):
                    roff = Roff()
                    roff.append_text(f"\\f[I]{compound.name}\\f[R]")
                    return roff
                elif isinstance(compound, Typedef):
                    roff = Roff()
                    roff.append_text(f"\\f[I]{compound.name}\\f[R]")
                    return roff
                elif isinstance(compound, Define):
                    roff = Roff()
                    roff.append_text(f"\\f[I]{compound.name}\\f[R]")
                    return roff
        return content

    # Check for an external URL link, i.e. a link to a webpage.
    if elem.tag == "ulink":
        url = elem.get("url")
        roff = Roff()
        roff.append_macro(f".UR {url}")
        roff.append_roff(process_children(ctx, elem))
        roff.append_macro(".UE")
        return roff

    # Sections and subsections.
    # The element tag name has the section depth appended as a number, e.g. <sect1>, <sect2>, etc...
    if elem.tag.startswith("sect"):
        section_depth = int(elem.tag[4:])
        if section_depth > 1:
            print("warning: flattening subsections", file=args.stdout)
        title_xml = elem.find("title")
        assert title_xml is not None
        title = title_xml.text or ""
        title = title.capitalize() # Man page sections should be lowercase with the first letter uppercased.
        roff = Roff()
        roff.append_macro(f".SS {title}")
        roff.append_roff(process_children(ctx, elem))
        return roff

    # Title elements should be extracted manually by their parent element.
    # Their content should not be emitted here otherwise it will appear
    # twice in the output.
    if elem.tag == "title":
        return Roff()

    # Ordered and undordered list.
    if elem.tag in ["orderedlist", "itemizedlist"]:
        roff = Roff()
        roff.append_macro(".RS")
        for index,child in enumerate(elem):
            assert child.tag == "listitem", "expected <listitem> as child of list"
            listitem = Roff()
            if elem.tag == "itemizedlist":
                listitem.append_macro(".IP \\[bu] 2")
            else:
                index += 1
                indent = int(math.log(index, 10)) + 3
                listitem.append_macro(f".IP {index}. {indent}")
            listitem.append_roff(process_children(ctx, child))
            # Lists should NOT begin with a .PP macro otherwise Roff will begin a new paragraph
            # which puts the content of the list item on the next line below the bullet point.
            # Unfortunatly, Doxygen's XML output likes to insert a <para> element as an
            # immediate child of the <listitem> element; the following check catches
            # and removes it.
            if len(listitem) > 2 and listitem.has_command(1, ".PP"):
                listitem.pop(1)
            listitem.entries = list(filter(lambda x: not (isinstance(x, Macro) and x.name == ".PP"), listitem.entries)) 
            roff.append_roff(listitem)
        roff.append_macro(".RE")
        return roff

    # Multi-line source code examples.
    if elem.tag == "programlisting":
        # Do not style references to types in code examples.
        # Normally, when something is referenced, like a function, it is emphasized
        # e.g. the function "foobar" becomes ".BR foober (3)" but for code examples
        # this behavior should be disabled.
        ctx.ignore_refs = True
        roff = Roff()
        roff.append_macro(".PP")
        roff.append_macro(".in +4n")
        roff.append_macro(".EX")
        for codeline in elem:
            assert codeline.tag == "codeline", "expected <codeline> element in <programlisting>"
            text = ""
            for entry in process_children(ctx, codeline).entries:
                assert isinstance(entry, Text)
                text += entry.content
            roff.append_source(text)
        roff.append_macro(".EE")
        roff.append_macro(".in")
        roff.append_macro(".PP")
        ctx.ignore_refs = False
        return roff
    
    # The <highlight> elements appears in <programlisting> blocks.
    # They are used to indicate which keywords are to be highlighted.
    # Styling isn't applied to code examples in man page output so return their content as-is.
    if elem.tag == "highlight":
        return process_children(ctx, elem)

    # The <simplesect> element is used to contain function parameters, return type, and admonitions.
    if elem.tag == "simplesect":
        kind = elem.get("kind")
        if kind == "par":
            roff = Roff()
            roff.append_roff(process_children(ctx, elem))
            return roff
        elif kind == "return":
            ctx.return_type = process_children(ctx, elem)
            return Roff()
        elif kind == "see":
            # Visit the child elements but discard the Roff result. The purpose
            # for visiting the children is to check what's being referenced:
            # If it's a function, then it will be added to the SEE ALSO
            # section of the man page (see "ref" element handler).
            process_children(ctx, elem)
            return Roff()
        elif kind in ["since", "note", "warning", "attention"]:
            print("warning: excluding admonition from generated documentation", file=args.stdout)
            return Roff()
        elif kind in ["author", "authors"]:
            ctx.authors.append(process_children(ctx, elem))
            return Roff()
        else:
            raise Exception("unknown simplesect kind", kind)

    # Referencable section.
    if elem.tag == "xrefsect":
        title_xml = elem.find("xreftitle")
        if title_xml is not None and title_xml.text is not None:
            if title_xml.text == "Bug":
                description_xml = elem.find("xrefdescription")
                assert description_xml is not None
                ctx.bugs.append(process_children(ctx, description_xml))
            elif title_xml.text == "Deprecated":
                description_xml = elem.find("xrefdescription")
                assert description_xml is not None
                ctx.deprecated.append(process_children(ctx, description_xml))
            else:
                print("warning: unsupported xrefsect: {0}".format(title_xml.text), file=args.stdout)
        return Roff()
    
    # Move to the next line.
    if elem.tag == "linebreak":
        roff = Roff()
        roff.append_macro(".br")
        return roff

    # Ignore index tags as they're only useful for LaTeX and DocBook formats.
    # They have no use in man pages so no warning is needed.
    if elem.tag == "indexentry":
        return Roff()
    
    # This element appears in various parts of the documentation, i.e. to indicate the type of a struct field.
    # Just visit its children without any other special handling.
    if elem.tag == "type":
        return process_children(ctx, elem)

    # Misc tags to visit that might be encountered during normal parsing.
    # Don't do anything special with them, just visit their children.
    if elem.tag in ["briefdescription", "detaileddescription", "parameterdescription"]:
        return process_children(ctx, elem)

    # Ignore all other commands.
    if elem.tag in ["emoji", "table", "image", "formula"]:
        print("warning: ignoring \\{0} command".format(elem.tag), file=args.stdout)
        return Roff()

    # Misc tags: https://www.doxygen.nl/manual/htmlcmds.html
    tags = {
        "ndash": "\\[en]",
        "mdash": "\\[em]",
    }
    if elem.tag in tags:
        roff = Roff()
        roff.append_text(tags[elem.tag])
        return roff

    # Raise an exception for unknown tags so we're alerted
    # to then and can properly deal with it.
    raise Exception("unknown node", elem.tag)

def process_brief(elem: Optional[lxml.etree._Element]) -> str:
    # Brief descriptions should consist of a single line so remove any
    # commands, like .PP, because they will force text onto another line.
    roff = process_as_roff(Context(True), elem)
    roff.entries = list(filter(lambda x: isinstance(x, Text), roff.entries))
    return str(roff).strip()

def process_description(ctx: Context, elem: Optional[lxml.etree._Element]) -> str:
    roff = process_as_roff(ctx, elem)
    return str(roff)

def process_text(elem: Optional[lxml.etree._Element]) -> str:
    text = ""
    if elem is not None:
        if elem.text:
            text += elem.text
        for child in elem:
            text += process_text(child)
            if child.tail:
                text += child.tail
    return text.strip()

def lowerify(text: str) -> str:
    if len(text) == 0:
        return text
    if len(text) >= 2 and text[0].isupper() and not text[1].isupper():
        text = text[0].lower() + text[1:] # Lowercase first letter, unless it begins an acronym.
    return text

def briefify(brief: str) -> str:
    return lowerify(brief).rstrip('.') # Remove trailing punctuation.

def emit_special_sections(ctx: Context, file: TextIOWrapper) -> None:
    if len(ctx.deprecated) > 0:
        file.write('.\\" --------------------------------------------------------------------------\n')
        file.write('.SH DEPRECATION\n')
        roff = Roff()
        for bug in ctx.deprecated:
            roff.append_roff(bug)
            roff.append_macro(".PP")
        file.write(str(roff))
        file.write("\n")

    if len(ctx.bugs) > 0:
        file.write('.\\" --------------------------------------------------------------------------\n')
        file.write('.SH BUGS\n')
        roff = Roff()
        for bug in ctx.bugs:
            roff.append_roff(bug)
            roff.append_macro(".PP")
        file.write(str(roff))
        file.write("\n")

    if len(ctx.examples) > 0:
        file.write('.\\" --------------------------------------------------------------------------\n')
        file.write('.SH EXAMPLES\n')
        roff = Roff()
        for example in ctx.examples:
            roff.append_roff(example)
            roff.append_macro(".PP")
        file.write(str(roff))
        file.write("\n")

    if len(ctx.authors) > 0:
        file.write('.\\" --------------------------------------------------------------------------\n')
        file.write('.SH AUTHORS\n')
        roff = Roff()
        for author in ctx.authors:
            roff.append_roff(author)
            roff.append_macro(".PP")
        file.write(str(roff))
        file.write("\n")

    if len(ctx.referenced_functions) > 0:
        file.write('.\\" --------------------------------------------------------------------------\n')
        file.write('.SH SEE ALSO\n')
        for index,page in enumerate(ctx.referenced_functions):
            file.write(f'.BR {page} (3)')
            if index < len(ctx.referenced_functions) - 1:
                file.write(',')
            file.write('\n')

# Construct the '.TH' macro.
def heading() -> str:
    assert state.project_name is not None
    params: List[str] = []

    # The '.TH' macro always includes topic and section number.
    if args.topic is not None:
        params.append(f'"{args.topic}"')
    else:
        params.append(f'"{state.project_name.upper()}"')
    params.append(f'"{args.section}"')

    # Optional the '.TH' macro may include a footer-middle...
    if args.footer_middle is not None:
        params.append(f'"{args.footer_middle}"')
    elif args.autofill:
        # Compute the ordinal suffix for the day, i.e. "1st", "2nd", "3rd", etc...
        dt = datetime.date.today()
        if 11 <= (dt.day % 100) <= 13:
            suffix = 'th'
        else:
            suffix = ['th', 'st', 'nd', 'rd', 'th'][min(dt.day % 10, 4)]
        now = dt.strftime(f"%b {str(dt.day) + suffix} %Y")
        params.append(f'"{now}"')
    else:
        params.append("")

    # ... and a footer-inside.
    if args.footer_inside is not None:
        params.append(f'"{args.footer_inside}"')
    elif args.autofill and state.project_version is not None:
        params.append(f'"{state.project_name} {state.project_version}"')
    else:
        params.append("")

    # There isn't a need to specify a header-middle
    # as it will be auto-provided if omitted.
    if args.header_middle is not None:
        params.append(f'"{args.header_middle}"')
    else:
        params.append("")

    # Remove trailing empty spaces.
    while len(params) > 0 and params[-1] == "":
        params.pop()

    th = f".TH "
    th += " ".join(params)
    th += "\n"
    return th

def parse_function_signature(element: lxml.etree._Element) -> str:
    type = process_text(element.find("type"))
    name = process_text(element.find("name"))
    signature = f'.BI "{type}'
    # If the return type ends with an astrisk, then that means it's a pointer type
    # and there should be no whitespace between it and the function name.
    if not type.endswith("*"):
        signature += " "
    signature += f'{name}('
    params = element.findall("param")
    for index, param in enumerate(params):
        param_type = process_text(param.find("type"))
        declname = param.find("declname")
        signature += param_type
        if declname is not None:
            # If the parameter type ends with an astrisk, that means it's pointer type
            # and there should be no whitespace between it and the parameter name.
            if not param_type.endswith("*"):
                signature += " "
            # Emit the name of the paramter.
            param_name = process_text(declname)
            signature += f'" {param_name} "'
        # Add a comma between each parameter.
        if index < len(params) - 1:
            signature += ', '
    signature += ');"'
    return signature

def parse_function(element: lxml.etree._Element, header_display_name: str) -> None:
    id = element.get("id")
    assert id is not None, "function must have a Doxygen assigned identifier"

    ctx = Context()
    if id in state.compounds:
        compound = state.compounds[id]
        if isinstance(compound, Function):
            ctx.active_function = compound

    name = process_text(element.find("name"))
    brief = briefify(process_brief(element.find("briefdescription")))
    description = process_description(ctx, element.find("detaileddescription"))
    file = open(output_path(f"{name}.3"), "w", encoding="utf-8")
    if args.preamble is not None:
        file.write(args.preamble)
    file.write(heading())
    file.write(".SH NAME\n")
    file.write(f'{name} \\- {brief}\n')
    if state.project_brief is not None:
        file.write('.\\" --------------------------------------------------------------------------\n')
        file.write('.SH LIBRARY\n')
        file.write(state.project_brief.strip() + "\n")
    file.write('.\\" --------------------------------------------------------------------------\n')
    file.write('.SH SYNOPSIS\n')
    file.write('.nf\n')
    file.write(f'.B #include <{header_display_name}>\n')
    file.write('.PP\n')
    file.write(parse_function_signature(element) + "\n")
    file.write('.fi\n')

    if len(description) > 0:
        file.write('.\\" --------------------------------------------------------------------------\n')
        file.write('.SH DESCRIPTION\n')
        file.write(description)
        file.write("\n")

    if ctx.function_params is not None and args.function_parameters is True:
        file.write('.\\" --------------------------------------------------------------------------\n')
        file.write('.SH PARAMETERS\n')
        file.write(str(ctx.function_params))
        file.write("\n")

    if ctx.return_type is not None:
        file.write('.\\" --------------------------------------------------------------------------\n')
        file.write('.SH RETURN VALUE\n')
        file.write(str(ctx.return_type))
        file.write("\n")

    # The function and group should have been discovered when preparsing the XML.
    assert id in state.compounds, "function was not discovered during preparse"
    compound = state.compounds[id]
    if isinstance(compound, Function):
        group_id = compound.group_id
        if group_id is not None:
            assert group_id in state.compounds, "group was not discovered during preparse"
            # Add all functions belonging to the same group as this one to its SEE ALSO man page section.
            compound = state.compounds[group_id]
            if isinstance(compound, Group):
                ctx.referenced_functions = ctx.referenced_functions.union(compound.functions)

    # Discard circular references, i.e. if this man page documents function X, then exclude
    # function X from the SEE ALSO section of its own man page.
    if name in ctx.referenced_functions:
        ctx.referenced_functions = ctx.referenced_functions.difference(set([name]))

    emit_special_sections(ctx, file)

    if args.epilogue is not None:
        file.write(args.epilogue)
    file.close()

def output_path(file: str) -> str:
    return os.path.join(args.output, file)

def parse_header(element: lxml.etree._Element) -> None:
    ctx = Context()
    header_name = process_text(element.find("compoundname"))
    header_display_name = header_name
    header_brief = briefify(process_brief(element.find("briefdescription")))
    content = process_as_roff(ctx, element.find("detaileddescription"))
    functions = Roff()
    composite_types = Roff()
    typedefs = Roff()
    enums = Roff()
    variables = Roff()
    macros = Roff()

    # Register all examples.
    location_xml = element.find("location")
    if location_xml is not None:
        file_xml = location_xml.get("file")
        if file_xml is not None:
            if args.include_path == "full":
                header_display_name = file_xml
            if file_xml in state.examples:
                for example in state.examples[file_xml]:
                    ctx.examples.append(process_as_roff(ctx, example.description))

    for innerclass in element.findall("innerclass"):
        refid_xml = innerclass.get("refid")
        assert refid_xml is not None
        compound = state.compounds[refid_xml]
        assert isinstance(compound, CompositeType)
        content.append_macro('.\\" -------------------------------------')
        if compound.is_struct:
            content.append_macro(f'.SS The {compound.name} structure')
        else:
            content.append_macro(f'.SS The {compound.name} union')
        content.append_text(compound.brief)
        content.append_macro('.PP')
        content.append_macro('.in +4n')
        content.append_macro('.EX')
        if compound.is_struct:
            content.append_source(f'struct {compound.name} {{')
            composite_types.append_macro(f'.B struct {compound.name} {{')
        else:
            content.append_source(f'union {compound.name} {{')
            composite_types.append_macro(f'.B union {compound.name} {{')
        for field in compound.fields:
            # If the field type ends with an astrisk, then that means it's a pointer type
            # and there should be no whitespace between it and the field name.
            if field.type.endswith("*"):
                content.append_source("    {0}{1}{2};".format(field.type, field.name, field.argstring))
                composite_types.append_macro('.BI "    {0}" {1} "{2};"'.format(field.type, field.name, field.argstring))
            else:
                content.append_source("    {0} {1}{2};".format(field.type, field.name, field.argstring))
                composite_types.append_macro('.BI "    {0} " {1} "{2};"'.format(field.type, field.name, field.argstring))
        content.append_source('};')
        composite_types.append_macro('.B };')
        composite_types.append_macro(".PP")
        content.append_macro('.EE')
        content.append_macro('.in')
        content.append_macro('.PP')
        content.append_roff(compound.description)

        if (compound.is_struct or compound.is_union) and args.composite_fields is True:
            content.append_macro(".PP")
            if compound.is_struct:
                content.append_text(f"The fields in the\n.I {compound.name}\nstructure are as follows:\n")
            else:
                content.append_text(f"The fields in the\n.I {compound.name}\nunion are as follows:\n")
            for field in compound.fields:
                # Do not emit the field if it contains no documentation.
                # Otherwise it just redundantly appears by itself.
                if len(field.brief) > 0:
                    content.append_macro(".TP")
                    content.append_macro(f".I {field.name}")
                    content.append_text(field.brief)

    for sectiondef in element.findall("sectiondef"):
        kind = sectiondef.get("kind")
        if kind == "func":
            content.append_macro('.\\" -------------------------------------')
            content.append_macro('.SS Functions')
            for memberdef in sectiondef.findall("memberdef"):
                name_xml = memberdef.find("name")
                name = (name_xml.text or "") if name_xml is not None else ""
                brief = process_brief(memberdef.find("briefdescription"))
                content.append_macro('.TP')
                content.append_macro(f'.BR {name} (3)')
                content.append_text(brief)
                functions.append_macro(parse_function_signature(memberdef))
                ctx.referenced_functions.add(name)
        elif kind == "typedef":
            for memberdef in sectiondef.findall("memberdef"):
                name_xml = memberdef.find("name")
                if name_xml is not None and name_xml.text is not None:
                    type_xml = memberdef.find("type")
                    if type_xml is not None:
                        type_content = process_brief(type_xml)
                        brief = process_brief(memberdef.find("briefdescription"))
                        description_roff = process_as_roff(ctx, memberdef.find("detaileddescription"))
                        content.append_macro('.\\" -------------------------------------')
                        content.append_macro(f'.SS The {name_xml.text} type')
                        content.append_text(brief)
                        content.append_macro('.PP')
                        content.append_macro('.in +4n')
                        content.append_macro('.EX')
                        # If the type being aliased ends with an astrisk, then that means it's a pointer
                        # type and there should be no whitespace between it the name of the alias.
                        if type_content.endswith("*"):
                            content.append_source(f"typedef {type_content}{name_xml.text};")
                            typedefs.append_macro(f".B typedef {type_content}{name_xml.text};")
                        else:
                            content.append_source(f"typedef {type_content} {name_xml.text};")
                            typedefs.append_macro(f".B typedef {type_content} {name_xml.text};")
                        content.append_macro('.EE')
                        content.append_macro('.in')
                        content.append_macro('.PP')
                        content.append_roff(description_roff)
        elif kind == "enum":
            for memberdef in sectiondef.findall("memberdef"):
                name_xml = memberdef.find("name")
                if name_xml is not None and name_xml.text is not None:
                    brief = process_brief(memberdef.find("briefdescription"))
                    description_roff = process_as_roff(ctx, memberdef.find("detaileddescription"))
                    content.append_macro('.\\" -------------------------------------')
                    content.append_macro(f'.SS The {name_xml.text} enumeration')
                    content.append_text(brief)
                    content.append_macro('.PP')
                    content.append_macro('.in +4n')
                    content.append_macro('.EX')
                    content.append_source(f'enum {name_xml.text} {{')
                    enums.append_macro(f'.B enum {name_xml.text} {{')
                    for enumval in memberdef.findall('enumvalue'):
                        name = process_text(enumval.find('name'))
                        content.append_source('    {0},'.format(name))
                        enums.append_macro('.B "    {0},"'.format(name))
                    content.append_source('};')
                    enums.append_macro('.B };')
                    content.append_macro('.EE')
                    content.append_macro('.in')
                    content.append_macro('.PP')
                    content.append_roff(description_roff)
                    content.append_macro('.PP')
                    for enumval in memberdef.findall("enumvalue"):
                        name = process_text(enumval.find("name"))
                        brief = process_brief(enumval.find("briefdescription"))
                        if len(brief) > 0:
                            description_roff = process_as_roff(ctx, enumval.find("detaileddescription")).simplify()
                            content.append_macro(".TP")
                            content.append_macro(f".I {name}")
                            content.append_text(brief)
                            if len(description_roff) > 0:
                                content.append_macro(".PP")
                                content.append_roff(description_roff)
        elif kind == "var":
            for memberdef in sectiondef.findall("memberdef"):
                name_xml = memberdef.find("name")
                if name_xml is not None and name_xml.text is not None:
                    brief = process_brief(memberdef.find("briefdescription"))
                    description_roff = process_as_roff(ctx, memberdef.find("detaileddescription"))
                    type_xml = memberdef.find("type")
                    name_xml = memberdef.find("name")
                    if type_xml is not None and type_xml.text is not None \
                        and name_xml is not None and name_xml.text is not None:
                        argsstring = process_text(memberdef.find("argsstring"))
                        content.append_macro('.\\" -------------------------------------')
                        content.append_macro(f'.SS The {name_xml.text} variable')
                        content.append_text(brief)
                        content.append_macro('.PP')
                        content.append_macro('.in +4n')
                        content.append_macro('.EX')
                        # If the type being aliased ends with an astrisk, then that means it's a pointer
                        # type and there should be no whitespace between it the variable name.
                        if type_xml.text.endswith("*"):
                            content.append_source(f'{type_xml.text}{name_xml.text}{argsstring};')
                            variables.append_source(f'.B {type_xml.text}{name_xml.text}{argsstring};')
                        else:
                            content.append_source(f'{type_xml.text} {name_xml.text}{argsstring};')
                            variables.append_macro(f'.B {type_xml.text} {name_xml.text}{argsstring};')
                        content.append_macro('.EE')
                        content.append_macro('.in')
                        content.append_macro('.PP')
                        content.append_roff(description_roff)
                        content.append_macro('.PP')
        elif kind == "define":
            for memberdef in sectiondef.findall("memberdef"):
                id = memberdef.get("id") ; assert id is not None
                name_xml = memberdef.find("name")
                if name_xml is not None and name_xml.text is not None and id is not None:
                    signature = name_xml.text
                    params = memberdef.findall("param")
                    if len(params) > 0:
                        signature += "("
                        for index,param_xml in enumerate(params):
                            signature += process_text(param_xml)
                            if index < len(params) - 1:
                                signature += ","
                        signature += ")"
                    brief = process_brief(memberdef.find("briefdescription"))
                    ctx.clear_signature()
                    description_roff = process_as_roff(ctx, memberdef.find("detaileddescription"))
                    content.append_macro('.\\" -------------------------------------')
                    content.append_macro(f'.SS The {name_xml.text} macro')
                    content.append_text(brief)
                    content.append_macro('.PP')
                    content.append_macro('.in +4n')
                    content.append_macro('.EX')
                    content.append_source(f'#define {signature}')
                    macros.append_macro(f'.B #define {signature}')
                    content.append_macro('.EE')
                    content.append_macro('.in')
                    content.append_macro('.PP')
                    content.append_roff(description_roff)
                    content.append_macro('.PP')
                    if ctx.function_params is not None and args.macro_parameters is True:
                        content.append_text(f"The parameters to the\n.I {name_xml.text}\nmacro are as follows:\n")
                        content.append_roff(ctx.function_params)

    synopsis = Roff()
    synopsis.append_macro('.SH SYNOPSIS')
    synopsis.append_macro('.nf')
    synopsis.append_macro(f'.B #include <{header_display_name}>')
    if "functions" in args.synopsis:
        synopsis.append_macro('.PP')
        synopsis.append_roff(functions)
    if "composites" in args.synopsis:
        synopsis.append_macro('.PP')
        synopsis.append_roff(composite_types)
    if "enums" in args.synopsis:
        synopsis.append_macro('.PP')
        synopsis.append_roff(enums)
    if "typedefs" in args.synopsis:
        synopsis.append_macro('.PP')
        synopsis.append_roff(typedefs)
    if "variables" in args.synopsis:
        synopsis.append_macro('.PP')
        synopsis.append_roff(variables)
    if "macros" in args.synopsis:
        synopsis.append_macro('.PP')
        synopsis.append_roff(macros)
    while len(synopsis) > 0 and synopsis.has_command(-1, ".PP"):
        synopsis.pop(len(synopsis) - 1)
    synopsis.append_macro('.fi')

    file = open(output_path(f"{header_name}.3"), "w", encoding="utf-8")
    if args.preamble is not None:
        file.write(args.preamble)
    file.write(heading())
    file.write(".SH NAME\n")
    file.write(f'{header_name} \\- {header_brief}\n')
    if state.project_brief is not None:
        file.write('.\\" --------------------------------------------------------------------------\n')
        file.write('.SH LIBRARY\n')
        file.write(state.project_brief.strip() + "\n")
    file.write('.\\" --------------------------------------------------------------------------\n')
    file.write(str(synopsis))
    file.write("\n")

    description = str(content)
    if len(description) > 0:
        file.write('.\\" --------------------------------------------------------------------------\n')
        file.write('.SH DESCRIPTION\n')
        file.write(description)
        file.write("\n")

    emit_special_sections(ctx, file)

    if args.epilogue is not None:
        file.write(args.epilogue)
    file.close()

# Doxygen can begin Doxyfile options with quotes.
# Remove them here.
def dequote(string: str) -> str:
    if string.startswith('"'):
        string = string[1:]
    if string.endswith('"'):
        string = string[:-1]
    return string

def preparse_xml(file: str) -> None:
    tree = lxml.etree.parse(file)
    if tree.getroot().tag == "doxyfile":
        project_name_xml = cast(List[lxml.etree._Element], tree.xpath("//option[@id='PROJECT_NAME']/value"))
        project_brief_xml = cast(List[lxml.etree._Element], tree.xpath("//option[@id='PROJECT_BRIEF']/value"))
        project_number_xml = cast(List[lxml.etree._Element], tree.xpath("//option[@id='PROJECT_NUMBER']/value"))
        if len(project_name_xml) > 0:
            if text := project_name_xml[0].text:
                state.project_name = dequote(text)
        if len(project_brief_xml) > 0:
            if text := project_brief_xml[0].text:
                state.project_brief = dequote(project_brief_xml[0].text)
        if len(project_number_xml) > 0:
            if text := project_number_xml[0].text:
                state.project_version = dequote(project_number_xml[0].text)
        return
    element = tree.find("compounddef")
    if element is None:
        return
    kind = element.get("kind")
    # Only consider source files (e.g. ignore Markdown files).
    language = element.get("language")
    if language == "C++":
        # Doxygen writes docs for structs and unions in their own individual .xml files.
        if kind == "struct":
            name_xml = element.find("compoundname")
            if name_xml is not None:
                if name_xml.text is not None:
                    id = element.get("id")
                    assert id is not None
                    state.compounds[id] = CompositeType(True, name_xml.text, element)            
        elif kind == "union":
            name_xml = element.find("compoundname")
            if name_xml is not None:
                if name_xml.text is not None:
                    id = element.get("id")
                    assert id is not None
                    state.compounds[id] = CompositeType(False, name_xml.text, element)      
        elif kind == "file":
            # Parse all other definitions.
            for sectiondef in element.findall("sectiondef"):
                kind = sectiondef.get("kind")
                if kind == "func":
                    for memberdef in sectiondef.findall("memberdef"):
                        name = process_text(memberdef.find("name"))
                        if len(name) > 0:
                            group_id: Optional[str] = None
                            id = memberdef.get("id")
                            if id is not None:
                                if id.startswith("group__"):
                                    endpos = id.index("_1")
                                    if endpos > 0:
                                        group_id = id[:endpos]
                                function = Function(name, group_id)
                                state.compounds[id] = function
                                # Remember names of function parameter.
                                # Note that the following XPath recursivly searches the XML.
                                for param in memberdef.findall('.//parameterlist[@kind="param"]/*/*/parametername'):
                                    if param.text is not None:
                                        function.params.add(param.text)
                elif kind == "typedef":
                    for memberdef in sectiondef.findall("memberdef"):
                        id = memberdef.get("id")
                        assert id is not None
                        name_xml = memberdef.find("name")
                        if name_xml is not None and name_xml.text is not None:
                            state.compounds[id] = Typedef(name_xml.text)
                elif kind == "enum":
                    for memberdef in sectiondef.findall("memberdef"):
                        id = memberdef.get("id") ; assert id is not None
                        name_xml = memberdef.find("name")
                        if name_xml is not None and name_xml.text is not None and id is not None:
                            state.compounds[id] = Enum(name_xml.text)
                            # Store all enumeration members in the same dictionary as the enumeration itself.
                            # This is done because when Doxygen references them it does so using a global identifier.
                            for enumval in memberdef.findall("enumvalue"):
                                id = enumval.get("id") ; assert id is not None
                                name_xml = enumval.find("name")
                                if name_xml is not None and name_xml.text is not None:
                                    state.compounds[id] = EnumElement(name_xml.text)
                elif kind == "define":
                    for memberdef in sectiondef.findall("memberdef"):
                        id = memberdef.get("id") ; assert id is not None
                        name_xml = memberdef.find("name")
                        if name_xml is not None and name_xml.text is not None and id is not None:
                            state.compounds[id] = Define(name_xml.text)
    # Track all groups and the functions that belong to them.
    # This is used to reference all other functions under each functions SEE ALSO man page section.
    elif kind == "group":
        group_id = element.get("id")
        assert group_id is not None
        group = Group(group_id)
        for sectiondef in element.findall("sectiondef"):
            if sectiondef.get("kind") == "func":
                for memberdef in sectiondef.findall("memberdef"):
                    name = process_text(memberdef.find("name"))
                    if len(name) > 0:
                        group.functions.add(name)
        state.compounds[group_id] = group
    # Extract examples to latter include in the associated header file.
    # The examples associated with said header file will be added
    # to the EXAMPLES man page section of said header file.
    elif kind == "example":
        location_xml = element.find("location")
        description_xml = element.find("detaileddescription")
        if location_xml is not None \
            and description_xml is not None:
            file_xml = location_xml.get("file")
            if file_xml is not None:
                if file_xml in state.examples:
                    state.examples[file_xml].append(Example(description_xml))
                else:
                    state.examples[file_xml] = [Example(description_xml)]

def parse_xml(file: str) -> None:
    tree = lxml.etree.parse(file)
    element = tree.find("compounddef")
    if element is None:
        return
    # Only consider source files (e.g. ignore Markdown files).
    language = element.get("language")
    if language != "C++":
        return
    kind = element.get("kind")
    if kind == "file":
        header_display_name: Optional[str] = None
        location = element.find("location")
        if location is not None and args.include_path == "full":
            header_display_name = location.get("file")
        if header_display_name is None:
            header_display_name = process_text(element.find("compoundname"))
        parse_header(element)
        for sectiondef in element.findall("sectiondef"):
            if sectiondef.get("kind") == "func":
                for memberdef in sectiondef.findall("memberdef"):
                    parse_function(memberdef, header_display_name)

def exec(doxyfile: str) -> int:
    # Clone the doxyfile
    try:
        # Use the same working path as the Doxyfile.
        # If a path is not present in the input, then realpath() will fallback to the current path.
        working_dir = os.path.dirname(doxyfile)
        working_dir = os.path.realpath(working_dir)
        doxyfile_manos = os.path.join(working_dir, "Doxyfile.manos")
        shutil.copyfile(doxyfile, doxyfile_manos)
    except:
        print("error: cannot write to the directory of the doxygen configuration file", file=args.stderr)
        return 1

    # Generate output directory if it doesn't exist.
    if len(args.output) > 0:
        if not os.path.exists(args.output):
            os.mkdir(args.output)

    # Append additional options onto it.
    clone = open(doxyfile_manos, "a", encoding="utf-8")
    # Add user options.
    for key, value in args.doxygen_settings:
        clone.write(f"{key} = {value}\n")
    # Disable all generators except the XML generators.
    # Man pages are created by parsing the raw data from the XML.
    clone.write("GENERATE_XML = YES\n")
    clone.write("GENERATE_HTML = NO\n")
    clone.write("GENERATE_DOCSET = NO\n")
    clone.write("GENERATE_CHI = NO\n")
    clone.write("GENERATE_QHP = NO\n")
    clone.write("GENERATE_ECLIPSEHELP = NO\n")
    clone.write("GENERATE_LATEX = NO\n")
    clone.write("GENERATE_RTF = NO\n")
    clone.write("GENERATE_MAN = NO\n")
    clone.write("GENERATE_DOCBOOK = NO\n")
    # Dump syntax highlighting information.
    clone.write("XML_PROGRAMLISTING = NO\n")
    clone.write("XML_NS_MEMB_FILE_SCOPE = NO\n")
    # Write output to the same directory as the Doxygen config.
    clone.write("OUTPUT_DIRECTORY = .\n")
    clone.write("CREATE_SUBDIRS = NO\n")
    # Rename the directory where the XML output is written to avoid
    # clashing with the users directory (the user might be generating
    # xml output on their own, seperate from manos).
    clone.write("XML_OUTPUT = xml\n")
    clone.close()

    # Generate the XML documentation.
    # Type checking is disabled for run() because it would require
    # declaring a custom TypedDict and it's not worth the hassle.
    p = subprocess.Popen(["doxygen", "Doxyfile.manos"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=working_dir)
    result = p.communicate()
    stdout = result[0].decode("utf-8")
    stderr = result[1].decode("utf-8")
    if len(stdout) > 0:
        print(stdout, file=args.stdout)
    if len(stderr) > 0:
        print(stderr, file=args.stderr)

    # Extract metadata from all XML files.
    xml_files = glob.glob(os.path.join(working_dir, "xml", "*.xml"))

    # Figure out which files to process and which to skip.
    if args.pattern is not None:
        def matches(file: str) -> bool:
            file = os.path.basename(file)
            if r.match(file) is not None:
                return False
            return True
        r = re.compile(args.pattern)
        xml_files = list(filter(matches, xml_files))

    # Make sure there are XML files...
    if len(xml_files) == 0:
        print("error: no XML files match the pattern", file=args.stderr)
        return 1

    # Extract top-level documentation first.
    for file in xml_files:
        preparse_xml(file)

    # There must be a project name specified in the Doxygen config.
    # If the user does not specify a name, then Doxygen will default to "My Project".
    assert state.project_name is not None

    # Extract documentation for top-level compound data types.
    # Doxygen writes struct and union docs to their own XML files.
    # These are processed first before processing the header XML.
    for compound in state.compounds.values():
        if isinstance(compound, CompositeType):
            if compound.element is not None:
                compound.brief = process_brief(compound.element.find("briefdescription"))
                compound.description = process_as_roff(Context(), compound.element.find("detaileddescription"))
                for sectiondef in compound.element.findall("sectiondef"):
                    for memberdef in sectiondef.findall("memberdef"):
                        field = Field()
                        field.type = process_text(memberdef.find("type"))
                        field.name = process_text(memberdef.find("name"))
                        field.argstring = process_text(memberdef.find("argsstring"))
                        field.brief = process_brief(memberdef.find("briefdescription"))
                        field.description = process_as_roff(Context(), memberdef.find("detaileddescription"))
                        compound.fields.append(field)
                compound.element = None # Drop the reference so Python can garbage collect the XML tree.

    # Extract header file documentation next.
    for file in xml_files:
        parse_xml(file)

    # Delete the temporary Doxyfile cloned that was from the original.
    if os.path.exists(doxyfile_manos):
        os.remove(doxyfile_manos)
    return 0

def main(doxyfile: str, arguments: Arguments) -> int:
    # Reset globla state.
    global state, args
    state = State()
    args = arguments

    # For the premable to end with a new line character.
    # This ensures the first man page macro begins on its own line.
    if args.preamble is not None and not args.preamble.endswith("\n"):
        args.preamble += "\n"

    # Setup defaults.
    if args.section < 1 or args.section > 9:
        print("error: expected section in the inclusive range 1-9", file=args.stderr)
        return 1

    # Check if the Doxygen configuration file exists.
    if not os.path.exists(doxyfile):
        print("error: missing configuration file: {0}".format(doxyfile), file=args.stderr)
        return 1

    # Verify Doxygen is installed.
    if shutil.which("doxygen") is None:
        print("error: could not find doxygen;", file=args.stderr)
        print("       please install it https://www.doxygen.nl/", file=args.stderr)
        return 1

    # Verify Doxygen version.
    p = subprocess.Popen(["doxygen", "--version"], stdout=subprocess.PIPE)
    result = p.communicate()
    # It's possible for the verison to contain a Git commit hash, e.g. running "doxygen --verison"
    # might produce: "1.9.2 (caa4e3de211fbbef2c3adf58a6bd4c86d0eb7cb8)". Use the split() function
    # to discard the Git commit.
    raw_version = result[0].decode("utf-8").split()[0]
    # Use split() again to decode the version.
    components = raw_version.split(".")
    # Zero-pad the version, e.g. if its "1.2" then pad so it becomes "1.2.0".
    while len(components) < 3:
        components.append("0")
    # Convert each component from a string to an integer, e.g. convert ('1','2','3') into (1,2,3).
    version = tuple(map(lambda x: int(x), components))
    # Doxygen 1.9.2 began writing out "doxyfile.xml" which contains all settings used in the Doxyfile.
    # Manos uses this file to extract information about the project, like is name and version.
    if version < (1, 9, 2):
        print(f"error: doxygen version 1.9.2 or newer is required, found version {raw_version}", file=args.stderr)
        print("       please upgrade it https://www.doxygen.nl/", file=args.stderr)
        return 1

    # Run the main program.
    return exec(doxyfile)

def parse_args(arguments: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="manos", description="Man page generator for C projects.")
    parser.add_argument("doxyfile")
    parser.add_argument("-v", "--version", action="version", version='%(prog)s 1.0')
    parser.add_argument("-q", "--quite", action="store_true", dest="suppress_output", help="suppress output")

    group = parser.add_argument_group()
    group.add_argument("-o", "--output",
                        type=str,
                        dest="output",
                        default="man",
                        help="Path to write the generated man pages; defaults to the same directory as the doxyfile.",
                        metavar="PATH")
    group.add_argument("-f", "--filter",
                        type=str,
                        dest="pattern",
                        help="XML files matching this filter are excluded from processing.",
                        metavar="REGEX")
    group.add_argument("-S", "--synopsis",
                        action='append',
                        nargs='+',
                        choices=["functions", "composites", "enums", "variables", "typedefs", "macros"],
                        dest="_synopsis",
                        metavar="TYPE",
                        help="Includes TYPE in the SYNOPSIS section of man pages, where TYPE is 'functions', 'composites', 'enums' 'variables', 'typedefs, or 'macros'. "
                            "This option applies to header file man pages; function man pages implicitly include the function signature in their SYNOPSIS section."
                            "This option may be specified one or more times with a different TYPE.")

    group = parser.add_argument_group()
    group.add_argument("--function-params", action="store_true", dest="function_parameters", help="include function \\param documentation in the functions man page")
    group.add_argument("--macro-params", action="store_true", dest="macro_parameters", help="include macro \\param documentation when documenting macros")
    group.add_argument("--composite-fields", action="store_true", dest="composite_fields", help="include documentation for struct and union fields when documenting them")

    group = parser.add_argument_group()
    group.add_argument("--topic", type=str, dest="topic", help="text positioned at the top of the man page; defaults to PROJECT_NAME in the Doxygen config", metavar="TEXT")
    group.add_argument("--section", type=int, dest="section", help="integer from 1-9", default=3, metavar="NUMBER")
    group.add_argument("--footer-middle", type=str, dest="footer_middle", help="text centered at the bottom", metavar="TEXT")
    group.add_argument("--footer-inside", type=str, dest="footer_inside", help="text positioned at the bottom left", metavar="TEXT")
    group.add_argument("--header-middle", type=str, dest="header_middle", help="text centered in the header", metavar="TEXT")
    group.add_argument("--autofill", action="store_true", dest="autofill", help="autofill header and footer text where possible")

    group = parser.add_argument_group()
    group.add_argument("--preamble", type=str, dest="preamble_file", help="file name to extract preamble content from", metavar="FILE")
    group.add_argument("--epilogue", type=str, dest="epilogue_file", help="file name to extract epilogue content from", metavar="FILE")

    args = Arguments()
    args = parser.parse_args(arguments, namespace=args)
    args.finish()

    # Get the preamble.
    if args.preamble_file is not None:
        if not os.path.exists(args.preamble_file):
            print("error: could not find: {0}".format(args.preamble_file), file=args.stderr)
            return 1
        with open(args.preamble_file, "r", encoding="utf-8") as fp:
            args.preamble = fp.read()

    # Get the epilogue.
    if args.epilogue_file is not None:
        if not os.path.exists(args.epilogue_file):
            print("error: could not find: {0}".format(args.epilogue_file), file=args.stderr)
            return 1
        with open(args.epilogue_file, "r", encoding="utf-8") as fp:
            args.epilogue = fp.read()

    return main(args.doxyfile, args)

def start() -> None:
    sys.exit(parse_args())

if __name__ == "__main__": 
    start()
