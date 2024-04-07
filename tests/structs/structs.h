/*! \file structs.h
 *  \brief Record tests.
 *
 *  In computer science, a record (also called a structure, struct, or compound data) is a basic data structure.
 *  Records in a database or spreadsheet are usually called "rows".
 *
 *  A record is a collection of fields, possibly of different data types, typically in a fixed number and sequence.
 *  The fields of a record may also be called members, particularly in object-oriented programming; fields may also be called elements, though this risks confusion with the elements of a collection.
 *
 *  For example, a date could be stored as a record containing a numeric year field, a month field represented as a string, and a numeric day-of-month field.
 *  A personnel record might contain a name, a salary, and a rank.
 *  A Circle record might contain a center and a radius—in this instance, the center itself might be represented as a point record containing x and y coordinates.
 */

/*! \brief An empty, do nothing structure.
 *
 *  This structure has not contents.
 *
 *  What does it mean to be devoid of content?
 *  This is a philosophical question.
 */
struct Empty {};

/*! \brief Structure with one field.
 *
 *  This structure has one field.
 *  It doesn't do much otherwise.
 *  It is generally recommended to prefer the #Foo structure as it's more modern.
 */
struct Frob
{
    /*! \brief Useless field.
     *
     *  This field has no use.
     *  It can be treated as scratch storage.
     */
    const void *nop;
};

/*! \brief Represents a human.
 */
struct Person
{
    /*! \brief How many years old the person is.
     */
    int age;

    /*! \brief The persons height.
     */
    struct Height height;

    /*! \brief Full name of the person.
     *
     *  This is the persons first, middle, and last name delimited by spaces.
     *  The name of this field is intentionally long so it forces paragraph wrapping.
     */
    char fullname_delimited_by_spaces[64];
};

/*! \brief Nested structures.
 *
 *  This structure has substructres which define fields on their parent structure.
 *  This structure is better than the #Frob one.
 */
struct Foo
{
    /*! \brief Bar field docs.
     */
    struct
    {
        /*! \brief Qux struct documentation.
         */
        const struct Qux
        {
            /*! \brief Waldo field docs.
             */
            int ***waldo[];
        } qux;
    } bar;
};
