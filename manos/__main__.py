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

from typing import List, Dict, Tuple, Optional, cast
from pygments.lexers.c_cpp import CLexer

import lxml
import lxml.etree
import os
import sys
import subprocess
import glob
import shutil
import argparse
import datetime
import copy
import re

from .option import Arguments
from .roff import Roff, Macro
from . import doxygen as du
from . import option as op

def lowerify(text: str) -> str:
    if len(text) == 0:
        return text
    if len(text) >= 2 and text[0].isupper() and not text[1].isupper():
        text = text[0].lower() + text[1:] # Lowercase first letter, unless it begins an acronym.
    return text

def briefify(brief: str) -> str:
    return lowerify(brief).rstrip('.') # Remove trailing punctuation.

# Construct the '.TH' macro.
def heading() -> str:
    assert du.state.project_name is not None
    params: List[str] = []

    # The '.TH' macro always includes topic and section number.
    if op.args.topic is not None:
        params.append(f'"{op.args.topic}"')
    else:
        params.append(f'"{du.state.project_name.upper()}"')
    params.append(f'"{op.args.section}"')

    # Optional the '.TH' macro may include a footer-middle...
    if op.args.footer_middle is not None:
        params.append(f'"{op.args.footer_middle}"')
    elif op.args.autofill:
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
    if op.args.footer_inside is not None:
        params.append(f'"{op.args.footer_inside}"')
    elif op.args.autofill and du.state.project_version is not None:
        params.append(f'"{du.state.project_name} {du.state.project_version}"')
    else:
        params.append("")

    # There isn't a need to specify a header-middle
    # as it will be auto-provided if omitted.
    if op.args.header_middle is not None:
        params.append(f'"{op.args.header_middle}"')
    else:
        params.append("")

    # Remove trailing empty spaces.
    while len(params) > 0 and params[-1] == "":
        params.pop()

    th = f".TH "
    th += " ".join(params)
    th += "\n"
    return th

def output_path(file: str) -> str:
    return os.path.join(op.args.output, file)

def generate_boilerplate(roff: Roff, compound: du.Compound) -> None:
    if len(compound.deprecated) > 0:
        roff.append_macro('SH', 'DEPRECATION')
        for index,bug in enumerate(compound.deprecated):
            roff.append_roff(bug.simplify())
            if index < len(compound.deprecated) - 1:
                roff.append_macro('PP')

    if len(compound.bugs) > 0:
        roff.append_macro('SH', 'BUGS')
        for index,bug in enumerate(compound.bugs):
            roff.append_roff(bug.simplify())
            if index < len(compound.bugs) - 1:
                roff.append_macro('PP')

    if len(compound.examples) > 0:
        roff.append_macro('SH', 'EXAMPLES')
        for index,example in enumerate(compound.examples):
            if example.description is not None:
                roff.append_roff(example.description.simplify())
            elif example.brief is not None:
                roff.append_text(example.brief)
            if index < len(compound.examples) - 1:
                roff.append_macro('PP')

    if len(compound.authors) > 0:
        roff.append_macro('SH', 'AUTHORS')
        for index,author in enumerate(compound.authors):
            roff.append_roff(author.simplify())
            if index < len(compound.authors) - 1:
                roff.append_macro('PP')

    if len(compound.referenced) > 0:
        roff.append_macro('SH', 'SEE ALSO')
        for index,referenced_compound in enumerate(compound.referenced):
            if index < len(compound.referenced) - 1:
                trailing = ','
            else:
                trailing = ''
            roff.append_macro('BR', f'{referenced_compound.name} (3){trailing}')
 
    assert compound.manpage_name is not None, "cannot emit man page for compound without a man page name"
    file = open(output_path(f"{compound.manpage_name}.3"), "w", encoding="utf-8")
    if op.args.preamble is not None:
        file.write(op.args.preamble)
    file.write(heading())
    file.write(str(roff))
    if op.args.epilogue is not None:
        file.write("\n")
        file.write(op.args.epilogue)
    file.close()

def generate_composite(composite: du.CompositeType) -> None:
    roff = Roff()
    roff.append_macro("SH", "NAME")

    if composite.brief is not None:
        roff.append_text(f'{composite.name} \\- {briefify(composite.brief)}')
    else:
        roff.append_text(f'{composite.name}')

    if du.state.project_brief is not None:
        roff.append_macro('SH', 'LIBRARY')
        roff.append_text(du.state.project_brief.strip())
    roff.append_macro('SH', 'SYNOPSIS')
    roff.append_macro('nf')
    roff.append_macro('B', f'#include <{composite.header}>')
    roff.append_macro('PP')
    roff.append_macro('B', f'{"struct" if composite.is_struct else "union"} {composite.name} {{')
    roff.append_macro('RS')
    for field in composite.fields:
        field_string = field.type
        if not field_string.endswith("*"):
            field_string += " "
        field_string += f"{field.name}{field.argsstring}"
        roff.append_macro('B', f'{field_string};')
    roff.append_macro('RE')
    roff.append_macro('B', '};')
    roff.append_macro('fi')

    if composite.description is not None:
        roff.append_macro('SH', 'DESCRIPTION')
        roff.append_roff(composite.description)
    elif composite.brief is not None:
        roff.append_macro('SH', 'DESCRIPTION')
        roff.append_text(composite.brief)

    if op.args.composite_fields is True and len(composite.fields) > 0:
        roff.append_macro('SH', 'FIELDS')
        for field in composite.fields:
            roff.append_macro('TP')
            roff.append_macro('BR', field.name)
            if field.description is not None:
                # Change each .PP macro into an .IP macro so it's indented under the .TP macro.
                desc = copy.deepcopy(field.description)
                for entry in desc.entries:
                    if isinstance(entry, Macro):
                        if entry.command == "PP":
                            entry.command = "IP"
                roff.append_roff(desc)
            elif field.brief is not None:
                roff.append_text(field.brief)

    # Write the file.
    generate_boilerplate(roff, composite)

