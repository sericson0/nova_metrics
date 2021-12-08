Tutorial
=========
This tutorial walks through how to set up the Nova Metrics workflow to create REopt posts, call the REopt API to produce REopt results, and then generate metrics.
See https://reopt.nrel.gov/ for further details on NREL's REopt optimization tool.

To begin, create a new folder named **nova_tutorial** where we will store the results of this tutorial. 

The three steps to run the workflow are:

#. Create a *default_post.json* file which serves as a template for all posts.
#. Create an *Inputs.xlsx* file, where scenario specific attributes are defined.
#. Run the workflow.

Set Defaults
--------------

Create an empty file in the **nova_tutorial** folder and name it **default_post.json**. This file will contain default inputs for each of the REopt scenarios you will run.
Any value not specified in **default_post.json** will be given the REopt default. REopt default values can be found `here <https://github.com/NREL/REopt_Lite_API/blob/master/reo/nested_inputs.py>`_  

Copy the following inputs into your **default_post.json** file. It includes the following changes to the REopt default values

* Updated PV and Storage costs for recent and potential future cost declines. 
* Added a `URDB label <https://openei.org/wiki/Utility_Rate_Database>`_ for a Consolidated Edison residential electric tariff rate. 
* Added a load profile. 
* Set the default sizing of solar and storage to zero.  

.. code-block:: 

	{

		"Scenario": {
			"Site": {
				"latitude": 40.71,
				"longitude": -74.01,
				"LoadProfile": {
				    "doe_reference_name": "RetailStore",
            		"annual_kwh": 17520.0,
            		"city": "Baltimore"
				},
				"ElectricTariff": {
					"urdb_label": "6112d2875457a3233ef802ce" 
				},
				"PV": {
					"min_kw": 0,
					"max_kw": 0,
					"installed_cost_us_dollars_per_kw": 2300.0, 
					"federal_itc_pct": 0.26
				},
				"Storage": {
					"min_kwh": 0.0,
					"max_kwh": 0.0,
					"min_kw": 0.0,
					"max_kw": 0.0,
					"macrs_option_years": 5,
					"installed_cost_us_dollars_per_kwh": 300.0,
					"installed_cost_us_dollars_per_kw":  600.0,
					"replace_cost_us_dollars_per_kwh":  175.0,
					"replace_cost_us_dollars_per_kw":  350.0,
					"canGridCharge": true
				}
			}
		}
	}

Templates for both the **default_post.json** and the **Inputs.xlsx** file can be found in the templates folder at the root of the Nova Metrics folder. 

Inputs File
------------

Navigate to the **templates** folder found in the root folder of nova_metrics. Copy the Inputs.xlsx template from and save the copy back in the **nova_tutorial** folder. The inputs file has four sheets: 

* File Paths
* REopt Posts
* Generate Metrics
* API Keys

See the Inputs section (TODO figure out how to link sections) for details on inputs for each sheet. The template is set up to compare a home without any system, one with solar PV, and one with PV+storage.

For this tutorial the only sheet we will change is to the API keys. 

* The *pv_watts* and *reopt* keys are the same, and can be obtained from the `NREL Developer Network <https://developer.nrel.gov/signup/>`_.
* The *urdb* key can be obtained `here <https://openei.org/services/api/signup/>. 

Run Workflow
---------------
Open a command line and change directories into the nova_metrics folder which contains the **workflow.py** Python script. Now type

.. code-block:: 

	python workflow.py <path to nova_tutorial folder> --all

The path to the nova_tutorial folder can be an absolute path or relative to the folder containing **workflow.py**. Running this command will run the workflow and create several folders in the nova_tutorial folder. See *Running a Project* Section (LINK TO SECTION) for more information on how to run parts of workflow.

* **REopt Posts** REopt input json files.
* **Solar Factors** PV factors for each unique location. 
* **REopt Results** REopt output json files.
* **Metrics** contains compiled metrics outputs and csv values of timeseries. 

The Metrics.xlsx file contains compiled metrics for each run. See the *Metrics* Section (LINK TO SECTION) for more information. 

