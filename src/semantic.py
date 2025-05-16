class SemanticAnalyzer:
    def __init__(self):
        # Initialize symbol table as a dictionary to store variable information
        self.symbol_table = {}
        # Stack to manage scopes (for nested blocks)
        self.scope_stack = [self.symbol_table]

    def enter_scope(self):
        """Enter a new scope by pushing a new dictionary onto the scope stack."""
        new_scope = {}
        self.scope_stack.append(new_scope)
        return new_scope

    def exit_scope(self):
        """Exit the current scope by popping the scope stack."""
        if len(self.scope_stack) > 1:
            self.scope_stack.pop()

    def declare_variable(self, var_name, var_type):
        """Declare a variable in the current scope."""
        current_scope = self.scope_stack[-1]
        if var_name in current_scope:
            raise ValueError(f"Variable '{var_name}' already declared in current scope")
        current_scope[var_name] = {'type': var_type, 'initialized': False}

    def lookup_variable(self, var_name):
        """Look up a variable in the current and outer scopes."""
        for scope in reversed(self.scope_stack):
            if var_name in scope:
                return scope[var_name]
        raise ValueError(f"Variable '{var_name}' not declared")

    def set_initialized(self, var_name):
        """Mark a variable as initialized after assignment."""
        for scope in reversed(self.scope_stack):
            if var_name in scope:
                scope[var_name]['initialized'] = True
                return
        raise ValueError(f"Variable '{var_name}' not declared")

    def check_type(self, expected_type, actual_type, operation):
        """Check if the actual type matches the expected type for an operation."""
        if expected_type.lower() != actual_type.lower():
            raise ValueError(f"Type mismatch in {operation}: expected {expected_type}, got {actual_type}")

    def analyze(self, ast):
        """
        Perform semantic analysis on the Abstract Syntax Tree (AST).
        This includes symbol table management and type checking for Pascal constructs.
        Returns the AST with any necessary annotations or modifications.
        """
        if isinstance(ast, tuple):
            node_type = ast[0]
            if node_type == 'program':
                _, prog_name, var_decls, stmts = ast
                # Process variable declarations
                self.process_var_declarations(var_decls)
                # Analyze statements in the main program scope
                self.analyze_statements(stmts)
            return ast
        return ast

    def process_var_declarations(self, var_decls):
        """Process variable declarations and add them to the symbol table."""
        if var_decls[1]:  # If there are declarations
            for decl in var_decls[1]:
                var_type = decl[2]
                for var_name in decl[1]:
                    self.declare_variable(var_name, var_type)

    def analyze_statements(self, stmts):
        """Analyze a list of statements."""
        for stmt in stmts:
            self.analyze_statement(stmt)

    def analyze_statement(self, stmt):
        """Analyze a single statement."""
        if isinstance(stmt, tuple):
            stmt_type = stmt[0]
            if stmt_type == 'assign':
                var_name, expr = stmt[1], stmt[2]
                var_info = self.lookup_variable(var_name)
                expr_type = self.get_expression_type(expr)
                self.check_type(var_info['type'], expr_type, f"assignment to {var_name}")
                self.set_initialized(var_name)
            elif stmt_type == 'if':
                cond, then_stmts, else_stmts = stmt[1], stmt[2], stmt[3]
                cond_type = self.get_expression_type(cond)
                self.check_type('BOOLEAN', cond_type, "if condition")
                # Enter new scope for then block
                self.enter_scope()
                self.analyze_statements(then_stmts)
                self.exit_scope()
                # Enter new scope for else block if it exists
                if else_stmts:
                    self.enter_scope()
                    self.analyze_statements(else_stmts)
                    self.exit_scope()
            elif stmt_type == 'while':
                cond, body_stmts = stmt[1], stmt[2]
                cond_type = self.get_expression_type(cond)
                self.check_type('BOOLEAN', cond_type, "while condition")
                # Enter new scope for loop body
                self.enter_scope()
                self.analyze_statements(body_stmts)
                self.exit_scope()
            elif stmt_type == 'writeln':
                expr = stmt[1]
                if isinstance(expr, list):
                    for e in expr:
                        self.get_expression_type(e)  # Just to check if expressions are valid
                else:
                    self.get_expression_type(expr)

    def get_expression_type(self, expr):
        """Determine the type of an expression."""
        if isinstance(expr, int):
            return 'INTEGER'
        elif isinstance(expr, str):
            if expr in self.symbol_table or any(expr in scope for scope in self.scope_stack):
                var_info = self.lookup_variable(expr)
                if not var_info['initialized']:
                    raise ValueError(f"Variable '{expr}' used before initialization")
                return var_info['type']
            elif expr.startswith("'") and expr.endswith("'"):
                return 'STRING'  # For string literals
            else:
                try:
                    int(expr)  # Check if it's a numeric string
                    return 'INTEGER'
                except ValueError:
                    raise ValueError(f"Unknown identifier or literal: {expr}")
        elif isinstance(expr, tuple):
            op = expr[0]
            if op in ('+', '-', '*', '/'):
                left_type = self.get_expression_type(expr[1])
                right_type = self.get_expression_type(expr[2])
                self.check_type('INTEGER', left_type, f"left operand of {op}")
                self.check_type('INTEGER', right_type, f"right operand of {op}")
                return 'INTEGER'
            elif op in ('<', '>', '=', '<=', '>='):
                left_type = self.get_expression_type(expr[1])
                right_type = self.get_expression_type(expr[2])
                self.check_type(left_type, right_type, f"comparison {op}")
                return 'BOOLEAN'
            elif op == 'and':
                left_type = self.get_expression_type(expr[1])
                right_type = self.get_expression_type(expr[2])
                self.check_type('BOOLEAN', left_type, "left operand of and")
                self.check_type('BOOLEAN', right_type, "right operand of and")
                return 'BOOLEAN'
        raise ValueError("Unknown expression type")

    def get_symbol_table(self):
        """Return the current symbol table (for output purposes)."""
        return self.scope_stack[0]  # Return the global scope for simplicity
