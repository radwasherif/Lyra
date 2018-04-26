import os
from lyra.quality_analysis.controller import Controller
from lyra.engine.quality.assumption_analysis import AssumptionAnalysis
from lyra.quality_analysis.input_checker import InputChecker
from lyra.quality_analysis.json_handler import JSONHandler


class AssumptionController(Controller):

    def __init__(self, analysis, checker, handler, path, name):
        super().__init__(analysis, checker, handler, path, name)


if __name__ == "__main__":
    path = os.getcwd() + '/example'
    name = 'checker_example'
    AssumptionController(AssumptionAnalysis(), InputChecker(), JSONHandler(), path, name).run()
