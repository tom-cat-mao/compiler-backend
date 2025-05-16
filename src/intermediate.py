class IntermediateCodeGenerator:
    def __init__(self):
        # Initialize counters and storage for intermediate code generation
        self.temp_count = 0  # Counter for generating unique temporary variable names
        self.label_count = 0  # Counter for generating unique labels for control flow
        self.code = []       # List to store the generated four-tuple instructions
        self.symbol_table = None  # Reference to symbol table for type information

    def new_temp(self):
        """Generate a new temporary variable name."""
        temp = f"t{self.temp_count}"
        self.temp_count += 1
        return temp

    def new_label(self):
        """Generate a new label for control flow."""
        label = f"L{self.label_count}"
        self.label_count += 1
        return label

    def set_symbol_table(self, symbol_table):
        """Set the symbol table reference for type information."""
        self.symbol_table = symbol_table

    def generate(self, ast):
        """
        Generate four-tuple intermediate code from the Abstract Syntax Tree (AST).
        Four-tuple format is (operator, operand1, operand2, result).
        Resets the code list and counters before generation.
        Returns the result of the code generation process.
        """
        self.code = []       # Reset the code list for a new generation
        self.temp_count = 0  # Reset the temporary variable counter
        self.label_count = 0 # Reset the label counter
        if isinstance(ast, tuple) and ast[0] == 'program':
            _, _, var_decls, stmts = ast
            # Process variable declarations if needed (though handled by semantic analyzer)
            # Generate code for statements
            self.generate_statements(stmts)
        return self.code

    def generate_statements(self, stmts):
        """Generate code for a list of statements."""
        for stmt in stmts:
            self.generate_statement(stmt)

    def generate_statement(self, stmt):
        """Generate code for a single statement."""
        if isinstance(stmt, tuple):
            stmt_type = stmt[0]
            if stmt_type == 'assign':
                var_name, expr = stmt[1], stmt[2]
                result = self.generate_expression(expr)
                self.code.append((':=', result, '', var_name))
            elif stmt_type == 'if':
                cond, then_stmts, else_stmts = stmt[1], stmt[2], stmt[3]
                cond_result = self.generate_expression(cond)
                label_then = self.new_label()
                label_end = self.new_label()
                label_else = label_end if else_stmts is None else self.new_label()
                self.code.append(('if', cond_result, '', label_then))
                self.code.append(('goto', '', '', label_else))
                self.code.append(('label', '', '', label_then))
                self.generate_statements(then_stmts)
                if else_stmts:
                    self.code.append(('goto', '', '', label_end))
                    self.code.append(('label', '', '', label_else))
                    self.generate_statements(else_stmts)
                self.code.append(('label', '', '', label_end))
            elif stmt_type == 'while':
                cond, body_stmts = stmt[1], stmt[2]
                label_start = self.new_label()
                label_body = self.new_label()
                label_end = self.new_label()
                self.code.append(('label', '', '', label_start))
                cond_result = self.generate_expression(cond)
                self.code.append(('if', cond_result, '', label_body))
                self.code.append(('goto', '', '', label_end))
                self.code.append(('label', '', '', label_body))
                self.generate_statements(body_stmts)
                self.code.append(('goto', '', '', label_start))
                self.code.append(('label', '', '', label_end))
            elif stmt_type == 'writeln':
                expr = stmt[1]
                if isinstance(expr, list):
                    for e in expr:
                        result = self.generate_expression(e)
                        self.code.append(('write', result, '', ''))
                else:
                    result = self.generate_expression(expr)
                    self.code.append(('write', result, '', ''))

    def generate_expression(self, expr):
        """Generate code for an expression and return the result (temp variable or value)."""
        if isinstance(expr, int):
            return expr
        elif isinstance(expr, str):
            return expr  # Variable name or string literal
        elif isinstance(expr, tuple):
            op = expr[0]
            if op in ('+', '-', '*', '/', '<', '>', '=', '<=', '>=', 'and'):
                left_val = self.generate_expression(expr[1])
                right_val = self.generate_expression(expr[2])
                temp = self.new_temp()
                self.code.append((op, left_val, right_val, temp))
                return temp
        raise ValueError(f"Unsupported expression type: {expr}")

    def get_code(self):
        """Return the generated intermediate code."""
        return self.code
