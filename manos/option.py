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

from typing import List, Set, Tuple, Optional, TextIO

import os
import sys
import argparse

class Arguments(argparse.Namespace):
    def __init__(self) -> None:
        self.doxyfile = ""
        self.output = "man"
        self._synopsis: List[List[str]] = []
        self.synopsis: Set[str] = set()
        self.function_parameters = False
        self.composite_fields = False
        self.subsections = False
        self.preserve_styles = False
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

args = Arguments()
