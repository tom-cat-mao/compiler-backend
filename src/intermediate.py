class IntermediateCodeGenerator:
    def __init__(self):
        # Initialize counters and storage for intermediate code generation
        self.temp_count = 0  # Counter for generating unique temporary variable names
        self.code = []       # List to store the generated three-address code instructions

    def new_temp(self):
        """Generate a new temporary variable name."""
        temp = f"t{self.temp_count}"
        self.temp_count += 1
        return temp

    def generate(self, ast):
        """
        Generate three-address code from the Abstract Syntax Tree (AST).
        Three-address code is an intermediate representation where each instruction
        has at most three operands, simplifying further processing and optimization.
        Resets the code list and temporary counter before generation.
        Returns the result of the code generation process (a temporary variable or value).
        """
        self.code = []       # Reset the code list for a new generation
        self.temp_count = 0  # Reset the temporary variable counter
        return self._gen_code(ast)  # Start recursive code generation

    def _gen_code(self, node):
        """
        Recursively generate three-address code for the given AST node.
        If the node is a number (integer), return it directly.
        If the node is an operation, recursively generate code for left and right operands,
        create a new temporary variable, and store the operation result in it.
        Returns the temporary variable name or the numeric value.
        """
        if isinstance(node, int):  # Base case: node is a numeric value
            return node
        op, left, right = node  # Unpack operation node into operator and operands
        left_val = self._gen_code(left)    # Recursively get value or temp for left operand
        right_val = self._gen_code(right)  # Recursively get value or temp for right operand
        temp = self.new_temp()             # Generate a new temporary variable name
        self.code.append(f"{temp} = {left_val} {op} {right_val}")  # Add instruction to code
        return temp                        # Return the temporary variable name

    def get_code(self):
        """Return the generated intermediate code."""
        return self.code