def generate_enum(enum: du.Enum) -> None:
    roff = Roff()
    roff.append_macro("SH", "NAME")

    if enum.brief is not None:
        roff.append_text(f'{enum.name} \\- {briefify(enum.brief)}')
    else:
        roff.append_text(f'{enum.name}')

    if du.state.project_brief is not None:
        roff.append_macro('SH', 'LIBRARY')
        roff.append_text(du.state.project_brief.strip())
    roff.append_macro('SH', 'SYNOPSIS')
    roff.append_macro('nf')
    roff.append_macro('B', f'#include <{enum.header}>')
    roff.append_macro('PP')
    roff.append_macro('B', f'enum {enum.name} {{')
    roff.append_macro('RS')
    for elem in enum.elements:
        roff.append_macro('B', f'{elem.name},')
    roff.append_macro('RE')
    roff.append_macro('B', '};')
    roff.append_macro('fi')

    if enum.description is not None:
        roff.append_macro('SH', 'DESCRIPTION')
        roff.append_roff(enum.description)
    elif enum.brief is not None:
        roff.append_macro('SH', 'DESCRIPTION')
        roff.append_text(enum.brief)

    if len(enum.elements) > 0:
        roff.append_macro('SH', 'CONSTANTS')
        for elem in enum.elements:
            roff.append_macro('TP')
            roff.append_macro('BR', elem.name)
            if elem.description is not None:
                # Change each .PP macro into an .IP macro so it's indented under the .TP macro.
                desc = copy.deepcopy(elem.description)
                for entry in desc.entries:
                    if isinstance(entry, Macro):
                        if entry.command == "PP":
                            entry.command = "IP"
                roff.append_roff(desc)
            elif elem.brief is not None:
                roff.append_text(elem.brief)

    # Write the file.
    generate_boilerplate(roff, enum)

def generate_typedef(typedef: du.Typedef) -> None:
    roff = Roff()
    roff.append_macro("SH", "NAME")

    if typedef.brief is not None:
        roff.append_text(f'{typedef.name} \\- {briefify(typedef.brief)}')
    else:
        roff.append_text(f'{typedef.name}')

    if du.state.project_brief is not None:
        roff.append_macro('SH', 'LIBRARY')
        roff.append_text(du.state.project_brief.strip())

    roff.append_macro('SH', 'SYNOPSIS')
    roff.append_macro('nf')
    roff.append_macro('B', f'#include <{typedef.header}>')
    roff.append_macro('PP')
    decl = f'"typedef {typedef.type}'
    # If the parameter type ends with an astrisk, that means it's pointer type
    # and there should be no whitespace between it and the parameter name.
    if not decl.endswith("*"):
        decl += " "
    decl += typedef.name

    # The Doxygen typedef argsstring, when it presents a function prototype, does not
    # tokenize the paramters for us so instead we'll tokenize them ourselves and
    # determine if any match the name of the referenced parameter.
    lexer = CLexer() # type: ignore[no-untyped-call,unused-ignore]
    for _, token in lexer.get_tokens(typedef.argsstring):
        # There shouldn't be any new lines in the argstring, but Pygments is adding them...
        if token == '\n':
            continue
        if token in typedef.argsstring_params:
            decl += f'" {token} "'
        else:
            decl += token

    decl += ';"'
    roff.append_macro("BI", decl)
    roff.append_macro('fi')

    if typedef.description is not None:
        roff.append_macro('SH', 'DESCRIPTION')
        roff.append_roff(typedef.description)
    elif typedef.brief is not None:
        roff.append_macro('SH', 'DESCRIPTION')
        roff.append_text(typedef.brief)

    # Write the file.
    generate_boilerplate(roff, typedef)

