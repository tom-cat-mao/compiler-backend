import unittest
from src.parser import parse
from src.backend import process

class TestCompiler(unittest.TestCase):
    def test_parse_simple_number(self):
        result = parse("42")
        self.assertEqual(result, 42)

    def test_parse_addition(self):
        result = parse("1 + 2")
        self.assertEqual(result, ('+', 1, 2))

    def test_parse_multiplication(self):
        result = parse("3 * 4")
        self.assertEqual(result, ('*', 3, 4))

    def test_parse_complex_expression(self):
        result = parse("(1 + 2) * 3")
        self.assertEqual(result, ('*', ('+', 1, 2), 3))

    def test_backend_process_simple(self):
        ast = parse("1 + 2")
        intermediate, target = process(ast)
        self.assertEqual(intermediate, ["t0 = 1 + 2"])
        self.assertEqual(target, ["LOAD 1", "ADD 2", "STORE t0"])

    def test_backend_process_complex(self):
        ast = parse("(1 + 2) * 3")
        intermediate, target = process(ast)
        self.assertTrue("t0 = 1 + 2" in intermediate)
        self.assertTrue("t1 = t0 * 3" in intermediate)
        self.assertTrue("LOAD t0" in target)
        self.assertTrue("MUL 3" in target)
        self.assertTrue("STORE t1" in target)

    def test_optimization_constant_folding(self):
        ast = parse("5 + 5")
        intermediate, target = process(ast)
        self.assertEqual(intermediate, ["t0 = 10"])
        self.assertEqual(target, ["MOV 10, t0"])

if __name__ == '__main__':
    unittest.main()
