from semantic import SemanticAnalyzer
from intermediate import IntermediateCodeGenerator
from optimizer import Optimizer
from target import TargetCodeGenerator

class Backend:
    def __init__(self):
        self.semantic_analyzer = SemanticAnalyzer()
        self.intermediate_generator = IntermediateCodeGenerator()
        self.optimizer = Optimizer()
        self.target_generator = TargetCodeGenerator()

    def process(self, ast):
        # Step 1: Semantic Analysis
        checked_ast = self.semantic_analyzer.analyze(ast)
        # Step 2: Intermediate Code Generation
        self.intermediate_generator.generate(checked_ast)
        intermediate_code = self.intermediate_generator.get_code()
        # Step 3: Optimization
        optimized_code = self.optimizer.optimize(intermediate_code)
        # Step 4: Target Code Generation
        target_code = self.target_generator.generate(optimized_code)
        return intermediate_code, target_code

def process(ast):
    backend = Backend()
    return backend.process(ast)

if __name__ == "__main__":
    from parser import parse
    while True:
        try:
            s = input('backend > ')
            if s == 'exit':
                break
            ast = parse(s)
            intermediate, target = process(ast)
            print("Intermediate Code:")
            for line in intermediate:
                print(line)
            print("\nTarget Code:")
            for line in target:
                print(line)
        except EOFError:
            break
