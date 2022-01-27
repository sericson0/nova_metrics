from git import Repo
import os
from git import RemoteProgress
from tqdm import tqdm

class CloneProgress(RemoteProgress):
    def __init__(self):
        super().__init__()
        self.pbar = tqdm()

    def update(self, op_code, cur_count, max_count=None, message=''):
        self.pbar.total = max_count
        self.pbar.n = cur_count
        self.pbar.refresh()

def clone_repository(repo_url, github_main_folder, branch = ""):
    repo_name = repo_url.rsplit("/", 1)[1].replace(".git", "")
    output_folder = os.path.join(github_main_folder, repo_name)
    if branch == "":
        Repo.clone_from( repo_url, output_folder, progress=CloneProgress())
    else:
        Repo.clone_from( repo_url, output_folder, branch = branch, progress=CloneProgress())


github_main_folder = "C:/Users/sericson/Desktop/Github Files"
url = 'https://github.com/NREL/resstock.git'
branch='restructure-v3'

clone_repository(url, github_main_folder, branch)
