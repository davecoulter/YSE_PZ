.. YSE_PZ documentation master file, created by
   sphinx-quickstart on Tue Nov  5 13:49:21 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to the YSE_PZ documentation!
====================================

The modern study of astrophysical transients has been transformed by an exponentially growing volume of data. Within the last decade, the transient discovery rate has increased by a factor of ~20, with associated survey data, archival data, and metadata also increasing with the number of discoveries. To manage the data at this increased rate, we require new tools. Here we present YSE_PZ, a transient survey management platform that ingests multiple live streams of transient discovery alerts, identifies the host galaxies of those transients, downloads coincident archival data, and retrieves photometry and spectra from ongoing surveys. YSE_PZ also presents a user with a range of tools to make and support timely and informed transient follow-up decisions. Those subsequent observations enhance transient science and can reveal physics only accessible with rapid follow-up observations. Rather than automating out human interaction, YSE_PZ focuses on accelerating and enhancing human decision making, a role we describe as empowering the human-in-the-loop. Finally, YSE_PZ is built to be flexibly used and deployed; YSE_PZ can support multiple, simultaneous, and independent transient collaborations through group-level data permissions, allowing a user to view the data associated with the union of all groups in which they are a member. YSE_PZ can be used as a local instance installed via Docker or deployed as a service hosted in the cloud. We provide YSE_PZ as an open-source tool for the community.

.. toctree::
   :maxdepth: 1

   install
   queries
   dashboards
   observing
   status_tags
   detail
   triage
   adding_data
   forms
   docker
   howto
   contributing
   api
   
Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

Citing YSE_PZ
=============

If you are using YSE_PZ in your research please cite the paper and Zenodo record

.. code:: none
      
      @ARTICLE{2023arXiv230302154C,
       author = {{Coulter}, D.~A. and {Jones}, D.~O. and {McGill}, P. and {Foley}, R.~J. and {Aleo}, P.~D. and {Bustamante-Rosell}, M.~J. and {Chatterjee}, D. and {Davis}, K.~W. and {Dickinson}, C. and {Engel}, A. and {Gagliano}, A. and {Jacobson-Gal{\'a}n}, W.~V. and {Kilpatrick}, C.~D. and {Kutcka}, J. and {Le Saux}, X.~K. and {Pan}, Y. -C. and {Qui{\~n}onez}, P.~J. and {Rojas-Bravo}, C. and {Siebert}, M.~R. and {Taggart}, K. and {Tinyanont}, S. and {Wang}, Q.},
        title = "{YSE-PZ: A Transient Survey Management Platform that Empowers the Human-in-the-Loop}",
      journal = {arXiv e-prints},
      keywords = {Astrophysics - Instrumentation and Methods for Astrophysics},
      year = 2023,
      month = mar,
      eid = {arXiv:2303.02154},
      pages = {arXiv:2303.02154},
      archivePrefix = {arXiv},
      eprint = {2303.02154},
      primaryClass = {astro-ph.IM},
      adsurl = {https://ui.adsabs.harvard.edu/abs/2023arXiv230302154C},
      adsnote = {Provided by the SAO/NASA Astrophysics Data System}
      }


.. code:: none

      @software{coulter_d_a_2022_7278430,
      author       = {Coulter, D. A and
                  Jones, D. O. and
                  McGill, P. and
                  Foley, R. J. and
                  Aleo, P. D. and
                  Bustamante-Rosell, M. J. and
                  Chatterjee, D. and
                  Davis, K. W. and
                  Engel, A. and
                  Gagliano, A. and
                  Jacobson-Galán, W. V. and
                  Kilpatrick, C. D. and
                  Pan, Y.-C. and
                  Rojas-Bravo, C. and
                  Siebert, M. R. and
                  Taggart, K. L. and
                  Tinyanont, S. and
                  Wang, Q.},
   title        = {{YSE-PZ: An Open-source Target and Observation
                   Management System}},
   month        = nov,
   year         = 2022,
   note         = {{YSE-PZ was developed by the UC Santa Cruz
                   Transients Team. The UCSC team is supported in
                   part by NASA grants NNG17PX03C, 80NSSC19K1386, and
                   80NSSC20K0953; NSF grants AST-1518052,
                   AST-1815935, and AST-1911206; the Gordon \&amp;
                   Betty Moore Foundation; the Heising-Simons
                   Foundation; a fellowship from the David and Lucile
                   Packard Foundation to R. J. Foley; Gordon and
                   Betty Moore Foundation postdoctoral fellowships
                   and a NASA Einstein fellowship, as administered
                   through the NASA Hubble Fellowship program and
                   grant HST-HF2-51462.001, to D. O. Jones; and a
                   National Science Foundation Graduate Research
                   Fellowship, administered through grant No.
                   DGE-1339067, to D. A. Coulter.}},
   publisher    = {Zenodo},
   version      = {v0.3.0},
   doi          = {10.5281/zenodo.7278430},
   url          = {https://doi.org/10.5281/zenodo.7278430}
   }

