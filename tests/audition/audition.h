/*! \file audition.h
 *  \brief This header defines the full API for the library.
 *
 *  The main header file for the library.
 *
 *  \defgroup TestAPI Test Cases
 *  \defgroup FixturesAPI Fixtures
 *  \defgroup AssertAPI Assertions
 *  \defgroup AssertValuesAPI Value Assertions
 *  \defgroup AssertStringsAPI String Assertions
 *  \defgroup AssertMemoryAPI Memory Assertions
 *  \defgroup MockingAPI Mocking
 *  \defgroup UtilityAPI Helpers
 */

#pragma once

#ifndef DOXYGEN
    #if defined(_WIN32) || defined(__CYGWIN__)
        #if defined(DLL_EXPORT)
            #define XAPI __declspec(dllexport)
        #elif defined(AUDITION_STATIC)
            #define XAPI
        #else
            #define XAPI __declspec(dllimport)
        #endif
    #elif __GNUC__ >= 4 || defined(__clang__)
        #define XAPI __attribute__ ((visibility ("default")))
    #else
        #define XAPI
    #endif
#endif

/*! \brief Entry point for a unit test.
 *
 *  It should be followed by a pair of opening and closing curly braces with the test
 *  statements inserted between them.
 *
 *  \param[in] SUITE_NAME the test suite this unit test is part of.
 *  \param[in] TEST_NAME the name of the unit test.
 *  \param[in] ... optional #TestOptions
 *
 *  \since 1.0
 */
#define TEST(SUITE_NAME, TEST_NAME, ...)

#if defined(DOXYGEN)
/*! \var TEST_ITERATION
 *  \brief The iteration index of the currently executing loop test case.
 *
 *  If the currently executing test is not a loop test, then zero is returned.
 *
 *  \return The iteration index of the current test case.
 *
 *  \since 1.0
 */
extern int32_t TEST_ITERATION;
#else
#define TEST_ITERATION
#endif

/*! \def ABORT(...)
 *  \brief Aborts the test case with an error message.
 *
 *  \param[in] ... error message
 *
 *  \since 1.0
 */
#define ABORT(...)

/*! \typedef int64_t StatusCode
 *  \brief Integer representing an application status code.
 *
 *  POSIX requires the exit code to be in the inclusive range 0 to 255.
 *  Windows uses 32-bit unsigned integers as exit codes.
 *
 *  \since 1.0
 */
typedef int64_t StatusCode;

/*! \struct TestOptions
 *  \brief Test configuration options.
 *
 *  This structure defines configuration options applied to the test.
 *
 *  \since 1.0
 */

/*! \property TestOptions::iterations
 *  \brief The number of times to invoke the test (default=1).
 *
 *  Sets the number of times the test case executes.
 *  By default, each test case only executes once.
 *
 *  The following example causes the test case to execute three times:
 *
 *  \code{.c}
 *  TEST(yourSuite, yourTest, .iterations=3) {
 *      // ...
 *  }
 *  \endcode
 *
 *  The \ref TestOptions::iterations "iterations" option is useful for defining _parameterized_ tests.
 *  Parameterized tests are test cases that are invoked multiple times with different data.
 *  Using this option, in conjunction with #TEST_ITERATION, you can execute the same test case multiple
 *  times while extracting test data from an array.
 *
 *  \since 1.0
 */

/*! \property TestOptions::exit_status
 *  \brief Check the exit status of a test that intentionally terminate the application.
 *
 *  If the test does not terminate the application with exit status \p CODE, the test fails.
 *  This option is mutually exclusive with the \ref TestOptions::signal "signal" option.
 *
 *  \code{.c}
 *  TEST(yourSuite, yourTest, .exit_status=7) {
 *      // ...
 *  }
 *  \endcode
 *
 *  This option implicitly enables the #sandbox.
 *
 *  \since 1.0
 */

/*! \property TestOptions::signal
 *  \brief Signal the test is expected to raise.
 *
 *  If the test does not raise this signal, then it fails.
 *  This option is mutually exclusive with the \ref TestOptions::exit_status "exit status" option.
 *
 *  \code{.c}
 *  TEST(yourSuite, yourTest, .signal=SIGABRT) {
 *      // ...
 *  }
 *  \endcode
 * 
 *  This option implicitly enables the #sandbox.
 *
 *  \since 1.0
 */

/*! \property TestOptions::timeout
 *  \brief Test timeout duration (in milliseconds).
 *
 *  Each iteration of a test case will be aborted if it exceeds the specified timeout.
 *  If this option is zero, then there is no timeout.
 * 
 *  The following code example sets the timeout to 3000 milliseconds (or 3 seconds).
 *
 *  \code{.c}
 *  TEST(yourSuite, yourTest, .timeout=3000) {
 *      // ...
 *  }
 *  \endcode
 *
 *  This option implicitly enables the #sandbox.
 *
 *  \since 1.0
 */

/*! \property TestOptions::sandbox
 *  \brief Flag indicating if the sandbox should be used.
 *
 *  The sandbox isolates each test case iteration in a separate address space.
 *  This ensures if it unexpectedly terminates it will not bring down the test runner.
 *  The sandbox is also useful for testing expected terminations, signals, and to terminate the test if it exceeds a specified timeout.
 *
 *  \code{.c}
 *  TEST(yourSuite, yourTest, .sandbox=true) {
 *      // ...
 *  }
 *  \endcode
 * 
 *  \note
 *  The #exit_status, #signal, and #timeout options implicitly enable the sandbox.
 *
 *  \since 1.0
 */
typedef struct TestOptions
{
    int32_t iterations;
    StatusCode exit_status;
    int64_t signal;
    int timeout;
    bool sandbox;
} TestOptions;

