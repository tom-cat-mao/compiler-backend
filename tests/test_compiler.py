import unittest
from src.parser import parse
from src.backend import Backend
from src.semantic import SemanticAnalyzer
from src.intermediate import IntermediateCodeGenerator
from src.optimizer import Optimizer
from src.target import TargetCodeGenerator

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

    def test_parse_nested_expression(self):
        result = parse("((1 + 2) * 3) + 4")
        self.assertEqual(result, ('+', ('*', ('+', 1, 2), 3), 4))

    def test_semantic_analysis(self):
        ast = parse("1 + 2")
        analyzer = SemanticAnalyzer()
        result = analyzer.analyze(ast)
        self.assertEqual(result, ast)  # For now, semantic analysis returns the same AST

    def test_intermediate_code_simple(self):
        ast = parse("1 + 2")
        generator = IntermediateCodeGenerator()
        generator.generate(ast)
        code = generator.get_code()
        self.assertEqual(code, ["t0 = 1 + 2"])

    def test_intermediate_code_complex(self):
        ast = parse("(1 + 2) * 3")
        generator = IntermediateCodeGenerator()
        generator.generate(ast)
        code = generator.get_code()
        self.assertTrue("t0 = 1 + 2" in code)
        self.assertTrue("t1 = t0 * 3" in code)

    def test_optimization_constant_folding_addition(self):
        code = ["t0 = 5 + 5"]
        optimizer = Optimizer()
        optimized = optimizer.optimize(code)
        self.assertEqual(optimized, ["t0 = 10"])

    def test_optimization_constant_folding_multiplication(self):
        code = ["t0 = 4 * 2"]
        optimizer = Optimizer()
        optimized = optimizer.optimize(code)
        self.assertEqual(optimized, ["t0 = 8"])

    def test_optimization_no_folding(self):
        code = ["t0 = t1 + 5"]
        optimizer = Optimizer()
        optimized = optimizer.optimize(code)
        self.assertEqual(optimized, ["t0 = t1 + 5"])

    def test_target_code_simple(self):
        code = ["t0 = 1 + 2"]
        generator = TargetCodeGenerator()
        target = generator.generate(code)
        self.assertEqual(target, ["LOAD 1", "ADD 2", "STORE t0"])

    def test_target_code_complex(self):
        code = ["t0 = 1 + 2", "t1 = t0 * 3"]
        generator = TargetCodeGenerator()
        target = generator.generate(code)
        self.assertTrue("LOAD 1" in target)
        self.assertTrue("ADD 2" in target)
        self.assertTrue("STORE t0" in target)
        self.assertTrue("LOAD t0" in target)
        self.assertTrue("MUL 3" in target)
        self.assertTrue("STORE t1" in target)

    def test_target_code_optimized(self):
        code = ["t0 = 10"]
        generator = TargetCodeGenerator()
        target = generator.generate(code)
        self.assertEqual(target, ["MOV 10, t0"])

    def test_full_backend_process_simple(self):
        ast = parse("1 + 2")
        backend = Backend()
        intermediate, target = backend.process(ast)
        self.assertEqual(intermediate, ["t0 = 1 + 2"])
        self.assertEqual(target, ["LOAD 1", "ADD 2", "STORE t0"])

    def test_full_backend_process_complex(self):
        ast = parse("(1 + 2) * 3")
        backend = Backend()
        intermediate, target = backend.process(ast)
        self.assertTrue("t0 = 1 + 2" in intermediate)
        self.assertTrue("t1 = t0 * 3" in intermediate)
        self.assertTrue("LOAD t0" in target)
        self.assertTrue("MUL 3" in target)
        self.assertTrue("STORE t1" in target)

    def test_full_backend_process_optimization(self):
        ast = parse("5 + 5")
        backend = Backend()
        intermediate, target = backend.process(ast)
        self.assertEqual(intermediate, ["t0 = 10"])
        self.assertEqual(target, ["MOV 10, t0"])

if __name__ == '__main__':
    unittest.main()
