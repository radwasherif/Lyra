"""
Lyra Static Program Analyzer
============================
"""

import argparse
from lyra.engine.quality.assumption_analysis import AssumptionAnalysis
from lyra.abstract_domains.numerical.interval_domain import IntervalState
from lyra.abstract_domains.quality.character_inclusion_domain import CharacterInclusionState
from lyra.engine.liveness.liveness_analysis import StrongLivenessAnalysis
from lyra.engine.numerical.interval_analysis import ForwardIntervalAnalysis
from lyra.engine.usage.usage_analysis import UsageAnalysis
from lyra.quality_analysis.assumption_controller import AssumptionController
from lyra.quality_analysis.input_checker import InputChecker
from lyra.quality_analysis.json_handler import JSONHandler


def main():
    """Static analyzer entry point."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'python_file',
        help='Python file to analyze')
    parser.add_argument(
        '--analysis',
        help='analysis to be used (interval, liveness, or usage)',
        default='usage')
    args = parser.parse_args()

    if args.analysis == 'intervals':
        ForwardIntervalAnalysis().main(args.python_file)
    if args.analysis == 'liveness':
        StrongLivenessAnalysis().main(args.python_file)
    if args.analysis == 'usage':
        UsageAnalysis().main(args.python_file)
    if args.analysis == 'assumptions':
        AssumptionController(AssumptionAnalysis(IntervalState, CharacterInclusionState), InputChecker(), JSONHandler(),
                             args.python_file).run()


if __name__ == '__main__':
    main()