def generate_variable(variable: du.Variable) -> None:
    roff = Roff()
    roff.append_macro("SH", "NAME")

    if variable.brief is not None:
        roff.append_text(f'{variable.name} \\- {briefify(variable.brief)}')
    else:
        roff.append_text(f'{variable.name}')

    if du.state.project_brief is not None:
        roff.append_macro('SH', 'LIBRARY')
        roff.append_text(du.state.project_brief.strip())

    roff.append_macro('SH', 'SYNOPSIS')
    roff.append_macro('nf')
    roff.append_macro('B', f'#include <{variable.header}>')
    roff.append_macro('PP')
    decl = variable.type
    # If the parameter type ends with an astrisk, that means it's pointer type
    # and there should be no whitespace between it and the parameter name.
    if not decl.endswith("*"):
        decl += " "
    decl += variable.name + variable.argsstring + ';'
    roff.append_macro("B", decl)
    roff.append_macro('fi')

    if variable.description is not None:
        roff.append_macro('SH', 'DESCRIPTION')
        roff.append_roff(variable.description)
    elif variable.brief is not None:
        roff.append_macro('SH', 'DESCRIPTION')
        roff.append_text(variable.brief)

    # Write the file.
    generate_boilerplate(roff, variable)

def generate_define(define: du.Define) -> None:
    roff = Roff()
    roff.append_macro("SH", "NAME")

    if define.brief is not None:
        roff.append_text(f'{define.name} \\- {briefify(define.brief)}')
    else:
        roff.append_text(f'{define.name}')

    if du.state.project_brief is not None:
        roff.append_macro('SH', 'LIBRARY')
        roff.append_text(du.state.project_brief.strip())

    roff.append_macro('SH', 'SYNOPSIS')
    roff.append_macro('nf')
    roff.append_macro('B', f'#include <{define.header}>')
    roff.append_macro('PP')
    if define.function_like:
        signature = f'"#define {define.name}('
        for index, param in enumerate(define.parameters):
            # Emit the name of the paramter.
            signature += f'" {param.name} "'
            # Add a comma between each parameter.
            if index < len(define.parameters) - 1:
                signature += ', '
        signature += ');"'
        roff.append_macro("BI", signature)
    else:
        signature = f'#define {define.name}'
        if define.initializer is not None:
            signature += f' {define.initializer}'
        roff.append_macro("B", signature)
    roff.append_macro('fi')

    if define.description is not None:
        roff.append_macro('SH', 'DESCRIPTION')
        roff.append_roff(define.description)
    elif define.brief is not None:
        roff.append_macro('SH', 'DESCRIPTION')
        roff.append_text(define.brief)

    if define.function_params is not None and op.args.function_parameters is True:
        roff.append_macro('SH', 'PARAMETERS')
        roff.append_roff(define.function_params)

    if define.description_return is not None:
        roff.append_macro('SH', 'RETURN VALUE')
        roff.append_roff(define.description_return)

    # Write the file.
    generate_boilerplate(roff, define)

def generate_function(func: du.Function) -> None:
    roff = Roff()
    roff.append_macro("SH", "NAME")

    if func.brief is not None:
        roff.append_text(f'{func.name} \\- {briefify(func.brief)}')
    else:
        roff.append_text(f'{func.name}')

    if du.state.project_brief is not None:
        roff.append_macro('SH', 'LIBRARY')
        roff.append_text(du.state.project_brief.strip())

    roff.append_macro('SH', 'SYNOPSIS')
    roff.append_macro('nf')
    roff.append_macro('B', f'#include <{func.header}>')
    roff.append_macro('PP')
    signature = f'"{func.return_type}'
    # If the return type ends with an astrisk, then that means it's a pointer type
    # and there should be no whitespace between it and the function name.
    if not func.return_type.endswith("*"):
        signature += " "
    signature += f'{func.name}('
    for index, param in enumerate(func.parameters):
        signature += param.type
        if param.name is not None or param.array is not None:
            # If the parameter type ends with an astrisk, that means it's pointer type
            # and there should be no whitespace between it and the parameter name.
            if not signature.endswith("*"):
                signature += " "
        if param.name is not None:
            signature += f'" {param.name} "'
        if param.array is not None:
            signature += param.array
        # Add a comma between each parameter.
        if index < len(func.parameters) - 1:
            signature += ', '
    signature += ');"'
    roff.append_macro('BI', signature)
    roff.append_macro('fi')

    if func.description is not None:
        roff.append_macro('SH', 'DESCRIPTION')
        roff.append_roff(func.description)
    elif func.brief is not None:
        roff.append_macro('SH', 'DESCRIPTION')
        roff.append_text(func.brief)

    if func.function_params is not None and op.args.function_parameters is True:
        roff.append_macro('SH', 'PARAMETERS')
        roff.append_roff(func.function_params)

    if func.description_return is not None:
        roff.append_macro('SH', 'RETURN VALUE')
        roff.append_roff(func.description_return)

    # Write the file.
    generate_boilerplate(roff, func)

