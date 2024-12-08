/*! \file functions-params.h
 *  \brief Testing function parameters.
 *
 *  Lets see if function parameters can be referenced.
 */

/*! \brief Closes a file descriptor.
 *
 *  Closes the file descriptor \p fd with options specified by \p flags.
 *
 *  \param[in] fd File descriptor.
 *  \param[in] flags Flags for file descriptor \p fd.
 *  \return Non-zero if file descriptor \p fd was closed.
 */
int close_me(int fd, int flags);

/*! \brief Copies a buffer.
 *
 *  Copies content from file descriptors \a fd to \a dest.
 *
 *  \param[in] dest Destination bufer.
 *  \param[in] fds File descriptors.
 *  \return String content of \a buffer.
 */
const char *copy_me(char dest[64], int ***fds[2]);
