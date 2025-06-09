# Define constants for stack frame layout
LINKAGE_SIZE = 3  # Slots for Static Link, Dynamic Link, Return Address
METADATA_SLOTS_BEFORE_PARAMS = 1 # Additional slots before parameters (e.g., for param count, return value space)
PARAMS_BASE_OFFSET = LINKAGE_SIZE + METADATA_SLOTS_BEFORE_PARAMS # Parameters start at this offset (e.g., 4)

class SemanticAnalyzer:
    def __init__(self):
        # Main Symbol Table (SYNBL) - list of symbol entries
        self.synbl = []
        # Type Table (TYPEL) - list of type descriptors
        self.typel = []
        # Function/Procedure Info Table (PFINFL)
        self.pfinfl = []
        # Array Info Table (AINFL)
        self.ainfl = []
        # Constant Table (CONSL)
        self.consl = []

        # Scope Management
        self.current_level = 0  # Static nesting depth
        self.scope_id_counter = 0
        self.current_scope_id = self.scope_id_counter # Global scope ID
        
        # MODIFIED: Initialize scope_stack for global scope with PARAMS_BASE_OFFSET
        # This will make global variables also start their offsets from PARAMS_BASE_OFFSET.
        # If global variables should start from 0 (which is more typical for globals), 
        # then the third element should be 0.
        self.scope_stack = [(self.current_level, self.current_scope_id, PARAMS_BASE_OFFSET)] 
        
        # Initialize built-in types
        self._ensure_basic_type("INTEGER")
        self._ensure_basic_type("BOOLEAN")
        self._ensure_basic_type("REAL") 
        self._ensure_basic_type("CHAR")   
        self._ensure_basic_type("STRING") # Added

    def _get_next_scope_id(self):
        self.scope_id_counter += 1
        return self.scope_id_counter

    def enter_scope(self, is_function_scope=False, param_slots_used=0): # Modified signature
        """Enter a new scope. If it's a function, level increases."""
        if is_function_scope:
            self.current_level += 1
        
        new_scope_id = self._get_next_scope_id()
        
        initial_offset_for_scope = 0 # Default for global or non-function block scopes
        if is_function_scope:
            # Local variables start after the fixed linkage/metadata area and all parameters.
            # PARAMS_BASE_OFFSET is where parameters begin (e.g., 4).
            # param_slots_used is the number of slots occupied by parameters.
            initial_offset_for_scope = PARAMS_BASE_OFFSET + param_slots_used
            
        self.scope_stack.append((self.current_level, new_scope_id, initial_offset_for_scope)) 
        self.current_scope_id = new_scope_id
        # print(f"Entered scope: Level {self.current_level}, ID {self.current_scope_id}, Initial Offset: {initial_offset_for_scope}")


    def exit_scope(self, is_function_scope=False):
        """Exit the current scope."""
        if len(self.scope_stack) > 1:
            exiting_level, exiting_scope_id, _ = self.scope_stack.pop()
            # print(f"Exited scope: Level {exiting_level}, ID {exiting_scope_id}")
            if is_function_scope:
                if self.current_level != exiting_level:
                    # This might happen if enter/exit calls are mismatched
                    print(f"Warning: Exiting function scope level mismatch. Current: {self.current_level}, Exited: {exiting_level}")
                self.current_level = self.scope_stack[-1][0] # Restore level from parent scope

            self.current_scope_id = self.scope_stack[-1][1]
        else:
            raise Exception("Cannot exit global scope")

    def _get_current_offset_and_increment(self, type_size=1): # Simplified size
        """Gets current offset for VALL and increments it for the current scope."""
        level, scope_id, current_offset = self.scope_stack[-1]
        self.scope_stack[-1] = (level, scope_id, current_offset + type_size)
        return current_offset

    def _ensure_basic_type(self, type_name_upper):
        """Ensures a basic type exists in TYPEL and returns its index."""
        for i, type_entry in enumerate(self.typel):
            if type_entry.get('KIND') == 'basic' and type_entry.get('NAME') == type_name_upper:
                return i
        self.typel.append({'KIND': 'basic', 'NAME': type_name_upper})
        return len(self.typel) - 1

    def _add_array_type_to_typel(self, element_type_ptr, lower_bound, upper_bound, size):
        """Adds an array type to AINFL and TYPEL."""
        ainfl_entry = {
            'ELEMENT_TYPE_PTR': element_type_ptr,
            'LOWER_BOUND': lower_bound,
            'UPPER_BOUND': upper_bound,
            'SIZE': size 
        }
        self.ainfl.append(ainfl_entry)
        ainfl_ptr = len(self.ainfl) - 1

        typel_entry = {'KIND': 'array', 'AINFL_PTR': ainfl_ptr}
        self.typel.append(typel_entry)
        return len(self.typel) - 1

    def _add_constant_to_consl(self, value, type_ptr):
        """Adds a constant to CONSL and returns its index."""
        # Could add check for existing identical constant to reuse
        self.consl.append({'VALUE': value, 'TYPE_PTR': type_ptr})
        return len(self.consl) - 1

    def _get_type_size(self, type_ptr):
        """
        Returns the size of a type in memory units (e.g., words).
        Simplified: assumes basic types are size 1. Arrays/complex types might need more logic.
        """
        if type_ptr < 0 or type_ptr >= len(self.typel):
            return 1 # Default size for unknown or unresolved types

        type_info = self.typel[type_ptr]
        kind = type_info.get('KIND')

        if kind == 'basic':
            # For simplicity, all basic types take 1 memory unit.
            # Refine if different basic types have different sizes (e.g., REAL vs INTEGER).
            return 1
        elif kind == 'array':
            # This is complex: could be size of descriptor or full array.
            # For stack allocation of variable itself (not the array data), often 1 (pointer/descriptor).
            # If full array is on stack, calculate from AINFL.
            # ainfl_entry = self.ainfl[type_info['AINFL_PTR']]
            # element_size = self._get_type_size(ainfl_entry['ELEMENT_TYPE_PTR'])
            # num_elements = ainfl_entry['SIZE']
            # return element_size * num_elements
            return 1 # Simplified: size of an array variable on stack (e.g. pointer)
        # Add other kinds (records, etc.)
        return 1 # Default for other complex types


    def declare_symbol(self, name, category, type_name_or_struct, details=None):
        """
        Declare a symbol in SYNBL.
        name: identifier name
        category: 'v'(variable), 'c'(constant), 't'(type), 'f'(function/procedure), 
                  'p_val'(param by value), 'p_ref'(param by reference)
        type_name_or_struct: For basic types, a string like "INTEGER". 
                             For user-defined types, the name of the type.
                             For arrays, a structure describing the array.
                             For functions, the return type name.
        details: Dict for extra info (e.g., const value, func params, array bounds)
        """
        current_level, current_scope_id, _ = self.scope_stack[-1]

        # Check for redefinition in the same name, level, and exact scope_id
        for entry in self.synbl:
            if entry['NAME'] == name and entry['LEVEL'] == current_level and entry['SCOPE_ID'] == current_scope_id:
                raise ValueError(f"Symbol '{name}' already declared in scope (L{current_level}, S{current_scope_id})")

        type_ptr = -1
        addr_ptr = None # Can be int (index) or dict like {'level': l, 'offset': o}

        # Determine TYPE_PTR
        if category in ['v', 'c', 'p_val', 'p_ref'] or (category == 'f' and type_name_or_struct is not None): # Functions can be procedures (None type)
            if isinstance(type_name_or_struct, str): # Basic type or named type
                # Is it a basic type?
                type_name_upper = type_name_or_struct.upper()
                is_basic = any(t.get('NAME') == type_name_upper and t.get('KIND') == 'basic' for t in self.typel)
                if is_basic:
                    type_ptr = self._ensure_basic_type(type_name_upper)
                else: # User-defined type name, look it up
                    type_symbol = self.lookup_symbol(type_name_or_struct, category_filter='t')
                    if not type_symbol:
                        raise ValueError(f"Type '{type_name_or_struct}' not declared.")
                    type_ptr = type_symbol['TYPE_PTR'] # The type_symbol itself points to a TYPEL entry
            elif isinstance(type_name_or_struct, dict) and type_name_or_struct.get('kind') == 'array':
                # e.g. {'kind': 'array', 'element_type': 'INTEGER', 'lower': 1, 'upper': 5}
                el_type_name = type_name_or_struct['element_type']
                el_type_ptr = self._resolve_type_name_to_ptr(el_type_name)
                # TODO: Calculate size properly
                size = type_name_or_struct['upper'] - type_name_or_struct['lower'] + 1
                type_ptr = self._add_array_type_to_typel(
                    el_type_ptr, 
                    type_name_or_struct['lower'], 
                    type_name_or_struct['upper'], 
                    size
                )
            else:
                raise ValueError(f"Unsupported type structure for '{name}': {type_name_or_struct}")
        elif category == 't': # Type declaration itself
            # type_name_or_struct is the definition of the type being declared
            # e.g. VAR arr : ARRAY_DEF; -> type_name_or_struct is ARRAY_DEF
            # TYPE arr = ARRAY_DEF; -> here type_name_or_struct is ARRAY_DEF
            if isinstance(type_name_or_struct, str): # Alias to an existing type
                 type_symbol = self.lookup_symbol(type_name_or_struct, category_filter='t')
                 if not type_symbol: # Or basic type
                     type_ptr = self._resolve_type_name_to_ptr(type_name_or_struct)
                 else:
                    type_ptr = type_symbol['TYPE_PTR']
            elif isinstance(type_name_or_struct, dict) and type_name_or_struct.get('kind') == 'array':
                el_type_name = type_name_or_struct['element_type']
                el_type_ptr = self._resolve_type_name_to_ptr(el_type_name)
                size = type_name_or_struct['upper'] - type_name_or_struct['lower'] + 1
                type_ptr = self._add_array_type_to_typel(
                    el_type_ptr, 
                    type_name_or_struct['lower'], 
                    type_name_or_struct['upper'], 
                    size
                )
            else:
                 raise ValueError(f"Invalid type definition for type '{name}'")


        # Determine ADDR_PTR
        addr_ptr = None # Default

        if category == 'p_val' or category == 'p_ref':
            if details and 'param_ordinal' in details:
                # param_ordinal is 0-indexed (0 for 1st param, 1 for 2nd, etc.)
                # Parameters start at PARAMS_BASE_OFFSET.
                param_offset = PARAMS_BASE_OFFSET + details['param_ordinal'] 
                addr_ptr = {'level': current_level, 'offset': param_offset}
            else:
                raise ValueError(f"Parameter '{name}' is missing 'param_ordinal' in details for offset calculation.")
        
        elif category == 'v': # Local or global variables
            # For global variables (current_level == 0), offsets start from 0 
            # (as initialized in scope_stack for global scope).
            # For local variables (current_level > 0), offsets start from 
            # PARAMS_BASE_OFFSET + param_count_for_this_function, 
            # which should have been set as the initial 'next_offset_for_scope' 
            # when entering the function's scope.
            
            size_of_type = self._get_type_size(type_ptr)
            offset = self._get_current_offset_and_increment(size_of_type)
            addr_ptr = {'level': current_level, 'offset': offset}
            
        elif category == 'c':
            if details is None or 'value' not in details:
                raise ValueError(f"Constant '{name}' declared without a value.")
            const_val = details['value']
            # Ensure type_ptr is resolved for the constant
            if type_ptr == -1: # If not resolved during general type processing
                if isinstance(type_name_or_struct, str):
                    type_ptr = self._resolve_type_name_to_ptr(type_name_or_struct)
                else: # Fallback or error if type cannot be resolved for constant
                    raise ValueError(f"Cannot determine type for constant '{name}'.")
            addr_ptr = self._add_constant_to_consl(const_val, type_ptr)

        elif category == 'f': # Function or Procedure
            # Procedures might have type_name_or_struct as None
            return_type_ptr = -1
            if type_name_or_struct: # If it's a function with a return type
                return_type_ptr = self._resolve_type_name_to_ptr(str(type_name_or_struct))

            param_count = len(details.get('params', [])) if details else 0
            # param_synbl_indices would be filled as params are declared in the function's scope
            pfinfl_entry = {
                'LEVEL': current_level, # Level of function definition
                'PARAM_COUNT': param_count,
                'PARAM_SYNBL_INDICES': [], # To be filled later
                'ENTRY_LABEL': f"FUNC_{name.upper()}", # Placeholder
                'RETURN_TYPE_PTR': return_type_ptr
            }
            self.pfinfl.append(pfinfl_entry)
            addr_ptr = len(self.pfinfl) - 1
        elif category == 't':
            addr_ptr = None # Type declarations don't have a runtime address in this sense
                           # Their 'address' is their definition in TYPEL via TYPE_PTR

        new_symbol = {
            'NAME': name,
            'TYPE_PTR': type_ptr,
            'CAT': category,
            'ADDR_PTR': addr_ptr,
            'LEVEL': current_level,
            'SCOPE_ID': current_scope_id,
            'INITIALIZED': False,
            'DETAILS': details if details else {} # Store original details like param names for functions
        }
        self.synbl.append(new_symbol)
        # print(f"Declared: {new_symbol}")
        return new_symbol

    def _resolve_type_name_to_ptr(self, type_name):
        """Resolves a type name (string) to a TYPEL pointer. Handles basic and declared types."""
        type_name_upper = type_name.upper()
        # Check basic types first
        for i, t_entry in enumerate(self.typel):
            if t_entry.get('KIND') == 'basic' and t_entry.get('NAME') == type_name_upper:
                return i
        # Check user-defined types
        type_symbol = self.lookup_symbol(type_name, category_filter='t')
        if type_symbol:
            return type_symbol['TYPE_PTR']
        raise ValueError(f"Type '{type_name}' not found.")


    def lookup_symbol(self, name, category_filter=None):
        """Look up a symbol, respecting scope and level."""
        # Iterate from current scope outwards
        for level_on_stack, scope_id_on_stack, _ in reversed(self.scope_stack):
            for entry in reversed(self.synbl): # Search most recent declarations first
                if entry['NAME'] == name:
                    # Check if symbol's definition level is accessible from current level
                    # And if its scope_id matches one on the stack (or is global and level matches)
                    if entry['LEVEL'] <= level_on_stack:
                        # More precise scope check: is entry's scope an ancestor or current?
                        is_accessible_scope = False
                        for l_s, s_id_s, _ in self.scope_stack:
                            if entry['LEVEL'] == l_s and entry['SCOPE_ID'] == s_id_s:
                                is_accessible_scope = True
                                break
                        
                        if is_accessible_scope:
                            if category_filter and entry['CAT'] != category_filter:
                                continue # Skip if category doesn't match
                            return entry
        return None # Not found

    def set_initialized(self, var_name):
        """Mark a variable as initialized."""
        var_symbol = self.lookup_symbol(var_name, category_filter='v') # Or 'p_val', 'p_ref'
        if not var_symbol: # Also check params
            var_symbol = self.lookup_symbol(var_name, category_filter='p_val')
        if not var_symbol:
            var_symbol = self.lookup_symbol(var_name, category_filter='p_ref')

        if var_symbol:
            # Since synbl entries are dicts, directly modify (if not copying entries)
            # Need to find the actual entry in self.synbl list to modify
            for i, entry in enumerate(self.synbl):
                if entry['NAME'] == var_symbol['NAME'] and \
                   entry['LEVEL'] == var_symbol['LEVEL'] and \
                   entry['SCOPE_ID'] == var_symbol['SCOPE_ID']: # Ensure it's the exact symbol
                    self.synbl[i]['INITIALIZED'] = True
                    return
            raise ValueError(f"Internal error: Symbol '{var_name}' found by lookup but not in list for update.")
        else:
            raise ValueError(f"Variable or parameter '{var_name}' not declared (for set_initialized).")

    def check_type_compatibility(self, type_ptr1, type_ptr2, operation_desc):
        """Checks if two types (by TYPEL pointers) are compatible for an operation."""
        # This is a simplified check. Real type compatibility is complex.
        # For now, assume types are compatible if their pointers are the same,
        # or handle specific known compatible pairs (e.g., INTEGER and REAL for some ops).
        if type_ptr1 == type_ptr2:
            return True

        type1_info = self.typel[type_ptr1]
        type2_info = self.typel[type_ptr2]

        # Example: Allow assigning INTEGER to REAL
        if type1_info.get('NAME') == 'REAL' and type2_info.get('NAME') == 'INTEGER':
            return True # Target is REAL, value is INTEGER - usually allowed with conversion

        raise ValueError(f"Type mismatch in {operation_desc}: Type1 ({self.get_type_name_from_ptr(type_ptr1)}) vs Type2 ({self.get_type_name_from_ptr(type_ptr2)})")

    def get_type_name_from_ptr(self, type_ptr):
        if type_ptr < 0 or type_ptr >= len(self.typel): return "invalid_type_ptr"
        t_info = self.typel[type_ptr]
        if t_info['KIND'] == 'basic': return t_info['NAME']
        if t_info['KIND'] == 'array':
            el_ptr = self.ainfl[t_info['AINFL_PTR']]['ELEMENT_TYPE_PTR']
            return f"ARRAY OF {self.get_type_name_from_ptr(el_ptr)}"
        return "unknown_complex_type"

    def analyze(self, ast):
        if not ast: return
        node_type = ast[0]

        if node_type == 'program':
            # ast: ('program', prog_name, var_declarations_node, block_node)
            # block_node: ('block', statements_list) or similar for main
            # var_declarations_node: ('var_declarations', list_of_decl_tuples)
            # decl_tuple: (id_list, type_node)
            prog_name_token = ast[1] 
            self.declare_symbol(prog_name_token, 'program_name', None) # Special category

            var_decls_node = ast[2] # Assuming structure ('var_declarations', decls_list) or None
            if var_decls_node and var_decls_node[0] == 'var_declarations':
                self.process_declarations(var_decls_node[1], 'v') # 'v' for variable

            # Process function/procedure declarations if they are part of AST structure here
            # For now, assuming they might be mixed with statements or in a specific section

            main_block_node = ast[3] # Assuming ('block', statements)
            if main_block_node and main_block_node[0] == 'block':
                 self.analyze_statements(main_block_node[1])
            else: # Simpler structure like ('program', name, var_decls, statements_list)
                self.analyze_statements(ast[3])


    def process_declarations(self, decls_list, category_default):
        """
        Processes a list of declarations (variables, constants, types).
        decls_list from parser seems to be: [('var', ['id_str'], 'type_str'), ...]
        """
        if not decls_list: return

        # print(f"DEBUG: Processing declarations list: {decls_list}")

        for decl_item in decls_list:
            # AST structure from parser for var decls: ('var', ['identifier_string'], 'type_string')
            if decl_item[0] == 'var': # CORRECTED: Match AST node type
                
                # id_list_from_ast is like ['counter'] or ['id1', 'id2'] if parser supports multiple ids per line this way
                id_list_from_ast = decl_item[1] 
                type_name_str = decl_item[2] # This is directly the type string like 'integer'

                # print(f"DEBUG: Declaration item: {decl_item}, Extracted id_list: {id_list_from_ast}, Extracted type_name: {type_name_str}")

                ids_to_declare = []
                if isinstance(id_list_from_ast, list):
                    for id_name in id_list_from_ast:
                        if isinstance(id_name, str):
                            ids_to_declare.append(id_name)
                        else:
                            print(f"WARNING: Unexpected item in id_list_from_ast: {id_name}")
                else:
                    # Handle if parser could produce a single string instead of a list for a single ID
                    # e.g. ('var', 'counter', 'integer') - this is less likely given current debug output
                    if isinstance(id_list_from_ast, str):
                         ids_to_declare.append(id_list_from_ast)
                    else:
                        print(f"WARNING: Unhandled id_list_from_ast format: {id_list_from_ast}")
                
                # print(f"DEBUG: IDs to declare for type {type_name_str}: {ids_to_declare}")

                for var_name in ids_to_declare:
                    # print(f"DEBUG: Declaring symbol: Name='{var_name}', Cat='{category_default}', Type='{type_name_str}'")
                    try:
                        self.declare_symbol(var_name, category_default, type_name_str)
                    except Exception as e:
                        print(f"ERROR during declare_symbol for '{var_name}': {e}")
            else:
                print(f"WARNING: Skipped declaration item with unknown type: {decl_item[0]}")
            # Add elif for 'const_declaration', 'type_declaration' etc. if their AST structure differs

    def analyze_statements(self, stmts_list):
        for stmt in stmts_list:
            self.analyze_statement(stmt)

    def analyze_statement(self, stmt_node):
        if not stmt_node: return
        node_type = stmt_node[0]

        # Add this print statement for debugging
        # print(f"DEBUG: Analyzing statement node: {stmt_node}")

        if node_type == 'assign':
            # AST node is actually: ('assign', var_name_string, expr_node)
            # Example: ('assign', 'counter', '10')
            
            # Print the part of the AST you expect to contain the variable name
            # print(f"DEBUG: Assignment - stmt_node[1]: {stmt_node[1]}")
            # The following 'if' and print statement for stmt_node[1][1] are based on a wrong assumption
            # if isinstance(stmt_node[1], tuple) and len(stmt_node[1]) > 1:
            #      print(f"DEBUG: Assignment - stmt_node[1][1] (expected var_name or token): {stmt_node[1][1]}")

            var_name = stmt_node[1] # CORRECTED: Directly use stmt_node[1]
            expr_node = stmt_node[2]

            # print(f"DEBUG: Assignment - Extracted var_name: '{var_name}', Type: {type(var_name)}") # Crucial print

            var_symbol = self.lookup_symbol(var_name)
            if not var_symbol:
                raise ValueError(f"Variable '{var_name}' not declared before assignment.")
            if var_symbol['CAT'] not in ['v', 'p_val', 'p_ref']: # Cannot assign to const, type, func name
                raise ValueError(f"Cannot assign to '{var_name}' of category '{var_symbol['CAT']}'.")

            expr_type_ptr = self.get_expression_type_ptr(expr_node)
            self.check_type_compatibility(var_symbol['TYPE_PTR'], expr_type_ptr, f"assignment to '{var_name}'")
            self.set_initialized(var_name)

        elif node_type == 'if_statement':
            # ('if_statement', cond_expr, then_block_node, else_block_node_optional)
            # then_block_node: ('block', stmts_list)
            cond_expr = stmt_node[1]
            then_block = stmt_node[2]
            else_block = stmt_node[3] if len(stmt_node) > 3 else None

            cond_type_ptr = self.get_expression_type_ptr(cond_expr)
            bool_type_ptr = self._ensure_basic_type('BOOLEAN')
            self.check_type_compatibility(bool_type_ptr, cond_type_ptr, "if condition")

            self.enter_scope()
            self.analyze_statements(then_block[1]) # Assuming ('block', stmts)
            self.exit_scope()

            if else_block:
                self.enter_scope()
                self.analyze_statements(else_block[1]) # Assuming ('block', stmts)
                self.exit_scope()

        elif node_type == 'while_statement':
            # ('while_statement', cond_expr, body_block_node)
            cond_expr = stmt_node[1]
            body_block = stmt_node[2]

            cond_type_ptr = self.get_expression_type_ptr(cond_expr)
            bool_type_ptr = self._ensure_basic_type('BOOLEAN')
            self.check_type_compatibility(bool_type_ptr, cond_type_ptr, "while condition")

            self.enter_scope(is_function_scope=False) # Loop body is a new block scope
            self.analyze_statements(body_block[1]) # Assuming ('block', stmts)
            self.exit_scope()
        
        elif node_type == 'writeln_statement':
            # ('writeln_statement', expr_list_node) or ('writeln_statement', single_expr_node)
            # expr_list_node: ('expr_list', [expr1, expr2])
            args_node = stmt_node[1]
            if args_node[0] == 'expr_list':
                for expr in args_node[1]:
                    self.get_expression_type_ptr(expr) # Analyze for type correctness and side effects
            else: # Single expression
                self.get_expression_type_ptr(args_node)


    def get_expression_type_ptr(self, expr_node):
        # print(f"DEBUG: get_expression_type_ptr called with: {expr_node}, type: {type(expr_node)}")

        # 1. Handle direct literals or identifiers if parser provides them as raw values
        if isinstance(expr_node, str):
            if expr_node.lower() == 'true':
                return self._ensure_basic_type('BOOLEAN')
            elif expr_node.lower() == 'false':
                return self._ensure_basic_type('BOOLEAN')
            try:
                int(expr_node) # Check if it's a number string
                return self._ensure_basic_type('INTEGER')
            except ValueError:
                # If it's a string, not 'true'/'false', not a number string,
                # it must be an identifier.
                # print(f"DEBUG: Treating string '{expr_node}' as an ID.")
                symbol = self.lookup_symbol(expr_node) # Treat as ID
                if not symbol:
                    raise ValueError(f"Identifier '{expr_node}' not declared.")
                if symbol['CAT'] in ['v', 'p_val', 'p_ref'] and not symbol['INITIALIZED']:
                    print(f"Warning: Variable '{expr_node}' used before explicit assignment (in an expression).")
                return symbol['TYPE_PTR']

        if isinstance(expr_node, int): # If parser directly gives an int
            return self._ensure_basic_type('INTEGER')
        if isinstance(expr_node, bool): # If parser directly gives a bool
            return self._ensure_basic_type('BOOLEAN')

        # 2. Handle tuple-based AST nodes
        if not isinstance(expr_node, tuple) or not expr_node: 
            # This should ideally not be reached if all string/int/bool cases are handled above
            # or if the only remaining non-tuple is an error.
            raise ValueError(f"Expression node '{expr_node}' is not a recognized literal, direct ID, or valid AST tuple.")

        node_type = expr_node[0]

        if node_type == 'NUMBER': # Literal integer, e.g., ('NUMBER', '10') or ('NUMBER', 10)
            # val_repr = expr_node[1] # Value is expr_node[1]
            # No .value needed if val_repr is the direct string or int.
            # Type is directly INTEGER.
            return self._ensure_basic_type('INTEGER')
        elif node_type == 'STRING_LITERAL': # e.g., ('STRING_LITERAL', 'hello')
            # val_repr = expr_node[1] # String value is expr_node[1]
            return self._ensure_basic_type('STRING')
        elif node_type == 'BOOLEAN_LITERAL': # e.g., ('BOOLEAN_LITERAL', 'true') or ('BOOLEAN_LITERAL', True)
            # val_repr = expr_node[1] # Boolean value is expr_node[1]
            return self._ensure_basic_type('BOOLEAN')
        elif node_type == 'ID': # Variable or constant, e.g., ('ID', 'varname')
            name = expr_node[1] # Direct string name, no .value needed
            symbol = self.lookup_symbol(name)
            if not symbol:
                raise ValueError(f"Identifier '{name}' not declared.")
            if symbol['CAT'] in ['v', 'p_val', 'p_ref'] and not symbol['INITIALIZED']:
                print(f"Warning: Variable '{name}' used before explicit assignment (in an expression).")
            return symbol['TYPE_PTR']
        
        # CORRECTED LIST OF OPERATORS:
        # Ensure this list matches exactly what your parser uses for expr_node[0] for operators
        elif node_type in ['+', '-', '*', '/',  # Arithmetic (assuming parser uses these symbols)
                           '<', '>', '=', '<=', '>=', '<>', # Relational (Pascal uses single char for some, e.g. =, <, >)
                                                            # and two chars for others like <=, >=, <>
                                                            # Adjust to your parser's output for EQ, NE, LE, GE etc.
                           'and', 'or', 'not']: # Logical (Pascal uses keywords 'and', 'or', 'not')
                                                 # Add 'not' if it's a unary op handled here, or separately
            
            # Handle unary 'not' separately if it has a different AST structure (e.g., ('not', operand))
            if node_type == 'not' and len(expr_node) == 2: # Example for unary 'not'
                operand_expr = expr_node[1]
                operand_type_ptr = self.get_expression_type_ptr(operand_expr)
                bool_type_ptr = self._ensure_basic_type('BOOLEAN')
                self.check_type_compatibility(bool_type_ptr, operand_type_ptr, f"operand of {node_type}")
                return bool_type_ptr

            # For binary operators:
            if len(expr_node) < 3: # Should not happen for binary ops
                raise ValueError(f"Malformed binary operator node: {expr_node}")

            left_expr = expr_node[1]
            right_expr = expr_node[2]
            left_type_ptr = self.get_expression_type_ptr(left_expr)
            right_type_ptr = self.get_expression_type_ptr(right_expr)

            int_type_ptr = self._ensure_basic_type('INTEGER')
            bool_type_ptr = self._ensure_basic_type('BOOLEAN')
            # real_type_ptr = self._ensure_basic_type('REAL')

            if node_type in ['+', '-', '*', '/']: # Arithmetic
                self.check_type_compatibility(int_type_ptr, left_type_ptr, f"left operand of {node_type}")
                self.check_type_compatibility(int_type_ptr, right_type_ptr, f"right operand of {node_type}")
                return int_type_ptr 
            elif node_type in ['<', '>', '=', '<=', '>=', '<>']: # Relational
                                                                # Adjust these symbols if your parser uses others like 'EQ', 'NE'
                if left_type_ptr != right_type_ptr:
                    left_t_name = self.get_type_name_from_ptr(left_type_ptr)
                    right_t_name = self.get_type_name_from_ptr(right_type_ptr)
                    is_numeric_comparison = (left_t_name in ["INTEGER", "REAL"] and right_t_name in ["INTEGER", "REAL"])
                    # Add string comparison if needed: or (left_t_name == "STRING" and right_t_name == "STRING")
                    if not is_numeric_comparison: # Add other allowed comparisons here
                         self.check_type_compatibility(left_t_ptr, right_t_ptr, f"operands of {node_type}")
                return bool_type_ptr 
            elif node_type in ['and', 'or']: # Logical
                self.check_type_compatibility(bool_type_ptr, left_type_ptr, f"left operand of {node_type}")
                self.check_type_compatibility(bool_type_ptr, right_type_ptr, f"right operand of {node_type}")
                return bool_type_ptr
        
        # Add NOT, function calls, array access etc. here
        raise ValueError(f"Cannot determine type of expression node: {expr_node}")

    def get_symbol_tables_snapshot(self):
        """Returns a snapshot of all internal tables for debugging/output."""
        return {
            "SYNBL": self.synbl,
            "TYPEL": self.typel,
            "PFINFL": self.pfinfl,
            "AINFL": self.ainfl,
            "CONSL": self.consl,
            "SCOPE_STACK_SNAPSHOT": list(self.scope_stack) # Make a copy
        }

    # --- Old methods to be removed or fully refactored ---
    # def get_symbol_table(self):
    #     # This old method returned only the global scope of the old symbol_table
    #     # The new way is get_symbol_tables_snapshot() or specific queries
    #     # For compatibility, could try to reconstruct something similar if needed
    #     # but it's better to use the new structure.
    #     # For now, let's return the whole SYNBL for a flat view.
    #     return self.synbl


# Example of how AST nodes might look (parser dependent):
# Program: ('program', prog_name_token, var_decls_node, block_node)
# VarDecls: ('var_declarations', [ ('var_declaration', id_list_node, type_node), ... ])
# IdList: ('id_list', [id_token1, id_token2]) or ('ID', id_token)
# TypeNode: e.g., Token('INTEGER', 'INTEGER')
# BlockNode: ('block', [stmt1, stmt2, ...])
# AssignStmt: ('assign', ('ID', var_name_token), expr_node)
# IfStmt: ('if_statement', cond_expr_node, then_block_node, else_block_node_opt)
# WhileStmt: ('while_statement', cond_expr_node, body_block_node)
# WritelnStmt: ('writeln_statement', expr_list_node_or_single_expr_node)
# ExprListNode: ('expr_list', [expr_node1, expr_node2])
# NumberLiteral: ('NUMBER', token)
# StringLiteral: ('STRING_LITERAL', token)
# ID_Expr: ('ID', token)
# BinOpExpr: ('PLUS', left_expr_node, right_expr_node)
