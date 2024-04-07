/*! \file functions_grouped.h
 *  \brief Defines grouped functions.
 *
 *  This header file defines functions belonging to various groups and subgroups.
 *  The purpose of this test case is to verify that functions in the same group
 *  are always added to each functions SEE ALSO man page section.
 */

/*! \addtogroup groupA
 *  @{
 */

/*! \addtogroup groupB
 *  @{
 */

/*! \brief Performs foo actons.
 *
 *  Does foo things.
 */
void foo(void);

/*! \brief Performs bar actons.
 *
 *  Does bar things.
 */
void bar(void);

/*! \brief Performs baz actons.
 *
 *  Does baz things.
 */
void baz(void);

/*! @} */

/*! \addtogroup groupC
 *  @{
 */

/*! \brief Performs qux actons.
 *
 *  Does qux things.
 */
void qux(void);

/*! \addtogroup groupD
 *  @{
 */

/*! \brief Finds waldo.
 *
 *  Discover the location of Waldo.
 */
void waldo(void);

/*! \brief Finds fred.
 *
 *  Discover the location of Fred.
 */
void fred(void);

/*! @} */

/*! @} */

/*! @} */
