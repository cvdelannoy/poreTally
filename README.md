# poreTally: standardized nanopore reads assembler benchmarking
#### [Carlos de Lannoy](https://www.vcard.wur.nl/Views/Profile/View.aspx?id=77824), [Dick de Ridder](https://www.vcard.wur.nl/Views/Profile/View.aspx?id=56806&ln=eng)

poreTally brings all you need to benchmark nanopore assembly pipelines
together. It also generates a report for you in article style, which you
can publish in a readable format on Github/Gitlab.

See [here](https://github.com/cvdelannoy/poreTally_example) for an example of the report, based on a 1000 reads
subset of an <i>E. coli</i> dataset found [here](http://lab.loman.net/2017/03/09/ultrareads-for-nanopore/).

#### Included assembly pipelines
|             	|                          	|
|-------------	|--------------------------	|
| **Canu**        	| **Minimap2 + miniasm**       	|
| **Flye**        	| **Minimap2 + miniasm + racon x 2**    |
| **SMARTdenovo** 	|   Minimap2 + miniasm + nanopolish 	|
| wtdbg2      	|             	|
assembly pipelines displayed **bold** are ran if no pipelines are specified.

#### Important: improving poreTally
Nanopore sequencing is a young field that is in constant motion, thus so should poreTally! Is your favorite assembly
pipeline not included in poreTally or did you find poreTally's current implementation of an existing pipeline outdated? 
[Let us know](https://github.com/cvdelannoy/poreTally/issues) or make a pull request with a [yaml file detailing
your pipeline](#custom-pipelines) and we would be happy to add it! 

## Installation
Before installing poreTally, ensure you have python3.6, miniconda/anaconda and git
installed on your system. Building and running poreTally can be achieved on resource-limited systems (2 CPU, 4 GB RAM), 
though some assemblers may not run successfully (e.g. Canu stipulates a minimum of 8 GB RAM and will forcibly exit). 
Be aware that you cannot install conda through pip to use it as an application.  poreTally also requires the zlib 
development library to build mappy, as well as more recent versions of setuptools and requests than you may have 
by default:

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

### Quick start
The entire benchmarking process (assemble, analyze, publish) only requires some light preparation and is started in
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

Below, the running process is broken down in steps.

### Step 1: prepare your files
At minimum, poreTally requires your nanopore reads, a reference genome and a 
[yaml file containing user information](#user-information-file). The construction of this and any additional files you may want to 
prepare is detailed here.

#### User information file
poreTally requires some information on you and the sequenced organism to generate reports. Create a yaml file containing
 `authors` (that's you), `species`, `basecaller`, `flowcell` code and ONT prep `kit` code. For example:

```
authors: B. Honeydew
species: Escherichia coli
basecaller: Albacore 2.2.7
flowcell: FLO-MIN106
kit: SQK-LSK108
```

`species` may be entered using either its latin name or NCBI taxonomy ID. `species`, `kit` and `flowcell` are all 
checked for validity.

#### Create a Github/Gitlab repository for publication (optional)
If you plan to share your results online, create a Github/Gitlab repository and keep the SSH address for it at hand.
You can easily find this address on Gitlab at the top of your page, or on Github by clicking 'clone or download'. It
should be formatted as `git@domain:username/repo_name.git`, for example: `git@github.com:cvdelannoy/poreTally_example.git`


#### SLURM settings file (optional)
If you plan to run poreTally in parallel using SLURM, prepare a json-file with SLURM header info. Ensure that there is 
at least a \_\_default\_\_. Partition should be stated there and nowhere else. Add other items if you want
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

### Step 2: run poreTally
To start benchmarking, simply provide your freshly generated `user_info.yaml` file, a `working_directory`, 
`reference_genome` and (the directory containing) your nanopore reads in fastq-format to poreTally.

#### Optional arguments
Optionally, you may provide:

- the number of threads an assembler may use (option `-t`, default is 4).
- the original fast5-files if this is required by one or more tools in your pipelines (e.g. Nanopolish) (option `-f`).
- short accurate reads if this is required by one or more tools in your pipelines (e.g. Pilon) (option `-a`).
- a gene annotation file in gff format to include gene finding results by Quast in the report (option `-g`).
- the SSH address of a Github/Gitlab repository you have an SSH key stored for to publish your report (option `--git`).
Note that you are required to have an SSH key set up for the account to which the repository belongs. If you are running
poreTally from a container, this key must also be added to the container! 
- the names of one of the default pipelines if you just want to run a subset of these (`canu`, `SMARTdenovo`, `Flye`, 
`minimap2_miniasm`, `minimap2_miniasm_raconX2`). You may also provide the names of yaml files storing your
own assembly pipelines! The file name without the `.yaml` extension will be used to refer to this pipeline in the report,
so ensure that these are unique (option `-p`). See [here](#custom-pipelines) on how to construct such a file. 
- If you plan to run poreTally in parallel using SLURM, the header you prepared in 
[step 1](#slurm-settings-file-optional) (option `-s`).


#### An extended running example
If you completely tricked out your poreTally command, it may end up looking somewhat like this:
```
poreTally run_benchmark \
                -w path/to/working_directory \
                -t 16 \
                -f path/to/fast5_files
                -s path/to/slurm_header.json \
                -r reference_genome.fasta \
                -f path/to/fast5_files_dir \
                -p minimap2_miniasm canu path/to/my_pipeline.yaml \
                -g gene_annotation.gff \
                -i user_info.yaml \
                --git git@github.com:username/repository_to_store_results.git \
                path/to/read_fastqs_dir

```

### Step 3: supporting the collective benchmark
After running the benchmark and (optionally) publishing your results in an online repository, you will be requested
to add your results to the poreTally collective benchmarking effort. If you choose to submit your results, you
will be asked to enter the username and password for the Github account from which your results will be submitted. Your
information will only be used to submit your results to the collective benchmark and will not be shared in any way. 
Periodically, we will aggregate submitted results and present a summary in a 
[separate repository](https://github.com/cvdelannoy/poreTallyCommunity).

The collective benchmarking effort aims to present a more inclusive cross-species overview of the <i>de novo</i>
assembly pipeline landscape, one more comprehensive than any single research group could make. As prices for sequencing 
continue to decline and more organisms can be sequenced on any lab bench (or kitchen table), we think that an 
up-to-date, broad collective benchmarking effort will have even more value in the future.

If you use this tool, please consider sharing your results. Your work will always be duly credited!

#### Running part of poreTally
Apart from the full benchmark routine, you can also (re-)run specific parts: 
- `poreTally run_assemblies`: only generate the assemblies
- `poreTally run_analysis`: (re-) analyze the produced assemblies from a working directory previously generated by 
`run_assemblies` or `run_benchmark` and produce the report. Handy if you want to see how another reference or 
gene annotation file works out. This deletes previously generated analyses!
- `poreTally publish_results`: only publish a working directory generated by `run_analysis` or `run_benchmark` 
to a Github/Gitlab repository, or share your data with the online benchmark.

#### Custom pipelines
Running your own pipelines should be almost as straightforward as using the included ones. Just construct a yaml-file
stating:
- a short `description` of your pipeline
- the bash commands required to print the `versions` of included tools 
- the `commands` that should be run. Be sure to supply the correct key words for your reads (fastq vs fast5) and to 
pipe the produced assembly into the output variable (see below). Some special rules apply to curly brackets:
 - Use single curly brackets around any variables provided by poreTally, i.e.: `{NB_THREADS}` (number of threads), 
 `{REFGENOME_SIZE}` (reference genome size) and `{COVERAGE}` (average coverage).
 - double curly brackets for the input and output key words, i.e.: `{{input.fastq}}` (reads in fasta-format),
  `{{input.fast5}}` (reads in fast5-format) and `{{output}}` (the produced assembly).
 - Quadruple curly brackets if you want your curly brackets to stay curly, e.g. `awk {{{{print ">"$1"\\n"$2}}}}` will
 translate to `awk {print ">"$1"\\n"$2}` in the eventual bash script for your pipeline.
- If your pipeline includes tools that can be found in the Anaconda cloud,you can tell poreTally to construct a `conda` 
environment by providing the `channels` in which said tools are found
and the names of the tools under `dependencies`.

All together, your yaml file should look like this:

```
versions:
  minimap2: 'minimap2 -V'
  miniasm: 'miniasm -V'
description: >
  Minimap2 is a fast all-vs-all mapper of reads that relies on sketches of sequences, composed of
  minimizers. Miniasm uses the found overlaps to construct an assembly graph.
  As a consensus step is lacking in this pipeline, post-assembly polishing is often required.
commands: |
  minimap2 -x ava-ont -t {NB_THREADS} {{input.fastq}} {{input.fastq}} | gzip -1 > minimap2.paf.gz
  miniasm -f {{input.fastq}} minimap2.paf.gz > minimap2_miniasm.gfa
  grep -Po '(?<=S\t)utg.+' minimap2_miniasm.gfa | awk '{{{{print ">"$1"\\n"$2}}}}' | fold > {{output}}
conda:
  channels:
    - bioconda
  dependencies:
    - minimap2
    - miniasm
```

You may also add your pipeline to poreTally by adding your file in the 
`installation_dir/poreTally/poreTally/assembler_commands` folder. Think your pipeline is a valuable addition to others?
Make a pull request and we'll add your pipeline as a standard!

## Notes

### Significance
MinION assembly pipeline benchmarks have been published in traditional peer-reviewed literature before, however we
argue that this format is not ideal for the MinION, considering the frequency with which its hardware and software is
updated and the significance of those updates to read accuracy. Our intention is to make benchmarking of <i>de novo</i>
assembly pipelines and subsequent publishing of results standardized and easy, so that the user community may easily
keep its members up to date on best practices for any taxa sequenced so far, for the most recent hardware and software
versions.


### User friendliness
poreTally should take away many of the obstacles you may encounter when benchmarking pipelines on your own dataset.
If you found the poreTally user experience not as click-and-go as you would have liked it to be or see anything else
that could use improvement (new metrics, new pipelines to benchmark etc.), please let us know by creating a
new [issue](https://github.com/cvdelannoy/poreTally/issues)!

Happy Benchmarking!