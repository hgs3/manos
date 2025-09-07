# Change Log

All notable changes to this project will be documented in this file.
This project adheres to [Semantic Versioning](http://semver.org/).
Dates are represented via [ISO 8601](https://www.iso.org/iso-8601-date-and-time-format.html)

## [0.6.0] - ???

## [0.5.0] - September 7th, 2025

### Changed

* Substituting Unicode quotation mark characters with Basic Latin (US-ASCII) characters in man page output for maximum compatibility.

## [0.4.0] - February 13th, 2025

### Changed

* Doxygen references only link to man page compounds if custom link text is **not** used. If custom link text is used, the text is shown as-is.

## [0.3.1] - February 11th, 2025

### Fixed

* Correcting a mishandling of compound members when the compound is declared inside a Doxygen group.

## [0.3.0] - January 9th, 2025

### Changed

* Adding 'e.g.' to the set of sentence break exceptions.

### Fixed

* Escaped backslash characters in code examples.
* Removed duplicate fields from structure/union field listings.

## [0.2.0] - December 14th, 2024

### Added

* Introducing output for Doxygen tables.
* Added the `--with-styles` option to include bold, italic, underline, and strikethrough styles in the output.

### Changed

* Remove the `.h` from the header files man page name.
* Generating separate man pages for enumerations, structures, unions, typedefs, and variables.
* Merged the `--macro-params` option with `--with-parameters`.
* Renamed the `--function-params` option to `--with-parameters`.
* Renamed the `--composite-fields` option to `--with-fields`.
* Raising Doxygen version requirements from v1.9.x to v1.12.x.

### Fixed

* Fixing a bug where punctuation was separated from the URL link it followed.

## [0.1.0] - April 6th, 2024

Initial public release.
