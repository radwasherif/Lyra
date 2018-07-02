import os
from abc import ABCMeta, abstractmethod
# import lyra.quality_analysis.controller as q


class Checker(metaclass=ABCMeta):

    def __init__(self):
        super().__init__()
        # full path to input data file
        self._filename = None
        self._input_filename = None
        self.error_filename = None
        # pointer to controller of the class
        self._analysis_result = None
        # dict to store values of every id
        self.id_assumption = dict()
        self._errors = None
    @property
    def filename(self):
        return self._filename

    @filename.setter
    def filename(self, filename: str):
        self._filename = filename
        self._input_filename = f"{self.filename}.in"
        self.error_filename = f"{self.filename}.error.txt"

    @property
    def input_filename(self):
        return self._input_filename

    @input_filename.setter
    def input_filename(self, input_filename):
        # canonical path to input file
        self._input_filename = input_filename
        self.error_filename = f"{self._input_filename}.error"

    @property
    def analysis_result(self):
        return self._analysis_result

    @analysis_result.setter
    def analysis_result(self, analysis_result):
        self._analysis_result = analysis_result

    @property
    def errors(self):
        return self._errors

    @errors.setter
    def errors(self, errors):
        self._errors = errors

    def main(self):
        """Runs the input checker"""
        self.errors = self.perform_checking()
        self.write_errors()

    @abstractmethod
    def perform_checking(self):
        """Performs checking of analysis result against input data"""

    @abstractmethod
    def write_errors(self):
        """Writes errors found by the checker into designated file"""

