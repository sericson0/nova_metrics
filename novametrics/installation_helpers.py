from git import Repo
import os

def clone_repository(repo_url, github_main_folder, branch = ""):
    repo_name = repo_url.rsplit("/", 1)[1].replace(".git", "")
    output_folder = os.path.join(github_main_folder, repo_name)
    if branch == "":
        Repo.clone_from( repo_url, output_folder)
    else:
        Repo.clone_from( repo_url, output_folder, branch = branch)


github_main_folder = "C:/Users/sericson/Desktop/Github Files"
url = 'https://github.com/NREL/resstock.git'
branch='restructure-v3'

clone_repository(url, github_main_folder, branch)