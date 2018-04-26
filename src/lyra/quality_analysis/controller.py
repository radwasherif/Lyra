"""
    Controller
    =========
    A controller class responsible for running data quality analysis, checkers and outputting results

"""
from abc import ABCMeta, abstractmethod
from lyra.engine.runner import Runner
from lyra.quality_analysis.checker import Checker
from lyra.quality_analysis.handler import ResultHandler


class Controller (metaclass= ABCMeta):

    def __init__(self, analysis_runner: Runner, checker: Checker, result_handler: ResultHandler, path: str, name: str):
        super().__init__()
        self.analysis_runner = analysis_runner
        self.result_handler = result_handler
        self.checker = checker
        self.checker.controller = self
        self.program_path = path
        self.program_name = name
        self.analysis_result = None

    @property
    def filename(self):
        return f"{self.program_path}/{self.program_name}"

    def run_analysis(self):
        """ Calls runner to run the analysis for this controller. """
        return self.analysis_runner.main(f"{self.filename}.py")

    def run_checker(self):
        """ Run input checker associated with this controller. """
        self.checker.filename = self.filename
        self.checker.controller = self
        return self.checker.main()

    def write_result(self):
        """Call handler to write analysis result to a file"""
        self.result_handler.result = self.analysis_result
        self.result_handler.filename = self.filename
        self.result_handler.write_result()

    def read_result(self):
        """
        Calls handler to parse analysis result from a file
        :return: Result of the analysis in some data structure
        """
        return self.result_handler.read_result()


    def run(self):
        """ Run the controller """
        self.analysis_result = self.run_analysis()
        self.write_result()
        errors = self.run_checker()
        for err in errors:
            print(err)