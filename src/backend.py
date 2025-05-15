class Backend:
    def __init__(self):
        self.temp_count = 0
        self.code = []

    def new_temp(self):
        """Generate a new temporary variable name."""
        temp = f"t{self.temp_count}"
        self.temp_count += 1
        return temp

    def semantic_analysis(self, ast):
        """Perform basic semantic analysis on the AST."""
        # For this simple grammar, semantic analysis is minimal
        # Just return the AST as is for now
        return ast

    def generate_intermediate_code(self, ast):
        """Generate three-address code from the AST."""
        self.code = []
        self.temp_count = 0
        return self._gen_code(ast)

    def _gen_code(self, node):
        """Recursively generate code for the AST node."""
        if isinstance(node, int):
            return node
        op, left, right = node
        left_val = self._gen_code(left)
        right_val = self._gen_code(right)
        temp = self.new_temp()
        self.code.append(f"{temp} = {left_val} {op} {right_val}")
        return temp

    def optimize(self):
        """Perform basic optimization on the intermediate code."""
        # Simple optimization: constant folding
        optimized_code = []
        for line in self.code:
            parts = line.split(' = ')
            if len(parts) != 2:
                optimized_code.append(line)
                continue
            result_var = parts[0]
            expr = parts[1].split()
            if len(expr) == 3 and expr[0].isdigit() and expr[2].isdigit():
                if expr[1] == '+':
                    result = int(expr[0]) + int(expr[2])
                elif expr[1] == '*':
                    result = int(expr[0]) * int(expr[2])
                else:
                    optimized_code.append(line)
                    continue
                optimized_code.append(f"{result_var} = {result}")
            else:
                optimized_code.append(line)
        self.code = optimized_code

    def generate_target_code(self):
        """Generate target code (simple assembly-like output)."""
        target_code = []
        for line in self.code:
            parts = line.split(' = ')
            if len(parts) != 2:
                target_code.append(line)
                continue
            result_var = parts[0]
            expr = parts[1].split()
            if len(expr) == 3:
                target_code.append(f"LOAD {expr[0]}")
                if expr[1] == '+':
                    target_code.append(f"ADD {expr[2]}")
                elif expr[1] == '*':
                    target_code.append(f"MUL {expr[2]}")
                target_code.append(f"STORE {result_var}")
            else:
                target_code.append(f"MOV {expr[0]}, {result_var}")
        return target_code

def process(ast):
    backend = Backend()
    # Step 1: Semantic Analysis
    checked_ast = backend.semantic_analysis(ast)
    # Step 2: Intermediate Code Generation
    backend.generate_intermediate_code(checked_ast)
    # Step 3: Optimization
    backend.optimize()
    # Step 4: Target Code Generation
    target_code = backend.generate_target_code()
    return backend.code, target_code

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
