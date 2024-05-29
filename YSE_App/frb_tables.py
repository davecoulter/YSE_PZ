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

    # Host
    for col, key in zip(['Host', 'Host_POx', 'z', 'Host_mag'],
                        ['HostString', 'HostPOxString', 'HostzString', 'HostMagString']):
        frbs[col] = [getattr(frb, key)() for frb in all_frbs]

    # More redshift info
    z_qual = [int(frb.host.redshift_quality) if frb.host else -1 for frb in all_frbs]
    frbs['z_qual'] = z_qual
    z_src = [frb.host.redshift_source if frb.host else '' for frb in all_frbs]
    frbs['z_src'] = z_src

    # Return
    frbs