from copy import deepcopy

from lyra.abstract_domains.quality.assumption_graph import AssumptionNode
from lyra.quality.checker import Checker


class InputChecker(Checker):

    def __init__(self):
        super().__init__()

    def perform_checking(self):
        # unrolling assumptions
        unrolled_assumptions = self.unroll_assumptions(self.analysis_result)
        # read inputs one by one from file and perform checking
        infile = open(self.input_filename, "r")
        line_number = 1
        start_offset = 0
        end_offset = 0
        # list of errors
        errors = []
        id_value = dict()  # maps every program point to the last input value read from it
        id_input_line = dict()  # maps every program point to the last line number from which its input has been read
        for input_value in infile:
            input_value = input_value.strip()
            end_offset = start_offset + len(input_value) - 1
            if line_number-1 >= len(unrolled_assumptions):
                break
            assumption_node = unrolled_assumptions[line_number - 1]
            id_value[assumption_node.id] = input_value
            old_id_input_line = deepcopy(id_input_line)
            id_input_line[assumption_node.id] = line_number

            error = assumption_node.check_input(line_number, start_offset, end_offset, input_value, id_value, id_input_line)
            # if there is an error
            if error is not None:
                errors.append(error)
                id_value[assumption_node.id] = error
                id_input_line = old_id_input_line
            line_number += 1
            print(input_value, start_offset, end_offset)
            start_offset = end_offset + 3
        return errors

    def write_errors(self):
        outfile = open(self.error_filename, "w")
        outfile.write(InputError.separator)
        outfile.write("\n")
        for err in self.errors:
            outfile.write(f"{repr(err)}\n")
        outfile.close()
        print("ERRORS", self.errors)

    def unroll_assumptions(self, ag):
        """
        Unrolls assumptions from a graph into a list to facilitate input checking against a file
        :param ag: AssumptionGraph carrying the result of the analysis.
        :return: A list containing the unrolled assumptions.
        """
        if isinstance(ag, AssumptionNode):
            return [ag]
        mult = int(ag.mult.val)
        result = []
        while mult > 0:
            mult-=1
            for assmp in ag.assumptions:
                result = result + self.unroll_assumptions(assmp)

        return result


class InputError:
    separator = "|"

    def __init__(self, code_line, input_line, start_offset, end_offset, message):
        self.code_line = code_line
        self.input_line = input_line
        self.display_line = input_line
        self.start_offset = start_offset
        self.end_offset = end_offset
        self.message = message

    def __repr__(self):
        return f"{self.display_line}{InputError.separator}{self.start_offset}{InputError.separator}{self.end_offset}{InputError.separator}{self.get_message()}"

    def get_message(self):
        if self.input_line == self.display_line:
            return f"Value on this line {self.message}"
        else:
            return f"Value on line {self.input_line} {self.message}"

