/*! \file subgroups.h
 *  \brief This header defines the full API for the library.
 *
 *  The main header file for the library.
 *
 *  \defgroup AssertAPI Assertions
 *  \defgroup AssertValuesAPI Value Assertions
 */

/*! \brief Fake a function.
 *
 *  Redirect execution from \p src to \p dest.
 *
 *  \param[in] src source function
 *  \param[in] dest mock function
 *
 *  \since 1.0
 */
void fake(void *src, void *dest);

/*! \addtogroup AssertAPI
 *  \brief Verify the expected behavior of a system.
 *
 *  Assertions are statements that check whether a particular condition holds true during the execution of tests.
 * 
 * @{
 */

/*! \brief Abort a test case.
 *
 *  Aborts the test case with an error message.
 *
 *  \param[in] ... error message
 *
 *  \since 1.0
 */
void abort(...);

/*! \brief Fail a test case.
 *
 *  Fails the test case with an error message.
 *
 *  \param[in] ... error message
 *
 *  \since 1.0
 */
void fail(...);

/*! \addtogroup AssertValuesAPI
 *  \brief Compare integers, floating-point numbers, pointers, and booleans.
 * @{
 */

/*! \name Assert Macros
 *  \brief \e Assert macros fail and abort the test case.
 * @{
 */

/*! \brief Check two integers, floating-point numbers, or pointers to determine if \a X == \a Y.
 *
 *  If \a X != \a Y, the test case is aborted.
 *  If you need to compare floats, use #assert_eq_approx.
 *
 *  \param[in] X value
 *  \param[in] Y value to compare against X
 *  \param[in] ... optional message
 *
 *  \since 1.0
 */
void assert_eq(int X, int Y, ...);

/*! \brief Check two floating-point numbers to determine if \a X ≈ \a Y with the specified tolerance
 *
 *  If \a X ≉ \a Y, the test case is aborted.
 * 
 *  \param[in] X floating point number
 *  \param[in] Y floating point number to compare against X
 *  \param[in] T tolerance
 *  \param[in] ... optional message
 * 
 *  \since 1.0
 */
void assert_eq_approx(double X, double Y, double T, ...);

/**@}*/

/*! \name Expect Macros
 *  \brief \e Expect macros fail but do \b not abort the test case.
 * @{
 */

/*! \brief Check two integers, floating-point numbers, or pointers to determine if \a X == \a Y.
 *
 *  If \a X != \a Y, the test case fails.
 *
 *  \param[in] X value
 *  \param[in] Y value to compare against X
 *  \param[in] ... optional message
 *
 *  \since 1.0
 */
void expect_eq(int X, int Y, ...);

/*! \brief Check two floating-point numbers to determine if \a X ≈ \a Y with the specified tolerance
 *
 *  If \a X ≉ \a Y, the test case fails.
 * 
 *  \param[in] X floating point number
 *  \param[in] Y floating point number to compare against X
 *  \param[in] T tolerance
 *  \param[in] ... optional message
 * 
 *  \since 1.0
 */
void expect_eq_approx(double X, double Y, double T, ...);

/**@}*/

/**@}*/

/**@}*/
