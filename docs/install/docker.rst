.. _install-docker:

===============================
Installing Locally using Docker
===============================

.. admonition:: Is this the best install method for you?
  :class: attention

  In most cases, we recommend doing an :ref:`internet-based installation on Heroku <install-heroku>` instead. If you decide to do a local installation, be sure to read our page on :ref:`local installations <install-local>` to help you understand what's going on, particularly this section: :ref:`install-decision`

.. attention:: If you need an offline copy of Tabbycat, installing using Docker should be simpler and quicker than using the "Install Locally on…" instructions for your operating system. However if a Docker installation doesn't work as outlined below, it's harder to address what isn't working. If you encounter any problems with Docker, we recommend using the "Install Locally on…" option as a fallback, but if you need to do so, `please also report the issue you're having on GitHub <https://github.com/TabbycatDebate/tabbycat/issues/new?labels=installation-docker&title=Docker%20installation%20problem&body=Please%20be%20sure%20to%20include%20your%20operating%20system%20and%20version,%20and%20please%20be%20as%20specific%20as%20you%20can%20about%20the%20problem%20you%20encountered%3A%0D%0D>`_ or :ref:`contact the developers <authors>`.

Docker is an application that makes it very easy to load and run a specific collection of software. It allows us to bundle everything necessary to run Tabbycat into a single package rather than have users install everything needed step-by-step. Once set up, Docker will allow you to start and stop a webserver (that in turn runs Tabbycat) on your computer whenever you want and without the need for internet access.


1. Download Tabbycat
====================

1. `Go to the page for our latest release <https://github.com/TabbycatDebate/tabbycat/releases/latest>`_.

2. Download the zip or tar.gz file.

3. Extract all files in it to a folder of your choice.


2. Install Docker
=================

If using macOS
--------------

- Install the **Docker Desktop for Mac** from the `Docker store page <https://store.docker.com/search?type=edition&offering=community>`_.

If using Linux
--------------

- Install the **Docker Engine** for your OS from the `Docker store page <https://store.docker.com/search?type=edition&offering=community>`_.

If using Windows 10 Pro, Enterprise, or Education Edition
---------------------------------------------------------

.. rst-class:: spaced-list

1. Install the ****Docker Desktop for Windows*** from the `Docker store page <https://store.docker.com/search?type=edition&offering=community>`_.
2. Before or shortly after installing it, Docker may ask you to enable hypervisor and restart your PC. If it asks you this follow the prompts and restart as asked.
3. Once Docker has finished installing, open up the newly-installed Docker application, then right-click the app's icon (the whale) in the Taskbar.
4. From there, hit *Settings* in the menu and *Shared Drives* in the sidebar. Tick the checkbox next to your hardrive and then click *Apply*. After that has applied exit and reopen the docker app (ie right-click the taskbar icon and hit exit) and verify that the checkbox is still there.

  .. image:: images/tabbycat-docker-drives.png
      :alt: Share Drives with Docker App

If using Windows 7, Windows 8, or Windows 10 Home Edition
---------------------------------------------------------

- Install the **Docker Toolbox** from the `Docker Toolbox downloads page <https://www.docker.com/products/docker-toolbox>`_.

.. tip:: Not sure which edition of Windows you have? Click Start, search for "System", and open the Control Panel item "System".


3. Run Tabbycat in Docker
=========================

If using the Docker App
-----------------------

*These instructions apply if you installed the Docker App, i.e., if you are using macOS, Linux or Windows Pro/Enterprise/Education.*

.. rst-class:: spaced-list

1. Ensure that Docker application is open (there should be a whale icon in your menu/task bar) and that it says that Docker is running.

2. Browse to the location where you extracted Tabbycat to. Open up the **bin** folder there. Within that folder:

    - If you're on macOS, press the Control key, click the icon for **osx_docker_start.command**, then choose Open from the shortcut menu.
    - If you're on Windows, open **windows_docker_start.bat**.
    - If you're on Linux, open up a terminal in the Tabbycat folder (*i.e.* the folder containing ``README.md``) and run ``docker-compose up``.

3. A terminal window should popup and bunch of text scroll by. If this is your first time running Docker it may take a while (30 minutes or more) to download the virtual machine. When the text has stopped scrolling by you should see a `Finished building Tabbycat!` message.

4. Open up http://localhost:8000/ (Windows) or http://0.0.0.0:8000 (OSX/Linux) in a browser of your choice!

.. note:: If you want to reopen Tabbycat at a later time (say after restarting) repeat steps 1 through 4 here.

If using the Docker Toolbox
---------------------------

*These instructions apply if you installed the Docker Toolbox, i.e., if you are using Windows 7, Windows 8 or Windows 10 Home.*

.. rst-class:: spaced-list

1. Start the **Docker Quickstart Terminal**.

2. Run the command ``docker-machine ip``. Take note of the IP address it shows, for example::

    $ docker-machine ip
    192.168.99.100

3. Navigate to the Tabbycat folder (*i.e.* the folder containing ``README.md``) and run ``docker-compose up``.

4. Open a browser and go to http://192.168.99.100:8000/, replacing "192.168.99.100" with whatever IP address was shown in step 2.

5. Once you're done and want to stop the Tabbycat server, press Ctrl+C, wait until the next prompt appears, and then run ``docker-machine stop``.

.. note:: If you want to reopen Tabbycat at a later time (say after restarting) repeat steps 1 through 4 here.
