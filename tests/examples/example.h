/*! \file example.h
 *  \brief Examples section.
 *
 *  This header file has an EXAMPLES section in this man page.
 *  It also defines functions which themselves have an EXAMPLES section.
 */

/*! \example foo.c
 *  This is an example found in foo.c source file.
 *
 *  It's a very cool example and you will learn a lot from it!
 */

/*! \example bar.c
 *  This is an example found in bar.c source file.
 */

/*! \brief Frobnicate a foo.
 *
 *  This function frobnicates a foo and produces a bar.
 *
 *  \see \ref foo.c
 */
void Frobnicate(int xyz[64]);

/*! \brief Construct a foo.
 *
 *  This function constructs a foo.
 *
 *  \see \ref foo.c
 *  \see \ref bar.c
 */
void MakeFoo(void);