def generate_header_compounds(compounds: List[du.Compound]) -> Roff:
    if len(compounds) == 0:
        return Roff()

    variables: List[du.Compound] = []
    functions: List[du.Compound] = []
    defines: List[du.Compound] = []
    structs: List[du.Compound] = []
    unions: List[du.Compound] = []
    enums: List[du.Compound] = []

    for compound in compounds:
        if isinstance(compound, du.Function):
            functions.append(compound)
        elif isinstance(compound, du.Define):
            defines.append(compound)
        elif isinstance(compound, du.Enum):
            enums.append(compound)
        elif isinstance(compound, du.CompositeType):
            if compound.is_struct:
                structs.append(compound)
            else:
                unions.append(compound)
        elif isinstance(compound, du.Variable):
            variables.append(compound)

    tables: List[Tuple[str,List[du.Compound]]] = [
        ("Functions", functions),
        ("Defines", defines),
        ("Enumerations", enums),
        ("Structures", structs),
        ("Unions", unions),
        ("Variables", variables),
    ]

    roff = Roff()
    if True:
        emitted = False
        roff.append_macro('TS')
        roff.append_text('tab(;);\n')
        for table, compounds in tables:
            if len(compounds) > 0:
                if emitted:
                    roff.append_source('\n')
                    roff.append_macro('T&')
                roff.append_text('l l.\n')
                roff.append_text(f'\\fB{table}\\fR;\\fBDescription\\fR\n')
                roff.append_text('_\n')
                for compound in compounds:
                    roff.append_text(f'\\fB{compound.name}\\fR(3);')
                    roff.append_text('T{\n')
                    roff.append_text(f'{compound.brief}\n')
                    roff.append_text('T}\n')
                emitted = True
        roff.append_macro('TE')
    else:
        # TODO: Provide a command-line option for toggling the display of compounds.
        for table, compounds in tables:
            if len(compounds) > 0:
                roff.append_macro('PP')
                roff.append_text(f'{table}:')
                for compound in compounds:
                    roff.append_macro('TP')
                    roff.append_macro('BR', f'{compound.name} (3)')
                    roff.append_text(compound.brief)

    return roff

def generate_header(header: du.Header) -> None:
    roff = Roff()
    roff.append_macro("SH", "NAME")
    if header.brief is not None:
        roff.append_text(f'{header.name} \\- {briefify(header.brief)}')
    else:
        roff.append_text(f'{header.name}')

    if du.state.project_brief is not None:
        roff.append_macro('SH', 'LIBRARY')
        roff.append_text(du.state.project_brief.strip())
    roff.append_macro('SH SYNOPSIS')
    roff.append_macro('nf')
    roff.append_macro('B', f'#include <{header.name}>')
    roff.append_macro('fi')

    if header.description is not None:
        roff.append_macro('SH', 'DESCRIPTION')
        roff.append_roff(header.description)
    elif header.brief is not None:
        roff.append_macro('SH', 'DESCRIPTION')
        roff.append_text(header.brief)

    # Top-level and grouped compounds.
    globals: List[du.Compound] = []
    locales: Dict[str, List[du.Compound]] = {}

    # Gather all compounds that belong to groups.
    for compound_id in header.compound_refs:
        # Ignore unsupported compounds or compounds that don't get their own man pages.
        if compound_id not in du.state.compounds:
            continue
        compound = du.state.compounds[compound_id]
        group_id = compound.group_id
        if group_id is None:
            globals.append(compound)
        else:
            if group_id not in locales:
                locales[group_id] = []
            locales[group_id].append(compound)

    # Emit all top-level compounds.
    roff.append_roff(generate_header_compounds(globals))

    # Emit group documentation and their compounds.
    groups: List[Tuple[int,Roff]] = []
    for group_id, compounds in locales.items():
        group = du.state.compounds[group_id]
        group_roff = Roff()
        group_roff.append_macro('SS', group.name)
        if group.description is not None:
            group_roff.append_roff(group.description)
        elif group.brief is not None:
            group_roff.append_text(group.brief)
        group_roff.append_roff(generate_header_compounds(compounds))
        # Keep groups sorted.
        groups.append((du.state.group_ordering.index(group_id), group_roff))

    # Sort by group order in the Doxyfile.
    groups = sorted(groups, key=lambda x: x[0])

    # Emit the sorted groups.
    for order, group_roff in groups:
        roff.append_roff(group_roff)

    # Write the file.
    generate_boilerplate(roff, header)

# Doxygen can begin Doxyfile options with quotes.
# Remove them here.
def dequote(string: str) -> str:
    if string.startswith('"'):
        string = string[1:]
    if string.endswith('"'):
        string = string[:-1]
    return string

def manpageify(compound: du.Compound) -> str:
    # Lowercase the man page name.
    outname = compound.name
    # If the compound is a header file, then truncate its extension.
    if isinstance(compound, du.Header):
        outname = os.path.splitext(outname)[0]
    return outname.lower()

def register_compund(compound: du.Compound) -> None:
    def typeof(compound: du.Compound) -> str:
        if isinstance(compound, du.CompositeType):
            if compound.is_struct:
                return "struct"
            else:
                return "union"
        elif isinstance(compound, du.Typedef):
            return "typedef"
        elif isinstance(compound, du.Define):
            return "define"
        elif isinstance(compound, du.Function):
            return "function"
        elif isinstance(compound, du.Enum):
            return "enumeration"
        elif isinstance(compound, du.Variable):
            return "variable"
        raise Exception("missing compound type")

    if compound.manpage_name is not None:
        if compound.manpage_name not in du.state.manpages:
            du.state.manpages[compound.manpage_name] = compound
        else:
            other = du.state.manpages[compound.manpage_name]
            print(f"error: cannot have {typeof(compound)} and {typeof(other)} man pages both named '{compound.manpage_name}.3'", file=op.args.stderr)
            sys.exit(1)
    du.state.compounds[compound.id] = compound

