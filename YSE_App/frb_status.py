""" Code related to the Status of FRBs """

import numpy as np


from YSE_App import frb_tags

from IPython import embed

# Create the FRB ones
all_status = [\
    'Unassigned', # Does not meet the criteria for FFFF FollowUp
    'BrightStar', # Localization is too close to a very bright star
    'TooDusty', # Sightline exceeds E(B-V) threshold
    'RunPublicPATH', # Needs to be run through PATH with public data
        # P_Ux is None
        # At least one frb_tag is in the list of run_public_path entries below
    'NeedImage', # Needs deeper imaging
        # P_Ux > maximum of all P_Ux_max for the frb_tags
        #  or r-mag of the top candidate is too faint for the public survey
        #   23.0 for Blanco/DECam, 21.0 for Pan-STARRS
        # No successful Image taken
        # No Image pending
    'NeedSpectrum', # Needs spectroscopy for redshift
        # P(O|x) of top 2 > P_Ox_min
        # No pending spectrum
        # No succesfully observed spectrum
    'NeedSecondary', # Needs spectroscopy for redshift of a secondary candidate
        # P(O|x) of top 2 > P_Ox_min
        # Successful redshift for the primary
        # P(O|x) of primary < P_Ox_min
    'RunDeepPATH', # Needs PATH run on deeper (typically private) imaging
        # Image taken with success
    'ImagePending', # Pending deeper imaging with an FRBFollowUp
        # FRB appears in FRBFollowUpRequest with mode='image'
    'SpectrumPending', # Pending spectroscopy with an FRBFollowUp
        # FRB appears in FRBFollowUpRequest with mode='longslit','mask'
    'GoodSpectrum', # Observed with spectroscopy successfully
        # P(O|x) of top 2 > P_Ox_min
        # If Primary does not exceed min_POx, then the top two must have a spectrum
    'TooFaint', # Host is too faint for spectroscopy
        # r-magnitude (or equivalent; we use the PATH band) of the top host candidate
        #   is fainter than the maximum(mr_max) for the sample/surveys
    'AmbiguousHost',  # Host is considered too ambiguous for further follow-up
        #  For primary-only, it isn't satisfied and for top two, the top two P(O|x) are not satisfied
    'UnseenHost',  # Even with deep imaging, no compelling host was found
        # P(U|x) is set
        # deep PATH was run
        # P(U|x) > P_Ux_max
        # Note that this takes precedence over 'AmbiguousHost' 
    'Redshift', # Redshift measured
        # P(O|x) of top 2 > P_Ox_min
        # If Primary does not exceed min_POx, then the top two redshifts must be nearly the same
        # Else, take primary
]



