#!/usr/bin/python3
import argparse
import sys
import argparse_dicts

import run_assemblies
import run_analysis
import run_benchmark
import publish_results


def main(args=None):
    if args is None:
        args = sys.argv[1:]

    commands = [
        ('run_benchmark',
         'Run entire benchmark procedure: construct assemblies, evaluate them and publish.',
         argparse_dicts.get_benchmark_parser(),
         run_benchmark.main),
        ('run_assemblies',
         'Construct assemblies',
         argparse_dicts.get_assemblies_parser(),
         run_assemblies.main),
        ('run_analysis',
         'Analyse constructed assemblies',
         argparse_dicts.get_analysis_parser(),
         run_analysis.main),
        ('publish_results',
         'Publish results of assembly analyses',
         argparse_dicts.get_publication_parser(),
         publish_results.main)
    ]

    parser = argparse.ArgumentParser(
        prog='poreTally',
        description='A tool for for easy MinION de-novo assembler benchmarking. Runs a number of assemblers, produces '
                    'read quality measures, assembly quality and assembler performance measures and parses the results '
                    'into a format immediately publishable on Github/Gitlab. Optionally, upload your data to a '
                    'collaborative benchmarking effort and help the MinION user community gain insight in assembler '
                    'performance.'
    )
    subparsers = parser.add_subparsers(
        title='commands'
    )

    for cmd, hlp, ap, fnc in commands:
            subparser = subparsers.add_parser(cmd, add_help=False, parents=[ap, ])
            subparser.set_defaults(func=fnc)
    args = parser.parse_args(args)
    args.func(args)


if __name__ == '__main__':
    main()