def extract_group_id(id: str) -> Optional[str]:
    if id.startswith("group__"):
        endpos = id.index("_1")
        if endpos > 0:
            return id[:endpos]
    return None

def preparse_sectiondef(element: lxml.etree._Element) -> None:
    for sectiondef in element.findall("sectiondef"):
        for memberdef in sectiondef.findall("memberdef"):
            # Extract the unique identifiers for this compound.
            id = memberdef.get("id"); assert id is not None
            group_id = extract_group_id(id)
            # Extract the location.
            location = memberdef.find("location"); assert location is not None
            location_file = location.get("file"); assert location_file is not None
            # Doxygen is iconsistant how it stores file locations.
            # We want the base name for the man page.
            if op.args.include_path == "short":
                location_file = os.path.basename(location_file)
            # Create an object for this compound.
            if memberdef.get("kind") == "enum":
                enum = du.Enum(id, group_id)
                enum.name = du.process_text(memberdef.find("name"))
                enum.brief = du.process_brief(memberdef.find("briefdescription"), enum)
                enum.header = location_file
                enum.manpage_name = manpageify(enum)
                register_compund(enum)
                # Store all enumeration members in the same dictionary as the enumeration itself.
                # This is done because when Doxygen references them it does so using a global identifier.
                for enumval in memberdef.findall("enumvalue"):
                    enumval_id = enumval.get("id")
                    assert enumval_id is not None
                    elem = du.EnumElement(enumval_id, enum)
                    elem.name = du.process_text(enumval.find("name"))
                    elem.brief = du.process_brief(enumval.find("briefdescription"), enum)
                    enum.elements.append(elem)
                    register_compund(elem)

def preparse_xml(filename: str) -> None:
    tree = lxml.etree.parse(filename)
    compounddef = tree.find("compounddef")
    if compounddef is None:
        return
    kind = compounddef.get("kind")
    # Only consider source files (e.g. ignore Markdown files).
    language = compounddef.get("language")
    if language == "C++":
        # Doxygen writes docs for structs and unions in their own individual .xml files.
        if kind in ["struct", "union"]:
            id = compounddef.get("id")
            assert id is not None
            composite = du.CompositeType(id, kind == "struct")
            composite.name = du.process_text(compounddef.find("compoundname"))
            composite.manpage_name = manpageify(composite)
            for sectiondef in compounddef.findall("sectiondef"):
                for member in sectiondef.findall("member"):
                    field_id = member.get("refid")
                    assert field_id is not None
                    field = du.Field(field_id, composite)
                    field.name = du.process_text(member.find("name"))
                    composite.fields.append(field)
                    du.state.compounds[field_id] = field
                # For whatever reason, Doxygen only uses "member" when the struct is in a group.
                # If the struct is free standing, then it uses "memberdef" instead.
                for memberdef in sectiondef.findall("memberdef"):
                    field_id = memberdef.get("id")
                    assert field_id is not None
                    field = du.Field(field_id, composite)
                    field.type = du.process_text(memberdef.find("type"))
                    field.name = du.process_text(memberdef.find("name"))
                    field.argsstring = du.process_text(memberdef.find("argsstring"))
                    field.brief = du.process_brief(memberdef.find("briefdescription"), composite)
                    composite.fields.append(field)
            # Extract the location.
            location = compounddef.find("location"); assert location is not None
            location_file = location.get("file"); assert location_file is not None
            # Doxygen is iconsistant how it stores file locations.
            # We want the base name for the man page.
            if op.args.include_path == "short":
                location_file = os.path.basename(location_file)
            composite.header = location_file
            composite.manpage_name = manpageify(composite)
            register_compund(composite)
        elif kind == "file":
            preparse_sectiondef(compounddef)
    elif kind == "group":
        preparse_sectiondef(compounddef)
    # Extract examples to latter include in the associated header file.
    # The examples associated with said header file will be added
    # to the EXAMPLES man page section of said header file.
    elif kind == "example":
        id = compounddef.get("id"); assert id is not None
        example = du.Example(id)
        example.brief = du.process_brief(compounddef.find("briefdescription"), example)
        du.state.compounds[example.id] = example

# Find the first alias compound child element.
def find_aliased_compound(elem: lxml.etree._Element) -> Optional[str]:
    if elem.tag == "ref":
        refid = elem.get("refid")
        assert refid is not None
        return refid
    for child in elem:
        ref = find_aliased_compound(child)
        if ref is not None:
            return ref
    return None

