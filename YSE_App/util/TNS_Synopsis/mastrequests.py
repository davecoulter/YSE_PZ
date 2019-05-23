from casjobs import CasJobs

#Partially from https://github.com/rlwastro/mastcasjobs. Adapted to Python 3.6 by T. Hung 05/15/2019


__all__ = ["MastCasJobs", "contexts"]

# some common MAST database contexts
contexts = [
            "GAIA_DR1",
            "GALEX_Catalogs",
            "GALEX_GR6Plus7",
            "GALEX_UV_BKGD",
            "HLSP_47Tuc",
            "HSLP_GSWLC",
            "HSCv3",
            "HSCv2",
            "HSCv1",
            "Kepler",
            "PanSTARRS_DR1",
            "PanSTARRS_DR2",
            "PHATv2",
            "SDSS_DR12",
            ]

class MastCasJobs(CasJobs):
    """
    Wrapper around the MAST CasJobs services.
    ## Keyword Arguments
    * `username` (str): Your CasJobs user name. It can also be
      provided by the `CASJOBS_USERID` environment variable.
    * `password` (str): Your super-secret CasJobs password. It can also be
      provided by the `CASJOBS_PW` environment variable.
    * `userid` (int): The WSID from your CasJobs profile. This is not used
      if `username` is specified.  Note that when this alternate login method is
      used, the get_fast_table method will not work.  This can also be
      provided by the `CASJOBS_WSID` environment variable.
    * `request_type` (str): The type of HTTP request to use to access the
      CasJobs services.  Can be either 'GET' or 'POST'.  Typically you
      may as well stick with 'GET', unless you want to submit some long
      queries (>~2000 characters or something like that).  In that case,
      you'll need 'POST' because it has no length limit.
    * `context` (str): Default context that is used for queries.
    * `base_url` (str): The base URL that you'd like to use depending on the
      service that you're accessing. Default is the MAST CasJobs URL.
    * `wsid_url` (str): The service URL that is used to login using the username
      and password.  Default is the MAST CasJobs service URL.
    * `fast_url` (str): The URL that provides fast non-queued retrieval for MAST
      CasJobs tables.  Note that this is a non-standard method that only works
      for MAST databases!
    """
    def __init__(self, username=None, password=None, userid=None,
                 request_type="GET", context="PanSTARRS_DR1",
                 base_url="http://mastweb.stsci.edu/ps1casjobs/services/jobs.asmx",
                 wsid_url=None, fast_url=None):

        if base_url.lower().find("//mastweb.stsci.edu/") >= 0:
            # set defaults for MAST CasJobs
            if wsid_url is None:
                wsid_url="https://mastweb.stsci.edu/ps1casjobs/casusers.asmx/GetWebServiceId"
            if fast_url is None:
                fast_url="https://ps1images.stsci.edu/cgi-bin/quick_casjobs.cgi"


        super().__init__()
        self.wsid_url = wsid_url
        self.fast_url = fast_url
        self.context = context
        self.base_url = base_url
        self.request_type = request_type

    def quick(self, q, context=None, task_name="quickie"):
        """
        Run a quick job. Like CasJobs method but adds astropy option.
        ## Arguments
        * `q` (str): The SQL query.
        ## Keyword Arguments
        * `context` (str): Casjobs context used for this query.
        * `task_name` (str): The task name.
        * `system` (bool) : Whether or not to run this job as a system job (not
          visible in the web UI or history)
        * `astropy` (bool) : If True, returns output as astropy.Table
        ## Returns
        * `results` (str): The result of the job as a long string (or as Table if astropy=True).
        """
        if not context:
            context = self.context
        results = super().quick(q, context=context, task_name=task_name)

        return results

