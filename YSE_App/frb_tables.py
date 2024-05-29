import numpy as np
import pandas 

from YSE_App.models import FRBTransient

from IPython import embed


def summary_table():
    # Get it started
    all_frbs = FRBTransient.objects.all()
    all_tns = [frb.name for frb in all_frbs]
    frbs = pandas.DataFrame()
    frbs['TNS'] = all_tns

    # Add basic columns
    cols = ['ra', 'dec', 'a_err', 'b_err', 'theta', 'DM']
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
    mags = [frb.host.path_mag if frb.host else -1. for frb in all_frbs]
    POx = [frb.host.P_Ox if frb.host else -1. for frb in all_frbs]

    # Redshifts
    z = [frb.host.redshift if frb.host else -1. for frb in all_frbs]
    z_qual = [frb.host.redshift_quality if frb.host else -1 for frb in all_frbs]

    # Replace None's
    for ilist, replace in zip([mags, POx, z, z_qual], [-1., -1., -1., -1]):
        ilist = [replace if item is None else item for item in ilist]
    embed(header='43 of frb_table.py')

    # Assign
    frbs['Host_mag'] = mags
    #POx = [-1. if item is None else item for item in POx]
    frbs['POx'] = POx

    #z = [-1. if item is None else item for item in z]
    frbs['z'] = z
    #z_qual = [-1 if item is None else item for item in z_qual]
    frbs['z_qual'] = z_qual

    z_src = [frb.host.redshift_source if frb.host else '' for frb in all_frbs]
    frbs['z_src'] = z_src

    # Return
    return frbs