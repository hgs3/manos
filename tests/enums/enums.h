/*! \file enums.h
 *  \brief Enumeration element tests.
 *
 *  An enumeration is a complete, ordered listing of all the items in a collection.
 *  The term is commonly used in mathematics and computer science to refer to a listing of all of the elements of a set.
 *  The precise requirements for an enumeration (for example, whether the set must be finite, or whether the list
 *  is allowed to contain repetitions) depend on the discipline of study and the context of a given problem.
 */

/*! \brief Represents an empty enumeration.
 *
 *  This enumeration doesn't do anything other than take up space (what a free loader)!
 *
 *  \since 0.1.0
 */
enum Empty {};

/*! \brief This enumeration lacks documentation for its elements.
 *
 *  The documentation for the elements is intentionally omitted.
 */
enum FooBar
{
    ABC,
    XYZ,
};

/*! \brief Represents the states of a Frob object.
 *
 *  Represents various error and success states of a Frobnicator object instance.
 *  Consult the documentation for for more details.
 *  The default state of #Frob is #FOO so see its documentation for more details.
 *
 *  \since 0.1.0
 */
enum Frob
{
    FOO,
    BAR,
    BAZ = 100,
};

/*! \var Frob::FOO
 *  \brief Represents a FOO constant.
 *
 *  This is a #FOO and it will never be a #BAR.
 */

/*! \var Frob::BAR
 *  \brief Represents a BAR constant.
 *
 *  This is a #BAR and it will never ever be a #FOO.
 */

/*! \var Frob::BAZ
 *  \brief Represents a BAZ constant.
 *
 *  This is a #BAZ.
 *  It is the best constant belonging to #Frob according to myself.
 */
