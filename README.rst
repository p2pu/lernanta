=========
Lernanta
=========

Lernanta is the new platform for P2PU. We are building on the codebase from
Batucada, a rewrite of drumbeat.org by Mozilla. 


Get Involved
------------

To help out with Lernanta, join the `P2PU dev mailing list`_ and introduce yourself. We're currently looking for help from Django / Python and front-end (HTML, CSS, Javascript) developers. 

.. _P2PU dev mailing list: http://lists.p2pu.org/mailman/listinfo/p2pu-dev

Interested in getting involved in Lernanta code development? Check out the development wiki [0] for more info! For a broader view on the development and tech team at P2PU, check out the P2PU Development and Tech team [1] page on the P2PU wiki [2] . 

[0] https://github.com/p2pu/lernanta/wiki
[1] http://wiki.p2pu.org/w/page/31978748/Development-and-tech-team
[2] http://wiki.p2pu.org


Setting up a local development environment in Ubuntu (Please note that your system most be updated before following these instructions.)
------------

You will need to `configure git and upload your SSH keys to github`_ 

.. _configure git and upload your SSH keys to github: http://help.github.com/set-up-git-redirect
     

You need a few libraries and can grab them with this command::

   sudo apt-get install git-core
   sudo apt-get install libxml2-dev
   sudo apt-get install libxslt-dev
   sudo apt-get install mysql-client
   sudo apt-get install mysql-server
   sudo apt-get install libmysqlclient-dev
   sudo apt-get install python-dev
   sudo apt-get install python-setuptools

To obtain the lernanta's source code that you will be modifying, first `fork the repository on the github website`_ and then clone it by running::

   git clone git@github.com:<your github username>/lernanta.git

.. _fork the repository on the github website: https://github.com/p2pu/lernanta/wiki/Github-Cheat-Sheet

Next, you'll need to install ``virtualenv`` and ``pip`` if you don't already have them.  Using `virtualenvwrapper`_ is also recommended. ::

   sudo easy_install virtualenv
   sudo easy_install pip
   sudo pip install virtualenvwrapper
   
Be sure to configure your shell so that pip knows where to find your virtual environments: ::

   # in .bashrc or .bash_profile
   export WORKON_HOME=$HOME/.virtualenvs
   export PIP_VIRTUALENV_BASE=$WORKON_HOME
   export PIP_RESPECT_VIRTUALENV=true
   source /usr/local/bin/virtualenvwrapper.sh

.. _virtualenvwrapper: http://www.doughellmann.com/docs/virtualenvwrapper/

Once installed, create your virtual environment for ``lernanta`` and install the dependencies. There's a chance that packages listed in ``requirements/compiled.txt`` won't install cleanly if your system is missing some key development libraries. For example, lxml requires ``libxml2-dev`` and ``libxslt-dev``. These should be available from your system's package manager. ::

   cd lernanta
   mkvirtualenv --no-site-packages lernanta 
   workon lernanta
   pip install -r requirements/compiled.txt
   pip install -r requirements/prod.txt
   pip install -r requirements/dev.txt

To be extra sure you're working from a clean slate, you might find it helps to delete ``.pyc`` files: ::

    ./sh/rmpyc

If the mysql database doesn't exist yet, create it. You need to `create the user`_ you'll use. You will use the database name, user, and password in the next file (settings_local.py) ::

   mysqladmin -u <user> -p create <database name>

.. _create the user: http://www.debuntu.org/how-to-create-a-mysql-database-and-set-privileges-to-a-user

Create a ``settings_local.py`` based on the template provided in the checkout. Edit the database parameters as needed ::

   cp settings_local.dist.py settings_local.py

If you not installed a local version of mysql, you will need to do so now. 

Next, sync the database and run migrations. ::

   ./sh/syncdb

Finally, start the development server to take it for a spin. You can register a new account and look in the terminal window where the server is running to find the activation link (If you get 404 error for that url, remove the "=": http://www.flickr.com/photos/digifoo/5593967846/). ::

   python manage.py runserver 

Once you have your development environment running, you can make changes or get the latest from github. See the wiki for more information: https://github.com/p2pu/lernanta/wiki
