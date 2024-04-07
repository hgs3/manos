/*! \file code-references.h
 *  \brief Code examples.
 *
 *  Recognition of the inherent dignity and of the equal and inalienable rights of
 *  all members of the human family.
 *  The foundation of freedom, justice and peace in the world.
 *  Disregard and contempt for human rights have resulted in barbarous acts which have
 *  outraged the conscience of mankind.
 *  The advent of a world in which human beings shall enjoy freedom from fear and want has been proclaimed
 *  as the highest aspiration of the common people.
 *
 *  \code{.c}
 *  // https://google.com
 *  int main(void) {
 *      struct Foo foo = {0};
 *      foobar(&foo);
 *      return 0;
 *  }
 *  \endcode
 *
 *  Whereas it is essential to promote the development of friendly relations between nations.
 * 
 *  This is a code blurb that referenes `Foo` and `foobar` which should NOT be linked.
 */

/*! \brief This is a structure.
 *
 *  The following is a code example that references #Foo and #foobar.
 *
 *  \code{.c}
 *  struct Foo fb = {0};
 *  fb.bar = 42;
 *  foobar(&fb);
 *  \endcode
 */
struct Foo {
    int bar;
};

/*! \brief This is a function.
 *
 *  The following is a code example that references #Foo and #foobar.
 *  This is a code blurb that referenes `Foo` and `foobar` which should NOT be linked.
 *
 *  \code{.c}
 *  void DoThing(void) {
 *      const struct Foo f = {0};
 *      foobar(&f);
 *  }
 *  \endcode
 */
void foobar(const struct Foo *foo);
