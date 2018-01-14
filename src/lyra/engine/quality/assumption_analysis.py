from lyra.abstract_domains.quality.assumption_domain import AssumptionState
from lyra.abstract_domains.quality.assumption_lattice import AssumptionLattice
from lyra.engine.backward import BackwardInterpreter
from lyra.engine.runner import Runner
from lyra.semantics.backward import DefaultBackwardSemantics


class AssumptionAnalysis(Runner):

    def __init__(self, do_render=True):
        super().__init__()
        self.do_render = do_render

    def interpreter(self):
        return BackwardInterpreter(self.cfg, DefaultBackwardSemantics(), 3)

    def state(self):
        return AssumptionState(self.variables)

    def run(self):
        result = self.interpreter().analyze(self.state())
        for node, items in result.result.items():
            if node.identifier == 1:
                items[0] = self.result_to_input_assmps(items[0].current_stack_top.assmps)
        if self.do_render:
            self.render(result)
        return result

    def result_to_input_assmps(self, assmps):
        new_assmps = []
        for assmp in assmps:
            #if isinstance(assmp, AssumptionLattice):
            if assmp.iterations > 1:
                assmp._assmps = self.result_to_input_assmps(assmp.assmps)
                new_assmps.append(assmp)
            else:
                relations = assmp.relations.store[assmp.var_name]
                new_assmps.append((assmp.assmps.type_assumption, relations))
            #else:
            #    assmp._assmps = self.result_to_input_assmps(assmp.assmps)
            #    new_assmps.append(assmp)
        return new_assmps
