/*! \file functions.h
 *  \brief Various function signatures.
 *
 *  This file attempts to test against various function signatures.
 */

/*! \brief Does nothing.
 *
 *  Performs no action.
 */
void nop(void);

/*! \brief Does nothing but accepts arguments.
 *
 *  Test whether empty function signatures format correctly.
 */
void nop2();

/*! \brief Cast to a frob.
 *
 *  Reinterpret \a bar into a frob object.
 * 
 *  \param[in] bar Object to be cast.
 *  \return The casting of the input object to another.
 */
const void *foo(const void *bar);

/*! \brief Cast to a Foo.
 *
 *  Reinterpret \a qux into a Foo object.
 *
 *  \param[in] very_long_argument_name_to_force_wrapping Numeric informative entry.
 *  \return Informational object.
 */
const Foo bar(const double **const very_long_argument_name_to_force_wrapping);

/*! \brief Do the thing.
 *
 *  Perform a mapping of \a a and \a b against \a c.
 * 
 *  \param[in] a Random integer pointer.
 *  \param[inout] b Random volatile integer pointer.
 *  \param[out] c Record with data about the #bar function.
 * 
 *  \retval Address of the mmapping of \a c.
 *  \retval NULL if something went wrong.
 */
volatile int *baz(int *a, volatile int *b, const Bar *restrict c);

/*! \brief Print some formatted text.
 *
 *  Formats \a fmt using the same format escape characters as \c printf
 *  and then writes the result to \a buf.
 *
 *  \param[out] buf Buffer the formatted string will be written to.
 *  \param[in] fmt Format of the resulting string, using printf format specifiers.
 *  \return The number of characters written to \a buf or \c -1 if an error occured.
 */
int println(char *buf, const char *fmt, ...);

/*! \brief Check for errors.
 *
 *  Checks for an error by its code.
 * 
 *  \retval OK no error occured.
 *  \retval NOMEM Out of memory error occured.
 *  \retval NOPERM,NOACCESS,NOWRITE Missing permissions error
 */
int chkerr(void);