/*! \addtogroup AssertValuesAPI
 *  \brief Compare integers, floating-point numbers, pointers, and booleans.
 * @{
 */

/*! \name Assert Macros
 *  \brief \e Assert macros fail and abort the test case.
 * @{
 */

/*! \def ASSERT_EQ(X, Y, ...)
 *  \brief Check two integers, floating-point numbers, or pointers to determine if \a X == \a Y.
 *
 *  If \a X != \a Y, the test case is aborted.
 *
 *  \param[in] X value
 *  \param[in] Y value to compare against X
 *  \param[in] ... optional message
 *
 *  \since 1.0
 */
#define ASSERT_EQ(X, Y, ...) XUNIT_ASSERT_EQ(X, Y, #X, #Y, true, "" __VA_ARGS__)

/**@}*/

/*! \name Expect Macros
 *  \brief \e Expect macros fail but do \b not abort the test case.
 * @{
 */

/*! \def EXPECT_EQ_APPROX(X, Y, T, ...)
 *  \brief Check two floating-point numbers to determine if \a X ≈ \a Y with the specified tolerance
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
#define EXPECT_EQ_APPROX(X, Y, T, ...) XUNIT_ASSERT_EQ_APPROX(X, Y, T, #X, #Y, false, "" __VA_ARGS__)

/**@}*/
/**@}*/

///  \brief Redirects all function calls to a mock function.
///
///  This macro allows detouring function calls to _another_ function known as the **mock function**.
///  The signature of the mock function must be identical to the function being mocked otherwise the
///  behavior is undefined.
///  Depending upon what compiler extensions are available and the version of the C standard being
///  built against, Audition can error if the signatures do not match.
///
///  This function-like macro is intended to be called from the body of a test case or fixture.
///  Invoking it elsewhere is undefined.
/// 
///  \code{.c}
///  int foo(void); // forward declaration
/// 
///  static int mock_foo(void) // mock function
///  {
///      return 123; // hard-coded return value
///  }
/// 
///  /* ... */
/// 
///  FAKE(foo, mock_foo) // redirect foo() to mock_foo()
///  \endcode
/// 
///  \param[in] FUNC function to be mocked
///  \param[in] FAKE fake function
/// 
///  \warning
///  The signature of the mock function must be identical to the function being mocked
///  otherwise the behavior is undefined.
///
///  \since 1.0
///
#define FAKE(FUNC, FAKE)                                                            \
    do {                                                                            \
        XUNIT_EXPECT_TYPES_EQUAL(FUNC, FAKE, "function signatures do not match");   \
        audit_fake((FUNC), (FAKE), #FUNC, #FAKE, __FILE__, __LINE__);               \
    } while (0)

/*! \def CALL(FUNC, ...)
 *  \brief Call the original function being mocked.
 *
 *  The original implementation of \p FUNC is invoked bypassing any registered mock.
 *  If \p FUNC is not mocked, then it is invoked directly.
 *
 *  The return value (if any) is discarded.
 *  To retrieve it use #CALL_GET instead.
 *
 *  \warning
 *  Recursive calls to the function will **not** be mocked.
 * 
 *  \warning
 *  Never longjmp from the invoked function to a point before #CALL.
 *
 *  \param[in] FUNC original function
 *  \param[in] ... arguments
 *
 *  \since 1.0
 */
#define CALL(FUNC, ...)                             \
    do {                                            \
        const int _id = audit_suspend(FUNC, #FUNC); \
        (FUNC)(__VA_ARGS__);                        \
        audit_reinstate(_id);                       \
    } while (0)

/*! \def CALL_GET(FUNC, RESULT, ...)
 *  \brief Call the original function being mocked and save its return value.
 *
 *  The original implementation of \p FUNC is invoked bypassing any registered mock.
 *  If \p FUNC is not mocked, then it is invoked directly.
 *  The return value is stored in \p RESULT.
 *
 *  If \p FUNC does not return a value or the return value isn't needed, then use #CALL.
 *
 *  \warning
 *  Recursive calls to the function will **not** be mocked.
 * 
 *  \warning
 *  Never longjmp from the invoked function to a point before #CALL_GET.
 *
 *  \param[in] FUNC original function
 *  \param[out] RESULT return value
 *  \param[in] ... arguments
 *
 *  \since 1.0
 */
#define CALL_GET(FUNC, RESULT, ...)                 \
    do {                                            \
        const int _id = audit_suspend(FUNC, #FUNC); \
        *(RESULT) = (FUNC)(__VA_ARGS__);            \
        audit_reinstate(_id);                       \
    } while (0)


/*! \addtogroup UtilityAPI
 *  \brief Portable system abstractions and framework interfaces.
 * @{
 */

/*! \typedef unsigned long long audit_time;
 *  \brief Elapsed time (in milliseconds).
 *
 *  This is used by various test utilities for measuring time.
 *
 *  \since 1.0
 */
typedef unsigned long long audit_time;

/*! \name Timing Functions
 * @{
 */

/*! \fn audit_now(void);
 *  \brief Monotonic time in milliseconds.
 *
 *  This function returns a monotonic time instance measured in milliseconds.
 *  This is intended for benchmarking.
 *
 *  \return Monotonic time in milliseconds.
 *
 *  \since 1.0
 */
XAPI audit_time audit_now(void);

/*! \fn audit_sleep(audit_time duration);
 *  \brief Suspends the execution of the current thread until the time-out interval elapses.
 *
 *  This is useful for introducing artificial delays.
 *
 *  \param[in] duration Time in milliseconds.
 *
 *  \since 1.0
 */
XAPI void audit_sleep(audit_time duration);

/**@}*/

/**@}*/
