/*! \file doodad.h
 *  \brief \copybrief DoodadAPI
 *  \copydetails DoodadAPI
 */

/*! \addtogroup DoodadAPI
 *  \brief Create and manipulate doodad objects.
 * 
 *  Doodads are little gizmos of nothingness.
 *  They don't do much by themselves but when combined with a #Frob they form the building blocks of something much more complex.
 * 
 * @{
 */

/*! \brief Bitflag type.
 */
typedef int DoodadFlags;

/*! \brief The default Doodad configuration.
 */
extern const int DoodadFlagDefault;

/*! \brief Flag indicating the Doodad should come preassembled.
 */
extern const int DoodadFlagAssembled;

/*! \brief Represents a Doodad object.
 *
 *  This is presented as an opaque pointer.
 *
 *  \since 0.1.0
 */
typedef struct Doodad
{
    /*! \brief Gizmo handle.
     *
     *  This is an interesting doohicky on the #Doodad.
     *
     *  \since 0.1.0
     */
    int gizmo;

    /*! \brief Gadget data flag.
     *
     *  This is a flag for controlling the gadget connected to the #Doodad.
     *
     *  \since 0.1.0
     */
    int gadget;
} Doodad;

/*! \brief Possible Doodad assembly results.
 */
enum Result
{
    RESULT_OK,
    RESULT_HALF,
    RESULT_FAIL,
};

/*! \brief Construct a Doodad object.
 *
 *  Create a #Doodad object with options.
 *  You must release the #Doodad object to prevent resource leakage by calling #doodad_free.
 *
 *  \param flags Option flags.
 *  \return Instance of a #Doodad object or \c NULL on allocation failure.
 *
 *  \since 0.1.0
 */
Doodad *doodad_new(DoodadFlags flags);

/*! \brief Free a Doodad object.
 *
 *  Release all resources associated with the #Doodad object.
 *
 *  \param[in] doodad Doodad object.
 *
 *  \since 0.1.0
 */
void doodad_free(Doodad *doodad);

/*! \brief Assemble a Doodad object.
 *
 *  Doodads must be assembled before being used.
 *  You can construct a #Doodad object preassembled by calling #doodad_new with the #DoodadFlagAssembled flag.
 *
 *  \param[in] doodad Doodad object.
 *  \retval RESULT_OK The doodad was assembled successfully.
 *  \retval RESULT_HALF The doodad was half assembled.
 *  \retval RESULT_FAIL The doodad could not be assembled.
 *
 *  \since 0.1.0
 */
Result doodad_assemble(Doodad *doodad);

/**@}*/
