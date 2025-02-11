#ifndef JUDO_H
#define JUDO_H

#include <stdint.h>

#if defined(JUDO_PARSER)
#include <stddef.h>
#include <stdbool.h>
#endif

#ifdef DOXYGEN
#define JUDO_MAXDEPTH
typedef long double judo_number;
#endif

#define JUDO_ERRMAX 36

// An "element" marks a point of interests when parsing the JSON stream.
// They may or may not correspond with a token in the stream.
enum judo_element
{
    JUDO_UNDEFINED,
    JUDO_NULL,
    JUDO_TRUE,
    JUDO_FALSE,
    JUDO_NUMBER,
    JUDO_STRING,
    JUDO_ARRAY_PUSH,
    JUDO_ARRAY_POP,
    JUDO_OBJECT_PUSH,
    JUDO_OBJECT_POP,
    JUDO_OBJECT_NAME,
    JUDO_EOF
};

struct judo_stream
{
#ifndef DOXYGEN
    int32_t s_at;
#endif
    int32_t where;
    int32_t length;
    enum judo_element element;
#ifndef DOXYGEN
    int8_t s_stack;
    int8_t s_state[JUDO_MAXDEPTH];
#endif
    char error[JUDO_ERRMAX];
};

#if defined(JUDO_PARSER)
struct judo_error
{
    int32_t where;
    int32_t length;
    char description[JUDO_ERRMAX];
};
#endif

#endif