def parse_sectiondef(element: lxml.etree._Element) -> None:
    for sectiondef in element.findall("sectiondef"):
        for memberdef in sectiondef.findall("memberdef"):
            # Extract the unique identifiers for this compound.
            id = memberdef.get("id"); assert id is not None
            group_id = extract_group_id(id)
            # Extract the location.
            location = memberdef.find("location"); assert location is not None
            location_file = location.get("file"); assert location_file is not None
            # Doxygen is iconsistant how it stores file locations.
            # We want the base name for the man page.
            if op.args.include_path == "short":
                location_file = os.path.basename(location_file)
            # Create an object for this compound.
            kind = memberdef.get("kind")
            if kind == "function":
                function = du.Function(id, group_id)
                function.name = du.process_text(memberdef.find("name"))
                function.return_type = du.process_text(memberdef.find("type"))
                function.header = location_file
                function.manpage_name = manpageify(function)
                for param_xml in memberdef.findall("param"):
                    param_name_xml = param_xml.find("declname")
                    param_array_xml = param_xml.find("array")
                    param = du.Function.Parameter()
                    param.name = du.process_text(param_name_xml) if param_name_xml is not None else None
                    param.type = du.process_text(param_xml.find("type"))
                    param.array = du.process_text(param_array_xml) if param_array_xml is not None else None
                    function.parameters.append(param)
                # This must parse AFTER gather the parameter names so if a paramter is referenced
                # then it is referenced _correctly_ as a parameter and not as inline code.
                function.brief = du.process_brief(memberdef.find("briefdescription"), function)
                register_compund(function)
            elif kind == "typedef":
                typedef = du.Typedef(id, group_id)
                typedef.name = du.process_text(memberdef.find("name"))
                typedef.brief = du.process_brief(memberdef.find("briefdescription"), typedef)
                typedef.type = du.process_text(memberdef.find("type"))
                typedef.argsstring = du.process_text(memberdef.find("argsstring"))
                typedef.header = location_file
                typedef.manpage_name = manpageify(typedef)

                # Typedefs that reference a struct, union, or enum and have the same name as said
                # type should be emitted as part of that types man page. This is so two different
                # man pages (one for the type, one for the typedef) are not emitted thereby
                # overwriting each other (last one written would win).
                type_xml = memberdef.find("type")
                if type_xml is not None:
                    ref_id = find_aliased_compound(type_xml)
                    if ref_id in du.state.compounds:
                        referenced_compound = du.state.compounds[ref_id]
                        if isinstance(referenced_compound, du.Enum) or isinstance(referenced_compound, du.CompositeType):
                            if referenced_compound.name == typedef.name:
                                referenced_compound.aliases.append(typedef)
                                du.state.compounds[typedef.id] = referenced_compound
                                continue

                register_compund(typedef)
            elif kind == "define":
                define = du.Define(id, group_id)
                define.name = du.process_text(memberdef.find("name"))
                define.header = location_file
                define.manpage_name = manpageify(define)
                for param_xml in memberdef.findall("param"):
                    declname_xml = param_xml.find("defname")
                    # Mark this macro as being function-like so even if it doesn't have any arguments
                    # it will still appear in the documentation with empty parentheses as parameters.
                    define.function_like = True
                    # For whatever reason even if a macro accepts no parameters doxygen still emits a
                    # en empty <param> element. This should never happen when there are parameters.
                    if declname_xml is None or declname_xml.text is None:
                        define.parameters.clear()
                        break
                    define.parameters.append(du.Define.Parameter(declname_xml.text))
                # Check if this macro defines a simple value that we can emit in the documentation.
                initializer_xml = memberdef.find("initializer")
                if initializer_xml is not None:
                    define.initializer = initializer_xml.text
                # This must parse AFTER gather the parameter names so if a paramter is referenced
                # then it is referenced _correctly_ as a parameter and not as inline code.
                define.brief = du.process_brief(memberdef.find("briefdescription"), define)
                register_compund(define)
            elif kind == "variable":
                # Variables that are members of structs/unions should not be parsed here.
                # These properties are documented alongside the struct/union.
                definition_xml = memberdef.find("definition")
                if definition_xml is not None:
                    if "::" in (definition_xml.text or ""):
                        field = du.state.compounds[id]
                        assert field is not None
                        assert isinstance(field, du.Field)
                        field.type = du.process_text(memberdef.find("type"))
                        field.argsstring = du.process_text(memberdef.find("argsstring"))
                        field.brief = du.process_brief(memberdef.find("briefdescription"), field)
                        continue
                variable = du.Variable(id, group_id)
                variable.brief = du.process_brief(memberdef.find("briefdescription"), variable)
                variable.name = du.process_text(memberdef.find("name"))
                variable.type = du.process_text(memberdef.find("type"))
                variable.argsstring = du.process_text(memberdef.find("argsstring"))
                variable.header = location_file
                variable.manpage_name = manpageify(variable)
                register_compund(variable)

