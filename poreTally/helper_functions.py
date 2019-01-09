import os
import sys
import fnmatch
import yaml
import json
import warnings
from Bio import SeqIO
from git import Repo, GitCommandError
import tempfile
from pathlib import Path
from shutil import rmtree


def parse_output_path(location):
    """
    Take given path name. Add '/' if path. Check if exists, if not, make dir and subdirs.
    """
    location = os.path.realpath(location) + '/'
    if not os.path.isdir(location):
        os.makedirs(location)
    return location


def parse_input_path(location, pattern=None):
    """
    Take path, list of files or single file, Return list of files with path name concatenated.
    """
    if not isinstance(location, list):
        location = [location]
    all_files = []
    for loc in location:
        loc = os.path.abspath(loc)
        if os.path.isdir(loc):
            if loc[-1] != '/':
                loc += '/'
            for root, dirs, files in os.walk(loc):
                if pattern:
                    for f in fnmatch.filter(files, pattern):
                        all_files.append(os.path.join(root, f))
                else:
                    for f in files:
                        all_files.append(os.path.join(root, f))
        elif os.path.exists(loc):
            if pattern:
                if fnmatch.filter([loc], pattern):
                    all_files.append(loc)
        else:
            warnings.warn('Given file/dir %s does not exist, skipping' % loc, RuntimeWarning)
    if not len(all_files):
        ValueError('Input file location(s) did not exist or did not contain any files.')
    return all_files


def parse_version_commands(v_dict, description):
    """
    Take dict with version commands as values and tool names as keys and parse into list
     of strings that will print tool name and version in yaml format in log files.
    """
    cmds = ['echo "START METHODS PRINTING"']
    cmds.append('echo "description: {}"'.format(description).replace('\n', ''))
    cmds.append('echo "versions:"')
    for cv in v_dict:
        cmds.append('echo "  {cv}: "$({version})'.format(cv=cv, version=v_dict[cv]))
    cmds.append('echo "END METHODS PRINTING"')
    return cmds


def get_nb_bases(file, type='fasta'):
    """
    Get number of bases stored in a fasta/fastq file
    """
    lens_list = []
    for seq in SeqIO.parse(file, type):
        lens_list.append(len(seq))
    return sum(lens_list)


def dict_to_snakefile(cmds_dict, sf_dict):
    """
    Convert dicts to string that can serve as input for snakemake
    """
    sf_out = ''
    for rn in sf_dict:
        sf_rule = 'rule {}:\n'.format(rn)
        for rn2 in sf_dict[rn]:
            sf_rule += '\t{}:\n'.format(rn2)
            for l in sf_dict[rn][rn2]:
                if l:
                    if type(sf_dict[rn][rn2]) is dict:
                        sf_rule += '\t\t{k}=\'{v}\',\n'.format(k=l, v=sf_dict[rn][rn2][l].replace('\'', '\\\''))
                    elif type(l) is str:
                        sf_rule += '\t\t\'{}\'\n'.format(l.replace('\'', '\\\''))
                    elif type(l) is int:
                        sf_rule += '\t\t{}\n'.format(l)
        sf_out += sf_rule
        sf_out += '\tshell:\n\t\t\'\'\'\n\t\t'
        sf_out += 'echo [$(date +%Y-%m-%d_%H:%M:%S)] started pipeline {}\n\t\t'.format(rn)
        for l in cmds_dict[rn]:
            if l:
                if ' > ' in l:
                    sf_out += '{} 2>> {{log}}\n\t\t'.format(l)
                    # sf_out += 'echo $({} 2>&1 ) >> {{log}} 2>&1\n\t\t'.format(l)
                else:
                    sf_out += '{} >> {{log}} 2>&1\n\t\t'.format(l)
        sf_out += 'echo [$(date +%Y-%m-%d_%H:%M:%S)] finished pipeline {}\n\t\t'.format(rn)
        sf_out += '\'\'\'\n\n'
    return sf_out


