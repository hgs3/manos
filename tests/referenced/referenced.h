/*! \file referenced.h
 *  \brief Referenced functions.
 *
 *  Let's reference other functions.
 *  Like #foo and #bar.
 * 
 *  \sa #baz
 */

/*! \brief Foo.
 *
 *  Let's reference #bar.
 * 
 *  Lets also reference ourselves - i.e. function #foo - just to prove that circular
 *  references do not appear under the SEE ALSO section of its own man page.
 */
void foo(void);

/*! \brief Bar.
 *
 *  Let's reference multiple functions use Doxygen commands.
 *
 *  \sa foo
 *  \sa baz
 */
void bar(void);

/*! \brief Baz.
 *
 *  Let's reference another function.
 * 
 *  \sa bar
 */
void baz(void);
