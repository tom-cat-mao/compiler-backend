class TargetCodeGenerator:
    def generate(self, code):
        """
        Generate target code from the intermediate code in a simple assembly-like format.
        Converts three-address code instructions into a sequence of basic operations
        that mimic low-level assembly instructions (LOAD, ADD, MUL, STORE, MOV).
        This represents the final stage of the compiler backend, producing code
        that could be further translated to machine code in a real compiler.
        Returns the list of target code instructions.
        """
        target_code = []
        for line in code:
            parts = line.split(' = ')  # Split instruction into result and expression
            if len(parts) != 2:  # If not a standard assignment, keep unchanged
                target_code.append(line)
                continue
            result_var = parts[0]  # Variable to store result (e.g., t0)
            expr = parts[1].split()  # Split expression into operands and operator
            if len(expr) == 3:  # Handle operation with two operands and an operator
                target_code.append(f"LOAD {expr[0]}")  # Load first operand into register
                if expr[1] == '+':  # Addition operation
                    target_code.append(f"ADD {expr[2]}")  # Add second operand to register
                elif expr[1] == '*':  # Multiplication operation
                    target_code.append(f"MUL {expr[2]}")  # Multiply second operand with register
                target_code.append(f"STORE {result_var}")  # Store result from register to variable
            else:  # Direct assignment (e.g., after optimization)
                target_code.append(f"MOV {expr[0]}, {result_var}")  # Move value directly to variable
        return target_code
