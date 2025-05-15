class TargetCodeGenerator:
    def generate(self, code):
        """Generate target code (simple assembly-like output)."""
        target_code = []
        for line in code:
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
