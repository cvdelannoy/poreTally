import helper_functions as hp
import shutil
import yaml
import json
import os
from subprocess import check_output
import warnings
import snakemake
import datetime


def main(args):
    __location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
    if args.reads_fastq:
        reads_list = hp.parse_input_path(args.reads_fastq, pattern='*.f*q')
        read_type = 'fastq'
    else:
        reads_list = hp.parse_input_path(args.reads_fasta, pattern='*.f*a')
        read_type = 'fasta'
    wd = args.working_dir

    # Make necessary subdirs
    wd_envs = hp.parse_output_path(wd + 'envs/')
    wd_results = hp.parse_output_path(wd + 'assembler_results/')
    wd_assemblies = hp.parse_output_path(wd_results + 'assemblies/')
    wd_logs = hp.parse_output_path(wd_results + 'log_files/')
    wd_cpu = hp.parse_output_path(wd_results + 'cpu_files/')
    wd_condas = hp.parse_output_path(wd_results + 'conda_files/')
    wd_commands = hp.parse_output_path(wd_results + 'command_files/')

    if os.path.exists(wd+'Snakefile'):
        os.remove(wd+'Snakefile')

    # merge fastq's
    all_reads = f'{wd}all_reads.{read_type}'
    with open(all_reads, 'wb') as afq:
        for f in reads_list:
            with open(f, 'rb') as fd:
                shutil.copyfileobj(fd, afq)

    if args.short_reads_dir:
        # merge short read fastq's
        sr_list = hp.parse_input_path(args.short_reads_dir, pattern='*.f*q')
        short_reads_fastq = wd + 'short_reads.fastq'
        with open(short_reads_fastq, 'wb') as asr:
            for sr in sr_list:
                with open(sr, 'rb') as srh:
                    shutil.copyfileobj(srh, asr)

    param_dict = dict()
    param_dict['NB_THREADS'] = args.threads_per_job
    param_dict['REFGENOME_SIZE'] = hp.get_nb_bases(args.ref_fasta, 'fasta')
    param_dict['SEQUENCED_SIZE'] = hp.get_nb_bases(all_reads, read_type)
    param_dict['COVERAGE'] = param_dict['SEQUENCED_SIZE'] / param_dict['REFGENOME_SIZE']
    param_dict['WD'] = wd
    if args.fast5_dir:
        fast5_dir_abs = os.path.abspath(args.fast5_dir) + '/'
        param_dict['FAST5_DIR'] = fast5_dir_abs
    if args.short_reads_dir:
        param_dict['SHORT_READS'] = short_reads_fastq

    # Construct Snakefile
    # construct unique name for snakefile first
    sf_fn = wd + 'Snakefile_assemblies_' + datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    cmds_dict = dict()
    sf_dict = dict()
    if 'default' in args.pipelines:
        args.pipelines += ['canu', 'flye', 'smartdenovo', 'minimap2_miniasm', 'minimap2_miniasm_raconX2']
        args.pipelines.remove('default')
    nb_pipelines = 0
    pipelines_list = []
    for pipeline in args.pipelines:
        if os.path.isfile(pipeline):
            yaml_fn = pipeline
            pipeline = os.path.splitext(os.path.basename(pipeline))[0]
        else:
            yaml_fn = __location__ + '/assembler_commands/' + pipeline + '.yaml'
        if os.path.isfile(yaml_fn):
            with open(yaml_fn, 'r') as plf:
                pl_dict = yaml.full_load(plf)
        else:
            warnings.warn('Could not find yaml file for {pl}, skipping'.format(pl=yaml_fn))
            continue

        wd_cur_path = wd_results + pipeline
        if os.path.isdir(wd_cur_path):  # Ensure clean output folder, as some assemblers error out otherwise
            shutil.rmtree(wd_cur_path)
        wd_cur = hp.parse_output_path(wd_cur_path)

        sf_dict[pipeline] = {
            'input': {'fastq': f'{wd}all_reads.{read_type}'},
            'threads': [args.threads_per_job],
            'output': [wd_assemblies + pipeline + '.fasta'],
            'log': [wd_logs + pipeline + '.log'],
            'benchmark': [wd_cpu + pipeline + '.bm']
        }


        conda = pl_dict.get('conda')
        if conda:
            with open(wd_condas + pipeline + '.yaml', 'w') as cf:
                yaml.dump(conda, cf, default_flow_style=False)
            sf_dict[pipeline]['conda'] = [wd_condas + pipeline + '.yaml']
        sf_dict[pipeline]['group'] = ['pipelines']
        try:
            assembly_cmds = pl_dict['commands'].format(**param_dict)
        except KeyError as e:
            raise KeyError(f'Could not fill key word {e} in yaml file {pipeline}. Did you enter all required '
                           f'resources for this assembler (e.g. fast5 files, short reads...)?')
        cmds = list()
        cmds.extend(hp.parse_version_commands(pl_dict['versions'],
                                              pl_dict['description']))
        cmds.append('cd {}'.format(wd_cur))
        cmds.extend(assembly_cmds.split(sep='\n'))
        cmds_dict[pipeline] = cmds
        with open(wd_commands + pipeline + '.cmd', 'w') as f:
            f.write(assembly_cmds)
        nb_pipelines += 1
        pipelines_list.append(pipeline)
    sf_string = 'workdir: \'{}\'\n\n'.format(wd_envs)  # save envs in same location as results (otherwise defaults to current loc)
    sf_string += hp.dict_to_snakefile(cmds_dict, sf_dict)
    with open(sf_fn, 'a') as sf:
        sf.write(sf_string)

    sm_dict = {'targets': pipelines_list,
               'use_conda': True,
               'cores': args.threads_per_job,
               'keepgoing': True}

    # ---- Cluster-related ----
    if args.slurm_config is not None:
        with open(args.slurm_config, 'r') as slurmf:
            slurm_config_dict = json.load(slurmf)
        partition_name = slurm_config_dict['__default__']['partition']
        sinfo_list = check_output(['sinfo']).decode('utf-8').split('\n')
        sinfo_header = {n: i for i, n in enumerate(sinfo_list[0].split())}
        nb_nodes = None
        for sil in sinfo_list[1:]:
            if partition_name in sil:
                nb_nodes = int(sil.split()[sinfo_header['NODES']])
                break
        if nb_nodes is None:
            raise ValueError('supplied SLURM partition {} not found'.format(partition_name))
        nb_nodes = min(nb_nodes, nb_pipelines)
        sm_dict['nodes'] = nb_nodes
        tasks_per_node = max(nb_pipelines // nb_nodes, 1)
        sbatch_line = 'sbatch --nodes={nbn} --ntasks-per-node={tpn} --cpus-per-task={cpt}'.format(nbn=nb_nodes,
                                                                                                  tpn=tasks_per_node,
                                                                                                  cpt=args.threads_per_job
                                                                                                   )
        for n in list(slurm_config_dict['__default__']):
            sbatch_line += ' --{opt}={{cluster.{opt}}}'.format(opt=n)
        sm_dict['cluster'] = sbatch_line
        sm_dict['cluster_config'] = args.slurm_config
        sm_dict['local_cores'] = args.threads_per_job

    snakemake.snakemake(sf_fn, **sm_dict)
