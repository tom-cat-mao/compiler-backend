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
        # The symbol_table is now the entire SYNBL list from the analyzer
        self.symbol_table = {entry['NAME']: entry for entry in symbol_table}

    def generate(self, ast):
        """
        Generate four-tuple intermediate code from the Abstract Syntax Tree (AST).
        Quadruple format is (operator, operand1, operand2, result) as per markdown.
        """
        self.code = []
        self.temp_count = 0
        self.label_count = 0
        if isinstance(ast, tuple) and ast[0] == 'program':
            # AST structure: ('program', prog_name, var_declarations, statements)
            _, _, _, stmts = ast
            self.generate_statements(stmts)
        return self.code

    def generate_statements(self, stmts):
        """Generate code for a list of statements."""
        for stmt in stmts:
            self.generate_statement(stmt)

    def generate_statement(self, stmt):
        """Generate code for a single statement."""
        if not isinstance(stmt, tuple):
            # Potentially skip empty statements or handle errors
            return

        stmt_type = stmt[0]
        if stmt_type == 'assign':
            # Rule: v = E  =>  (=, res(E), _, v)
            var_name, expr = stmt[1], stmt[2]
            expr_result = self.generate_expression(expr)
            self.code.append(('=', expr_result, '_', var_name))
        elif stmt_type == 'if':
            # Assuming (if, cond, _, L_true_target) means "if cond is TRUE, jump to L_true_target"
            #
            # Structure for if E then S1 else S2:
            #   code for E -> cond_result
            #   L_then = new_label()
            #   L_else = new_label()
            #   L_end  = new_label()
            #   (if, cond_result, _, L_else)  // If false, jump to S1
            #   code for S1
            #   (el, _, _, L_end)            // After S1, unconditional jump to L_end
            #   (lb, _, _, L_else)           // Label for S2
            #   code for S2
            #   (ie, _, _, L_end)            // Mark end of if structure
            #
            # Structure for if E then S1 (no else):
            #   code for E -> cond_result
            #   L_then = new_label()
            #   L_end  = new_label()
            #   (if, cond_result, _, L_end)  // If false, jump to S1
            #   code for S1
            #   (ie, _, _, L_end)                // Mark end of if structure

            cond, then_stmts, else_stmts = stmt[1], stmt[2], stmt[3]
            cond_result = self.generate_expression(cond)

            label_then_start = self.new_label()
            label_if_end = self.new_label()
            
            if else_stmts:
                label_else_start = self.new_label()
                # If cond_result is FALSE, jump to label_else_start
                self.code.append(('if', cond_result, '_', label_else_start))
            
                self.generate_statements(then_stmts)
                # After 'then' block, unconditionally jump to the end of the if-else. This is 'el'.
                self.code.append(('el', '_', '_', label_if_end)) 

                # Else block
                self.code.append(('lb', '_', '_', label_else_start))
                self.generate_statements(else_stmts)
                # Fall through to the end label after the else block

                # End of if-else statement
                self.code.append(('ie', '_', '_', label_if_end)) # Mark if-end
            else: # No else statement
                # If cond_result is FALSE, jump to label_then_start
                self.code.append(('if', cond_result, '_', label_if_end))
                
                self.generate_statements(then_stmts)
                # Fall through to the end label after the then block

                # End of if statement
                self.code.append(('ie', '_', '_', label_if_end)) # Mark if-end

        elif stmt_type == 'while':
            # Following the rule: while (E) S
            # L_eval_E: (label for start of condition evaluation)
            # ... code for E ... -> cond_res
            # (do, cond_res, _, L_exit) ; if cond_res is false, jump to L_exit
            # ... code for S ...
            # (we, _, _, L_eval_E)     ; jump back to L_eval_E
            # L_exit: (label for loop exit)
            
            cond_expr, body_stmts = stmt[1], stmt[2]

            label_eval_E = self.new_label()    # Label for the start of condition evaluation (target for 'we')
            label_loop_exit = self.new_label() # Label for loop exit (target for 'do')

            self.code.append(('wh', '_', '_', '_'))  # Emit the 'while' instruction

            # Create the label for the start of condition evaluation.
            self.code.append(('lb', '_', '_', label_eval_E))
            
            # Generate quadruples for condition E, result in res(E).
            cond_result = self.generate_expression(cond_expr)

            # Emit: (do, cond_result, _, label_loop_exit)
            # This instruction means: if cond_result is false, jump to label_loop_exit.
            self.code.append(('do', cond_result, '_', label_loop_exit))

            # Generate quadruples for statement S (the loop body).
            self.generate_statements(body_stmts)

            # Emit: (we, _, _, label_eval_E)
            # This instruction means: unconditional jump to label_eval_E.
            self.code.append(('we', '_', '_', label_eval_E))
            # self.code.append(('gt', '_', '_', label_eval_E))

            # Create the label for the loop exit.
            self.code.append(('lb', '_', '_', label_loop_exit))

        elif stmt_type == 'writeln':
            # Assuming 'writeln' translates to one or more 'write' operations
            # The markdown doesn't specify 'writeln' or 'write' opcodes.
            # We'll use a 'write' opcode for each argument.
            expr_list = stmt[1] # This is a list of expressions from parser
            if isinstance(expr_list, list):
                for expr_item in expr_list:
                    item_result = self.generate_expression(expr_item)
                    self.code.append(('write', item_result, '_', '_'))
            else: # Single expression for writeln (should be list based on parser)
                item_result = self.generate_expression(expr_list)
                self.code.append(('write', item_result, '_', '_'))


    def generate_expression(self, expr):
        """Generate code for an expression and return the result (temp variable or value)."""
        if isinstance(expr, int) or isinstance(expr, bool): # Constants
            return expr
        elif isinstance(expr, str):
            # Could be an identifier (variable name) or a string literal.
            # If it's a variable, its value is used directly.
            # If it's a string literal (e.g. from writeln), it's also used directly.
            return expr
        elif isinstance(expr, tuple):
            # Binary/Unary operations: (operator, operand1, operand2) or (operator, operand1)
            op = expr[0]
            
            # For binary operations like +, -, *, /, <, >, =, <=, >=, and
            if op in ('+', '-', '*', '/', '<', '>', '=', '<=', '>=', 'and', 'or'): # Added 'or' for completeness
                if len(expr) == 3: # Binary operation
                    left_val = self.generate_expression(expr[1])
                    right_val = self.generate_expression(expr[2])
                    temp_result = self.new_temp()
                    self.code.append((op, left_val, right_val, temp_result))
                    return temp_result
            # Potentially handle unary minus or NOT if your AST supports it
            # elif op == 'uminus' and len(expr) == 2:
            #     operand_val = self.generate_expression(expr[1])
            #     temp_result = self.new_temp()
            #     self.code.append(('-', 0, operand_val, temp_result)) # Or a specific 'uminus' op
            #     return temp_result
            
        raise ValueError(f"Unsupported expression type or structure: {expr}")

    def get_code(self):
        """Return the generated intermediate code."""
        return self.code
