import re
import yaml
import os
from tabulate import tabulate

int_directory = os.path.dirname(snakemake.input[0]) + '/'
multiqc_dir = int_directory + 'multiqc_report/REPORT_data/'

with open(multiqc_dir + 'ab_methods.yaml') as f:
    methods_dict = yaml.load(f)

header = (
    '# Assembler benchmark for ONT MinION data\n'
    '#### Authors: {authors}\n'
    'Generated using [poreTally](https://github.com/cvdelannoy/poreTally), a benchmarking tool. '
    'For an interactive version of this report, download REPORT.html from this repository.\n\n'.format(authors=methods_dict['authors']))


# METHODS SECTION

md_txt = [header,
          "<h2>Abstract</h2>",
          methods_dict['abstract'],
          "<h2>Methods</h2>",
          "<h3>Readset quality assessment</h3>",
          methods_dict['readset_quality'],
          "<h3>Assembly pipelines</h3>",
          methods_dict['pipelines'],
          "<h3>Assembly quality assessment</h3>",
          methods_dict['assembly_quality']]


# RESULTS SECTION
results = ["<h2>Results</h2><h3>General Statistics</h3>"]
with open(multiqc_dir + 'multiqc_general_stats.yaml') as f:
    general_stats_dict = yaml.load(f)
gtable_header = list(general_stats_dict[list(general_stats_dict)[0]])
gtable_header_processed = [re.search('(?<=-)[^-]+$', gt).group(0).replace('_', ' ') for gt in gtable_header]

gtable_data = []
for k in list(general_stats_dict):
    cur_row = [k]
    for h in gtable_header:
        cur_val = general_stats_dict[k].get(h)
        cur_row.append(cur_val)
    gtable_data.append(cur_row)

general_stats_md = tabulate(gtable_data, gtable_header_processed,
                            tablefmt="html",
                            numalign="center",
                            stralign="center")
results.append(general_stats_md)

if os.path.isfile(multiqc_dir + 'multiqc_readqual_summary.yaml'):
    results.append("<h3>Readset quality</h3>\n")
    with open(multiqc_dir + 'multiqc_readqual_summary.yaml') as f:
        readset_dict = yaml.load(f)
    readqual_header = ['', 'Value', '', 'N', '%']
    readqual_data = []
    for mm, ns in zip(list(readset_dict['minimap2']), list(readset_dict['nanostats'])):
        readqual_data.append(['<b>'+ns+'</b>', readset_dict['nanostats'][ns],
                              '<b>'+mm+'</b>', readset_dict['minimap2'][mm]['absolute'],
                             '{:.2f}'.format(readset_dict['minimap2'][mm]['relative'])])
    readqual_table_md = tabulate(readqual_data, readqual_header,
                                 tablefmt="html",
                                 numalign="center",
                                 stralign="center")
    results.append(readqual_table_md)

if os.path.isfile(multiqc_dir + 'multiqc_quast.yaml'):
    results.append("<h3>QUAST</h3><h4>Assembly Statistics</h4>")
    with open(multiqc_dir + 'multiqc_quast.yaml') as f:
        quast_dict = yaml.load(f)

    # Avoid errors if some line is wasn't available for particular run
    quast_header_dict = {'N50': 'N50 (Kbp)',
                         'N75': 'N75 (Kbp)',
                         'L50': 'L50 (K)',
                         'L75': 'L75 (K)',
                         'Largest contig': 'Largest contig (Kbp)',
                         'Total length': 'Length (Mbp)',
                         '# misassemblies': 'Misas- semblies',
                         '# mismatches per 100 kbp': 'Mismatches /100Kbp',
                         '# indels per 100 kbp': 'Indels /100Kbp',
                         '# genes': 'Genes',
                         '# genes_partial': 'Genes (partial)',
                         'Genome fraction (%)': 'Genome Fraction'}
    quast_header = []
    quast_metrics = []
    quast_dict_keys = list(quast_dict[list(quast_dict)[0]])
    for k in quast_header_dict:
        if k in quast_dict_keys:
            quast_metrics.append(k)
            quast_header.append(quast_header_dict[k])

    quast_data = []
    for assembler in quast_dict:
        cur_row = [quast_dict[assembler][k] if quast_dict[assembler].get(k) else None for k in quast_metrics]
        cur_row.insert(0, assembler)
        quast_data.append(cur_row)

    quast_table_md = tabulate(quast_data, quast_header,
                              tablefmt="html",
                              numalign="center",
                              stralign="center")
    results.append(quast_table_md)

    results.append('<h4>Number of Contigs</h4>\n\n')
    results.append('![alt text](multiqc_report/multiqc_plots/png/mqc_quast_num_contigs_1.png "contig numbers")')
    results.append('![alt text](multiqc_report/multiqc_plots/png/mqc_quast_num_contigs_1_pc.png "contig percentages")')

results.append('<h3> <i>k</i>-mer Counts</h3>\n\n')
results.append('![alt text](multiqc_report/multiqc_plots/png/mqc_jellyfish_kmer_scatterplot.png "kmer plots")')

results.append('<h3> Synteny Plots</h3>\n\n')
results.append('![alt text](multiqc_report/multiqc_plots/png/mqc_mummerplot.png "synteny plots")')

results.append('<h3>CPU usage</h3>\n\n')
results.append('CPU usage was monitored during runs using the psutil package in Python3. Reported here '
               'are CPU time and memory usage(proportional and unique set size, PSS and USS '
               'respectively).')

if os.path.isfile(multiqc_dir+'cpu_usage.yaml'):
    with open(multiqc_dir+'cpu_usage.yaml') as f:
        cpu_dict = yaml.load(f)
    cpu_data = []
    cpu_header = list(cpu_dict[list(cpu_dict)[0]])
    cpu_header = sorted(cpu_header)
    for k in cpu_dict:
        cpu_data.append([cpu_dict[k][l] for l in cpu_header])
    cpu_table_md = tabulate(cpu_data, cpu_header,
                            tablefmt="html",
                            numalign="center",
                            stralign="center")
    results.append(cpu_table_md)

md_txt.append(''.join(results))
md_txt = ''.join(md_txt)

with open(snakemake.output[0], "w") as f:
    f.write(md_txt)
