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

from manos import process
from manos.__main__ import parse_args

from typing import Set, List, Tuple, Optional, Generator, TextIO
from typing_extensions import TypedDict, Unpack

import pytest
import pytest_mock
import pathlib
import filecmp
import os

class Params(TypedDict, total=False):
    function_parameters: bool
    macro_parameters: bool
    composite_fields: bool
    topic: Optional[str]
    section: int
    include_path: str
    footer_middle: Optional[str]
    footer_inside: Optional[str]
    header_middle: Optional[str]
    autofill: bool
    preamble: Optional[str]
    epilogue: Optional[str]
    exclusion_pattern: Optional[str]
    synopsis: Set[str]
    stdout: Optional[TextIO]
    stderr: Optional[TextIO]
    doxygen_settings: List[Tuple[str,str]]

WORKING_DIR = pathlib.Path(__file__).parent

@pytest.fixture(autouse=True)
def run_before_and_after_tests() -> Generator[None, None, None]:
    dir = os.getcwd()
    yield
    os.chdir(dir)

def assert_snapshot(path: str, outdir: str = "snapshot", **kwargs: Unpack[Params]) -> None:
    os.chdir(os.path.join(WORKING_DIR, path))
    assert process("Doxyfile", **kwargs) == 0
    if os.path.exists(outdir):
        dcmp = filecmp.dircmp(outdir, "man")
        for name in dcmp.diff_files:
            print("{0} found in {1} and {2}".format(name, dcmp.left, dcmp.right))
        assert len(dcmp.diff_files) == 0
    else:
        # The test is either being executed for the first time OR the output directory
        # was deleted. In either case, rename the "man" directory to the name of the
        # expected results directory so it is present when the test is re-run.
        os.rename("man", outdir)

def assert_snapshot_parse_args(path: str, arguments: List[str], outdir: str = "snapshot") -> None:
    os.chdir(os.path.join(WORKING_DIR, path))
    assert parse_args(arguments) == 0
    if os.path.exists(outdir):
        dcmp = filecmp.dircmp(outdir, "man")
        for name in dcmp.diff_files:
            print("{0} found in {1} and {2}".format(name, dcmp.left, dcmp.right))
        assert len(dcmp.diff_files) == 0
    else:
        # The test is either being executed for the first time OR the output directory
        # was deleted. In either case, rename the "man" directory to the name of the
        # expected results directory so it is present when the test is re-run.
        os.rename("man", outdir)

def test_missing_configfile(capsys: pytest.CaptureFixture[str]) -> None:
    assert parse_args(["DoesNotExist"]) == 1
    assert capsys.readouterr().err == "error: missing configuration file: DoesNotExist\n"

def test_missing_preamble(capsys: pytest.CaptureFixture[str]) -> None:
    assert parse_args(["--preamble", "DoesNotExist", os.path.join(WORKING_DIR, "empty", "Doxyfile")]) == 1
    assert capsys.readouterr().err == "error: could not find: DoesNotExist\n"

def test_missing_epilogue(capsys: pytest.CaptureFixture[str]) -> None:
    assert parse_args(["--epilogue", "DoesNotExist", os.path.join(WORKING_DIR, "empty", "Doxyfile")]) == 1
    assert capsys.readouterr().err == "error: could not find: DoesNotExist\n"

def test_section_underflow(capsys: pytest.CaptureFixture[str]) -> None:
    assert parse_args(["--section", "0", os.path.join(WORKING_DIR, "empty", "Doxyfile")]) == 1
    assert capsys.readouterr().err == "error: expected section in the inclusive range 1-9\n"

def test_section_overflow(capsys: pytest.CaptureFixture[str]) -> None:
    assert parse_args(["--section", "10", os.path.join(WORKING_DIR, "empty", "Doxyfile")]) == 1
    assert capsys.readouterr().err == "error: expected section in the inclusive range 1-9\n"

# Test the minimum allowed section number.
def test_section_min() -> None:
    assert_snapshot("empty", "snapshot-section-min", section=1)

# Test the maximum allowed section number.
def test_section_max() -> None:
    assert_snapshot("empty", "snapshot-section-max", section=9)

def test_empty() -> None:
    assert_snapshot("empty")

def test_styling() -> None:
    assert_snapshot("styling")

def test_lists_ordered() -> None:
    assert_snapshot("lists-ordered")

def test_lists_unordered() -> None:
    assert_snapshot("lists-unordered")

def test_links() -> None:
    assert_snapshot("links")

def test_sections() -> None:
    assert_snapshot("sections")

def test_deprecated() -> None:
    assert_snapshot("deprecated")

