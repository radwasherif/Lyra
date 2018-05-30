import glob
import os
from lyra.quality.controller import Controller
from lyra.engine.quality.assumption_analysis import AssumptionAnalysis
from lyra.quality_analysis.input_checker import InputChecker
from lyra.quality_analysis.json_handler import JSONHandler


class AssumptionController(Controller):

    def __init__(self, analysis, checker, handler, path, name):
        super().__init__(analysis, checker, handler, path, name)


if __name__ == "__main__":
    name = os.getcwd() + '/example/**.py'
    for path in glob.iglob(name):
        if os.path.basename(path) != "__init__.py":
            path, name = os.path.split(path)
            name = name.split(".")[0]
            AssumptionController(AssumptionAnalysis(), InputChecker(), JSONHandler(), path, name).run()
