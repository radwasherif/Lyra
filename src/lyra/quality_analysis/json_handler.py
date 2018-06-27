import json
from json import JSONDecoder

from lyra.abstract_domains.quality.assumption_graph import AssumptionGraph, Mult, AssumptionNode
from lyra.abstract_domains.quality.type_domain import TypeState
from lyra.core.cfg import Basic
from lyra.core.types import IntegerLyraType
from lyra.quality.handler import ResultHandler


class AssumptionDecoder(json.JSONDecoder):
    def __init__(self):
        JSONDecoder.__init__(self, object_hook=self.default)

    def default(self, obj):
        return self.decode_assumption(obj)

    def decode_assumption(self, obj):
        if "mult" in obj:
            ag = AssumptionGraph()
            ag.mult = Mult(val=obj["mult"], typ=IntegerLyraType)
            ag.assumptions = [self.decode_assumption(a) for a in obj["assumptions"]]
        if "type" in obj:
            an = AssumptionNode()
            an.id = obj["id"]
            an.type_element = TypeState.from_json(obj["type"])
            if obj["type"] == "string":
               an.lattice_element = self.string_domain.from_json(obj["lattice"])
            else:
               an.lattice_element = self.numerical_domain.from_json(obj["lattice"])
            return an


class JSONHandler(ResultHandler):
    def __init__(self):
        super().__init__()
        self.file_extension = "json"

    def write_result(self):
        self.result = self.result.get_node_result(Basic(1, None))[0].stack.stack[0]
        js = self.result.to_json()
        print("FILENAME", self.filename)
        with open(self.filename, 'w') as outfile:
            json.dump(js, outfile, indent=4)

    def read_result(self):
        ag = AssumptionGraph()
        js = None
        with open(self.filename, 'r') as infile:
            js = json.load(infile)
        ag = self.decode_assumption(js)
        print(ag)
        print(js)
        return ag

    def process_result(self):
        pass

    def decode_assumption(self, obj) -> 'AssumptionGraph':
        if "mult" in obj:
            ag = AssumptionGraph()
            ag.mult = Mult(val=obj["mult"], typ=IntegerLyraType)
            ag.assumptions = [self.decode_assumption(a) for a in obj["assumptions"]]
            return ag
        if "type" in obj:
            an = AssumptionNode()
            an.id = obj["id"]
            an.type_element = TypeState.from_json(obj["type"])
            if obj["type"] == "string":
               an.lattice_element = self.string_domain.from_json(obj["lattice"])
            else:
               an.lattice_element = self.numerical_domain.from_json(obj["lattice"])
            return an


