Inputs
==================
Inputs which are constant for all runs are specified in the **default_post.json** file. A **default_post** template can be found at the root of the Nova Metrics folder. Any input which is not specified at all uses the REopt default. REopt defaults can be found `Here <https://github.com/NREL/REopt_Lite_API/blob/master/reo/nested_inputs.py>`_. 

The Inputs.xlsx file defines scenario-specific inputs and determines what comparison metrics will be calculated. The Inputs.xlsx has **N** Sheets (Update when OCHRE and ResStock are integrated).

* **File Paths** Defines folder structure for main inputs and outputs. 
* **REopt Posts** Each column sets a REopt input and each row specifies a post.
* **Generate Metrics** Specifies run and baseline for metric calculations.
* **API Keys**  User adds API keys to query various programs and data sets.
* **OCHRE** Optional sheet containing OCHRE model inputs. 

File Paths
----------------
Most file paths are relative to the *main_folder*. The folder *timeseries_output_folder* is relative to the *metrics_folder*. The workflow will create folders as necessary so the user does not need to create the folder structure ahead of time. The following is the list of folder paths:

* **reopt_posts** Folder to save REopt posts. 
* **reopt_results** Folder where REopt output json files are saved. 
* **timeseries_output_folder** Folder to store timeseries csv files for each run. Folder path is relative to *metrics_folder*. 
* **solar_profile_folder** Folder to store PV watts production factor outputs.
* **default_values_file** Path (including file name) to *default_post.json*.
* **metrics_folder** Folder to store metrics outputs. 
* **reopt_root_url** optional path to api branch. If not omitted then defaults to 'https://developer.nrel.gov/api/reopt'.
* **ochre_output_main_folder** optional path to folder containing OCHRE output subfolders. If omitted then defaults to "".

REopt Posts
------------------
The *REopt Posts* sheet specifies inputs for REopt post json files. he only required input is **post_name**. All other inputs are optional. Rows signify a single post while columns signify inputs for that post. Input columns are divided into two components: special inputs and post inputs. 

Special inputs include the following:

* **post_name** Defines what the resulting json file will be named (.json is appended programatically).  
* **output_subfolder** Sets a subfolder to save post in. Subfolder is relative to **reopt_posts** main folder. If no value is specified then will save post in **reopt_posts**. 
* **description** Adds description to REopt post and output. 
* **ochre_folder** Specifies a folder which contains OCHRE building model outputs. Only required if integrating with OCHRE load or using dispatchable EE models.
* **load_file** Specifies path to a csv file which contains hourly building load. Load is on first column with no header. 
* **solar_production_factor_file** Specifies path to a csv file which contains PV production factors. PV production is on first column with no header. If no path is specified then will use value from PV watts. 



Post inputs will insert the value directly into the REopt post. Inputs can be added to the REopt nested structure with the following conventions:

* ScenarioLevel|<name> will add to the top level Scenario
* <name> will add to Scenario[Site]
* <Upper_Level>|<lower_level> will add to Scenario[Site][Upper_level][lower_level]

For example, to input a value for PV max_kw, located at Scenario[Site][PV][max_kw], specify the column name as PV|max_kw. 

Blank input values are ignored.  



Generate Metrics
-------------------------
The *Generate Metrics* sheet specifies the results and baseline comparison for metrics calculations. The columns are specified as follows:

* **results_folder** Subfolder relative to *reopt_results* main folder. Only applies if *output_subfolders* were specified in the *REopt posts* sheet. 
* **results_name** Name	of REopt results json file as specified in *reopt_posts* from the *REopt posts* sheet. 
* **baseline_folder** Subfolder for baseline results relative to *reopt_results* main folder. Only applies if *output_subfolders* were specified in the *REopt posts* sheet. 
* **baseline_name**	Name of REopt results json file for baseline.
* **baseline_type** Optional string which specifies baseline comparison type in metrics outputs
* **wholesale_price_path** Optional path to wholesle price csv file. CSV file format should be single column of prices with no header.


API Keys
------------
The *API Keys* sheet specifies user keys for various api databases. There are two columns, *key_name* (which specifies what the api key is for) and *key_val* (which specifies the actual key). 
* **pv_watts** NREL API key for downloading solar profiles. Can be obtained `here <https://developer.nrel.gov/signup/>`_.
* **urdb** API key for downloading utility rates. Can be obtained from this `link <https://openei.org/services/api/signup/>`_.
* **reopt** NREL API key for running REopt (same as pv_watts). 


OCHRE
---------
Optional sheet which specifies various values for the OCHRE-REopt integration. The two columns are *ochre_type* and *ochre_value*. 
* **ochre_inputs_main_folder** Specifies the path relative to the main folder where OCHRE input subfolders or files are stored.
* **ochre_outputs_main_folder** Specifies the path relative to the main folder where OCHRE output subfolders or files are stored.
* **<output file identifier>** Can input rows to overwrite how REopt searches for the various OCHRE output files. Options are:
* *properties_file* Defaults to ".properties".
* *envelope_matrixA* Defaults to "_Envelope_matrixA.csv".
* *envelope_matrixB* Defaults to "_Envelope_matrixB.csv".
* *hourly_inputs* Defaults to "_hourly.csv"
* *water_tank_matrixA* Defaults to "_Water Tank_matrixA.csv".
* *water_tank_matrixB* Defaults to "_Water Tank_matrixB.csv".
