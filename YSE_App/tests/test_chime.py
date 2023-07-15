""" Tests for CHIME """
import os, sys
import numpy as np

import pandas 

try:
    sys.path.append(os.path.abspath("../galaxies"))
    import path
except ModuleNotFoundError:
    from YSE_App.galaxies import path

from IPython import embed

def internal_test_of_path():
    """ Check PATH analysis internally (i.e. not with the DB)"""
    # Load up the table
    chime_frbs = pandas.read_csv('../chime/chime_tests.csv')

    # Work on one
    ifrb = np.where(chime_frbs['name'] == 'FRB20300714A')[0][0]
    frb = chime_frbs.iloc[ifrb]

    # Path me
    candidates, P_Ux, Path = path.run_path_on_instance(frb, priors=None)

    # Test
    assert len(candidates) == 2, "Wrong number of candidates"
    assert P_Ux < 0.02, "P_Ux is too large"


# Command line execution
if __name__ == '__main__':
    internal_test_of_path()

# Repos installed