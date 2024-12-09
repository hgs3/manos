/*! \file preprocessor.h
 *  \brief Preprocessor definition tests.
 *
 *  The C preprocessor is the macro preprocessor for several computer programming languages,
 *  such as C, Objective-C, C++, and a variety of Fortran languages.
 *  The preprocessor provides inclusion of header files, macro expansions, conditional compilation, and line control.
 *
 *  In many C implementations, it is a separate program invoked by the compiler as the first part of translation.
 *
 *  The language of preprocessor directives is only weakly related to the grammar of C, and so is sometimes used to process other kinds of text files.
 */

/*! \brief This preproccessor definition is defined when the super awsome feature is enabled.
 *
 *  If you don't want the super awesome feature then delete or comment this macro.
 */
#define ENABLE_AWESOME_FEATURE

/*! \brief This preproccessor macro evaluates to a constant.
 *
 *  You can treat this macro like a variable if you want.
 *  This macro accepts no arguments, but the #ADD macro does.
 */
#define INVALID_KEY "InvalidKey"

/*! \brief Sum two numbers and return the result.
 *
 *  This is a type-generic macro for performing addition between two numeric types.
 *  The left-side is given as \p X and the right-side is given as \p Y and the result of adding them is returned.
 *
 *  \param[in] X Number on the left-hand-side.
 *  \param[in] Y Number on the right-hand-side.
 *  \return The sum of \p X and \p Y.
 *
 *  \since 0.1.0
 */
#define ADD(X,Y) ((X) + (Y))
