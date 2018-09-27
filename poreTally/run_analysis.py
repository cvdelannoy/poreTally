import os
import datetime
import yaml
import snakemake
import shutil

import helper_functions as hp
from Metadata import Metadata


def main(args):
    __location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

    # additional argument checks
    if not os.path.isdir(args.working_dir):
        raise ValueError('Working directory not found')

    args.working_dir = os.path.realpath(args.working_dir) + '/'

    options_dict = dict()
    options_dict['wd_envs'] = hp.parse_output_path(args.working_dir + 'envs/')
    options_dict['threads'] = args.threads_per_job
    options_dict['ref_fasta'] = os.path.realpath(args.ref_fasta)
    options_dict['reads_fastq'] = args.working_dir + 'all_reads.fastq'
    options_dict['wd_analysis'] = hp.parse_output_path(args.working_dir + 'analysis/')
    options_dict['wd_analysis_condas'] = __location__ + '/analysis_conda_files/'
    options_dict['__location__'] = __location__

    # --- create output directories
    if os.path.isdir(options_dict['wd_analysis']):
        shutil.rmtree(options_dict['wd_analysis'])
    _ = hp.parse_output_path(options_dict['wd_analysis'] + 'quast')
    _ = hp.parse_output_path(options_dict['wd_analysis'] + 'jellyfish')
    _ = hp.parse_output_path(options_dict['wd_analysis'] + 'readset_analysis')

    options_dict['wd_analysis_summary'] = hp.parse_output_path(options_dict['wd_analysis'] + 'summary/')
    options_dict['wd_assembler_results'] = args.working_dir + 'assembler_results/'
    options_dict['wd_assemblies'] = args.working_dir + 'assembler_results/assemblies/'
    assemblies_list = hp.parse_input_path(options_dict['wd_assemblies'], pattern='*.fasta')
    if len(assemblies_list) == 0:
        raise ValueError('No succesful assemblies found to analyze!')
    assemblies_names_list = [os.path.splitext(os.path.basename(af))[0] for af in assemblies_list]
    options_dict['assemblies_string'] = ' '.join(assemblies_names_list)
    with open(args.user_info, 'r') as f:
        md_yaml = yaml.load(f)
    md = Metadata(md_yaml)
    md.write_publication_info(options_dict['wd_analysis_summary'] + 'publication_info.yaml')
    # --- Quast ---
    options_dict['quast_options'] = ''
    if md.is_eukaryote:
        options_dict['quast_options'] += '-e '
    if args.gff_file:
        options_dict['quast_options'] += '-G ' + os.path.abspath(args.gff_file) + ' '
    quast_output = ''
    quast_output_cmd = ''
    for anl in assemblies_names_list:
        quast_output += (',\n\t\t{anl}_fplot=\'{wd_analysis_summary}quast/{anl}.fplot\''
                         ',\n\t\t{anl}_rplot=\'{wd_analysis_summary}quast/{anl}.rplot\'').format(anl=anl,
                                                                                                 wd_analysis_summary=options_dict['wd_analysis_summary'])
        quast_output_cmd += ('if [ -e contigs_reports/nucmer_output/{anl}.fplot ]; then '
                             'cp contigs_reports/nucmer_output/{anl}.fplot {wd_analysis_summary}quast/.\n'
                             'cp contigs_reports/nucmer_output/{anl}.rplot {wd_analysis_summary}quast/.\n'
                             'fi').format(anl=anl, wd_analysis_summary=options_dict['wd_analysis_summary'])
    options_dict['quast_output'] = quast_output
    options_dict['quast_output_cmd'] = quast_output_cmd

    # --- Construct snakemake file ---
    sf_fn = args.working_dir + 'Snakefile_analysis_' + datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    with open(__location__+'/Snakemake_analysis', 'r') as f:
        sf = f.read()

    sf = sf.format(**options_dict)
    with open(sf_fn, 'w') as sf_handle:
        sf_handle.write(sf)

    sm_dict = {'use_conda': True}

    if args.slurm_config is not None:
        sm_dict['cluster'] = 'sbatch'
        sm_dict['cluster_config'] = args.slurm_config
        sm_dict['nodes'] = 5

    snakemake.snakemake(sf_fn, **sm_dict)
