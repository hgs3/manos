/*! \file foo.h
 *  \brief This header defines the full API for the library.
 *
 *  The main header file for the library.
 *
 *  \defgroup AssertAPI Assertions
 */

/*! \addtogroup AssertAPI
 *  \brief Verify the expected behavior of a system.
 *
 *  Assertions are statements that check whether a particular condition holds true during the execution of tests.
 * 
 * @{
 */

/*! \brief Quit a test case.
 *
 *  Quits the test case with an error message.
 *
 *  \param[in] ... error message
 *
 *  \since 1.0
 */
void quit(...);

/**@}*/
