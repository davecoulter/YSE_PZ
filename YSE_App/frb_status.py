""" Code related to the Status of FRBs """

import numpy as np


from YSE_App import frb_tags
from YSE_App.chime import tags as chime_tags 

# Create the FRB ones
all_status = [\
    'Unassigned', # Does not meet the criteria for FFFF FollowUp
    'RunPublicPATH', # Needs to be run through PATH with public data
        # P_Ux is None
    'NeedImage', # Needs deeper imaging
        # P_Ux > P_Ux_max
        # No Image + successful
    'NeedSpectrum', # Needs spectroscopy for redshift
    'RunDeepPATH', # Needs PATH run on deeper (typically private) imaging
    'ImagePending', # Pending deeper imaging with an FRBFollowUp
    'SpectrumPending', # Pending spectroscopy with an FRBFollowUp
    'GoodSpectrum', # Observed with spectroscopy successfully
    'TooFaint', # Host is too faint for spectroscopy
        # r-magnitude (or equivalent) of the top *two* host candidates
        #   are fainter than mr_max for the sample/survey
        # And
    'UnseenHost',  # Even with deep imaging, no compelling host was found
        # P(U|x) is set
        # Deep imaging must exist.  The list of telescope+intrument is below
        # P(U|x) > P_Ux_max
    'Complete', # Redshift measured (or deemed impossible)
]

# List of telescope+instruments that are considered Deep
deep_telinstr = []

# List of frb_rags where one should run a public PATH
run_public_path = []
# Include all of the CHIME samples
run_public_path += [sample['name'] for sample in chime_tags.all_samples]

# Add all of the chime

def set_status(frb):

    # Hide here for circular imports
    from YSE_App.models import TransientStatus
    from YSE_App.models import Path

    # Run in reverse order of completion

    # #########################################################
    # Complete?
    # #########################################################
    if frb.host is not None and frb.host.redshift is not None:
        frb.status = TransientStatus.objects.get(name='Complete') 
        frb.save()
        return

    # #########################################################
    # Unseen host
    # #########################################################

    # In PATH table?
    path_qs = Path.objects.filter(transient=frb)
    if len(path_qs) > 0:
        # Check on source of photometry (instrument) for all the galaxies
        all_telinstr = []
        for path in path_qs:
            # Grab a dict of the photometry
            phot_dict = path.galaxy.phot_dict
            all_telinstr += list(phot_dict.keys())
        # Unique tel+instruments

        # Too shallow
        too_shallow = True
        for uni_telins in np.unique(all_telinstr):
            if uni_telins in deep_telinstr:
                too_shallow = False

        # P(U|x) too large?
        if not too_shallow and frb.P_Ux is not None:

            PUx_maxs = frb_tags.values_from_tags(frb, 'P_Ux_max')
            if len(PUx_maxs) > 0:
                # Use the max
                PUx_max = np.max(PUx_maxs)
                if frb.P_Ux > PUx_max:
                    frb.status = TransientStatus.objects.get(name='UnseenHost') 
                    frb.save()
                    return

    # #########################################################
    # Too Faint? 
    # #########################################################

    if frb.host is not None:
        # 
        mrs = frb_tags.values_from_tags(frb, 'mr_max')
        # Find mr_max (if it exists)
        if len(mrs) > 0:
            mr_max = np.max(mrs)

            # Check host candidate magnitudes

    # #########################################################
    # Pending Spectrum
    # #########################################################

    # #########################################################
    # Need Spectrum
    # #########################################################
    if frb.host is not None:
        pass

        # MAKE A DEF OF THE PU criterion

        


    # #########################################################
    # Run Public PATH
    # #########################################################

    tag_names = [frb_tag.name for frb_tag in frb.frb_tags.all()]
    for tag in tag_names:
        if tag in run_public_path:
            frb.status = TransientStatus.objects.get(name='RunPublicPATH') 
            frb.save()
            return
        


    # #########################################################
    # Unassigned 
    # #########################################################

    frb.status = TransientStatus.objects.get(name='Unassigned') 
    frb.save()
    return