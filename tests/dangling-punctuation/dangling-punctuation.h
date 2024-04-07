/*! \file dangling-punctuation.h
 *  \brief Dangling punctuation test cases.
 *
 *  Link to #foobar.
 *  Lets follow it with another sentence that has a #foobar.
 *
 *  Link again to #foobar, but with a comma after it rather than a new sentence.
 * 
 *  Link again, but add a trailing period character after #foobar.
 * 
 *  Link again, but add a trailing exclamation point character after #foobar!
 *
 *  Link again, but add a trailing question mark character after #foobar?
 * 
 *  Style text as \b bold.
 * 
 *  Style text as \e italic.
 * 
 *  Style text as \c code.
 * 
 *  Style text as \b bold, \e italic, and \c code.
 *  Lets follow it with another sentence.
 * 
 *  Triple dot link #foobar...
 * 
 *  Triple dot \b bold...
 * 
 *  Triple dot \e italic...
 * 
 *  Triple dot \c code...
 *
 *  Repeated <b>bold bold bold</b> text.
 * 
 *  Repeated <em>italic italic italic</em> text.
 * 
 *  This is the end of the documentation.
 */

/*! \brief This is a function.
 *
 *  Lets link to #foobar.
 */
void foobar(void);
