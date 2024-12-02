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

from typing import List, Set, Dict, Union, Optional, TypeAlias

import lxml
import lxml.etree
import math

from .roff import Roff, Macro, Text
from .ordered_set import OrderedSet
from .option import args

class Compound:
    def __init__(self, id: str, group_id: Optional[str] = None) -> None:
        self.id = id
        self.group_id = group_id
        self.name = "unnamed"
        self.brief = ""
        self.description = Roff()

class Field(Compound):
    def __init__(self, id: str) -> None:
        super().__init__(id)
        self.type = "void"
        self.argstring = ""

class CompositeType(Compound):
    def __init__(self, id: str, is_struct: bool) -> None:
        super().__init__(id)
        self.is_struct = is_struct
        self.fields: List[Field] = []

    @property
    def is_union(self) -> bool:
        return not self.is_struct

class Function(Compound):
    def __init__(self, id: str, group_id: Optional[str] = None) -> None:
        super().__init__(id, group_id)
        self.params: Set[str] = set()

class Enum(Compound):
    def __init__(self, id: str, group_id: Optional[str] = None) -> None:
        super().__init__(id, group_id)
        self.elements: List[EnumElement] = []

class EnumElement(Compound):
    def __init__(self, id: str) -> None:
        super().__init__(id)

class Typedef(Compound):
    def __init__(self, id: str, group_id: Optional[str] = None) -> None:
        super().__init__(id, group_id)

class Define(Compound):
    def __init__(self, id: str, group_id: Optional[str] = None) -> None:
        super().__init__(id, group_id)

class File(Compound):
    def __init__(self, id: str) -> None:
        super().__init__(id)
        self.compounds: List[Compound] = []

class Group(Compound):
    def __init__(self, id: str) -> None:
        super().__init__(id)

class Example:
    def __init__(self, description: lxml.etree._Element) -> None:
        self.description = description

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
                content.append_text(str(process_as_roff(ctx, parameteritem.find("parameterdescription"))))
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
                content.append_text(str(process_as_roff(ctx, parameteritem.find("parameterdescription"))))
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

def process_description(elem: Optional[lxml.etree._Element]) -> Roff:
    return process_as_roff(Context(False), elem)

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

class State:
    def __init__(self) -> None:
        self.project_name: Optional[str] = None
        self.project_brief: Optional[str] = None
        self.project_version: Optional[str] = None
        self.examples: Dict[str, List[Example]] = {}
        self.compounds: Dict[str, Compound] = {}

state = State()