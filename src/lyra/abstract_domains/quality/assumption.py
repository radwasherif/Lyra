from lyra.abstract_domains.state import State
from abc import ABCMeta, abstractmethod


class AssumptionState(State, metaclass=ABCMeta):

    def __init__(self):
        super.__init__()
        self.collector_pairs = [(None, None)]

    @abstractmethod
    def transfer_relations(self, variable):
        """Transfer collected relations of a variable to the input assumption collector """
