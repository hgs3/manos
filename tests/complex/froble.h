/*! \file froble.h
 *  \brief \copybrief FrobAPI
 *  \copydetails FrobAPI
 */

#include "doodad.h"

/*! \addtogroup FrobAPI
 *  \brief Create and manipulate frob objects.
 * 
 *  The #Frob objects are constructed using the #frob_new function.
 *  Frob objects can be used to manipulate doodads which are constructed independntly using #doodad_new.
 *  Once a #Frob is constructed you can use it to manipulate one or more #Doodad.
 * 
 * @{
 */

/*! \brief Represents a Frob object.
 *
 *  This is presented as an opaque pointer.
 *
 *  \since 0.1.0
 */
typedef struct Frob Frob;

/*! \brief Construct a Frob object.
 *
 *  Create a #Frob object with default configuration.
 *  You can customize the object after its creation.
 *  You must release the #Frob object to prevent resource leakage by calling #frob_free.
 *
 *  \return Instance of a #Frob object or \c NULL on allocation failure.
 *
 *  \since 0.1.0
 */
Frob *frob_new(void);

/*! \brief Free a Frob object.
 *
 *  Release all resources associated with the #Frob object.
 *
 *  \param[in] frob Frob object.
 *
 *  \since 0.1.0
 */
void frob_free(Frob *frob);

/*! \brief Associate a doodad with a frob.
 *
 *  
 *
 *  \param[in] frob Frob object.
 *  \param[in] doodad Doodad object.
 *
 *  \since 0.1.0
 */
void frob_set_doodad(Frob *frob, Doodad *doodad);

/**@}*/
