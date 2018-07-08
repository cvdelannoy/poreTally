# poreTally: standardized nanopore reads assembler benchmarking
#### [Carlos de Lannoy](https://www.vcard.wur.nl/Views/Profile/View.aspx?id=77824), [Dick de Ridder](https://www.vcard.wur.nl/Views/Profile/View.aspx?id=56806&ln=eng)

poreTally brings all you need to benchmark MinION assembly pipelines together. It also generates a report for you in article style and can publish it in a readable format on Github/Gitlab.

#### NOTE: PRODUCT IN DEVELOPMENT, USE WITH CAUTION

## Installing poreTally
poreTally works with python3 and Linux.

## Running
We aimed to make benchmarking with poreTally as easy to run as possible.

The entire analysis process (assemble, analyze, publish) is strted in one command:
```
poreTally run_benchmark
                -w path/to/working_directory \
                -r reference_genome.fasta \
                -f path/to/fast5_files_dir \
                -g gene_annotation.gff \
                -i user_info.yaml \
                path/to/read_fastqs_dir
```

Conda environments will automatically be created for assembly pipelines and analysis tools.

Note that providing a gene annotation file (-a) and the original fast5 files (-f) is optional. Of course, gene finding
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
- -s : Do NOT run your pipelines in parallel by submitting them to a SLURM scheduler. By default, SLURM is used if it is detected.
- -p : Define which pipelines you want to run. Provide the name of the text file in the `assembler_commands` folder in
which the commands are stored, as a yaml. E.g. to run only SMARTdenovo, use: `-p smartdenovo`
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