def parse_xml(filename: str) -> None:
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
    if language == "C++" and kind == "file":
        # Create a compound for the file.
        id = element.get("id"); assert id is not None
        name_xml = element.find("compoundname"); assert name_xml is not None and name_xml.text is not None
        # If this file is NOT a header file, then ignore it;
        # files like C files and DOX files should be ignored.
        if not name_xml.text.lower().endswith(".h"):
            return
        header = du.Header(id)
        header.name = name_xml.text
        header.manpage_name = manpageify(header)
        register_compund(header)
        parse_sectiondef(element)
        # Know which compounds are associated with this header file.
        for sectiondef in element.findall("sectiondef"):
            for memberdef in sectiondef.findall("memberdef"):
                id = memberdef.get("id")
                assert id is not None
                header.compound_refs.add(id)
            for member in sectiondef.findall("member"):
                refid = member.get("refid")
                assert refid is not None
                header.compound_refs.add(refid)
    # Track all groups and the functions that belong to them.
    # This is used to reference all other functions under each functions SEE ALSO man page section.
    elif kind == "group":
        id = element.get("id"); assert id is not None
        group = du.Group(id)
        group.name = du.process_text(element.find("title"))
        register_compund(group)
        parse_sectiondef(element)

def postparse_sectiondef(element: lxml.etree._Element) -> None:
    # Parse all other definitions.
    for sectiondef in element.findall("sectiondef"):
        for memberdef in sectiondef.findall("memberdef"):
            if id := memberdef.get("id"):
                if id in du.state.compounds:
                    compound = du.state.compounds[id]
                    if isinstance(compound, du.Function):
                        compound.description = du.process_description(memberdef.find("detaileddescription"), compound)
                        for param_xml in memberdef.findall("param"):
                            type_xml = param_xml.find("type")
                            if type_xml is not None:
                                type_refid = find_aliased_compound(type_xml)
                                if type_refid is not None and type_refid in du.state.compounds:
                                    compound.referenced.append(du.state.compounds[type_refid])
                    elif isinstance(compound, du.Typedef) or isinstance(compound, du.Define) or isinstance(compound, du.Variable):
                        compound.description = du.process_description(memberdef.find("detaileddescription"), compound)
                    elif isinstance(compound, du.Enum):
                        compound.description = du.process_description(memberdef.find("detaileddescription"), compound)
                        # Store all enumeration members in the same dictionary as the enumeration itself.
                        # This is done because when Doxygen references them it does so using a global identifier.
                        for index,enumval in enumerate(memberdef.findall("enumvalue")):
                            elem = compound.elements[index]
                            elem.description = du.process_description(enumval.find("detaileddescription"), compound)

def postparse_xml(filename: str) -> None:
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
            if id := element.get("id"):
                compound = du.state.compounds[id]
                assert isinstance(compound, du.CompositeType)
                compound.description = du.process_description(element.find("detaileddescription"), compound)
                for sectiondef in element.findall("sectiondef"):
                    for index,memberdef in enumerate(sectiondef.findall("memberdef")):
                        field = compound.fields[index]
                        field.description = du.process_description(memberdef.find("detaileddescription"), compound)
        elif kind == "file":
            # Create a compound for the file.
            if id := element.get("id"):
                if id in du.state.compounds:
                    header = du.state.compounds[id]
                    header.brief = du.process_brief(element.find("briefdescription"), header)
                    header.description = du.process_description(element.find("detaileddescription"), header)
                    assert isinstance(header, du.Header)
                    postparse_sectiondef(element)
    # Track all groups and the functions that belong to them.
    # This is used to reference all other functions under each functions SEE ALSO man page section.
    elif kind == "group":
        if id := element.get("id"):
            group = du.state.compounds[id]
            group.brief = du.process_brief(element.find("briefdescription"), group)
            group.description = du.process_description(element.find("detaileddescription"), group)
            postparse_sectiondef(element)
    # Extract examples to latter include in the associated header file.
    # The examples associated with said header file will be added
    # to the EXAMPLES man page section of said header file.
    elif kind == "example":
        if id := element.get("id"):
            example = du.state.compounds[id]
            example.description = du.process_description(element.find("detaileddescription"), example)

