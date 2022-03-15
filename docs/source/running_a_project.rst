Running a Project
==================
Once the nova metrics package is installed (see Installation section), the Nova Analysis workflow can be run via the command line as follows: 

.. code-block:: bash

	nova_workflow <path to project main folder (optional)> --<run arguments> 

The <path to project main folder> is an absolute or relative path (relative to the command line wd) to where the input files reside and the outputs will be saved to. If left unspecified then will default to the command line working directory. 

The available run arguments are:

* main_folder (optional positional argument) to specify path to main folder. Only needed if main folder path is separate from command line directory.
* --all [-a] Runs full workflow. Will automatically run in by_building mode.
* --buildstock [-b] Call buildstockbatch to query ResStock buildings and run building simulations.
* --ochre [-o] Runs OCHRE simulations.  
* --posts [-p] Creates REopt posts.
* --reopt [-r] Runs REopt for each post.
* --metrics [-m] Generates metrics.
* --keep_runs [-k] If specified then will not rerun already saved runs. Defaults to false, where simulations and optimizations are rerun and results are overwritten.
* --inputs_file_path [-i] Optional specification for where the Inputs excel file is saved, relative to main_folder. Defaults to *Inputs.xlsx*. 
* --by_building [-g] If specified then runs REopt post and metrics for each building (subfolder) in OCHRE outputs main folder
* --start [-s] Optional input to set which folder or file REopt will start running. If omitted then start at first file or folder
* --n_workers Optional input to set the number of workers for buildstockbatch to run in parallel. Defaults to 2. 


Multiple run arguments may be added. Examples of valid commands include::

	nova_workflow --posts
	nova_workflow project_folder -oprmg
	nova_workflow --reopt --metrics
	nova_workflow 

if no named arguments are specified then will default to --all.

Run buildstock (ResStock)
----------------------------
Specifying --all or --buildstock will call buildstockbatch to query resstock buildings. ResStock inputs are controlled via a .yml file located in the main folder. This filename defaults to *resstock.yml* but can be specified via the *resstock_yaml* input in the File Paths tab.

.. note::
 OCHRE currently only supports single-family detached housing, and it is recommended to downselect to occupied buildings. This can be done with the following inputs in the .yml file

 ::

 	type: residential_quota_downselect
 	args: 
 		n_datapoints: <number of buildings to sample>
 		logic:
 			- Geometry Building Type RECS|Single-Family Detached
 			- Vacancy Status|Occupied
 			resample: true 

 Outputs for each building sampled consist of an *in.xml* file denoting home properties, and a *schedules.csv* file containing home hourly schedules. 




Run OCHRE
----------
The workflow will run OCHRE simulations if --ochre or --all is called. The OCHRE sheet can specify specific OCHRE controls such as where OCHRE inputs and outputs are saved to, and default values for the building simulations. *ochre_inputs_main_folder* can be specified in the the Inputs.xlsx File Paths tab. If unspecified then will check if *resstock_output_main_folder* is in the File Paths, and if not will default to **./ResStock**. OCHRE will simulate all buildings in the ochre inputs folder.  

Each input contains a properties file (generally either a .xml or a .yaml file), and a schedule file (generally denoted by <name>_schedule.csv). The workflow determines individual buildings as any folder which contains files, so building inputs can be added in a nested folder strucutre of any depth. The folder strucutre will be presered when saving outputs. 

Outputs maintain the same nested folder structure as inputs. 