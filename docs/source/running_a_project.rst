Running a Project
==================
The Nova Analysis workflow can be run via the command line. To run the workflow, open the command line and change directory to the **nova_metrics** folder where the *workflow.py* file resides. The following is how you call the workflow in the command line.

.. code-block:: bash

	python workflow.py <path to main folder> --<run arguments> 

The <path to main folder> is an absolute or relative path to where the input files reside and the outputs will be saved to. 

The available run arguments are:

* --all [-a] Runs full workflow.
* --posts [-p] Creates REopt posts.
* --reopt [-r] Runs REopt for each post.
* --metrics [-m] Generates metrics.
* --keep_runs [-k] If specified then will not rerun already saved runs. Defaults to false, where simulations and optimizations are rerun and results are overwritten.
* --inputs_file_path [-i] Optional specification for where the Inputs excel file is saved, relative to main_folder. Defaults to *Inputs.xlsx* 


Multiple run arguments may be added. Examples of valid commands include::

	python workflow.py ../ --posts
	python workflow.py ../ -pr
	python workflow.py ../ --reopt --metrics