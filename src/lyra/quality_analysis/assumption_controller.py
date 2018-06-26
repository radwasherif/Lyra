import glob
import os

from lyra.abstract_domains.numerical.interval_domain import IntervalState
from lyra.abstract_domains.quality.character_inclusion_domain import CharacterInclusionState
from lyra.quality.controller import Controller
from lyra.engine.quality.assumption_analysis import AssumptionAnalysis
from lyra.quality_analysis.input_checker import InputChecker
from lyra.quality_analysis.json_handler import JSONHandler


class AssumptionController(Controller):

    def __init__(self, analysis, checker, handler, path):
        super().__init__(analysis, checker, handler, path)
        print("Initialized assumption controller.")


if __name__ == "__main__":
    name = os.getcwd() + '/example/**.py'
    for path in glob.iglob(name):
        if os.path.basename(path) != "__init__.py":
            AssumptionController(AssumptionAnalysis(IntervalState, CharacterInclusionState), InputChecker(), JSONHandler(IntervalState, CharacterInclusionState), path).run()