def set_remote_safely(repo_obj, remote_name, url):
    remotes_list = [cur_remote.name for cur_remote in repo_obj.remotes]
    if remote_name in remotes_list:
        repo_obj.remote(remote_name).set_url(url)
        remote_obj = repo_obj.remote(remote_name)
    else:
        remote_obj = repo_obj.create_remote(url=url, name=remote_name)
    return remote_obj


# ---- Arg check functions ----

def raise_(ex):
    """
    Required to raise exceptions inside a lambda function
    """
    raise Exception(ex)


def is_fasta(filename):
    """
    Check whether file is existing, and if so, check if in fasta format.
    """
    if not os.path.isfile(filename):
        return raise_('reference file not found')
    with open(filename, "r") as handle:
        is_fasta_bool = any(SeqIO.parse(handle, "fasta"))
    if not is_fasta_bool:
        return raise_(f'{filename} file does not appear to be in fasta format')
    return os.path.realpath(filename)


def is_user_info_yaml(filename):
    """
    Check whether file is existing,
    """
    if not os.path.isfile(filename):
        return raise_('{} not found'.format(filename))
    with open(filename, "r") as handle:
        content = yaml.load(handle)
    if not type(content) is dict:
        return raise_('{} not a yaml'.format(filename))
    required_info = ['authors', 'species', 'basecaller', 'flowcell', 'kit']
    info_list = list(content)
    for ri in required_info:
        if ri not in info_list:
            return raise_('{} not in info file, but required'.format(ri))
    return os.path.realpath(filename)


def is_valid_repo(repo_url):
    repo_dir = tempfile.mkdtemp('poreTally_repo_test')
    tst_file = repo_dir+'/push_test.txt'
    Path(tst_file).touch()
    repo_obj = Repo.init(repo_dir)
    _ = repo_obj.index.add(['push_test.txt'])
    _ = repo_obj.index.commit('test write access')
    remote = set_remote_safely(repo_obj, 'push_test', repo_url)
    # remote = repo_obj.create_remote(url=repo_url, name='push_test')
    try:
        _ = remote.push('master:origin')
        _ = repo_obj.index.remove(['push_test.txt'])
        _ = repo_obj.index.commit('remove access test file')
        _ = remote.push('master:origin')
    except GitCommandError as e:
        print(f'Error encountered while testing write access to repo {repo_url}:\n{e}')
        sys.exit(1)
    finally:
        rmtree(repo_dir)
    return repo_url


def is_valid_fastq_path(path):
    if len(parse_input_path(path, '*.f*q')) == 0:
        return raise_('{} does not seem to contain fastq reads!'.format(path))
    return path


def is_valid_slurm_config(filename):
    """
    Test if provided slurm config file contains minimum info to run. Also check
    whether srun is actually available on the system.
    """
    srun_test = os.popen('command -V srun').read()
    if 'srun' not in srun_test:
        return raise_('A SLURM config file was provided, but '
                      'srun does not seem to be a command on this system.')
    try:
        with open(filename, 'r') as f:
            json_tst = json.load(f)
    except ValueError:
        print('{} is not recognized as a json-file'.format(filename))
        sys.exit(1)
    except FileNotFoundError:
        print('{} cannot be found'.format(filename))
        sys.exit(1)
    if '__default__' not in json_tst:
        return raise_('slurm json should contain at least __default__ settings.')
    check_list = ['partition', 'time', 'mem-per-cpu', 'output', 'error']
    test_bools = [x not in json_tst['__default__'] for x in check_list]
    if any(test_bools):
        missing = [check_list[ci] for ci in range(len(check_list)) if test_bools[ci]]
        missing = ', '.join(missing)
        return raise_('slurm json __default__ settings does not contain {}, '
                      'but this is required'.format(missing))
    return os.path.realpath(filename)


def is_integer(val):
    if type(val) is int:
        return True
    try:
        int(val)
        return True
    except ValueError:
        return False
