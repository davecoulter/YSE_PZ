.. _install:

************
Installation
************

This is a quick guide to performing a local installation
of :code:`YSE_PZ`.

Prerequisites
=============

MySQL
-----

If you don't already have MySQL, it's easy to get it
using Homebrew.  To get homebrew, run::

  /usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"

Then to install and start MySQL::

  brew install mysql

Check your :code:`MySQL` version with:

  mysql --version

If you're running version 5, you should try
to upgrade to :code:`MySQL` version 8 if possible::

  brew upgrade mysql

After that, start the :code:`MySQL` server with::

  brew tap homebrew/services
  brew services start mysql

Then set up your root password::

  mysqladmin -u root password 'yourpassword'

Make sure to put single quotes around your password!

Anaconda Python
---------------
<http://anaconda.org>

Database File and settings.ini file
-----------------------------------
If you're a YSE or UCSC team member (or other collaborator),
ask D. Jones for these files.  Otherwise, you can use the
public versions of the YSE_PZ database (updated approximately
whenever I feel like it, or please ask for the latest and greatest),
which are :code:`YSE_PZ/public_settings.ini` for the settings file
and the following Dropbox link for the database.

If you don't need to ingest any new transients into the database, you
can copy this file over to :code:`YSE_PZ/settings.ini` and you're
good to go!  Otherwise, *still* copy the file over and then see
the :ref:`ysecrons` to finish the setup.

Setting Up the YSE_PZ Database
==============================
Start up MySQL and run a few commands to get the database
permissions set properly::

  mysql -u root -p
  
Inside MySQL::

  CREATE DATABASE YSE;
  CREATE USER 'django'@'localhost' IDENTIFIED BY '4django!';
  GRANT ALL PRIVILEGES ON *.* TO 'django'@'localhost' WITH GRANT OPTION;
  CREATE USER 'django'@'%' IDENTIFIED BY '4django!';
  GRANT ALL PRIVILEGES ON *.* TO 'django'@'%' WITH GRANT OPTION;
  CREATE USER 'explorer'@'localhost' IDENTIFIED BY '4Explor3R!';
  GRANT ALL PRIVILEGES ON *.* TO 'explorer'@'localhost' WITH GRANT OPTION;

Finally, exit out of mysql and load the database using the existing YSE_PZ database
file that someone hopefully sent you.  For the DB backup taken on Nov. 4th,
that command would be::

  mysql -u root -p YSE < 20191104_YSE.sql

If this fails with a collation error, you might have to
open up the file and replace :code:`utf8mb4_0900_ai_ci` 
:code:`utf8mb4_unicode_ci`.

Installing the YSE_PZ Code
==========================

Should be straightforward::

   git clone https://github.com/davecoulter/YSE_PZ.git
   cd YSE_PZ
   conda env create -f yse_pz.yml
   conda activate yse_pz
   pip install -r requirements.txt

Put the :code:`settings.ini` file in the :code:`YSE_PZ/`
directory (**not** the main repository directory, the directory
with the same name one level down).

Please note that sometimes the extinction module is buggy.
It is needed for some functionality but I would 
recommend trying to install it last.

Alternatively, I haven't tried this myself, but - the latest YSE_PZ conda environment from my mac
is included as :code:`yse_pz_latest.yml`, so to avoid pip as
much as possible you can try::

  conda env create -f yse_pz_latest.yml
  conda activate yse_pz
  
Starting the Web Server
=======================

In the YSE_PZ directory, run::

  python manage.py migrate
  python manage.py runserver

Then in a web browser on your computer,
go to the url <http://127.0.0.1:8000>.  You
should be good to go!

.. _ysecrons:

Setting up the YSE-PZ Crons
===========================

Running YSE-PZ as a living database that ingests
new transient data requires setting up two crons
to add new transients from the Transient Name Server
and ingest new ZTF data from MARS.  Ingesting new
ZTF data for existing transients from MARS is relatively
easy, while creating new transients from TNS requires
setting up a TNS "bot" for yourself or your group at
`<https://wis-tns.weizmann.ac.il/bots>`_.  See the TNS bulk
reports manual at `<https://wis-tns.weizmann.ac.il/sites/default/files/api/TNS_bulk_reports_manual.pdf>`_
for more information.  Once the API key has been set up,
paste the key into the :code:`tnsapikey=` line in the :code:`YSE_PZ/settings.ini`
file.

There are sometimes errors related to ingesting new transients,
and for this reason it helps to link an email address to an account
where error messages can be sent.  This is the :code:`dbemail` key in
the :code:`YSE_PZ/settings.ini` file.  Unfortunately, to *send* those
emails, you need to link an email account to YSE_PZ.  You can
do this by setting :code:`SMTP_LOGIN` and :code:`SMTP_PASSWORD`
in the :code:`SMTP_provider` section of the :code:`settings.ini` file
to your email username and password (you'll need to change :code:`SMTP_HOST` if the
account is not gmail).  You'll also have to allow access to less secure
apps in google, which is easy to find instructions for online.

Once all this has been set up, you can run the TNS cron with::

  python manage.py runcrons YSE_App.util.TNS_Synopsis.TNS_uploads.TNS_recent --force

Every time you run this command (manually or with a cron, e.g., `<https://www.man7.org/linux/man-pages/man5/crontab.5.html>`_),
this will grab transients uploaded to TNS or updated within the last day.  To change the time interval (in YSE, we do
this every three minutes), change the :code:`tns_recent_ndays` parameter in the settings.ini file.

Finally, to get new ZTF or TNS photometry/spectra for objects, the following cron will grab everything for
transients with the statuses :code:`Watch`, :code:`Interesting`:, :code:`FollowupRequested`, :code:`Following`,
or :code:`FollowupFinished`::

  python manage.py runcrons YSE_App.util.TNS_Synopsis.TNS_uploads.TNS_updates --force

For everything marked as :code:`Ignore` for transients modified in the last 30 days, run this one::

  python manage.py runcrons YSE_App.util.TNS_Synopsis.TNS_uploads.TNS_Ignore_updates --force

This can be a *ton* of transients, so it's best not to run this too often.

Bugs, etc.
==========

Please feel free to use the GitHub page for bugs/issues.  Good luck!