# Sort groups and pages by the order in which they are defined.
def parse_index_xml(xmlfile: str) -> None:
    tree = lxml.etree.parse(xmlfile)
    for element in tree.findall("compound"):
        refid = element.get("refid")
        if refid is None:
            continue
        kind = element.get("kind")
        if kind == "group":
            du.state.group_ordering.append(refid)

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
        print("error: cannot write to the directory of the Doxygen configuration file", file=op.args.stderr)
        return 1

    # Generate output directory if it doesn't exist.
    if len(op.args.output) > 0:
        if not os.path.exists(op.args.output):
            os.mkdir(op.args.output)

    # Append additional options onto it.
    clone = open(doxyfile_manos, "a", encoding="utf-8")
    # Add user options.
    for key, value in op.args.doxygen_settings:
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
    # Enable sections only flagged for Manos man pages.
    clone.write("ENABLED_SECTIONS += MANOS\n")
    # This option ensures that if a struct has a typedef it emits
    # seperate documentation for the typedef. Manos will consolidate
    # the documentation for typedefs that merely alias a struct into
    # the structs man page.
    clone.write("TYPEDEF_HIDES_STRUCT = YES\n")
    # Manos expects structs to always be in a seperate XML document.
    clone.write("INLINE_SIMPLE_STRUCTS = NO\n")
    # Strip absolute path names from header file paths.
    clone.write("FULL_PATH_NAMES = NO\n")
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
        print(stdout, file=op.args.stdout)
    if len(stderr) > 0:
        print(stderr, file=op.args.stderr)

    # Extract metadata from all XML files.
    xml_files = glob.glob(os.path.join(working_dir, "xml", "*.xml"))

    # Figure out which files to process and which to skip.
    if op.args.pattern is not None:
        def matches(file: str) -> bool:
            file = os.path.basename(file)
            if r.match(file) is not None:
                return False
            return True
        r = re.compile(op.args.pattern)
        xml_files = list(filter(matches, xml_files))

    # Make sure there are XML files...
    if len(xml_files) == 0:
        print("error: no XML files match the pattern", file=op.args.stderr)
        return 1

    # Extract compound order.
    parse_index_xml(os.path.join(working_dir, "xml", "index.xml"))

    # Extract composite type documentation first.
    for file in xml_files:
        preparse_xml(file)

    # Extract top-level documentation first.
    for file in xml_files:
        parse_xml(file)

    # Extract documentation for top-level compound data types.
    # Doxygen writes struct and union docs to their own XML files.
    # These are processed first before processing the header XML.
    for file in xml_files:
        postparse_xml(file)

    # There must be a project name specified in the Doxygen config.
    # If the user does not specify a name, then Doxygen will default to "My Project".
    assert du.state.project_name is not None

    # Write documentation pages for compound data types.
    for compound in du.state.compounds.values():
        if isinstance(compound, du.Header):
            generate_header(compound)
        elif isinstance(compound, du.Function):
            generate_function(compound)
        elif isinstance(compound, du.CompositeType):
            generate_composite(compound)
        elif isinstance(compound, du.Enum):
            generate_enum(compound)
        elif isinstance(compound, du.Define):
            generate_define(compound)
        elif isinstance(compound, du.Variable):
            generate_variable(compound)
        elif isinstance(compound, du.Typedef):
            generate_typedef(compound)

    # Delete the temporary Doxyfile cloned that was from the original.
    if os.path.exists(doxyfile_manos):
        os.remove(doxyfile_manos)
    return 0

def main(doxyfile: str, arguments: Arguments) -> int:
    # Reset globla du.state.
    du.state = du.State()
    op.args = arguments

    # For the premable to end with a new line character.
    # This ensures the first man page macro begins on its own line.
    if op.args.preamble is not None and not op.args.preamble.endswith("\n"):
        op.args.preamble += "\n"

    # Setup defaults.
    if op.args.section < 1 or op.args.section > 9:
        print("error: expected section in the inclusive range 1-9", file=op.args.stderr)
        return 1

    # Check if the Doxygen configuration file exists.
    if not os.path.exists(doxyfile):
        print("error: missing configuration file: {0}".format(doxyfile), file=op.args.stderr)
        return 1

    # Verify Doxygen is installed.
    if shutil.which("doxygen") is None:
        print("error: could not find Doxygen", file=op.args.stderr)
        print("       please install it https://www.doxygen.nl/", file=op.args.stderr)
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
    if version < (1, 12, 0) or version >= (1, 13, 0):
        print(f"error: Doxygen 1.12 series is required, found version {raw_version}", file=op.args.stderr)
        print("        please upgrade or downgrade it https://www.doxygen.nl/", file=op.args.stderr)
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
    group.add_argument("--with-parameters", action="store_true", dest="function_parameters", help="include PARAMS section in function and macro documentation")
    group.add_argument("--with-fields", action="store_true", dest="composite_fields", help="include FIELDS section in structure and union documentation")
    group.add_argument("--with-subsections", action="store_true", dest="subsections", help="include subsection titles in detailed descriptions")
    group.add_argument("--with-styles", action="store_true", dest="styles", help="include bold, italic, underline, and strikethrough styles")

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

    op.args = Arguments()
    op.args = parser.parse_args(arguments, namespace=op.args)
    op.args.finish()

    # Get the preamble.
    if op.args.preamble_file is not None:
        if not os.path.exists(op.args.preamble_file):
            print("error: could not find: {0}".format(op.args.preamble_file), file=op.args.stderr)
            return 1
        with open(op.args.preamble_file, "r", encoding="utf-8") as fp:
            op.args.preamble = fp.read().strip()

    # Get the epilogue.
    if op.args.epilogue_file is not None:
        if not os.path.exists(op.args.epilogue_file):
            print("error: could not find: {0}".format(op.args.epilogue_file), file=op.args.stderr)
            return 1
        with open(op.args.epilogue_file, "r", encoding="utf-8") as fp:
            op.args.epilogue = fp.read().strip()

    return main(op.args.doxyfile, op.args)

def start() -> None:
    sys.exit(parse_args())

if __name__ == "__main__": 
    start()