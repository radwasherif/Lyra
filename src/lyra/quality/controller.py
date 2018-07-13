"""
    Controller
    =========
    A controller class responsible for running data quality analysis, checkers and outputting results

"""
import os
from abc import ABCMeta

from lyra.core.cfg import Basic
from lyra.engine.runner import Runner
from lyra.quality.checker import Checker
from lyra.quality.handler import ResultHandler


class Controller (metaclass= ABCMeta):

    def __init__(self, analysis_runner: Runner, checker: Checker, result_handler: ResultHandler, canonical_path: str, numerical_domain: 'State', string_domain: 'State', code_modified=True, input_file_path=None):
        super().__init__()
        self.analysis_runner = analysis_runner
        self.result_handler = result_handler
        self.checker = checker
        self.program_path, name = os.path.split(canonical_path)
        self.program_name = name.split(".")[0]
        self.result_handler.filename = self.filename
        self.analysis_result = None
        self.numerical_domain = numerical_domain
        self.string_domain = string_domain
        self.assign_domains()
        self.code_modified = code_modified
        print("CODE MODIFIED", self.code_modified)
        self.input_file_path = input_file_path

    @property
    def filename(self):
        return f"{self.program_path}/{self.program_name}"

    def run_analysis(self):
        """ Calls runner to run the analysis for this controller. """
        return self.analysis_runner.main(f"{self.filename}.py").get_node_result(Basic(1, None))[0].stack.stack[0]

    def run_checker(self):
        """ Run input checker associated with this controller. """
        if self.input_file_path is None:
            self.checker.filename = self.filename
        else:
            self.checker.input_filename = self.input_file_path
        self.checker.analysis_result = self.analysis_result
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
        if self.code_modified or not os.path.isfile(self.result_handler.filename):
            self.analysis_result = self.run_analysis()
            print("RESULT", self.analysis_result)
            self.write_result()

        self.analysis_result = self.read_result()
        print("READ RESULT", self.analysis_result)
        # self.run_checker()

    def assign_domains(self):
        self.analysis_runner.numerical_domain = self.numerical_domain
        self.analysis_runner.string_domain = self.string_domain
        self.result_handler.numerical_domain = self.numerical_domain
        self.result_handler.string_domain = self.string_domain
        self.checker.numerical_domain = self.numerical_domain
        self.checker.string_domain = self.string_domain