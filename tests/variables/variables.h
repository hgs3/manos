/*! \file variables.h
 *  \brief Variable tests.
 *
 *  In computer programming, a variable is an abstract storage location paired with an associated symbolic name, which contains some known or unknown quantity of information referred to as a value.
 *  In simpler terms, a variable is a named container for a particular set of bits or type of data (like integer, float, string etc...).
 *
 *  A variable can eventually be associated with or identified by a memory address.
 *  The variable name is the usual way to reference the stored value, in addition to referring to the variable itself, depending on the context.
 *  This separation of name and content allows the name to be used independently of the exact information it represents.
 * 
 *  The identifier in computer source code can be bound to a value during run time, and the value of the variable may thus change during the course of program execution.
 */

struct Foobar;

/*! \brief Person age handle.
 *
 *  This is a constant value.
 */
extern volatile const int PERSON_AGE;

/*! \brief This variable refers to a pointer to a structure.
 *
 *  Lets see how Doxygen handles it.
 */
extern const struct FooBar **FooBarDefaultValue;

/*! \brief This variable has an array portion associated with it.
 *
 *  It is intended to be a scratch buffer that anyone can write to.
 *  It is not thread safe.
 */
extern char scratch_buffer[64];
