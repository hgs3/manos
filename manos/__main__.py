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

from typing import List, Set, Dict, Tuple, Optional, TextIO, cast
from io import TextIOWrapper

import lxml
import lxml.etree
import os
import sys
import subprocess
import glob
import shutil
import argparse
import datetime
import re

from .option import args, Arguments
from .roff import Roff
from . import doxygen as du

def lowerify(text: str) -> str:
    if len(text) == 0:
        return text
    if len(text) >= 2 and text[0].isupper() and not text[1].isupper():
        text = text[0].lower() + text[1:] # Lowercase first letter, unless it begins an acronym.
    return text

def briefify(brief: str) -> str:
    return lowerify(brief).rstrip('.') # Remove trailing punctuation.

def emit_special_sections(ctx: du.Context, file: TextIOWrapper) -> None:
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
    assert du.state.project_name is not None
    params: List[str] = []

    # The '.TH' macro always includes topic and section number.
    if args.topic is not None:
        params.append(f'"{args.topic}"')
    else:
        params.append(f'"{du.state.project_name.upper()}"')
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
    elif args.autofill and du.state.project_version is not None:
        params.append(f'"{du.state.project_name} {du.state.project_version}"')
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

def generate_enum(enum: du.Enum) -> None:
    roff = Roff()
    roff.append_macro(".SH NAME")
    roff.append_text(f'{enum.name} \\- {briefify(enum.brief)}')

    if du.state.project_brief is not None:
        roff.append_macro('.SH LIBRARY')
        roff.append_text(du.state.project_brief.strip())
    roff.append_macro('.SH SYNOPSIS')
    roff.append_macro('.nf')
    #file.write(f'.B #include <{header_display_name}>\n')
    roff.append_macro('.PP')
    roff.append_text(f'enum {enum.name} {{\n')
    for elem in enum.elements:
        roff.append_text(f'    {elem.name},\n')
    roff.append_text('};')
    roff.append_macro('.fi')
    roff.append_macro('.SH DESCRIPTION')
    roff.append_roff(enum.description)

    # Write the file.
    file = open(output_path(f"{enum.name}.3"), "w", encoding="utf-8")
    if args.preamble is not None:
        file.write(args.preamble)
    file.write(heading())
    file.write(str(roff))
    if args.epilogue is not None:
        file.write(args.epilogue)
    file.close()

def parse_function_signature(element: lxml.etree._Element) -> str:
    type = du.process_text(element.find("type"))
    name = du.process_text(element.find("name"))
    signature = f'.BI "{type}'
    # If the return type ends with an astrisk, then that means it's a pointer type
    # and there should be no whitespace between it and the function name.
    if not type.endswith("*"):
        signature += " "
    signature += f'{name}('
    params = element.findall("param")
    for index, param in enumerate(params):
        param_type = du.process_text(param.find("type"))
        declname = param.find("declname")
        signature += param_type
        if declname is not None:
            # If the parameter type ends with an astrisk, that means it's pointer type
            # and there should be no whitespace between it and the parameter name.
            if not param_type.endswith("*"):
                signature += " "
            # Emit the name of the paramter.
            param_name = du.process_text(declname)
            signature += f'" {param_name} "'
        # Add a comma between each parameter.
        if index < len(params) - 1:
            signature += ', '
    signature += ');"'
    return signature

