""" Code related to FRB tags """

import numpy as np

from YSE_App import frb_status
from YSE_App import frb_utils

def add_frb_tags(frb, tags:str, user):
    """
    Adds tags to a Fast Radio Burst (FRB) object and updates its status.

    This function takes a comma-separated string of tag names, creates or retrieves
    corresponding FRBTag objects, associates them with the given FRB object, updates
    the FRB's status, and saves the changes.

    Args:
        frb: The FRB object to which tags will be added.
        tags (str): A comma-separated string of tag names to be added to the FRB.
        user: The user performing the operation, used for creating or retrieving FRBTag objects.

    Returns:
        None
    """
    # Avoid circular import
    from YSE_App.models import FRBTag

    # Add new ones
    for tag_name in tags.split(','):
        tag = frb_utils.add_or_grab_obj(
            FRBTag, dict(name=tag_name), {}, user)
        # TODO
        # Should we check if the tag already exists?
        frb.frb_tags.add(tag)

    # Set status
    frb_status.set_status(frb)

    # Save me!
    frb.save()

def values_from_tags(frb, key:str, tag_names:list=None, debug:bool=False):
    """ Grab a list of values for a given key from the tags
      of a given FRB

    Args:
        frb (FRBTransient): FRBTransient instance
        key (str): key to grab
        tag_names (list, optional): list of tags to work on
        debug (bool, optional): Debug flag. Defaults to False.

    Returns:
        list: list of values for the key;  can be empty
    """
    # Hiding here to avoid circular import (I hope)
    from YSE_App.models import FRBSampleCriteria

    # Prep
    if tag_names is None:
        tag_names = [frb_tag.name for frb_tag in frb.frb_tags.all()]
    if debug:
        print(f"tag_names = {tag_names} for {frb.name} and key {key}")

    # Get all samples with the frb survey
    #samples = FRBSampleCriteria.objects.filter(
    #    frb_survey=frb.frb_survey)

    # Loop through
    values = []
    for tag_name in tag_names:
        sample = frb_utils.add_or_grab_obj(
            FRBSampleCriteria, dict(name=tag_name), {})
        if getattr(sample,key) is not None:
            values.append(getattr(sample,key))

    return values

