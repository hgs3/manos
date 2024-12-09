/*! \file alias.h
 *  \brief Type alias tests.
 *
 *  The "typedef" keyword in the programming languages C, C++, and Objective-C is used to create an additional name (alias) for another data type.
 *  It is often used to simplify the syntax of declaring complex data structures consisting of struct and union types, although
 *  it is also commonly used to provide specific descriptive type names for integer data types of varying sizes.
 */

/*! \brief Unique handle identifier.
 *
 *  Used to identify an internal resource.
 */
typedef int handle_t;

/*! \brief Anonymous struct.
 *
 *  This is using the PIMPL idiom.
 */
typedef struct Zippy Zippy;

/*! \brief This is an unnamed enumeration.
 *
 *  It is anonymous but you may refer to it by the #frob_t typedef alias.
 */
typedef enum
{
    FOO,
    BAR,
    BAZ,
} frob_t;

/*! \brief This is an named enumeration with an alias.
 *
 *  This enumeration has a name and an alias associated with it.
 *  You can refer to it by #Barracuda or by the #barracuda_t alias.
 */
typedef enum Barracuda
{
    FISH,
    SHARK,
    OCTOPUS,
} barracuda_t;

/*! \brief Identifies nothing.
 *
 *  Not used; ignore it.
 */
typedef const void ***never_t;

/*! \brief Structure with typedef.
 *
 *  This structure is declared with a typedef.
 *  It's preferred to use this directly over the #ptrstring_t typedef because the latter hides the pointer.
 */
typedef struct String
{
    /*! \brief Length of the string
     */
    int length;

    /*! \brief Pointer to a character array of \a length bytes.
     */
    const char *buffer;
} string_t;

/*! \brief Structure pointer with typedef.
 *
 *  A pointer to this structure declared with a typedef.
 * 
 *  This is typically bad practice in real API's as it hides the pointer.
 *  Better to use #string_t instead or better yet use #String directly.
 */
typedef struct string_t *ptrstring_t;

/*! \brief Union with typedef.
 *
 *  This union is declared with a typedef.
 *  It's preferred to use this directly over the #ptrvariant_t typedef because the latter hides the pointer.
 */
typedef union Variant
{
    /*! \brief Length of the string
     */
    int length;

    /*! \brief Pointer to a character array of \a length bytes.
     */
    const char *buffer;
} variant_t;

/*! \brief Union pointer with typedef.
 *
 *  A pointer to this union declared with a typedef.
 * 
 *  This is typically bad practice in real API's as it hides the pointer.
 *  Better to use #variant_t instead or better yet use #Variant directly.
 */
typedef union variant_t *ptrvariant_t;