def parse_function(element: lxml.etree._Element, header_display_name: str) -> None:
    id = element.get("id")
    assert id is not None, "function must have a Doxygen assigned identifier"

    ctx = du.Context()
    if id in du.state.compounds:
        compound = du.state.compounds[id]
        if isinstance(compound, du.Function):
            ctx.active_function = compound

    name = du.process_text(element.find("name"))
    brief = briefify(du.process_brief(element.find("briefdescription")))
    description = du.process_description(ctx, element.find("detaileddescription"))
    file = open(output_path(f"{name}.3"), "w", encoding="utf-8")
    if args.preamble is not None:
        file.write(args.preamble)
    file.write(heading())
    file.write(".SH NAME\n")
    file.write(f'{name} \\- {brief}\n')
    if du.state.project_brief is not None:
        file.write('.\\" --------------------------------------------------------------------------\n')
        file.write('.SH LIBRARY\n')
        file.write(du.state.project_brief.strip() + "\n")
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
    assert id in du.state.compounds, "function was not discovered during preparse"
    compound = du.state.compounds[id]
    if isinstance(compound, du.Function):
        group_id = compound.group_id
        if group_id is not None:
            assert group_id in du.state.compounds, "group was not discovered during preparse"
            # Add all functions belonging to the same group as this one to its SEE ALSO man page section.
            compound = du.state.compounds[group_id]
            if isinstance(compound, du.Group):
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
    ctx = du.Context()
    header_name = du.process_text(element.find("compoundname"))
    header_display_name = header_name
    header_brief = briefify(du.process_brief(element.find("briefdescription")))
    content = du.process_as_roff(ctx, element.find("detaileddescription"))
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
            if file_xml in du.state.examples:
                for example in du.state.examples[file_xml]:
                    ctx.examples.append(du.process_as_roff(ctx, example.description))

    for innerclass in element.findall("innerclass"):
        refid_xml = innerclass.get("refid")
        assert refid_xml is not None
        compound = du.state.compounds[refid_xml]
        assert isinstance(compound, du.CompositeType)
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
        for memberdef in sectiondef.findall("memberdef"):
            kind = memberdef.get("kind")
            if kind == "function":
                content.append_macro('.\\" -------------------------------------')
                content.append_macro('.SS Functions')
                for memberdef in sectiondef.findall("memberdef"):
                    name_xml = memberdef.find("name")
                    name = (name_xml.text or "") if name_xml is not None else ""
                    brief = du.process_brief(memberdef.find("briefdescription"))
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
                            type_content = du.process_brief(type_xml)
                            brief = du.process_brief(memberdef.find("briefdescription"))
                            description_roff = du.process_as_roff(ctx, memberdef.find("detaileddescription"))
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
                        brief = du.process_brief(memberdef.find("briefdescription"))
                        description_roff = du.process_as_roff(ctx, memberdef.find("detaileddescription"))
                        content.append_macro('.\\" -------------------------------------')
                        content.append_macro(f'.SS The {name_xml.text} enumeration')
                        content.append_text(brief)
                        content.append_macro('.PP')
                        content.append_macro('.in +4n')
                        content.append_macro('.EX')
                        content.append_source(f'enum {name_xml.text} {{')
                        enums.append_macro(f'.B enum {name_xml.text} {{')
                        for enumval in memberdef.findall('enumvalue'):
                            name = du.process_text(enumval.find('name'))
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
                            name = du.process_text(enumval.find("name"))
                            brief = du.process_brief(enumval.find("briefdescription"))
                            if len(brief) > 0:
                                description_roff = du.process_as_roff(ctx, enumval.find("detaileddescription")).simplify()
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
                        brief = du.process_brief(memberdef.find("briefdescription"))
                        description_roff = du.process_as_roff(ctx, memberdef.find("detaileddescription"))
                        type_xml = memberdef.find("type")
                        name_xml = memberdef.find("name")
                        if type_xml is not None and type_xml.text is not None \
                            and name_xml is not None and name_xml.text is not None:
                            argsstring = du.process_text(memberdef.find("argsstring"))
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
                                signature += du.process_text(param_xml)
                                if index < len(params) - 1:
                                    signature += ","
                            signature += ")"
                        brief = du.process_brief(memberdef.find("briefdescription"))
                        ctx.clear_signature()
                        description_roff = du.process_as_roff(ctx, memberdef.find("detaileddescription"))
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
    if du.state.project_brief is not None:
        file.write('.\\" --------------------------------------------------------------------------\n')
        file.write('.SH LIBRARY\n')
        file.write(du.state.project_brief.strip() + "\n")
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

