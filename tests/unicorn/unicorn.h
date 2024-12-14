#ifndef UNICORN_H
#define UNICORN_H

#include <stdbool.h>
#include <stdint.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

#ifdef DOXYGEN
typedef uint32_t unichar;
#endif

typedef long unisize;

typedef enum unistat
{
    UNI_OK,
    UNI_DONE,
    UNI_NO_MEMORY,
    UNI_NO_SPACE,
    UNI_BAD_ENCODING,
    UNI_BAD_OPERATION,
    UNI_FEATURE_DISABLED,
    UNI_MALFUNCTION,
} unistat;

typedef enum unienc
{
    UNI_SCALAR = 0x1,
    UNI_UTF8 = 0x2,
    UNI_UTF16 = 0x4,
    UNI_UTF32 = 0x8,
    UNI_BIG = 0x10,
    UNI_LITTLE = 0x20,
#if defined(UNICORN_LITTLE_ENDIAN)
    UNI_NATIVE = UNI_LITTLE,
#elif defined(UNICORN_BIG_ENDIAN)
    UNI_NATIVE = UNI_BIG,
#else
    #error undefined endian
#endif
    UNI_TRUST = 0x40,
    UNI_NULIFY = 0x80,
} unienc;

#ifdef __cplusplus
// C++ enumerations do not support bitwise operators.
// For the convenience of C++ users, define them here.
static inline unienc operator|(unienc a, unienc b)
{
    return static_cast<unienc>(static_cast<int>(a) | static_cast<int>(b));
}
#endif

//
// Unicode and Library Version
//

void uni_getversion(int *major, int *minor, int *patch);

//
// Case Conversion
//

typedef enum unicaseconv
{
    UNI_LOWER,
    UNI_TITLE,
    UNI_UPPER,
} unicaseconv;

unistat uni_caseconv(unicaseconv casing, const void *src, unisize src_len, unienc src_enc, void *dst, unisize *dst_len, unienc dst_enc);

//
// Case Folding
//

typedef enum unicasefold
{
    UNI_DEFAULT,
    UNI_CANONICAL,
} unicasefold;

unistat uni_casefold(unicasefold op, const void *src, unisize src_len, unienc src_enc, void *dst, unisize *dst_len, unienc dst_enc);

//
// Collation
//

typedef enum unistrength
{
    UNI_PRIMARY = 1,
    UNI_SECONDARY = 2,
    UNI_TERTIARY = 3,
    UNI_QUATERNARY = 4,
} unistrength;

typedef enum uniweighting
{
    UNI_NON_IGNORABLE,
    UNI_SHIFTED,
} uniweighting;

unistat uni_sortkeymk(const void *text, unisize length, unienc encoding, uniweighting weighting, unistrength strength, uint16_t *sortkey, unisize *sortkey_cap);
unistat uni_sortkeycmp(const uint16_t *sk1, unisize sk1_len, const uint16_t *sk2, unisize sk2_len, int *result);
unistat uni_collate(const void *s1, unisize s1_len, unienc s1_enc, const void *s2, unisize s2_len, unienc s2_enc, uniweighting weighting, unistrength strength, int *result);

//
// Text Segmentation
//

typedef enum unibreak
{
    UNI_GRAPHEME,
    UNI_WORD,
    UNI_SENTENCE,
} unibreak;

unistat uni_nextbrk(unibreak type, const void *text, unisize length, unienc encoding, unisize *index);
unistat uni_prevbrk(unibreak type, const void *text, unisize length, unienc encoding, unisize *index);

#ifdef __cplusplus
}
#endif

#endif // UNICORN_H
