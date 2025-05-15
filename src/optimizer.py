class Optimizer:
    def optimize(self, code):
        """Perform basic optimization on the intermediate code."""
        # Simple optimization: constant folding
        optimized_code = []
        for line in code:
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
        return optimized_code
