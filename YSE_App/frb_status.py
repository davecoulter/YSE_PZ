""" Code related to the Status of FRBs """

import numpy as np


from YSE_App import frb_tags
from YSE_App.chime import tags as chime_tags 

from IPython import embed

# Create the FRB ones
all_status = [\
    'Unassigned', # Does not meet the criteria for FFFF FollowUp
    'RunPublicPATH', # Needs to be run through PATH with public data
        # P_Ux is None
    'NeedImage', # Needs deeper imaging
        # P_Ux > P_Ux_max
        # No Image + successful
    'NeedSpectrum', # Needs spectroscopy for redshift
        # P(O|x) of top 2 > P_Ux_max
        # No pending spectrum
        # No succesfully observed spectrum
    'RunDeepPATH', # Needs PATH run on deeper (typically private) imaging
    'ImagePending', # Pending deeper imaging with an FRBFollowUp
    'SpectrumPending', # Pending spectroscopy with an FRBFollowUp
    'GoodSpectrum', # Observed with spectroscopy successfully
    'TooFaint', # Host is too faint for spectroscopy
        # r-magnitude (or equivalent) of the top *two* host candidates
        #   are fainter than mr_max for the sample/survey
        # And
    'AmbiguousHost',  # Host is consideed too ambiguous for further follow-up
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
    from YSE_App.models import FRBFollowUpObservation
    from YSE_App.models import FRBFollowUpRequest

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
    if len(path_qs) > 0 and frb.P_Ux is not None:
        # Check on source of photometry (instrument) for all the galaxies
        all_telinstr = []
        for path in path_qs:
            # Grab a dict of the photometry
            phot_dict = path.galaxy.phot_dict
            all_telinstr += list(phot_dict.keys())

        # Too shallow?
        too_shallow = True
        for uni_telins in np.unique(all_telinstr):
            if uni_telins in deep_telinstr:
                too_shallow = False

        # P(U|x) too large?
        if not too_shallow: 
            PUx_maxs = frb_tags.values_from_tags(frb, 'max_P_Ux')
            if len(PUx_maxs) > 0:
                # Use the max
                PUx_max = np.max(PUx_maxs)
                if frb.P_Ux > PUx_max:
                    frb.status = TransientStatus.objects.get(
                        name='UnseenHost')
                    frb.save()
                    return

    # #########################################################
    # Ambiguous host
    # #########################################################

    if frb.host is not None:
        # Require top 2 P(O|x) > min(P_Ox_min)
        POx_mins = frb_tags.values_from_tags(frb, 'min_POx')
        if len(POx_mins) > 0 and (
            frb.sum_top_two_PATH < np.min(POx_mins)):
            frb.status = TransientStatus.objects.get(name='AmbiguousHost') 
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
    # Good Spectrum
    # #########################################################

    if FRBFollowUpObservation.objects.filter(
            transient=frb,
            success=True,
            mode__in=['longslit','mask']).exists():
        frb.status = TransientStatus.objects.get(name='GoodSpectrum') 
        frb.save()
        return

    # #########################################################
    # Pending Spectrum
    # #########################################################

    if FRBFollowUpRequest.objects.filter(
            transient=frb,
            mode__in=['longslit','mask']).exists():
        frb.status = TransientStatus.objects.get(name='SpectrumPending') 
        frb.save()
        return

    # #########################################################
    # Need Spectrum
    # #########################################################

    if frb.host is not None and (
        not FRBFollowUpRequest.objects.filter(
            transient=frb,
            mode__in=['longslit','mask']).exists()) and (
        not FRBFollowUpObservation.objects.filter(
            transient=frb,
            success=True,
            mode__in=['longslit','mask']).exists()): 

        # Require top 2 P(O|x) > min(P_Ox_min)
        POx_mins = frb_tags.values_from_tags(frb, 'min_POx')
        if (len(POx_mins) == 0) or (
            frb.sum_top_two_PATH > np.min(POx_mins)):
            frb.status = TransientStatus.objects.get(name='NeedSpectrum') 
            frb.save()
            return

    # #########################################################
    # Need Image
    # #########################################################

    if frb.P_Ux is not None and frb.host is not None and (
        not FRBFollowUpRequest.objects.filter(
            transient=frb,
            mode='image').exists()) and (
        not FRBFollowUpObservation.objects.filter(
            transient=frb,
            success=True,
            mode='image').exists()):

        # Require top P_Ux > min(P_Ux_max)
        PUx_maxs = frb_tags.values_from_tags(frb, 'max_P_Ux')
        if (len(PUx_maxs) == 0) or (
            frb.P_Ux > np.min(PUx_maxs)):
            frb.status = TransientStatus.objects.get(name='NeedImage') 
            frb.save()
            return

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