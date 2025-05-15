class IntermediateCodeGenerator:
    def __init__(self):
        self.temp_count = 0
        self.code = []

    def new_temp(self):
        """Generate a new temporary variable name."""
        temp = f"t{self.temp_count}"
        self.temp_count += 1
        return temp

    def generate(self, ast):
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

    def get_code(self):
        """Return the generated intermediate code."""
        return self.code
