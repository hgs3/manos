"""Manos is a man page generator for C projects using Doxygen.

See the documentation for the 'process' function for details.
"""

__all__ = [
    "process",
]

from typing import List, Set, Tuple, TextIO, Optional
import sys

def process(doxyfile: str,
            output_dir: str = "man",
            section: int = 3,
            include_path: str = "short",
            synopsis: Set[str] = set(),
            exclusion_pattern: Optional[str] = None,
            topic: Optional[str] = None,
            footer_middle: Optional[str] = None,
            footer_inside: Optional[str] = None,
            header_middle: Optional[str] = None,
            autofill: bool = False,
            preamble: Optional[str] = None,
            epilogue: Optional[str] = None,
            function_parameters: bool = False,
            macro_parameters: bool = False,
            composite_fields: bool = False,
            stdout: Optional[TextIO] = None,
            stderr: Optional[TextIO] = None,
            doxygen_settings: List[Tuple[str,str]] = []) -> int:
    """
    Generate man page(s) from a Doxygen configuration file specified by `doxyfile``.

    :param doxyfile: Doxygen configuration file.
    :param output_dir: Directory to write the man pages.
    :param section: Man page section number, must be in the inclusive range 1-9.
    :param include_path: Toggles if header paths include the full path or just the base file name.
    :param synopsis: C constructs to include in the SYNOPSIS of a header's man page (see below).
    :param exclusion_pattern: Excluding file names matching the given regex pattern from man page generation.
    :param topic: Text positioned at the top of the man page (defaults to PROJECT_NAME in the Doxygen config).
    :param autofill: Autofill header and footer text where possible.
    :param preamble: Content to prepend to each man page (e.g. copyright comment).
    :param epilogue: Content to append to each man page.
    :param function_parameters: Toggle \\param documentation in a functions man page.
    :param macro_parameters: Toggle \\param documentation when documenting macros.
    :param composite_fields: Toggle documentation for struct and union fields.
    :param stdout: Redirect Doxygen standard output.
    :param stderr: Redirect Doxygen error output.
    :param doxygen_settings: List of tuples where the first element is the Doxygen setting and the second is its value.
    :return: Zero on success.

    Where ``include_path`` is one of the following:

    * "short"
    * "full"

    Where ``synopsis`` is a set with one or more of the following:

    * "functions"
    * "composites"
    * "enums"
    * "variables"
    * "typedefs"
    * "macros"

    This function should **not** raise any exceptions.
    """

    from .__main__ import Arguments, main
    args = Arguments()
    args.output = output_dir
    args.section = section
    args.include_path = include_path
    args.synopsis = synopsis
    args.pattern = exclusion_pattern
    args.topic = topic
    args.footer_middle = footer_middle
    args.footer_inside = footer_inside
    args.header_middle = header_middle
    args.autofill = autofill
    args.preamble = preamble
    args.epilogue = epilogue
    args.function_parameters = function_parameters
    args.macro_parameters = macro_parameters
    args.composite_fields = composite_fields
    args.doxygen_settings = doxygen_settings
    if stdout is None:
        args.stdout = sys.stdout
    else:
        args.stdout = stdout
    if stderr is None:
        args.stderr = sys.stderr
    else:
        args.stderr = stderr
    return main(doxyfile, args)