# Add all of the chime
def set_status(frb):
    """ Set the status of an FRB transient 

    The frb is modified and saved

    Args:
        frb (FRBTransient): FRBTransient instance
    """
    log_message = ''

    # Hide here for circular imports
    from YSE_App.models import TransientStatus
    from YSE_App.models import Path
    from YSE_App.models import FRBFollowUpObservation
    from YSE_App.models import FRBFollowUpRequest

    # Check Criteria
    criteria, msg = frb_tags.chk_all_criteria(frb)
    log_message += msg
    PATH_run = False if frb.host is None else True

    # Is the top candidate too faint?
    r_too_faint = False  
    if frb.host is not None:
        POx_values, galaxies, _ = frb.get_Path_values()
        argsrt = np.argsort(POx_values)
        pri_gal = galaxies[argsrt[-1]]  # Primary galaxy
        # Check the top candidate magnitude
        rfilter, mag = pri_gal.FilterMagString()
        mag = float(mag)
        if 'Blanco' in rfilter or 'DECam' in rfilter:
            if mag > 23.0:
                r_too_faint = True
        elif 'Pan-STARRS' in rfilter:
            if mag > 21.0:
                r_too_faint = True

    # Run in reverse order of completion

    # #########################################################
    # #########################################################
    # Bright star?
    # #########################################################
    if np.all(criteria['bright_star']):
        frb.status = TransientStatus.objects.get(name='BrightStar')
        frb.save()
        return

    # #########################################################
    # #########################################################
    # Too Dusty??
    # #########################################################
    if np.all(np.invert(criteria['bright_star']) & np.invert(criteria['EBV'])):
        frb.status = TransientStatus.objects.get(name='TooDusty')
        frb.save()
        return

    # #########################################################
    # Run Public PATH
    # #########################################################
    if np.any(np.invert(criteria['bright_star']) & criteria['EBV'] & \
        criteria['run_public_PATH']):
        if not PATH_run:
            frb.status = TransientStatus.objects.get(name='RunPublicPATH')
            frb.save()
            return
    else: # We have chosen not to proceed with this FRB; all items that follow require PATH
        frb.status = TransientStatus.objects.get(name='Unassigned')
        frb.save()
        return

    # #########################################################
    # Grab the sample that satisfy the criteria so far
    # #########################################################
    good = np.invert(criteria['bright_star']) & criteria['EBV'] & \
        criteria['run_public_PATH']
    good_idx = np.where(good)[0]

    # #########################################################
    # Pending Image
    # #########################################################
    if FRBFollowUpRequest.objects.filter(
            transient=frb,
            mode='imaging').exists():
        frb.status = TransientStatus.objects.get(name='ImagePending')
        frb.save()
        return

    # #########################################################
    # Need Image
    # #########################################################
    if (np.any(criteria['PUx'][good_idx] & np.invert(criteria['skip_need_image'])) or (
        r_too_faint & (not np.all(criteria['skip_need_image'])))) and (
        not FRBFollowUpRequest.objects.filter(
            transient=frb,
            mode='imaging').exists()) and (
        not FRBFollowUpObservation.objects.filter(
            transient=frb,
            success=True,
            mode='imaging').exists()):

        frb.status = TransientStatus.objects.get(name='NeedImage')
        frb.save()
        return

    # #########################################################
    # Run deep PATH
    # #########################################################
    if FRBFollowUpObservation.objects.filter(
            transient=frb,
            success=True,
            mode='imaging').exists() and (not criteria['ran_deep_PATH'][0]):
        frb.status = TransientStatus.objects.get(name='RunDeepPATH')
        frb.save()
        return

    # #########################################################
    # Unseen host
    # #########################################################
    # In PATH table?
    if np.any(criteria['PUx'][good_idx] & criteria['ran_deep_PATH'][good_idx]):
        frb.status = TransientStatus.objects.get(
                        name='UnseenHost')
        frb.save()
        return

    # #########################################################
    # Ambiguous host
    # #########################################################
    if np.all(np.invert(criteria['POx'][good_idx])):
        frb.status = TransientStatus.objects.get(name='AmbiguousHost')
        frb.save()
        return


    # #########################################################
    # Redshift?
    # #########################################################
    flg_need_secondary = False
    if frb.host is not None and frb.host.redshift is not None and \
        np.any(criteria['POx'][good_idx]):  # This last query is superfluous but it is here for clarity 

        # We have a redshift
        if np.any(criteria['z_done'][good_idx] & criteria['z_consistent'][good_idx]):
            frb.status = TransientStatus.objects.get(name='Redshift')
            frb.save()
            return

        # Amibiguous host
        if np.any(criteria['z_done'][good_idx] & np.invert(criteria['z_consistent'][good_idx])):
            frb.status = TransientStatus.objects.get(name='AmbiguousHost')
            frb.save()
            return

        # Secondary?
        if np.any(criteria['z_primary'][good_idx]): 
            frb.status = TransientStatus.objects.get(name='NeedSecondary')
            frb.save()
            flg_need_secondary = True
            # Do not return yet, we want to check for spectrum next


    # #########################################################
    # Too Faint?
    # #########################################################
    if frb.host is not None and np.all(criteria['too_faint'][good_idx]):
        frb.status = TransientStatus.objects.get(name='TooFaint')
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
    # Need Secondary?
    # #########################################################
    if flg_need_secondary:
        return

    # #########################################################
    # Need Spectrum
    # #########################################################
    if frb.host is not None and np.any(criteria['POx'][good_idx]):
        frb.status = TransientStatus.objects.get(name='NeedSpectrum')
        frb.save()
        return

    # #########################################################
    # Unassigned
    # #########################################################
    # If you get to here, you are unassigned
    frb.status = TransientStatus.objects.get(name='Unassigned')
    frb.save()
    return