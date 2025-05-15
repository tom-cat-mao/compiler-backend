from semantic import SemanticAnalyzer
from intermediate import IntermediateCodeGenerator
from optimizer import Optimizer
from target import TargetCodeGenerator

class Backend:
    def __init__(self):
        # Initialize all backend components for the compiler pipeline
        self.semantic_analyzer = SemanticAnalyzer()        # Handles semantic checks
        self.intermediate_generator = IntermediateCodeGenerator()  # Generates three-address code
        self.optimizer = Optimizer()                      # Optimizes the intermediate code
        self.target_generator = TargetCodeGenerator()     # Converts to target assembly-like code

    def process(self, ast):
        """
        Process the Abstract Syntax Tree (AST) through the compiler backend pipeline.
        Returns a tuple of intermediate code and target code.
        """
        # Step 1: Semantic Analysis - Validate the AST for semantic correctness
        checked_ast = self.semantic_analyzer.analyze(ast)
        # Step 2: Intermediate Code Generation - Convert AST to three-address code
        self.intermediate_generator.generate(checked_ast)
        intermediate_code = self.intermediate_generator.get_code()
        # Step 3: Optimization - Apply optimizations like constant folding
        optimized_code = self.optimizer.optimize(intermediate_code)
        # Step 4: Target Code Generation - Convert optimized code to assembly-like instructions
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
