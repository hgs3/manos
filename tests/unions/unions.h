/*! \file unions.h
 *  \brief Union type tests.
 *
 *  In computer science, a union is a value that may have any of several representations or formats within the same position in memory;
 *  that consists of a variable that may hold such a data structure.
 *  Some programming languages support special data types, called union types, to describe such values and variables.
 *  In other words, a union type definition will specify which of a number of permitted primitive types may be stored in its instances,
 *  e.g., "float or long integer".
 *  In contrast with a record (or structure), which could be defined to contain both a float and an integer;
 *  in a union, there is only one value at any given time.
 */

/*! \brief An empty, do nothing union.
 *
 *  This union has not contents.
 *
 *  What does it mean to be devoid of content?
 *  This is a philosophical question.
 */
union Empty {};

/*! \brief union with one field.
 *
 *  This union has one field.
 *  It doesn't do much otherwise.
 *  It is generally recommended to prefer the #Foo union as it's more modern.
 */
union Frob
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
union Person
{
    /*! \brief How many years old the person is.
     */
    int age;

    /*! \brief The persons height.
     */
    union Height height;

    /*! \brief Full name of the person.
     *
     *  This is the persons first, middle, and last name delimited by spaces.
     *  The name of this field is intentionally long so it forces paragraph wrapping.
     */
    char fullname_delimited_by_spaces[64];
};

/*! \brief Nested unions.
 *
 *  This union has substructres which define fields on their parent union.
 *  This union is better than the #Frob one.
 */
union Foo
{
    /*! \brief Bar field docs.
     */
    struct
    {
        /*! \brief Qux union documentation.
         */
        const union Qux
        {
            /*! \brief Waldo field docs.
             */
            int ***waldo[];
        } qux;
    } bar;
};
