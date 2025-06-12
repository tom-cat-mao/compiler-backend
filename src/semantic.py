# Define constants for stack frame layout
LINKAGE_SIZE = 3 # Slots for Static Link, Dynamic Link, Return Address
METADATA_SLOTS_BEFORE_PARAMS = 1 # Additional slots before parameters (e.g., for param count, return value space)
PARAMS_BASE_OFFSET = LINKAGE_SIZE + METADATA_SLOTS_BEFORE_PARAMS # Parameters start at this offset (e.g., 4)

class SemanticAnalyzer:
    def __init__(self):
        self.synbl = []
        self.typel = []
        self.pfinfl = []
        self.ainfl = []
        self.consl = []

        # Define sizes for basic types
        self.type_sizes = {
            "INTEGER": 4,
            "REAL": 8,
            "BOOLEAN": 1,
            "CHAR": 1
            # Add other basic types if any
        }

        self.current_level = 0
        self.scope_id_counter = 0
        self.current_scope_id = self.scope_id_counter
        
        # Scope stack: (level, scope_id, next_available_offset_in_scope)
        # Global scope's first variable offset will start from PARAMS_BASE_OFFSET
        self.scope_stack = [(self.current_level, self.current_scope_id, PARAMS_BASE_OFFSET)] 
        
        self._initialize_basic_types()

    def _initialize_basic_types(self):
        self._ensure_basic_type("INTEGER")
        self._ensure_basic_type("REAL")
        self._ensure_basic_type("BOOLEAN")
        self._ensure_basic_type("CHAR")
        # Add any other predefined types here

    def _ensure_basic_type(self, type_name):
        type_name_upper = type_name.upper()
        for i, t_entry in enumerate(self.typel):
            if t_entry.get('KIND') == 'basic' and t_entry.get('NAME') == type_name_upper:
                return i # Return existing TYPEL index
        
        size = self.type_sizes.get(type_name_upper)
        if size is None:
            raise ValueError(f"Size not defined for basic type: {type_name_upper}")

        typel_entry = {'KIND': 'basic', 'NAME': type_name_upper, 'SIZE': size}
        self.typel.append(typel_entry)
        return len(self.typel) - 1
    
    def _resolve_type_name_to_ptr(self, type_name_str):
        """Resolves a type name (string) to a TYPEL pointer. Handles basic and declared types."""
        type_name_upper = type_name_str.upper()
        # Check basic types first
        for i, t_entry in enumerate(self.typel):
            if t_entry.get('KIND') == 'basic' and t_entry.get('NAME') == type_name_upper:
                return i
        # Check user-defined types
        type_symbol = self.lookup_symbol(type_name_str, category_filter='t')
        if type_symbol:
            return type_symbol['TYPE_PTR']
        raise ValueError(f"Type '{type_name_str}' not found.")

    def enter_scope(self, scope_type="block"): # Add scope_type if needed for different offset rules
        self.current_level += 1
        self.scope_id_counter += 1
        self.current_scope_id = self.scope_id_counter
        # For new scopes (e.g., procedures), offset might start from 0 (for locals)
        # or after parameters (e.g., PARAMS_BASE_OFFSET).
        # For simple nested blocks, it might continue or reset.
        # For now, let's assume a new local scope starts its own offset count from 0.
        # This needs refinement if/when procedures/functions with parameters are added.
        initial_offset_for_new_scope = 0
        if scope_type == "procedure_or_function": # Example
             initial_offset_for_new_scope = PARAMS_BASE_OFFSET # If locals start after params/linkage
        
        self.scope_stack.append((self.current_level, self.current_scope_id, initial_offset_for_new_scope))

    def exit_scope(self):
        """Exit the current scope."""
        if len(self.scope_stack) > 1:
            exiting_level, exiting_scope_id, _ = self.scope_stack.pop()
            # print(f"Exited scope: Level {exiting_level}, ID {exiting_scope_id}")
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

    def _add_array_type_to_typel(self, element_type_ptr, lower_bound, upper_bound):
        if not (0 <= element_type_ptr < len(self.typel)):
            raise ValueError(f"Invalid element_type_ptr {element_type_ptr} for array.")
        
        element_type_info = self.typel[element_type_ptr]
        element_size = element_type_info.get('SIZE')
        if element_size is None:
            raise ValueError(f"Element type {self.get_type_name_from_ptr(element_type_ptr)} for array has no defined size.")

        num_elements = upper_bound - lower_bound + 1
        if num_elements <= 0:
            raise ValueError(f"Array must have a positive number of elements. Bounds: {lower_bound}..{upper_bound}")
        
        array_total_size = num_elements * element_size

        # Optional: Check if an identical array type (same element type, bounds, and thus size) already exists in AINFL/TYPEL
        for i, typel_entry in enumerate(self.typel):
            if typel_entry.get('KIND') == 'array' and typel_entry.get('SIZE') == array_total_size:
                ainfl_ptr_candidate = typel_entry.get('AINFL_PTR')
                if 0 <= ainfl_ptr_candidate < len(self.ainfl):
                    existing_ainfl = self.ainfl[ainfl_ptr_candidate]
                    if (existing_ainfl.get('ELEMENT_TYPE_PTR') == element_type_ptr and
                        existing_ainfl.get('LOWER_BOUND') == lower_bound and
                        existing_ainfl.get('UPPER_BOUND') == upper_bound and
                        existing_ainfl.get('NUM_ELEMENTS') == num_elements and 
                        existing_ainfl.get('ELEMENT_SIZE') == element_size and
                        existing_ainfl.get('TOTAL_SIZE') == array_total_size): # Also check total size in AINFL
                        return i # Return existing TYPEL index

        ainfl_entry = {
            'ELEMENT_TYPE_PTR': element_type_ptr,
            'LOWER_BOUND': lower_bound,
            'UPPER_BOUND': upper_bound,
            'NUM_ELEMENTS': num_elements,
            'ELEMENT_SIZE': element_size,
            'TOTAL_SIZE': array_total_size # Store total size directly in AINFL
        }
        self.ainfl.append(ainfl_entry)
        ainfl_ptr = len(self.ainfl) - 1

        typel_entry = {'KIND': 'array', 'AINFL_PTR': ainfl_ptr, 'SIZE': array_total_size}
        self.typel.append(typel_entry)
        return len(self.typel) - 1

    def _resolve_type_ast_node_to_ptr(self, type_ast_node):
        """
        Resolves a type AST node (from parser) to a TYPEL pointer.
        Handles basic type names (strings) and array_type tuples.
        """
        if isinstance(type_ast_node, str): # e.g. 'INTEGER'
            return self._resolve_type_name_to_ptr(type_ast_node) # Existing method for name resolution
        elif isinstance(type_ast_node, tuple) and type_ast_node[0] == 'array_type':
            # type_ast_node is ('array_type', low_bound_node, high_bound_node, base_type_ast_node_for_element)
            low_bound_node = type_ast_node[1]
            high_bound_node = type_ast_node[2]
            base_type_ast_node_for_element = type_ast_node[3]

            if not (isinstance(low_bound_node, tuple) and low_bound_node[0] == 'NUMBER' and
                    isinstance(high_bound_node, tuple) and high_bound_node[0] == 'NUMBER'):
                raise ValueError(f"Array bounds must be number literals. Got {low_bound_node}, {high_bound_node}")
            
            lower_bound = low_bound_node[1] # e.g., 1 from ('NUMBER', 1)
            upper_bound = high_bound_node[1] # e.g., 5 from ('NUMBER', 5)

            if not isinstance(lower_bound, int) or not isinstance(upper_bound, int):
                raise ValueError(f"Array bounds must be integers. Got {lower_bound}, {upper_bound}")
            if lower_bound > upper_bound:
                raise ValueError(f"Array lower bound {lower_bound} cannot be greater than upper bound {upper_bound}.")

            # Recursively resolve the element's type AST node to get its type_ptr
            element_type_ptr = self._resolve_type_ast_node_to_ptr(base_type_ast_node_for_element)
            
            # num_elements = upper_bound - lower_bound + 1 # Calculated in _add_array_type_to_typel

            # Optional: Check if an identical array type already exists in TYPEL to avoid duplicates
            # This check is now more robustly handled within _add_array_type_to_typel
            return self._add_array_type_to_typel(element_type_ptr, lower_bound, upper_bound)
        else:
            raise ValueError(f"Unsupported type AST node structure for resolution: {type_ast_node}")

    def _add_constant_to_consl(self, value, type_ptr):
        """Adds a constant to CONSL and returns its index."""
        # Could add check for existing identical constant to reuse
        self.consl.append({'VALUE': value, 'TYPE_PTR': type_ptr})
        return len(self.consl) - 1



    def declare_symbol(self, name, category, type_name_or_struct, details=None):
        current_level, current_scope_id, current_next_offset = self.scope_stack[-1]

        for entry in self.synbl:
            if entry['NAME'] == name and entry['LEVEL'] == current_level and entry['SCOPE_ID'] == current_scope_id:
                raise ValueError(f"Symbol '{name}' already declared in scope (L{current_level}, S{current_scope_id})")

        type_ptr = -1
        var_size = 0 # Size of this specific variable/constant/type

        if category in ['v', 'c', 'p_val', 'p_ref'] or \
           (category == 'f' and type_name_or_struct is not None):
            if isinstance(type_name_or_struct, str):
                type_ptr = self._resolve_type_name_to_ptr(type_name_or_struct)
            elif isinstance(type_name_or_struct, int): 
                if 0 <= type_name_or_struct < len(self.typel):
                    type_ptr = type_name_or_struct
                else:
                    raise ValueError(f"Invalid type_ptr {type_name_or_struct} passed for '{name}'.")
            else:
                raise ValueError(f"Unsupported type information for '{name}' (category '{category}'): {type_name_or_struct}. Expected type name string or type_ptr int.")
            
            if 0 <= type_ptr < len(self.typel):
                var_size = self.typel[type_ptr].get('SIZE', 0) # Get size from TYPEL
            elif category == 'c' and details and 'value' in details: # For constants, size might depend on literal type if not explicitly typed
                if isinstance(details['value'], int): var_size = self.type_sizes['INTEGER']
                elif isinstance(details['value'], float): var_size = self.type_sizes['REAL']
                elif isinstance(details['value'], bool): var_size = self.type_sizes['BOOLEAN']
                elif isinstance(details['value'], str) and len(details['value']) == 1 : var_size = self.type_sizes['CHAR']
                # String literals would need more complex size handling if stored directly
        
        elif category == 't': # Actual Type definition (e.g. type MyArr = array...)
            type_ptr = self._resolve_type_ast_node_to_ptr(type_name_or_struct)
            if 0 <= type_ptr < len(self.typel): # The "size" of a type definition itself is its defined size
                var_size = self.typel[type_ptr].get('SIZE', 0)
        elif category == 'program_name' or (category == 'f' and type_name_or_struct is None): # Procedure
            type_ptr = -1 
            var_size = 0 # No direct data size for program name or procedure symbol itself
        else:
            raise ValueError(f"Unhandled category '{category}' or type_name_or_struct '{type_name_or_struct}' combination for type resolution in declare_symbol for '{name}'.")

        # ADDR_PTR calculation (offset within the current scope/activation record)
        addr_ptr_value = None # Default for symbols that don't have a direct memory offset (like type names, program name)
        
        if category in ['v', 'p_val', 'p_ref']: # Variables and parameters get a (level, offset)
            # current_next_offset is the starting offset for this symbol in the current scope
            # current_level is the static nesting level
            addr_ptr_value = (current_level, current_next_offset) 
            
            new_next_offset_for_scope = current_next_offset + var_size # Calculate the next available offset
            
            # Update the current scope's next available offset on the stack
            self.scope_stack[-1] = (current_level, current_scope_id, new_next_offset_for_scope)
        elif category == 'c': # Constants might point to CONSL or have a value directly
            if details and 'CONSL_PTR' in details:
                addr_ptr_value = details['CONSL_PTR'] # Or some other representation
            # else, addr_ptr_value remains None if constant value is embedded or not stored with an "address"
        # For 't' (type definitions), 'program_name', 'f' (functions/procedures themselves),
        # ADDR_PTR might be None or point to TYPEL/PFINFL.
        # For now, addr_ptr_value remains None if not 'v', 'p_val', or 'p_ref' unless specified (e.g. for constants).


        synbl_entry = {
            'NAME': name,
            'CAT': category,
            'TYPE_PTR': type_ptr,
            'LEVEL': current_level,
            'SCOPE_ID': current_scope_id,
            'ADDR_PTR': addr_ptr_value, # Storing (level, offset) for vars/params, or other info
            'SIZE': var_size, 
            'INITIALIZED': False 
        }
        self.synbl.append(synbl_entry)
        # print(f"Declared: {new_symbol}") # This was 'new_symbol', should be 'synbl_entry' if uncommented
        return synbl_entry


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
        var_symbol = self.lookup_symbol(var_name, category_filter='v') 
        if not var_symbol: 
            var_symbol = self.lookup_symbol(var_name, category_filter='p_val')
        if not var_symbol:
            var_symbol = self.lookup_symbol(var_name, category_filter='p_ref')
        if not var_symbol: # Add check for category 't'
            var_symbol = self.lookup_symbol(var_name, category_filter='t')

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
            prog_name_node = ast[1] # This is what the parser provides for the program name
            
            actual_prog_name_str = ""
            if isinstance(prog_name_node, str): # If parser gives a direct string
                actual_prog_name_str = prog_name_node
            elif hasattr(prog_name_node, 'value'): # If it's a PLY LexToken or similar object
                actual_prog_name_str = prog_name_node.value
            elif isinstance(prog_name_node, tuple) and len(prog_name_node) > 0: # If it's like ('ID', 'ProgName')
                actual_prog_name_str = prog_name_node[0] # Or prog_name_node[1] depending on your AST
                # Check the actual structure of prog_name_node from your parser
                # For instance, if it's ('PROG_ID_TOKEN_TYPE', 'ActualName'), then ast[1][1] might be it.
                # Let's assume for now your parser puts the string name directly or in .value
                # If it's a simple string from the parser, this 'if/elif' is overkill.
                # For example, if parser gives ('program', 'MyProgram', ...), then ast[1] is 'MyProgram'
                # If parser gives ('program', ('ID', 'MyProgram'), ...), then ast[1][1] is 'MyProgram'

            # Ensure actual_prog_name_str is a string before calling declare_symbol
            if not isinstance(actual_prog_name_str, str) or not actual_prog_name_str:
                # Handle error: program name couldn't be extracted as a string
                # This might happen if ast[1] is not what's expected.
                # For now, let's assume ast[1] IS the string name if the above doesn't fit.
                if isinstance(ast[1], str): # Defaulting to ast[1] if it's a string
                    actual_prog_name_str = ast[1]
                else:
                    # This is a fallback, ideally you know the structure from your parser
                    print(f"Warning: Program name token structure not fully handled: {ast[1]}. Attempting to use raw value.")
                    actual_prog_name_str = str(ast[1]) # Fallback, might not be ideal

            self.declare_symbol(actual_prog_name_str, 'program_name', None)

            var_decls_node = ast[2] # Assuming structure ('var_declarations', decls_list) or None
            if var_decls_node and var_decls_node[0] == 'var_declarations':
                self.process_declarations(var_decls_node) # Corrected: Removed the extra 'v' argument

            # Process function/procedure declarations if they are part of AST structure here
            # For now, assuming they might be mixed with statements or in a specific section

            main_block_node = ast[3] # Assuming ('block', statements)
            if main_block_node and main_block_node[0] == 'block':
                 self.analyze_statements(main_block_node[1])
            else: # Simpler structure like ('program', name, var_decls, statements_list)
                self.analyze_statements(ast[3])


    def process_declarations(self, decls_node):
        if decls_node is None or decls_node[0] != 'var_declarations':
            return # No declarations or not a var_declarations node

        decls_list = decls_node[1]
        
        for decl_item in decls_list:
            # AST structure from parser for var decls: ('var', ['identifier_string'], type_ast_node)
            # type_ast_node can be 'integer' or ('array_type', ...)
            if decl_item[0] == 'var': 
                id_list_from_ast = decl_item[1] 
                type_ast_node = decl_item[2] 

                actual_type_ptr = self._resolve_type_ast_node_to_ptr(type_ast_node)

                # All variables declared in a 'var' block will have category 'v'
                category_for_symbol = 'v' 
                
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
                    try:
                        self.declare_symbol(var_name, category_for_symbol, actual_type_ptr) # Use 'v' for all vars
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
            # AST node: ('assign', target_node, expr_node)
            # target_node from parser: ('ID', var_name_str) or ('array_access', array_name_str, index_expr_node)
            
            target_node = stmt_node[1]
            expr_node = stmt_node[2]

            target_actual_name = None # For set_initialized
            target_final_type_ptr = -1

            if target_node[0] == 'ID':
                var_name_str = target_node[1]
                target_actual_name = var_name_str
                var_symbol = self.lookup_symbol(var_name_str)
                if not var_symbol:
                    raise ValueError(f"Variable '{var_name_str}' not declared before assignment.")
                if var_symbol['CAT'] not in ['v', 'p_val', 'p_ref']:
                    raise ValueError(f"Cannot assign to '{var_name_str}' of category '{var_symbol['CAT']}'.")
                target_final_type_ptr = var_symbol['TYPE_PTR']
            elif target_node[0] == 'array_access':
                array_name_str = target_node[1]
                index_expr_node = target_node[2]
                target_actual_name = array_name_str # Mark the base array as initialized

                array_symbol = self.lookup_symbol(array_name_str)
                if not array_symbol:
                    raise ValueError(f"Array '{array_name_str}' not declared before assignment.")
                # Allow 't' if you are using it for array variables that can be assigned to.
                if array_symbol['CAT'] not in ['v', 'p_val', 'p_ref', 't']: 
                    raise ValueError(f"Identifier '{array_name_str}' is not an assignable array (category '{array_symbol['CAT']}').")

                array_type_ptr = array_symbol['TYPE_PTR']
                if not (0 <= array_type_ptr < len(self.typel)) or self.typel[array_type_ptr].get('KIND') != 'array':
                    raise ValueError(f"Identifier '{array_name_str}' is not an array type.")
                
                ainfl_ptr = self.typel[array_type_ptr]['AINFL_PTR']
                ainfl_entry = self.ainfl[ainfl_ptr]
                target_final_type_ptr = ainfl_entry['ELEMENT_TYPE_PTR']

                index_expr_type_ptr = self.get_expression_type_ptr(index_expr_node)
                int_type_ptr = self._ensure_basic_type('INTEGER')
                self.check_type_compatibility(int_type_ptr, index_expr_type_ptr, f"array index for '{array_name_str}'")
            else:
                raise ValueError(f"Invalid target for assignment: {target_node}")

            expr_type_ptr = self.get_expression_type_ptr(expr_node)
            self.check_type_compatibility(target_final_type_ptr, expr_type_ptr, f"assignment to '{target_node[0]}'")
            
            if target_actual_name:
                self.set_initialized(target_actual_name)

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
            # Handle cases where expr_node might already be a type pointer or is invalid
            # This logic might vary based on your implementation details
            # For now, assuming if it's not a tuple, it might be an error or already resolved.
            # The error message implies expr_node *is* a tuple when the error occurs.
            # So, the main issue is likely in the tuple processing below.
            pass # Or raise an error if it's an unexpected non-tuple

        # Assuming expr_node is a tuple, e.g., ('REAL_NUMBER', 3.14) or ('+', left, right)
        node_type = expr_node[0]

        if node_type == 'NUMBER':
            return self._ensure_basic_type('INTEGER')
        elif node_type == 'REAL_NUMBER':  # <<< इंश्योर दिस केस इज प्रेजेंट एंड करेक्ट
            return self._ensure_basic_type('REAL')
        elif node_type == 'CHAR_LITERAL': 
            return self._ensure_basic_type('CHAR')
        elif node_type == 'STRING_LITERAL':
            return self._ensure_basic_type('STRING')
        elif node_type == 'BOOLEAN_LITERAL':
            return self._ensure_basic_type('BOOLEAN')
        elif node_type == 'ID':
            # ... (your existing ID handling logic) ...
            name = expr_node[1]
            if name.lower() == 'true' or name.lower() == 'false': # Handle true/false if passed as ('ID', 'true')
                return self._ensure_basic_type('BOOLEAN')
            symbol = self.lookup_symbol(name)
            if not symbol:
                raise ValueError(f"Identifier '{name}' not declared.")
            # Example: Mark as initialized if it's a variable being read
            # if symbol['CAT'] in ['v', 'p_val', 'p_ref'] and not symbol.get('INITIALIZED', False):
            #     print(f"Warning: Variable '{name}' used before explicit assignment (in an expression).")
            #     # Optionally, you might not want to mark it initialized here, but rather upon assignment.
            return symbol['TYPE_PTR']
        elif node_type == 'array_access':
            # expr_node is ('array_access', array_name_str, index_expr_node)
            array_name_str = expr_node[1]
            index_expr_node = expr_node[2]

            array_symbol = self.lookup_symbol(array_name_str)
            if not array_symbol:
                raise ValueError(f"Array '{array_name_str}' not declared (in expression).")
            # Allow 't' if you are using it for array variables that can be read from.
            if array_symbol['CAT'] not in ['v', 'p_val', 'p_ref', 't']: 
                raise ValueError(f"Identifier '{array_name_str}' is not an array variable (category '{array_symbol['CAT']}').")
            
            # Check if the array (as a whole) has been initialized.
            # A more granular check would be per-element, which is harder.
            if not array_symbol.get('INITIALIZED', False):
                 print(f"Warning: Array '{array_name_str}' may not have been initialized before its element is accessed.")

            array_type_ptr = array_symbol['TYPE_PTR']
            if not (0 <= array_type_ptr < len(self.typel)) or self.typel[array_type_ptr].get('KIND') != 'array':
                raise ValueError(f"Identifier '{array_name_str}' is not of array type (in expression).")

            ainfl_ptr = self.typel[array_type_ptr]['AINFL_PTR']
            ainfl_entry = self.ainfl[ainfl_ptr]
            element_type_ptr = ainfl_entry['ELEMENT_TYPE_PTR']

            index_expr_type_ptr = self.get_expression_type_ptr(index_expr_node)
            int_type_ptr = self._ensure_basic_type('INTEGER')
            self.check_type_compatibility(int_type_ptr, index_expr_type_ptr, f"array index for '{array_name_str}' in expression")
            
            return element_type_ptr
        elif node_type in ['+', '-', '*', '/', '<', '>', '=', '<=', '>=', '<>', 'and', 'or']: # Binary operators
            # ... (your existing logic for binary operators) ...
            left_expr = expr_node[1]
            right_expr = expr_node[2]
            left_type_ptr = self.get_expression_type_ptr(left_expr)
            right_type_ptr = self.get_expression_type_ptr(right_expr)
            # ... (type checking logic for the operation) ...
            # Example for arithmetic:
            int_type_ptr = self._ensure_basic_type('INTEGER')
            real_type_ptr = self._ensure_basic_type('REAL')
            if node_type in ['+', '-', '*', '/']:
                if not ((left_type_ptr == int_type_ptr or left_type_ptr == real_type_ptr) and \
                        (right_type_ptr == int_type_ptr or right_type_ptr == real_type_ptr)):
                    raise ValueError(f"Arithmetic operation '{node_type}' requires numeric operands.")
                if left_type_ptr == real_type_ptr or right_type_ptr == real_type_ptr:
                    return real_type_ptr
                return int_type_ptr
            # ... (add logic for relational and logical operators) ...
            bool_type_ptr = self._ensure_basic_type('BOOLEAN') # Example for relational/logical
            return bool_type_ptr # Placeholder, replace with actual logic

        elif node_type == 'not': # Unary operator
            # ... (your existing logic for unary not) ...
            operand_expr = expr_node[1]
            operand_type_ptr = self.get_expression_type_ptr(operand_expr)
            bool_type_ptr = self._ensure_basic_type('BOOLEAN')
            if operand_type_ptr != bool_type_ptr:
                raise ValueError(f"'not' operator requires a boolean operand, got {self.get_type_name_from_ptr(operand_type_ptr)}.")
            return bool_type_ptr
        # ... (other existing elif conditions for other node types) ...
        else:
            # This is the fallback that raises the error you're seeing
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
