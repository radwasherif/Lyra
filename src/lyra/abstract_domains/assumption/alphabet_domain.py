from collections import defaultdict
from copy import deepcopy
from typing import Set

from lyra.abstract_domains.assumption.assumption_domain import JSONMixin, InputMixin
from lyra.abstract_domains.string.character_domain import CharacterLattice, CharacterState
from lyra.core.expressions import VariableIdentifier, Expression


class AlphabetLattice(CharacterLattice, JSONMixin):

    def to_json(self) -> dict:
        js = {
            'certainly': list(self.certainly),
            'maybe': list(self.maybe)
        }
        return js

    @staticmethod
    def from_json(json: dict) -> 'JSONMixin':
        return AlphabetLattice(set(json['certainly']), set(json['maybe']))


class AlphabetState(CharacterState, InputMixin):

    def __init__(self, variables: Set[VariableIdentifier], precursory: InputMixin = None):
        lattices = defaultdict(lambda: AlphabetLattice)
        super(CharacterState, self).__init__(variables, lattices)
        InputMixin.__init__(self, precursory)

    def replace(self, variable: VariableIdentifier, expression: Expression) -> 'InputMixin':
        return self

    def unify(self, other: 'InputMixin') -> 'InputMixin':
        return self

    class Refinement(CharacterState.ExpressionRefinement):

        def visit_Input(self, expr, state=None, evaluation=None, value=None):
            state.record(deepcopy(value))
            return state
    _refinement = Refinement()
