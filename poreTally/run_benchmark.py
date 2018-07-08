from run_assemblies import main as run_assemblies
from run_analysis import main as run_analysis
from publish_results import main as publish_results


def main(args):
    run_assemblies(args)
    run_analysis(args)
    publish_results(args)
