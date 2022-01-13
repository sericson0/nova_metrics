Running a Project
==================
The Nova Analysis workflow can be run via the command line. To run the workflow, open the command line and change directory to the **nova_metrics** folder where the *workflow.py* file resides. The following is how you call the workflow in the command line.

.. code-block:: bash

	python workflow.py <path to main folder> --<run arguments> 

The <path to main folder> is an absolute or relative path to where the input files reside and the outputs will be saved to. 

The available run arguments are:

* --all [-a] Runs full workflow. Will only run OCHRE simulations if OCHRE sheet is added to inputs. 
* --ochre [-o] Runs OCHRE simulations.  
* --posts [-p] Creates REopt posts.
* --reopt [-r] Runs REopt for each post.
* --metrics [-m] Generates metrics.
* --keep_runs [-k] If specified then will not rerun already saved runs. Defaults to false, where simulations and optimizations are rerun and results are overwritten.
* --inputs_file_path [-i] Optional specification for where the Inputs excel file is saved, relative to main_folder. Defaults to *Inputs.xlsx*. 


Multiple run arguments may be added. Examples of valid commands include::

	python workflow.py ../ --posts
	python workflow.py ../ -pr
	python workflow.py ../ --reopt --metrics


Run OCHRE
----------
The workflow will run OCHRE simulations if --ochre is called or if --all is called and an OCHRE sheet is in the *Inputs* file. The OCHRE sheet can specify specific OCHRE controls such as where OCHRE inputs and outputs are saved to, and default values for the building simulations. OCHRE will simulate all buildings in the *OCHRE Inputs* main folder. 

Each building contains a properties file (generally a yaml file), and a schedule file (generally denoted by <name>_schedule.csv). The workflow determines individual buildings as any folder which contains files, so building inputs can be added in a nested folder strucutre of any depth. The folder strucutre will be presered when saving outputs. 