def test_codeblock() -> None:
    assert_snapshot("codeblock")

def test_code_references() -> None:
    assert_snapshot("code-references")

def test_dangling_punctuation() -> None:
    assert_snapshot("dangling-punctuation")

def test_inline_code() -> None:
    assert_snapshot("inline-code")

def test_examples() -> None:
    assert_snapshot("examples")

def test_admonition() -> None:
    assert_snapshot("admonition")

def test_extra_sections() -> None:
    assert_snapshot("extra-sections")

def test_referenced() -> None:
    assert_snapshot("referenced")

def test_functions() -> None:
    assert_snapshot("functions")

def test_functions_params() -> None:
    assert_snapshot("functions-params")

def test_functions_with_arguments_section() -> None:
    assert_snapshot("functions", "snapshot-arguments-section", function_parameters=True)

def test_functions_grouped() -> None:
    assert_snapshot("functions-grouped")

def test_structs() -> None:
    assert_snapshot("structs")

def test_structs_with_field_docs() -> None:
    assert_snapshot("structs", "snapshot-with-field-docs", composite_fields=True)

def test_unions() -> None:
    assert_snapshot("unions")

def test_unions_with_field_docs() -> None:
    assert_snapshot("unions", "snapshot-with-field-docs", composite_fields=True)

def test_enums() -> None:
    assert_snapshot("enums")

def test_variables() -> None:
    assert_snapshot("variables")    

def test_typedefs() -> None:
    assert_snapshot("typedefs")

def test_preprocessor() -> None:
    assert_snapshot("preprocessor")

def test_preprocessor_with_param_docs() -> None:
    assert_snapshot("preprocessor", "snapshot-with-param-docs", macro_parameters=True)

def test_unsupported_commands() -> None:
    assert_snapshot("unsupported-commands")

def test_decorations() -> None:
    params: Params = {
        "topic": "Foo",
        "footer_middle": "Bar",
        "footer_inside": "Baz",
        "header_middle": "Qux",
        "preamble": '\\" This appears at the top.',
        "epilogue": '\\" This appears at the bottom.',
    }
    assert_snapshot("decorations", "snapshot", **params)

def test_preamble_file() -> None:
    assert_snapshot_parse_args("preamble", [
        "--preamble",
        os.path.join(WORKING_DIR, "preamble", "preamble.txt"),
        os.path.join(WORKING_DIR, "preamble", "Doxyfile"),
    ])

def test_epilogue_file() -> None:
    assert_snapshot_parse_args("epilogue", [
        "--epilogue",
        os.path.join(WORKING_DIR, "epilogue", "epilogue.txt"),
        os.path.join(WORKING_DIR, "epilogue", "Doxyfile"),
    ])

def test_filter() -> None:
    assert_snapshot("filter")

def test_filter_exclude() -> None:
    assert_snapshot("filter", "snapshot-exclude", exclusion_pattern="_.*")

def test_simple() -> None:
    assert_snapshot("simple")

def test_complex() -> None:
    assert_snapshot("complex")

def test_complex_detailed_synopsis() -> None:
    assert_snapshot("complex", "complex-detailed-synopsis", synopsis=set(
        ["functions", "composites", "enums", "variables", "typedefs", "macros"]))

def test_fullpath() -> None:
    assert_snapshot("functions", "snapshot-absolute-path",
                    include_path="full",
                    doxygen_settings=[
                        ("STRIP_FROM_PATH", os.path.dirname(os.path.abspath(__file__))),
                    ])

# Intentionally exclude all XML files.
def test_no_xml(capsys: pytest.CaptureFixture[str]) -> None:
    os.chdir(os.path.join(WORKING_DIR, "empty"))
    assert process(os.path.join(WORKING_DIR, "empty", "Doxyfile"), exclusion_pattern=".*xml") == 1
    assert capsys.readouterr().err == "error: no XML files match the pattern\n"

def test_no_doxygen_installed(mocker: pytest_mock.MockFixture, capsys: pytest.CaptureFixture[str]) -> None:
    mocker.patch("shutil.which").return_value = None
    assert process(os.path.join(WORKING_DIR, "empty", "Doxyfile")) == 1
    assert capsys.readouterr().err == "error: could not find doxygen;\n       please install it https://www.doxygen.nl/\n"

def test_copyfile_failed(mocker: pytest_mock.MockFixture, capsys: pytest.CaptureFixture[str]) -> None:
    mocker.patch("shutil.copyfile").side_effect = Exception('Boom!')
    assert process(os.path.join(WORKING_DIR, "empty", "Doxyfile")) == 1
    assert capsys.readouterr().err == "error: cannot write to the directory of the doxygen configuration file\n"
