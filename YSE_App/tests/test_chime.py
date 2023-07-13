""" Tests for CHIME """
import os, sys
import numpy as np

import pandas 

sys.path.append(os.path.abspath("../frbs"))
import path

def internal_test_path():
    """ Check PATH analysis internally (i.e. not with the DB)"""
    # Load up the table
    chime_frbs = pandas.read_csv('../chime/chime_tests.csv')

    # Work on one
    ifrb = np.where(chime_frbs['name'] == 'FRB20300714A')[0][0]
    frb = chime_frbs.iloc[ifrb]

    # Path me
    _ = path.run_path_on_instance(frb, priors=None)


# Command line execution
if __name__ == '__main__':
    internal_test_path()