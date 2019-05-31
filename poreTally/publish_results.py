import os
from git import Repo
from shutil import rmtree
import pexpect
from distutils.dir_util import copy_tree
import requests
from getpass import getpass
from helper_functions import parse_output_path, parse_input_path
from time import gmtime, strftime
import sys


def main(args):
    summary_dir = os.path.realpath(args.working_dir) + '/analysis/summary/'
    if not os.path.isdir(summary_dir):
        raise ValueError('No summary directory found at {}, '
                         'did you run analysis already?'.format(args.working_dir))
    if args.git:
        git_dir = os.path.realpath(args.working_dir) + '/analysis/to_github/'
        if os.path.isdir(git_dir):
            rmtree(git_dir)
        repo_obj = Repo.clone_from(url=args.git, to_path=git_dir)
        copy_tree(summary_dir, git_dir)
        file_list = [f for f in parse_input_path(git_dir) if '.git' not in f]
        repo_obj.index.add(file_list)
        repo_obj.index.commit(message='added benchmark results')
        repo_obj.remote('origin').push()
        print('Results summary pushed to {}'.format(args.git))
    share_results = input(f'\n\nporeTally has finished! Check your report here: {summary_dir+ "REPORT.html"} \n'
                          '\n'
                          'You can help the MinION user community gain insight in the performance of de novo '
                          'assemblers and pick the best one for their dataset, by submitting your results to a shared '
                          'Github repository (github.com/cvdelannoy/assembler_benchmark_new_submissions). In short, '
                          'this will be done completely automatically, by issuing a fork request from a given Github '
                          'account. The whole process is transparent, as all the pull requests are publicly visible. '
                          'The collected benchmark info will periodically be curated and summarized in insightful '
                          'tables and figures. Of course, submissions will be duely credited and no sequence-specific '
                          'information will be shared, only quality metrics!'
                          '\n'
                          'Would you like to submit your results? (y/n) ')
    while share_results not in ['y', 'n', 'yes', 'no']:
        share_results = input('please answer with y(es) or n(o): ')
    if share_results in ['y', 'yes']:
        print('\nGreat, thanks for sharing!\n')

        # ---- Forking ----
        while True:
            ses = requests.Session()

            github_username = input('Github username for the account from which you want to submit results: ')

            ses.auth = (github_username, getpass('Enter Github password: '))
            submission_url = 'https://github.com/{git_id}/poreTally_collective_submissions.git'.format(git_id=github_username)
            fork_req = ses.post('https://api.github.com/repos/cvdelannoy/poreTally_collective_submissions/forks')
            if int(fork_req.status_code) == 202:
                break
            elif int(fork_req.status_code) == 401:
                print('Authentication for Github account {} failed. Please retry.'.format(github_username))
            else:
                print('Authentication failed due to some unforeseen '
                      'circumstance (HTTP status code {status}). Please retry. '.format(status=fork_req.status_code))

        # ---- add, commit, push ----
        print('\nPushing results to fork...')
        all_submissions_dir = os.path.realpath(args.working_dir) + '/analysis/collective_submissions/'
        if os.path.isdir(all_submissions_dir):
            rmtree(all_submissions_dir)
        cur_foldername = strftime('%Y%m%d%H%M%S', gmtime())
        repo_obj = Repo.clone_from(url=submission_url, to_path=all_submissions_dir)
        branch_obj = repo_obj.create_head(cur_foldername)
        repo_obj.head.reference = branch_obj
        repo_obj.head.reset(index=True, working_tree=True)
        submission_dir = parse_output_path(all_submissions_dir + cur_foldername)
        copy_tree(summary_dir, submission_dir)
        file_list = [f for f in parse_input_path(submission_dir) if '.git' not in f]
        repo_obj.index.add(file_list)
        repo_obj.index.commit(message='collective benchmark submission')

        # child.logfile = sys.stdout
        child = pexpect.spawn('git push origin HEAD:{branch}'.format(branch=cur_foldername),
                              cwd=submission_dir)
        child.expect('Username for \'https://github.com\':.*', timeout=2)
        child.sendline(ses.auth[0]+'\n')
        child.expect('{un}\r\n\r\nPassword for \'https://{un}@github.com\':.*'.format(un=ses.auth[0]))
        child.sendline(ses.auth[1])
        push_check = child.read()
        if b'[new branch] HEAD' not in push_check:
            ValueError('''Pushing to collective benchmark fork has failed...Sorry, that should not happen!
            
            Please report the error below on the poreTally github:
            
            {push_txt}'''.format(push_txt=push_check))

        # ---- submit pull request ----
        print('\nResults pushed! Issuing pull request...')
        pull_url = 'https://api.github.com/repos/cvdelannoy/poreTally_collective_submissions/pulls'
        pull_bool = False
        for _ in range(3):
            pull_params = {'title': 'poreTally_collective_submissions',
                           'base': 'master',
                           'head': github_username+':'+cur_foldername}
            pull_req = ses.post(pull_url, json=pull_params)
            if int(pull_req.status_code) == 201:
                print('\nResults were successfully submitted to the poreTally collective benchmark!\n\n'
                      'Keep an Eye on https://github.com/cvdelannoy/poreTallyCommunity for future analyses.')
                pull_bool = True
                break
            elif int(pull_req.status_code) == 401:
                print('Authentication for Github account {} failed when attempting a pull request. '
                      'Retrying...'.format(github_username))
            else:
                print('Authentication for issuing a pull request failed due to some unforeseen '
                      'circumstance (HTTP status code {status}). Retrying... '.format(status=pull_req.status_code))
        if not pull_bool:
            ValueError('''Making a pull request for the collective benchmark fork has failed...Sorry, that 
            should not happen! Please report the error below on the poreTally github:
            
            HTTP status code {sc}: {pull_txt}'''.format(sc=pull_req.status_code, pull_txt=pull_req.reason))
