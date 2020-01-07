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
Ask D. Jones for these

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

Finally, load the database using the existing YSE_PZ database
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
   
Starting the Web Server
=======================

In the YSE_PZ directory, run::

  python manage.py migrate
  python manage.py runserver

Then in a web browser on your computer,
go to the url http://127.0.0.1:8000.  You
should be good to go!
