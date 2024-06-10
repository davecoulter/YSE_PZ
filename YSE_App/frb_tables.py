import numpy as np
import pandas 

from YSE_App.models import FRBTransient

from IPython import embed


def summary_table():
    """
    Generate a summary table of FRB transients.

    Returns:
        pandas.DataFrame: A DataFrame containing the summary information of FRB transients.
    """
    # Get it started
    all_frbs = FRBTransient.objects.all()
    all_tns = [frb.name for frb in all_frbs]
    frbs = pandas.DataFrame()
    frbs['TNS'] = all_tns

    # Add basic columns
    cols = ['ra', 'dec', 'a_err', 'b_err', 'theta', 'DM', 'DM_ISM']
    for col in cols:
        frbs[col] = [getattr(frb, col) for frb in all_frbs]

    # Foreign keys
    fkeys = ['frb_survey', 'status']
    for key in fkeys:
        frbs[key] = [str(getattr(frb, key)) for frb in all_frbs]

    # Host and other Strings
    for col, key in zip(['Tags', 'Resources', 'Host'],
                        ['FRBTagsString', 
                         'FRBFollowUpResourcesString',
                         'HostString', 
                         ]):
        frbs[col] = [getattr(frb, key)() for frb in all_frbs]

    # Host 
    mags = [frb.host.path_mag if frb.host else np.nan for frb in all_frbs]
    frbs['Host_mag'] = mags
    POx = [frb.host.P_Ox if frb.host else np.nan for frb in all_frbs]
    frbs['POx'] = POx

    # Redshifts
    z = [frb.host.redshift if frb.host else np.nan for frb in all_frbs]
    frbs['z'] = z

    z_qual = [frb.host.redshift_quality if frb.host else -1 for frb in all_frbs]
    z_qual = [-1 if item is None else item for item in z_qual]
    frbs['z_qual'] = z_qual

    z_src = [frb.host.redshift_source if frb.host else '' for frb in all_frbs]
    z_src = ['' if item is None else item for item in z_src]
    frbs['z_src'] = np.array(z_src)

    # Return
    return frbs