def chk_all_criteria(frb):
    from YSE_App.models import FRBSampleCriteria

    log_message = ''
    # Good redshift sources
    good_z_sources = ['FFFF', 'Keck', 'Lick', 'Gemini', 'MMT']

    criteria = {}
    criteria['sample'] = []
    criteria['bright_star'] = [] # True if the FRB has a bright star and it is to be enforced
    criteria['EBV'] = []  # True if the FRB has a low enough MW E(B-V)
    criteria['POx'] = []  # True if the FRB has a high enough P(O|x)
    criteria['POx_primary'] = []  # True if the primary has a high enough P(O|x)
    criteria['run_public_PATH'] = []  # True if we intend to run public PATH
    criteria['ran_deep_PATH'] = []  # True if we ran PATH on deeper imaging
    criteria['z_done'] = []  # True if redshift is done for this tag
    criteria['z_consistent'] = []  # Redshifts of two galaxies are consistent
    criteria['z_primary'] = []  # True if redshift of primary is done
    criteria['N_POx'] = []
    criteria['PUx'] = [] # True if P(U|x) > max_PUx;  used for NeedImage and Unseen
    criteria['too_faint'] = [] # True if mag of top P(O|x) > mr_max
    criteria['skip_need_image'] = [] # True if skip_need_image is set

    # Grab the Sample object
    for frb_tag in frb.frb_tags.all():
        # Grab the criteria
        sample = frb_utils.add_or_grab_obj(
            FRBSampleCriteria, dict(name=frb_tag.name), {})
        criteria['sample'].append(sample.name)

        # Bright star?
        if sample.apply_bright_star and frb.bright_star is not None and frb.bright_star:
            criteria['bright_star'].append(True)
        else:
            criteria['bright_star'].append(False)

        # Dust
        if frb.mw_ebv < sample.max_EBV:
            criteria['EBV'].append(True)
        else:
            criteria['EBV'].append(False)

        # Run Public PATH?
        criteria['run_public_PATH'].append(sample.run_public_path)

        # Skip need imaging?
        if sample.skip_need_image is not None and sample.skip_need_image:
            criteria['skip_need_image'].append(True)
        else:
            criteria['skip_need_image'].append(False)

        # PATH and redshift items
        if frb.host is not None:
            POx_values, galaxies, path_objs = frb.get_Path_values()
            argsrt = np.argsort(POx_values)
            pri_gal = galaxies[argsrt[-1]]  # Primary galaxy
            primary_POx = np.max(POx_values)

            # P(O|x)
            # Primary?
            if primary_POx > sample.min_POx:
                criteria['POx_primary'].append(True)
            else:
                criteria['POx_primary'].append(False)
            # Top two?
            if sample.use_top_two:
                criteria['N_POx'].append(2)
                if frb.sum_top_two_PATH > sample.min_POx:
                    criteria['POx'].append(True)
                else:
                    criteria['POx'].append(False)
            else:
                criteria['N_POx'].append(1)
                criteria['POx'].append(criteria['POx_primary'][-1])

            # P(U|x)
            if sample.max_PUx is not None and frb.P_Ux > sample.max_PUx:
                criteria['PUx'].append(True)
            else:
                criteria['PUx'].append(False)

            # Ran deep PATH?
            rfilter = pri_gal.FilterMagString()[0]
            log_message += rfilter
            if 'Blanco' in rfilter or 'DECam' in rfilter or 'Pan-STARRS' in rfilter: # Public
                criteria['ran_deep_PATH'].append(False)
            else:
                criteria['ran_deep_PATH'].append(True)

            # Redshift satisfied?
            # Items to loop over
            if criteria['POx_primary'][-1]: # Primary galaxy
                idxs = argsrt[-1:]  # Primary is the last one
            else:
                if len(galaxies) > 1:
                    idxs = argsrt[-2:]  # Top 2
                else:
                    idxs = argsrt[-1:]  # Only one galaxy

            # Check just the primary
            pri_gal = galaxies[argsrt[-1]]
            path_obj = path_objs[argsrt[-1]]

            if pri_gal.redshift is None:
                criteria['z_primary'].append(False)
            else:
                # Check the redshift source
                tmp_ok = False
                for gd_source in good_z_sources:
                    if gd_source in pri_gal.redshift_source:
                        tmp_ok = True
                if tmp_ok:
                    criteria['z_primary'].append(True)
                else:
                    criteria['z_primary'].append(False)

            # Too faint?
            if sample.max_mr is not None and path_obj.galaxy_mag > sample.max_mr:
                criteria['too_faint'].append(True)
            else:
                criteria['too_faint'].append(False)
            

            # Loop on the info
            has_redshift = []
            source_ok = []
            for ss, idx in enumerate(idxs):
                # Grab the galaxy
                gal = galaxies[idx]
                # Check redshift
                if gal.redshift is None:
                    has_redshift.append(False)
                else:
                    has_redshift.append(True)
                # Check the redshift source
                tmp_ok = False
                for gd_source in good_z_sources:
                    if gd_source in gal.redshift_source:
                        tmp_ok = True
                source_ok.append(tmp_ok)

            # Time to set the status
            if criteria['POx_primary'][-1]: # Primary galaxy
                log_message += "I AM A PRIMARY-"
                # Ok?
                if np.all(has_redshift) and np.all(source_ok):
                    criteria['z_done'].append(True)
                else:
                    criteria['z_done'].append(False)
                # Dummy True
                criteria['z_consistent'].append(True)
            else: # Top 2
                log_message += "I AM NOT A PRIMARY-"
                # Check the redshifts are nearly the same
                if np.all(has_redshift) and np.all(source_ok):
                    criteria['z_done'].append(True)
                    log_message += "I AM OK-"
                    if np.abs(galaxies[argsrt[-1]].redshift - galaxies[argsrt[-2]].redshift) > 0.003:
                        criteria['z_consistent'].append(False)
                    else:
                        criteria['z_consistent'].append(True)
                else:
                    criteria['z_done'].append(False)
                    criteria['z_consistent'].append(False)

        else:
            criteria['POx'].append(False)
            criteria['POx_primary'].append(False)
            criteria['N_POx'].append(0)
            criteria['PUx'].append(False)
            criteria['ran_deep_PATH'].append(False)
            criteria['z_done'].append(False)
            criteria['z_consistent'].append(False)
            criteria['z_primary'].append(False)
            criteria['too_faint'].append(False)


    # Convert to arrays
    for key in criteria:
        criteria[key] = np.array(criteria[key])

    # Return
    return criteria, log_message