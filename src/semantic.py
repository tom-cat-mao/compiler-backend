class SemanticAnalyzer:
    def __init__(self):
        # Symbol Table (SYNBL) - stores identifiers
        # Each entry: { 'NEME': name, 'TYP': type_table_idx, 'CAT': category, 'ADDR': addr_idx, 'scope': scope_id, 'initialized': bool }
        self.symbol_table_entries = [] # This will be the flat list for SYNBL output
        
        # Type Table (TVAL) - stores type definitions
        # Each entry: { 'id': unique_id, 'TVAL_CAT': type_code (i,r,c,b,a,d), 'TPOINT': pointer_to_detail_or_nul, 'name': type_name_str }
        self.type_table = []
        self._type_table_idx_counter = 0 # To generate unique IDs for type_table entries
        self._type_cache = {} # To avoid duplicate type entries, maps type_signature to index in self.type_table

        # Constant Table (CONSL) - stores constant values
        # Each entry: { 'id': unique_id, 'value': const_value, 'type_ptr': type_table_idx }
        self.constant_table = []
        self._constant_table_idx_counter = 0
        self._constant_cache = {} # To avoid duplicate constants, maps (value, type_str) to index in self.constant_table

        # Length Table (LENL) - stores size of data types
        # Each entry: { 'type_ptr': type_table_idx, 'size': num_value_units }
        self.length_table = []
        # No cache for length table as it's directly linked to type_table entries

        # Activity Record Table (VALL) - for function/procedure runtime info
        # Each entry: { 'scope_id': name, 'return_address': None, 'dynamic_link': None, ... }
        self.activity_record_table = []
        # self._activity_record_idx_counter = 0 # Not strictly needed if identified by scope_id
        
        # Scope management
        # Stack of scopes, each scope is a dict of symbols: {'var_name': symbol_table_entry_reference}
        # symbol_table_entry_reference is the actual dict stored in self.symbol_table_entries
        self.scope_stack = [{'name': 'global', 'symbols': {}}] 
        self.current_scope_id_counter = 0 # For generating unique scope IDs if needed beyond 'global'

        self._ensure_activity_record('global') # Add a default VALL entry for the global scope

    def _reset_state(self):
        self.symbol_table_entries = []
        self.type_table = []
        self._type_table_idx_counter = 0
        self._type_cache = {}
        self.constant_table = []
        self._constant_table_idx_counter = 0
        self._constant_cache = {}
        self.length_table = []
        self.activity_record_table = []
        self.scope_stack = [{'name': 'global', 'symbols': {}}]
        self.current_scope_id_counter = 0
        self._ensure_activity_record('global')

    def _get_next_type_id(self):
        idx = self._type_table_idx_counter
        self._type_table_idx_counter += 1
        return idx

    def _get_next_constant_id(self):
        idx = self._constant_table_idx_counter
        self._constant_table_idx_counter += 1
        return idx

    def _add_type_to_table(self, type_name_str):
        """Adds a type to TVAL if not exists, returns its index in self.type_table."""
        norm_type_name = type_name_str.upper()
        
        if norm_type_name in self._type_cache:
            return self._type_cache[norm_type_name]

        type_id_val = self._get_next_type_id() # This is the 'id' field for the type entry
        tval_cat = '?' 
        tpoint = 'nul' 
        size = 1 # Default size for basic types, Pascal units

        if norm_type_name == 'INTEGER':
            tval_cat = 'i'
        elif norm_type_name == 'REAL':
            tval_cat = 'r'
        elif norm_type_name == 'CHAR':
            tval_cat = 'c'
        elif norm_type_name == 'BOOLEAN':
            tval_cat = 'b'
        elif norm_type_name == 'STRING': 
             tval_cat = 's' 
             # Size for string could be variable. For LENL, might be fixed pointer size or length.
             # Let's assume 1 unit for the pointer/descriptor for now.
        # TODO: Handle array (a) and struct (d) types

        new_type_entry = {'id': type_id_val, 'TVAL_CAT': tval_cat, 'TPOINT': tpoint, 'name': norm_type_name}
        self.type_table.append(new_type_entry)
        new_type_idx = len(self.type_table) - 1 # Index in the list
        self._type_cache[norm_type_name] = new_type_idx


        if not any(lt_entry['type_ptr'] == new_type_idx for lt_entry in self.length_table):
            self.length_table.append({'type_ptr': new_type_idx, 'size': size})
        
        return new_type_idx # Return the index in the type_table list

    def _add_constant_to_table(self, value, value_type_str):
        """Adds a constant to CONSL if not exists, returns its index in self.constant_table."""
        const_key = (str(value), value_type_str.upper()) # Ensure value is string for key consistency
        if const_key in self._constant_cache:
            return self._constant_cache[const_key]

        const_id_val = self._get_next_constant_id()
        type_ptr_idx = self._add_type_to_table(value_type_str) 
        
        new_const_entry = {'id': const_id_val, 'value': value, 'type_ptr': type_ptr_idx}
        self.constant_table.append(new_const_entry)
        new_const_idx = len(self.constant_table) - 1
        self._constant_cache[const_key] = new_const_idx
        return new_const_idx

    def _ensure_activity_record(self, scope_name_or_id):
        """Ensures an activity record exists for the given scope, creates if not. Returns VALL index."""
        for i, ar_entry in enumerate(self.activity_record_table):
            if ar_entry['scope_id'] == scope_name_or_id:
                return i

        new_ar_entry = {
            'scope_id': scope_name_or_id,
            'return_address': 'N/A',
            'dynamic_link': 'N/A',
            'static_link': 'N/A',
            'formal_params': [],
            'local_variables': [], 
            'temp_units': 'N/A',
            'internal_vector': 'N/A'
        }
        self.activity_record_table.append(new_ar_entry)
        return len(self.activity_record_table) - 1

    def enter_scope(self, scope_name_prefix="scope"):
        self.current_scope_id_counter += 1
        scope_id = f"{scope_name_prefix}_{self.current_scope_id_counter}"
        new_scope_symbols_dict = {} # Symbols declared in this scope
        self.scope_stack.append({'name': scope_id, 'symbols': new_scope_symbols_dict})
        self._ensure_activity_record(scope_id)
        return new_scope_symbols_dict

    def exit_scope(self):
        if len(self.scope_stack) > 1:
            self.scope_stack.pop()

    def declare_variable(self, var_name, var_type_str):
        current_scope_dict = self.scope_stack[-1]
        current_scope_name = current_scope_dict['name']
        
        if var_name in current_scope_dict['symbols']:
            raise ValueError(f"Variable '{var_name}' already declared in scope '{current_scope_name}'")

        type_ptr_idx = self._add_type_to_table(var_type_str)
        vall_idx = self._ensure_activity_record(current_scope_name)

        symbol_entry = {
            'NEME': var_name,
            'TYP': type_ptr_idx, # Index in self.type_table
            'CAT': 'v', 
            'ADDR': vall_idx, # Points to the VALL entry for this scope
            'scope': current_scope_name,
            'initialized': False
        }
        self.symbol_table_entries.append(symbol_entry)
        current_scope_dict['symbols'][var_name] = symbol_entry # Reference to the entry in symbol_table_entries

        # Update VALL for the current scope
        self.activity_record_table[vall_idx]['local_variables'].append({
            'name': var_name,
            'type_ptr': type_ptr_idx,
            # 'offset': ... # Offset calculation would go here if doing memory layout
        })

    def lookup_variable(self, var_name):
        normalized_var_name = var_name.lower() # Normalize to lowercase
        for scope_dict in reversed(self.scope_stack):
            if normalized_var_name in scope_dict['symbols']:
                return scope_dict['symbols'][normalized_var_name] # Returns the actual symbol entry dict
        raise ValueError(f"Variable '{var_name}' not declared") # Original case in error message

    def set_initialized(self, var_name):
        normalized_var_name = var_name.lower() # Normalize to lowercase
        for scope_dict in reversed(self.scope_stack):
            if normalized_var_name in scope_dict['symbols']:
                scope_dict['symbols'][normalized_var_name]['initialized'] = True
                return
        raise ValueError(f"Variable '{var_name}' not declared") # Original case in error message

    def check_type(self, expected_type_idx, actual_type_idx, operation):
        if expected_type_idx == actual_type_idx:
            return

        expected_type_entry = self.type_table[expected_type_idx]
        actual_type_entry = self.type_table[actual_type_idx]

        # Allow assigning integer to real
        if expected_type_entry['TVAL_CAT'] == 'r' and actual_type_entry['TVAL_CAT'] == 'i':
            return

        raise ValueError(
            f"Type mismatch in {operation}: expected {expected_type_entry['name']}({expected_type_entry['TVAL_CAT']}), "
            f"got {actual_type_entry['name']}({actual_type_entry['TVAL_CAT']})"
        )
    
    def analyze(self, ast):
        self._reset_state() # Clear all tables and scope for a new analysis run

        if isinstance(ast, tuple):
            node_type = ast[0]
            if node_type == 'program':
                # Parser structure: ('program', ID_program_name, var_declarations_node, statements_node)
                # ID_program_name is p[2] from parser, which is a string.
                prog_name_str_from_ast, var_decls_node, stmts_node = ast[1], ast[2], ast[3]
                
                # Update global scope name if program name is available
                # Ensure prog_name_str_from_ast is a string, otherwise default.
                prog_name_str = prog_name_str_from_ast if isinstance(prog_name_str_from_ast, str) else 'global_program'
                self.scope_stack[0]['name'] = prog_name_str.lower() # Also normalize program name for scope ID consistency
                self.activity_record_table[0]['scope_id'] = prog_name_str.lower()
                
                self.process_var_declarations(var_decls_node)
                self.analyze_statements(stmts_node)
            else:
                raise ValueError(f"Unsupported AST root node type: {node_type}")
            return ast
        raise ValueError("Invalid AST structure: root is not a tuple.")

    def process_var_declarations(self, var_decls_node):
        # Expected from parser: ('var_declarations', [('var', [id_str1, id_str2], 'TYPE_STR'), ...]) or ('var_declarations', [])
        if var_decls_node and isinstance(var_decls_node, tuple) and len(var_decls_node) == 2 and \
           var_decls_node[0] == 'var_declarations' and var_decls_node[1] is not None:
            # var_decls_node[1] is the list of actual declaration tuples (var_list from parser)
            for decl_tuple in var_decls_node[1]: 
                if isinstance(decl_tuple, tuple) and len(decl_tuple) == 3 and decl_tuple[0] == 'var':
                    # decl_tuple is like ('var', ['id1', 'id2'], 'INTEGER')
                    var_representations_list = decl_tuple[1] # List of identifier strings
                    var_type_str = decl_tuple[2] # Type string like 'INTEGER'
                    
                    for item_repr in var_representations_list: # item_repr should be a string like 'counter'
                        var_name_str = None
                        if isinstance(item_repr, tuple) and len(item_repr) == 2 and item_repr[0] == 'ID':
                            # If parser gives ('ID', 'varname') for items in the declaration list
                            var_name_str = item_repr[1].lower() # Normalize to lowercase
                        elif isinstance(item_repr, str):
                            # If parser gives 'varname' directly
                            var_name_str = item_repr.lower() # Normalize to lowercase
                        else:
                            raise ValueError(f"Unexpected variable name format in AST declaration: {item_repr}")
                        
                        if var_name_str: # Ensure a name was extracted
                            self.declare_variable(var_name_str, var_type_str) # var_name_str is now lowercase
                        else:
                            # This case should ideally not be reached if the above logic is exhaustive for valid ASTs
                            raise ValueError(f"Could not extract variable name from declaration item: {item_repr}")
    
    def analyze_statements(self, stmts_list):
        for stmt in stmts_list:
            self.analyze_statement(stmt)

    def analyze_statement(self, stmt_tuple):
        if not isinstance(stmt_tuple, tuple) or not stmt_tuple:
            raise ValueError(f"Invalid statement structure: {stmt_tuple}")
            
        stmt_type = stmt_tuple[0]
        if stmt_type == 'assign':
            target_node, expr = stmt_tuple[1], stmt_tuple[2]
            
            actual_var_name = None
            if isinstance(target_node, str): # If parser gives 'varname' directly
                actual_var_name = target_node.lower() # Normalize to lowercase
            elif isinstance(target_node, tuple) and len(target_node) == 2 and target_node[0] == 'ID':
                # If parser gives ('ID', 'varname') for the assignment target
                actual_var_name = target_node[1].lower() # Normalize to lowercase
            else:
                raise ValueError(f"Invalid assignment target structure in AST: {target_node}")

            if actual_var_name is None: # Should not happen if above logic is correct
                 raise ValueError(f"Could not determine variable name from assignment target: {target_node}")

            var_info = self.lookup_variable(actual_var_name) # actual_var_name is already lowercase
            expr_type_idx = self.get_expression_type_idx(expr)
            self.check_type(var_info['TYP'], expr_type_idx, f"assignment to '{actual_var_name}'")
            self.set_initialized(actual_var_name) # actual_var_name is already lowercase
        elif stmt_type == 'if':
            cond, then_stmts, else_stmts_list = stmt_tuple[1], stmt_tuple[2], stmt_tuple[3]
            cond_type_idx = self.get_expression_type_idx(cond)
            expected_bool_type_idx = self._add_type_to_table('BOOLEAN')
            self.check_type(expected_bool_type_idx, cond_type_idx, "if condition")
            
            self.enter_scope("if_then")
            self.analyze_statements(then_stmts) # then_stmts should be a list of statements
            self.exit_scope()
            
            if else_stmts_list: 
                self.enter_scope("if_else")
                self.analyze_statements(else_stmts_list) # else_stmts_list should be a list
                self.exit_scope()
        elif stmt_type == 'while':
            cond, body_stmts = stmt_tuple[1], stmt_tuple[2]
            cond_type_idx = self.get_expression_type_idx(cond)
            expected_bool_type_idx = self._add_type_to_table('BOOLEAN')
            self.check_type(expected_bool_type_idx, cond_type_idx, "while condition")

            self.enter_scope("while_body")
            self.analyze_statements(body_stmts) # body_stmts should be a list
            self.exit_scope()
        elif stmt_type == 'writeln':
            expr_list_node = stmt_tuple[1] # This should be a list of expressions from parser
            for expr_item in expr_list_node:
                self.get_expression_type_idx(expr_item) 

    def get_expression_type_idx(self, expr_tuple):
        """Determine the type index (in TVAL) of an expression."""
        if not isinstance(expr_tuple, tuple) or not expr_tuple:
             # Handle raw literals if parser passes them directly (e.g. from a simple 'writeln(5)')
            if isinstance(expr_tuple, int):
                self._add_constant_to_table(expr_tuple, 'INTEGER')
                return self._add_type_to_table('INTEGER')
            elif isinstance(expr_tuple, float):
                self._add_constant_to_table(expr_tuple, 'REAL')
                return self._add_type_to_table('REAL')
            elif isinstance(expr_tuple, str): # Could be an ID, a boolean literal, or a string literal
                # Try lookup as variable first (parser provides IDs as raw strings in expressions)
                try:
                    # lookup_variable handles lowercasing internally
                    var_info = self.lookup_variable(expr_tuple) 
                    if not var_info['initialized']:
                        # Use original case of expr_tuple for error message consistency
                        raise ValueError(f"Variable '{expr_tuple}' used before initialization")
                    return var_info['TYP']
                except ValueError: # Not a declared variable, or other lookup error
                    # If not a variable, check if it's a boolean literal TRUE or FALSE
                    if (expr_tuple.upper() == 'TRUE' or expr_tuple.upper() == 'FALSE'):
                        self._add_constant_to_table(expr_tuple.upper() == 'TRUE', 'BOOLEAN')
                        return self._add_type_to_table('BOOLEAN')
                    # Check if it's a string literal (e.g. 'hello') that parser might have missed tagging
                    # (though t_STRING in lexer should catch these as STRING_LITERAL tuples)
                    # This case is less likely if parser's STRING_LITERAL rule is robust.
                    if expr_tuple.startswith("'") and expr_tuple.endswith("'"):
                         val = expr_tuple[1:-1] # Remove quotes
                         self._add_constant_to_table(val, 'STRING')
                         return self._add_type_to_table('STRING')
                    # If none of the above, it's an undeclared identifier or unhandled literal form
                    raise ValueError(f"Unknown identifier or malformed/unhandled literal: {expr_tuple}")

            raise ValueError(f"Invalid expression structure: {expr_tuple}")

        node_type = expr_tuple[0]
        
        if node_type == 'NUMBER': 
            value = expr_tuple[1]
            const_type_str = 'REAL' if isinstance(value, float) else 'INTEGER'
            self._add_constant_to_table(value, const_type_str)
            return self._add_type_to_table(const_type_str)
        elif node_type == 'STRING_LITERAL': 
            value = expr_tuple[1]
            self._add_constant_to_table(value, 'STRING')
            return self._add_type_to_table('STRING')
        elif node_type == 'BOOLEAN_LITERAL': # Assuming parser produces this for TRUE/FALSE
            value = expr_tuple[1] # True or False
            self._add_constant_to_table(value, 'BOOLEAN')
            return self._add_type_to_table('BOOLEAN')
        # Removed 'elif node_type == 'ID':' because parser provides IDs in expressions as raw strings,
        # which are now handled by the `isinstance(expr_tuple, str)` block above.
        elif node_type in ('+', '-', '*', '/'):
            left_expr, right_expr = expr_tuple[1], expr_tuple[2]
            left_type_idx = self.get_expression_type_idx(left_expr)
            right_type_idx = self.get_expression_type_idx(right_expr)
            
            # Basic numeric type promotion/checking (e.g. int + real = real)
            # For now, strict: if one is REAL, result is REAL, both must be numeric.
            # If both INTEGER, result is INTEGER.
            l_cat = self.type_table[left_type_idx]['TVAL_CAT']
            r_cat = self.type_table[right_type_idx]['TVAL_CAT']

            if l_cat == 'r' or r_cat == 'r': # Promotion to REAL
                real_idx = self._add_type_to_table('REAL')
                self.check_type(real_idx, left_type_idx, f"left operand of {node_type} (expecting numeric)")
                self.check_type(real_idx, right_type_idx, f"right operand of {node_type} (expecting numeric)")
                return real_idx
            elif l_cat == 'i' and r_cat == 'i': # Both INTEGER
                int_idx = self._add_type_to_table('INTEGER')
                return int_idx
            else:
                raise ValueError(f"Operands for '{node_type}' must be numeric (INTEGER or REAL). Got {l_cat}, {r_cat}")

        elif node_type in ('<', '>', '=', '<=', '>=', '<>'): # Relational
            left_expr, right_expr = expr_tuple[1], expr_tuple[2]
            left_type_idx = self.get_expression_type_idx(left_expr)
            right_type_idx = self.get_expression_type_idx(right_expr)
            # Allow comparison between INTEGER and REAL. Other types must match exactly.
            l_cat = self.type_table[left_type_idx]['TVAL_CAT']
            r_cat = self.type_table[right_type_idx]['TVAL_CAT']
            if not ((l_cat in ('i', 'r') and r_cat in ('i', 'r')) or (left_type_idx == right_type_idx)):
                 raise ValueError(f"Cannot compare types {l_cat} and {r_cat} with '{node_type}'")
            return self._add_type_to_table('BOOLEAN')
        elif node_type in ('AND', 'OR', 'NOT'): # Logical
            bool_idx = self._add_type_to_table('BOOLEAN')
            if node_type == 'NOT':
                operand_expr = expr_tuple[1]
                operand_type_idx = self.get_expression_type_idx(operand_expr)
                self.check_type(bool_idx, operand_type_idx, f"operand of {node_type}")
            else: # AND, OR
                left_expr, right_expr = expr_tuple[1], expr_tuple[2]
                left_type_idx = self.get_expression_type_idx(left_expr)
                right_type_idx = self.get_expression_type_idx(right_expr)
                self.check_type(bool_idx, left_type_idx, f"left operand of {node_type}")
                self.check_type(bool_idx, right_type_idx, f"right operand of {node_type}")
            return bool_idx
        
        raise ValueError(f"Unknown expression node type: {node_type} in {expr_tuple}")

    def get_symbol_table_entries(self):
        """Return the flat list of all symbol entries (SYNBL)."""
        return self.symbol_table_entries

    def get_type_table(self):
        """Return the Type Table (TVAL)."""
        return self.type_table

    def get_constant_table(self):
        """Return the Constant Table (CONSL)."""
        return self.constant_table

    def get_length_table(self):
        """Return the Length Table (LENL)."""
        return self.length_table

    def get_activity_record_table(self):
        """Return the Activity Record Table (VALL)."""
        return self.activity_record_table

    # Kept for potential compatibility if main.py's print logic isn't fully updated yet.
    # However, api.py and main.py should be updated to use the new specific getters.
    def get_symbol_table(self):
        """DEPRECATED or for specific internal use. Use get_symbol_table_entries() for SYNBL."""
        # This method's original purpose (returning global scope from old structure) is gone.
        # Returning the new SYNBL structure.
        return self.get_symbol_table_entries()