def preparse_xml(filename: str) -> None:
    tree = lxml.etree.parse(filename)
    if tree.getroot().tag == "doxyfile":
        project_name_xml = cast(List[lxml.etree._Element], tree.xpath("//option[@id='PROJECT_NAME']/value"))
        project_brief_xml = cast(List[lxml.etree._Element], tree.xpath("//option[@id='PROJECT_BRIEF']/value"))
        project_number_xml = cast(List[lxml.etree._Element], tree.xpath("//option[@id='PROJECT_NUMBER']/value"))
        if len(project_name_xml) > 0:
            if text := project_name_xml[0].text:
                du.state.project_name = dequote(text)
        if len(project_brief_xml) > 0:
            if text := project_brief_xml[0].text:
                du.state.project_brief = dequote(project_brief_xml[0].text)
        if len(project_number_xml) > 0:
            if text := project_number_xml[0].text:
                du.state.project_version = dequote(project_number_xml[0].text)
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
            composite = du.CompositeType(id, True)
            composite.name = du.process_text(element.find("compoundname"))
            du.state.compounds[id] = composite
        elif kind == "union":
            composite = du.CompositeType(id, False)
            composite.name = du.process_text(element.find("compoundname"))
            du.state.compounds[id] = composite
        elif kind == "file":
            # Create a compound for the file.
            id = element.get("id")
            assert id is not None
            name_xml = element.find("compoundname")
            assert name_xml is not None
            assert name_xml.text is not None
            file = du.File(name_xml.text)
            du.state.compounds[id] = file
            # Parse all other definitions.
            for sectiondef in element.findall("sectiondef"):
                for memberdef in sectiondef.findall("memberdef"):
                    # Extract the unique identifiers for this compound.
                    group_id: Optional[str] = None
                    id = memberdef.get("id")
                    assert id is not None
                    if id.startswith("group__"):
                        endpos = id.index("_1")
                        if endpos > 0:
                            group_id = id[:endpos]
                    # Create an object for this compound.
                    kind = memberdef.get("kind")
                    if kind == "function":
                        function = du.Function(id, group_id)
                        function.name = du.process_text(memberdef.find("name"))
                        du.state.compounds[id] = function
                    elif kind == "typedef":
                        typedef = du.Typedef(id, group_id)
                        typedef.name = du.process_text(memberdef.find("name"))
                        du.state.compounds[id] = typedef
                    elif kind == "enum":
                        enum = du.Enum(id, group_id)
                        enum.name = du.process_text(memberdef.find("name"))
                        du.state.compounds[id] = enum
                        # Store all enumeration members in the same dictionary as the enumeration itself.
                        # This is done because when Doxygen references them it does so using a global identifier.
                        for enumval in memberdef.findall("enumvalue"):
                            enumval_id = enumval.get("id")
                            assert enumval_id is not None
                            elem = du.EnumElement(enumval_id)
                            elem.name = du.process_text(enumval.find("name"))
                            enum.elements.append(elem)
                            du.state.compounds[enumval_id] = elem
                    elif kind == "define":
                        define = du.Define(id, group_id)
                        define.name = du.process_text(memberdef.find("name"))
                        du.state.compounds[id] = define
                    # Associate the compound with the file.
                    if id in du.state.compounds:
                        file.compounds.append(du.state.compounds[id])
    # Track all groups and the functions that belong to them.
    # This is used to reference all other functions under each functions SEE ALSO man page section.
    elif kind == "group":
        id = element.get("id")
        assert id is not None
        group = du.Group(id)
        group.name = du.process_text(element.find("name"))
        du.state.compounds[id] = group
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
                if file_xml in du.state.examples:
                    du.state.examples[file_xml].append(du.Example(description_xml))
                else:
                    du.state.examples[file_xml] = [du.Example(description_xml)]

