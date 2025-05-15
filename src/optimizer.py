class Optimizer:
    def optimize(self, code):
        """
        Perform optimization on the intermediate code to improve efficiency.
        Currently implements constant folding, which evaluates constant expressions
        at compile time instead of runtime. For example, 't0 = 5 + 3' becomes 't0 = 8'.
        Iterates through each instruction, checks for constant operands, and computes
        the result if possible, reducing the number of operations in the final code.
        Returns the optimized code list.
        """
        # Simple optimization: constant folding
        optimized_code = []
        for line in code:
            parts = line.split(' = ')  # Split instruction into result and expression
            if len(parts) != 2:  # If not a standard assignment, keep unchanged
                optimized_code.append(line)
                continue
            result_var = parts[0]  # Variable to store result (e.g., t0)
            expr = parts[1].split()  # Split expression into operands and operator
            # Check if expression has 3 parts (operand1 op operand2) and both operands are numbers
            if len(expr) == 3 and expr[0].isdigit() and expr[2].isdigit():
                if expr[1] == '+':  # Addition of constants
                    result = int(expr[0]) + int(expr[2])
                elif expr[1] == '*':  # Multiplication of constants
                    result = int(expr[0]) * int(expr[2])
                else:  # Unsupported operator, keep unchanged
                    optimized_code.append(line)
                    continue
                # Replace instruction with computed result
                optimized_code.append(f"{result_var} = {result}")
            else:  # Non-constant expression, keep unchanged
                optimized_code.append(line)
        return optimized_code
