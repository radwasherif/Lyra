"""
    Generic class to read/write analysis result from files.
"""
from abc import ABCMeta, abstractmethod

from lyra.abstract_domains.quality.assumption_graph import AssumptionGraph
from lyra.engine.interpreter import AnalysisResult


class ResultHandler (metaclass=ABCMeta):

    def __init__(self):
        super().__init__()
        self.result = None
        self._filename = None
        self._file_extension = None   # for example .json for JSON files
    @property
    def filename(self):
        return self._filename

    @filename.setter
    def filename(self, filename: str):
        self._filename = f"{filename}.{self.file_extension}"

    @property
    def file_extension(self):
        return self._file_extension

    @file_extension.setter
    def file_extension(self, file_extension: str):
        self._file_extension = file_extension

    @abstractmethod
    def write_result(self):
        """Write analysis result to file"""

    @abstractmethod
    def read_result(self) -> 'AssumptionGraph':
        """Read analysis result from file into data structure"""

    @abstractmethod
    def process_result(self):
        """Perform some optional user-defined processing on the analysis result"""