def parse_xml(filename: str) -> None:
    tree = lxml.etree.parse(filename)
    element = tree.find("compounddef")
    if element is None:
        return
    kind = element.get("kind")
    # Only consider source files (e.g. ignore Markdown files).
    language = element.get("language")
    if language == "C++":
        # Doxygen writes docs for structs and unions in their own individual .xml files.
        if kind in ["struct", "union"]:
            compound = du.state.compounds[id]
            assert isinstance(compound, du.CompositeType)
            compound.brief = du.process_brief(element.find("briefdescription"))
            compound.description = du.process_as_roff(du.Context(), element.find("detaileddescription"))
            for sectiondef in element.findall("sectiondef"):
                for memberdef in sectiondef.findall("memberdef"):
                    field = du.Field()
                    field.type = du.process_text(memberdef.find("type"))
                    field.name = du.process_text(memberdef.find("name"))
                    field.argstring = du.process_text(memberdef.find("argsstring"))
                    field.brief = du.process_brief(memberdef.find("briefdescription"))
                    field.description = du.process_as_roff(du.Context(), memberdef.find("detaileddescription"))
                    compound.fields.append(field)
        elif kind == "file":
            # Create a compound for the file.
            id = element.get("id")
            assert id is not None
            name_xml = element.find("compoundname")
            assert name_xml is not None
            assert name_xml.text is not None
            file = du.File(name_xml.text)
            du.state.compounds[id] = file
            # Parse all other definitions.
            for sectiondef in element.findall("sectiondef"):
                for memberdef in sectiondef.findall("memberdef"):
                    if id := memberdef.get("id"):
                        compound = du.state.compounds[id]
                        if isinstance(compound, du.Function) or isinstance(compound, du.Typedef) or isinstance(compound, du.Define):
                            compound = du.state.compounds[id]
                            compound.brief = du.process_brief(memberdef.find("briefdescription"))
                            compound.description = du.process_description(memberdef.find("detaileddescription"))
                        elif isinstance(compound, du.Enum):
                            enum = du.state.compounds[id]
                            enum.brief = du.process_brief(memberdef.find("briefdescription"))
                            enum.description = du.process_description(memberdef.find("detaileddescription"))
                            # Store all enumeration members in the same dictionary as the enumeration itself.
                            # This is done because when Doxygen references them it does so using a global identifier.
                            for enumval in memberdef.findall("enumvalue"):
                                if enumval_id := enumval.get("id"):
                                    elem = du.state.compounds[enumval_id]
                                    elem.brief = du.process_brief(enumval.find("briefdescription"))
                                    elem.description = du.process_description(enumval.find("detaileddescription"))
                        # # Parse function arguments.
                        # if isinstance(compound, du.Function):
                        #     # Note that the following XPath recursivly searches the XML.
                        #     for param in memberdef.findall('.//parameterlist[@kind="param"]/*/*/parametername'):
                        #         if param.text is not None:
                        #             function.params.add(param.text)
    # Track all groups and the functions that belong to them.
    # This is used to reference all other functions under each functions SEE ALSO man page section.
    elif kind == "group":
        if id := element.get("id"):
            group = du.state.compounds[id]
            group.brief = du.process_brief(element.find("brief"))
            group.description = du.process_description(element.find("description"))

# def parse_xml(file: str) -> None:
#     tree = lxml.etree.parse(file)
#     element = tree.find("compounddef")
#     if element is None:
#         return
#     # Only consider source files (e.g. ignore Markdown files).
#     language = element.get("language")
#     if language != "C++":
#         return
#     kind = element.get("kind")
#     if kind == "file":
#         header_display_name: Optional[str] = None
#         location = element.find("location")
#         if location is not None and args.include_path == "full":
#             header_display_name = location.get("file")
#         if header_display_name is None:
#             header_display_name = du.process_text(element.find("compoundname"))
#         parse_header(element)
#         for sectiondef in element.findall("sectiondef"):
#             for memberdef in sectiondef.findall("memberdef"):
#                 if memberdef.get("kind") == "function":
#                     parse_function(memberdef, header_display_name)

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
    assert du.state.project_name is not None

    # Extract documentation for top-level compound data types.
    # Doxygen writes struct and union docs to their own XML files.
    # These are processed first before processing the header XML.
    for file in xml_files:
        parse_xml(file)

    # Write documentation pages for compound data types.
    for compound in du.state.compounds.values():
        if isinstance(compound, du.Enum):
            generate_enum(compound)

    # Delete the temporary Doxyfile cloned that was from the original.
    if os.path.exists(doxyfile_manos):
        os.remove(doxyfile_manos)
    return 0

def main(doxyfile: str, arguments: Arguments) -> int:
    # Reset globla du.state.
    global args
    du.state = du.State()
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

# TODO: Handle groups by extracting the group documentation for the COMPOUNDs referenced in the HEADER and EMIT that documentation as an SS section flattening the subheaders of it.
#       List that groups FUNCTIONS, ENUMS, STRUCTS, etc... man page referneces in a table!
