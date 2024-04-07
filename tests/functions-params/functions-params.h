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

