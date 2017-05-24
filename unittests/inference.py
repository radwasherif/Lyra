import unittest
from frontend.pre_analysis import PreAnalyzer
from frontend.stmt_inferrer import *


class TestInference(unittest.TestCase):
    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path

    @staticmethod
    def parse_comment(comment, annotation_resolver):
        assignment_text = comment[2:]  # remove the '# ' text
        variable, type_annotation = assignment_text.split(" := ")
        return variable, annotation_resolver.resolve(type_annotation)

    @classmethod
    def parse_results(cls, source, annotation_resolver):
        result = {}
        for line in source:
            line = line.strip()
            if not line.startswith("#"):
                continue
            variable, t = cls.parse_comment(line, annotation_resolver)
            result[variable] = t
        return result

    @classmethod
    def infer_file(cls, path):
        """Infer a single python program

        :param path: file system path of the program to infer 
        :return: the z3 solver used to infer the program, and the global context of the program
        """
        r = open(path)
        t = ast.parse(r.read())

        analyzer = PreAnalyzer(t)

        config = analyzer.get_all_configurations()
        solver = z3_types.TypesSolver(config)

        context = Context()
        for stmt in t.body:
            infer(stmt, context, solver)

        solver.push()
        expected_result = cls.parse_results(open(path), solver.annotation_resolver)
        return solver, context, expected_result

    def runTest(self):
        """Test for expressions inference"""
        solver, context, expected_result = self.infer_file(self.file_path)

        self.assertNotEqual(solver.check(solver.assertions_vars), z3_types.unsat)

        model = solver.model()
        for v in expected_result:
            self.assertIn(v, context.types_map,
                          "Expected to have variable '{}' in the global context".format(v))

            z3_type = context.types_map[v]
            self.assertEqual(model[z3_type], expected_result[v],
                             "Expected variable '{}' to have type '{}', but found '{}'".format(v,
                                                                                               expected_result[v],
                                                                                               model[z3_type]))


def suite(files):
    s = unittest.TestSuite()
    for file in files:
        s.addTest(TestInference(file))
    runner = unittest.TextTestRunner()
    runner.run(s)

if __name__ == '__main__':
    suite(["tests/inference/expressions_test.py"])
