# Manos

**Manos** is a man page generator for C projects that use Doxygen for documentation generation.

Manos does **not** require any modifications to your project, code comments, or Doxygen configuration file.

[![Build Status](https://github.com/hgs3/manos/actions/workflows/build.yml/badge.svg)](https://github.com/hgs3/manos/actions/workflows/build.yml)

## Why?

Doxygen's man page output `(GENERATE_MAN = YES)` is less-than-stellar for projects written in the C programming language.
For example the formatting and lack of per-function man page is atypical of what one would expect.
Manos corrects these shortcomings by generating a man page per-function and with defacto standard formatting.

## Installation

Manos requires Python 3.10 or newer and Doxygen 1.9.2 or newer.

Install the project through git checkout or install using your package management tool of choice.
In these example `pip` is used.

```
$ pip install manos
```

or from repository checkout:

```
$ git clone https://github.com/hgs3/manos
$ cd manos
$ pip install .
```

## Usage

Manos can be used from the command-line or as a Python module in code.

After installing Manos, run the following command(s) substituting `Doxyfile` with the name of your Doxygen configuration file.
If successful, there will be a directory created named `man` with your beautiful man pages.

#### Command-line Usage

```
$ manos Doxyfile
```

#### Code Usage

```py
import manos
manos.process("path/to/your/Doxyfile")
```

## Documentation

Manos lets you customize the generated output in various ways.
The complete list of customization options can be retrieved by running `manos -h` locally.

Users on *nix systems are encouraged to review the man page for Manos with `man manos`.

## Local Development

If you intend to develop Manos locally, then first install the required development dependencies with:

```
$ pip install -r requirements.txt
```

Run unit tests with:

```
$ pytest
```

Run type checking with:

```
$ mypy --strict manos
$ mypy --strict tests
```

## License

**Manos** is available under the [GNU General Public License v3.0](LICENSE).

The project is named after the no-buget horror [cult-classic film](https://en.wikipedia.org/wiki/Manos:_The_Hands_of_Fate) of the same name.
