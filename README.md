# poreTally: standardized nanopore reads assembler benchmarking
#### [Carlos de Lannoy](https://www.vcard.wur.nl/Views/Profile/View.aspx?id=77824), [Dick de Ridder](https://www.vcard.wur.nl/Views/Profile/View.aspx?id=56806&ln=eng)

poreTally brings all you need to benchmark MinION assembly pipelines
together. It also generates a report for you in article style, which you
can publish in a readable format on Github/Gitlab.

See [here](https://github.com/cvdelannoy/poreTally_example) for an example of the report, based on a 1000 reads
subset of an <i>E. coli</i> dataset found [here](http://lab.loman.net/2017/03/09/ultrareads-for-nanopore/).

## Installing poreTally
Before installing poreTally, ensure you have python3, miniconda/anaconda and git
installed on your system. Be aware that you cannot install `conda` through `pip`
to use it as an application.
poreTally also requires the `zlib` development library to build `mappy`, as well as more recent versions of `setuptools` and `requests` than you may have by default:

```
sudo apt install zlib1g-dev
pip install setuptools --upgrade
pip install requests --upgrade
```

Install with pip:
```
pip install git+https://github.com/cvdelannoy/poreTally.git
```

Note that poreTally relies on Snakemake and conda environments to run assembly pipeline tools.
Due to a quirk between loading conda envs and virtualenvs in Snakemake, __poreTally does not run
well in a virtualenv__.

Alternatively, use the Docker image:
```
docker build https://github.com/cvdelannoy/poreTally.git -t poretally
docker run -t -v mount_this:to_that poretally run_benchmark -h
```



## Running
We aimed to make benchmarking with poreTally as easy to run as possible.

The entire analysis process (assemble, analyze, publish) is started in
one command:
```
poreTally run_benchmark \
                -w path/to/working_directory \
                -r reference_genome.fasta \
                -f path/to/fast5_files_dir \
                -g gene_annotation.gff \
                -i user_info.yaml \
                --git git@github.com:username/repository_to_store_results.git \
                path/to/read_fastqs_dir
```

Conda environments will automatically be created for assembly pipelines and analysis tools.

Note that providing a gene annotation file (-g) and the original fast5 files (-f) is optional. Of course, gene finding
on the finished assemblies and actions that require the fast5-files (only polishing by Nanopolish for now) will be
disabled if you do not provide these files.

user_info.yaml should contain information on the author, species, basecaller used, flowcell and ONT kit. Species
may be either an NCBI taxonomy ID or genus and species name as recognized by NCBI taxonomy. Use the
official kit and flowcell codes as provided by ONT (SQK-XXXXXX and FLO-MINXXX resp.). For example:
```
authors: B. Honeydew
species: Homo sapiens
basecaller: Albacore 2.2.7
flowcell: FLO-MIN106
kit: SQK-LSK108
```

Depending on your dataset and system, you may need some extra options:
- -s : if pipelines and analyses should be run in parallel using SLURM supply a json-file with SLURM header info.
Ensure that there is at least a \_\_default\_\_. Partition should be
stated there and nowhere else. Add other items if you want
a given pipeline to run with different parameters. For example:
```
{
    "__default__" :
    {
        "output": "output_%j.txt",
        "error": "error_%j.txt",
        "time" : "08:00:00",
        "partition" : "your_favorite_partition",
        "mem-per-cpu": "4096",
        "cpus-per-task": 8
    },
    "minimap2_miniasm":
    {
        "time" : "01:00:00"
    }
}
```
- -p : Define which pipelines you want to run. Provide the name of the text file in the `assembler_commands` folder in
which the commands are stored, as a yaml. E.g. to run only SMARTdenovo, use: `-p smartdenovo`. Alternatively, provide a
path to a custom yaml-file. Ensure that the yaml is properly formatted, e.g.:
```
versions: # bash commands that print versions for your tools
  minimap2: 'minimap2 -V'
  miniasm: 'miniasm -V'
description: > # short description of the pipeline
  Minimap2 is a fast all-vs-all mapper of reads that relies on sketches of sequences, composed of
  minimizers. Miniasm uses the found overlaps to construct an assembly graph.
  As a consensus step is lacking in this pipeline, post-assembly polishing is often required.
commands: |
  # bash commands that should be executed. use single curly brackets for variables
  # (NB_THREADS, REFGENOME_SIZE, COVERAGE), double for input/output arguments (see below) and
  # quadruple (yes, really) for curly brackets that should remain curly. ensure that final output
  # fasta is piped into {{output}}
  minimap2 -x ava-ont -t {NB_THREADS} {{input.fastq}} {{input.fastq}} | gzip -1 > minimap2.paf.gz
  miniasm -f {{input.fastq}} minimap2.paf.gz > minimap2_miniasm.gfa
  grep -Po '(?<=S\t)utg.+' minimap2_miniasm.gfa | awk '{{{{print ">"$1"\\n"$2}}}}' | fold > {{output}}
conda: # details for conda environment that should be loaded, if necessary
  channels:
    - bioconda
  dependencies:
    - minimap2
    - miniasm
```
- -t : Define number of threads the assemblers each may use

See [here](https://github.com/cvdelannoy/poreTally_example) for an example of the report, based on a 1000 reads
subset of an <i>E. coli</i> dataset found [here](http://lab.loman.net/2017/03/09/ultrareads-for-nanopore/).

## Partial runs
poreTally is actually divided in three steps, which are run in sequence if you call `run_benchmark`; assembly
generation, assembly analysis and report publication. If you are only interested in one step (e.g. you just want all
the assemblies) or poreTally stopped working during a particular step, you can run one of the subscripts
`run_assemblies`, `run_analysis` or `publish_results`.

## Notes

### Significance
MinION assembly pipeline benchmarks have been published in traditional peer-reviewed literature before, however we
argue that this format is not ideal for the MinION, considering the frequency with which its hardware and software is
updated and the significance of those updates to read accuracy. Our intention is to make benchmarking of <i>de novo</i>
assembly pipelines and subsequent publishing of results standardized and easy, so that the user community may easily
keep its members up to date on best practices for any taxa sequenced so far, for the most recent hardware and software
versions.

### The Collective Benchmark
As the benchmark that is most applicable to your user case may be hard to find, we also included the option for
benchmark users to submit their results to us, so that we may present a more inclusive overview of the <i>de novo</i>
assembly pipeline landscape. As prices for sequencing continue to decline and more organisms can be sequenced on any
lab bench (or kitchen table), we think that an up-to-date, broad collective benchmarking effort will have even more
value in the future. If you use this tool, please consider sharing your results. Your work will always be duely
credited!

### User Friendliness
poreTally should take away many of the obstacles you may encounter when benchmarking pipelines on your own dataset.
If you found the poreTally user experience not as click-and-go as you would have liked it to be or see anything else
that could use improvement (new metrics, new pipelines to benchmark etc.), please let us know by creating a
new [issue](https://github.com/cvdelannoy/poreTally/issues)!

Happy Benchmarking!
