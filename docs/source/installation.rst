Installation
==========================

.. note::
    This package is still in development phase. Installation instructions will change as it develops.

The novametrics workflow can be cloned or downloaded from Github here:
https://github.com/sericson0/nova_metrics.git

.. note::
   The github url will change once it is added to the NREl github

Install the library by doing the following

::

   cd /path/to/novametrics
   python -m pip install -e . --user

Full functionality of the novametrics workflow depends on
- ResStock https://resstock.readthedocs.io
- Weather files https://data.nrel.gov/system/files/156/BuildStock_TMY3_FIPS.zip
- Buildstockbatch https://buildstockbatch.readthedocs.io
- OCHRE https://github.nrel.gov/Customer-Modeling/ochre (currently only available on NREl VPN)
- REopt https://github.com/NREL/REopt_API
- Docker Desktop
.. note::

   Users using a Windows operating system should install 
   `Docker Desktop Community 2.1.0.5 <https://docs.docker.com/docker-for-windows/release-notes/#docker-desktop-community-2105>`_
   or below.


Each package can be downloaded and installed separately. Once the novametrics library is installed you can also run the following command from the command line, which calls up the installation helper

::

   nova_installer

 