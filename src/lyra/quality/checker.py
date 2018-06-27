from abc import ABCMeta, abstractmethod
# import lyra.quality_analysis.controller as q


class Checker(metaclass=ABCMeta):

    def __init__(self):
        super().__init__()
        # full path to input data file
        self._filename = None
        self.input_filename = None
        self.error_filename = None
        # pointer to controller of the class
        self._analysis_result = None
        # dict to store values of every id
        self.id_assumption = dict()

    @property
    def filename(self):
        return self._filename

    @filename.setter
    def filename(self, filename: str):
        self._filename = filename
        self.input_filename = f"{self.filename}.in"
        self.error_filename = f"{self.filename}.error.txt"

    @property
    def analysis_result(self):
        return self._analysis_result

    @analysis_result.setter
    def analysis_result(self, analysis_result):
        self._analysis_result = analysis_result

    def read_from_file(self):
        """
        Reads analysis results from a file and returns a data structure holding the result
        :return:
        """
        return self.controller.read_result()

    @abstractmethod
    def main(self):
        """Runs the input checker"""

