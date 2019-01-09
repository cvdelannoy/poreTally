import argparse
import os

from helper_functions import is_fasta, is_user_info_yaml, is_valid_repo, is_valid_slurm_config, parse_output_path, is_valid_fastq_path

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
included_pipelines = os.listdir(__location__+ '/assembler_commands/')
included_pipelines = [os.path.splitext(pl)[0] for pl in included_pipelines]
included_pipelines = ', '.join(included_pipelines)

working_dir = ('-w', '--working-dir', {
    'type': lambda x: parse_output_path(x),
    'required': True,
    'help': 'Intermediate folder where results are stored.'
})

# TODO: implement argcheck
fast5_dir = ('-f', '--fast5-dir', {
    'type': lambda x: os.path.realpath(x),
    'required': False,
    'help': 'Directory containing fast5-reads for the provided reads. Required for some tools (e.g. Nanopolish).'
})

shortreads_dir = ('-a', '--short-reads-dir', {
    'type': lambda x: is_valid_fastq_path(x),
    'required': False,
    'help': 'Directory containing short accurate reads in fasta format. Required for some tools '
            '(e.g. for error correction). Config file variable: {SHORT_READS}'

})

# TODO: implement argcheck
gff_file = ('-g', '--gff-file', {
    'type': lambda x: os.path.realpath(x),
    'required': False,
    'help': 'Gene annotation file in GFF(v2/3) format. If provided, report number of found genes.'
})

# TODO: implement argcheck
pipelines = ('-p', '--pipelines', {
    'type': str,
    'required': False,
    'nargs': '+',
    'default': ['default'],
    'help': 'Run benchmark for one or more specific pipelines, instead of the standard 5. '
            'Given names must either be one of the included pipelines ({}), or be a path to a yaml file '
            'defining the commands and prerequisites (mixing allowed). Provide keyword \'default\' to also run Canu, Flye,'
            'SMARTdenovo, Minimap2+Miniasm and Minimap2+Miniasm+RaconX2'.format(included_pipelines)
})

user_info = ('-i', '--user-info', {
    'type': lambda x: is_user_info_yaml(x),
    'required': True,
    'help': 'Provide a yaml-file with author names, organism name and/or NCBI Taxonomy ID, basecaller,'
            ' ONT flowcell type and ONT chemistry kit.'
})

ref_fasta = ('-r', '--ref-fasta', {
    'type': lambda x: is_fasta(x),
    'required': True,
    'help': 'Reference genome in fasta-format, not provided to assemblers but used to estimate genome size and stored '
            'for later use in analysis step.'
})

slurm_config = ('-s', '--slurm-config', {
    'type': lambda x: is_valid_slurm_config(x),
    'required': False,
    'default': None,
    'help': 'If jobs need to be run using SLURM, provide a json-file containing header information, '
            '(i.e. partition, running time, memory etc.)'
})

threads_per_job = ('-t', '--threads-per-job', {
    'type': int,
    'required': False,
    'default': 4,
    'help': 'Define how many threads each job (most importantly assembly pipeline, but '
            'also analysis job) can maximally use. (default is 4).'
})

git = ('--git', {
       'type': lambda x: is_valid_repo(x),
       'required': False,
       'help': 'Full ssh address of a Github/Gitlab repo for which you set up access with a key pair.'
               'If provided, poreTally pushes the results of your benchmark run to this repo.'
})

# Positional
# TODO: implement argcheck
reads_dir = ('reads_dir', {
    'type': lambda x: is_valid_fastq_path(x),
    'nargs': '+',
    'help': 'directory or list of MinION reads in fastq format'
})


def get_assemblies_parser():
    parser = argparse.ArgumentParser(description=' Run a set of MinION assemblers, as defined by the scripts in '
                                                 'the "assembler_commands" folder.')
    parser.add_argument(reads_dir[0], **reads_dir[1])
    parser.add_argument(working_dir[0], working_dir[1], **working_dir[2])
    parser.add_argument(fast5_dir[0], fast5_dir[1], **fast5_dir[2])
    parser.add_argument(shortreads_dir[0], shortreads_dir[1], **shortreads_dir[2])
    parser.add_argument(pipelines[0], pipelines[1], **pipelines[2])
    parser.add_argument(ref_fasta[0], ref_fasta[1], **ref_fasta[2])
    parser.add_argument(threads_per_job[0], threads_per_job[1], **threads_per_job[2])
    parser.add_argument(slurm_config[0], slurm_config[1], **slurm_config[2])
    return parser


def get_analysis_parser():
    parser = argparse.ArgumentParser(description='Assess quality of assemblies produced by RUN_ASSEMBLERS')
    parser.add_argument(ref_fasta[0], ref_fasta[1], **ref_fasta[2])
    parser.add_argument(working_dir[0], working_dir[1], **working_dir[2])
    parser.add_argument(gff_file[0], gff_file[1], **gff_file[2])
    parser.add_argument(slurm_config[0], slurm_config[1], **slurm_config[2])
    parser.add_argument(user_info[0], user_info[1], **user_info[2])
    parser.add_argument(threads_per_job[0], threads_per_job[1], **threads_per_job[2])
    return parser


def get_publication_parser():
    parser = argparse.ArgumentParser(description='Publish results to a Github/Gitlab repository.  Optionally, send '
                                                 'results to us at Wageningen University (The Netherlands) to '
                                                 'contribute to an open-source benchmarking effort for de novo MinION '
                                                 'read assemblers (for which you will be credited).')
    parser.add_argument(working_dir[0], working_dir[1], **working_dir[2])
    parser.add_argument(git[0], **git[1])
    return parser


def get_benchmark_parser():
    parser = argparse.ArgumentParser(description='Run all steps of the benchmarking procedure: assemble using several'
                                                 'pipelines, analyze the assemblies and (optionally) publish in an'
                                                 'online repository.')
    parser.add_argument(reads_dir[0], **reads_dir[1])
    parser.add_argument(working_dir[0], working_dir[1], **working_dir[2])
    parser.add_argument(fast5_dir[0], fast5_dir[1], **fast5_dir[2])
    parser.add_argument(shortreads_dir[0], shortreads_dir[1], **shortreads_dir[2])
    parser.add_argument(pipelines[0], pipelines[1], **pipelines[2])
    parser.add_argument(ref_fasta[0], ref_fasta[1], **ref_fasta[2])
    parser.add_argument(threads_per_job[0], threads_per_job[1], **threads_per_job[2])
    parser.add_argument(slurm_config[0], slurm_config[1], **slurm_config[2])
    parser.add_argument(gff_file[0], gff_file[1], **gff_file[2])
    parser.add_argument(user_info[0], user_info[1], **user_info[2])
    parser.add_argument(git[0], **git[1])
    return parser
