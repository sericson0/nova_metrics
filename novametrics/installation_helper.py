import os
import shutil
import subprocess
import requests
from git import Repo, RemoteProgress
from tqdm import tqdm

def download_weather_files(main_folder):
    check_download = input("Would you like to download weather files (speeds up ResStock and OCHRE calculations). Type y or yes to download.").lower()
    if check_download in ["y", "yes"]:
        print('Downloading Weather files')
        url = 'https://data.nrel.gov/system/files/156/BuildStock_TMY3_FIPS.zip'
        req = requests.get(url)
        filename = os.path.join(main_folder, url.split('/')[-1])
        with open(filename,'wb') as output_file:
            output_file.write(req.content)
        print('Downloading Completed')


class CloneProgress(RemoteProgress):
    def __init__(self):
        super().__init__()
        self.pbar = tqdm()

    def update(self, op_code, cur_count, max_count=None, message=''):
        self.pbar.total = max_count
        self.pbar.n = cur_count
        self.pbar.refresh()

def clone_repository(repo_url, main_folder, branch = ""):
    repo_name = repo_url.rsplit("/", 1)[1].replace(".git", "")
    output_folder = os.path.join(main_folder, repo_name)
    empty_repository = check_repository_folder(main_folder, repo_name)
    if empty_repository:
        try:
            if branch == "":
                Repo.clone_from(repo_url, output_folder, progress=CloneProgress())
            else:
                Repo.clone_from(repo_url, output_folder, branch = branch, progress=CloneProgress())
        except Exception as e:
            print(f"Could not clone repository due to error {e}")


def check_install(program_name):
    while True:
        continue_install = input(f"Would you like to install {program_name}? Type y to install or n to skip install:").lower()
        if continue_install in ["y", "yes"]:
            return True
        elif continue_install in ["n", "no"]:
            return False
        else:
            print("Not a valid input. Please type y, yes, n, or no:")
            continue

def get_branch_version(default):
    branch = input(f"By default, branch {default} will be used. If you would like an alternative branch type it here.\nOtherwise press enter to accept:")
    if branch == "":
        branch = default
    return branch


def check_repository_folder(main_folder, repo_name):
    output_folder = os.path.join(main_folder, repo_name)
    if not os.path.isdir(output_folder):
        return True
    else:
        overwrite = input(f"A repository for {repo_name} already exists. Type y or yes to overwrite:").lower()
        if overwrite in ["y", "yes"]:
            shutil.rmtree(output_folder)
            return True
        else:
            return False 


def run_setup(main_folder, repo_name, install_type = "setup"):
    working_dir = os.getcwd()
    repo_folder = os.path.join(main_folder, repo_name)
    os.chdir(repo_folder)
    print(f"Setting up package {repo_name}")
    if install_type == "setup":
        subprocess.call(['python', "setup.py", 'install'])
    elif install_type == "pip":
        subprocess.call(['python', "-m", "pip", "install", "-e", ".", "--user"])
    else:
        print("install type must be setup or pip")
    os.chdir(working_dir)

def install_ochre(main_folder):
    repo_name = "ochre"
    if not check_install(repo_name):
        return None
    else:
        branch = get_branch_version("hpxml")
        clone_repository("https://github.nrel.gov/Customer-Modeling/ochre.git", main_folder, branch = branch)
        run_setup(main_folder, repo_name)


def install_resstock(main_folder):
    repo_name = "resstock"
    if not check_install(repo_name):
        return None
    else:
        branch = get_branch_version("restructure-v3")
        clone_repository("https://github.com/NREL/resstock.git", main_folder, branch = branch)
        run_setup(main_folder, repo_name, install_type = "setup")
    

def install_buildstockbatch(main_folder):
    repo_name = "buildstockbatch"
    if not check_install(repo_name):
        return None
    else:
        branch = get_branch_version("restructure-v3")
        clone_repository("https://github.com/NREL/buildstockbatch.git", main_folder, branch = branch)
        run_setup(main_folder, repo_name, install_type = "pip")
        print("""
        Users using a Windows operating system with Python version 3.8 or higher may encounter the 
        following error when running simulations locally: 
        docker.errors.DockerException: Install pypiwin32 package to enable npipe:// support 
        Manually running the pywin32 post-install script using the following command may resolve the error: 
        python <path-to-python-env>\Scripts\pywin32_postinstall.py -install
        """
        )

def main():
    print(
    """
    The Nova Metrics workflow uses sevearl NREL developed packages.
    It can be difficult to correctly download and install all of these.
    This is an installer helper to help get the metrics workflow set up on your computer.

    To run the full Nova Metrics workflow you need to download and install ResStock, Buildstockbatch and OCHRE.
    These can be found in the links below
    -ResStock: https://github.com/NREL/resstock (uses restructure-v3 branch)
    -Buildstockbatch: https://github.com/NREL/buildstockbatch.git (uses restructure-v3 branch)
    -OCHRE: https://github.nrel.gov/Customer-Modeling/ochre (uses hpxml branch)

    It is also recommended to download the following weather files:
        https://data.nrel.gov/system/files/156/BuildStock_TMY3_FIPS.zip

    This installation helper faciltates downloading and installing these packages.
    ***NOTE*** for OCHRE to download correctly you currently must be connected to the NREL VPN)
    
    This installer does not download the following, which are useful for running program locally:
    In addition to the packages loaded, download Docker Desktop to run buildstockbatch and OCHRE locally. 
        https://www.docker.com/products/docker-desktop

    You can download REopt to run locally and for additional functionality (use nova_analysis branch)
        https://github.com/NREL/REopt_API
       
    """
    )
    while True:
        initiate_install = input("Would you like to use the installation helper? type y to continue and n to exit:").lower()
        if initiate_install in ["y", "yes"]:
            break
        elif initiate_install in ["n", "no"]:
            return None
        else:
            print("Type y or n")

    while True:
        main_folder = input("Please provide a path to where repositories will be downloaded:").replace("\\", "/")
        if os.path.isdir(main_folder):
            break
        else: 
            print("Path must be a valid path to an actual folder.")

    install_resstock(main_folder)
    install_buildstockbatch(main_folder)
    install_ochre(main_folder)
    download_weather_files(main_folder)



if __name__ == "__main__":
    main()