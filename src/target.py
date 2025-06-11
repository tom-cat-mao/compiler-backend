import re

class TargetCodeGenerator:
    def __init__(self, synbl=None, typel=None, ainfl=None): # MODIFIED
        self.assembly_code = []
        self.data_segment_lines = []
        self.code_segment_lines = []
        self.declared_variables = set() # Stores sanitized variable names
        self.string_literals = {}    # Stores original string content -> sanitized data label (e.g., STR1)
        self.label_uid_counter = 0   # For compiler-generated unique labels (e.g., for comparisons)
        self.string_label_counter = 0 # For unique labels for string data

        # Store symbol table information passed from the semantic analyzer
        self.synbl = synbl if synbl is not None else []
        self.typel = typel if typel is not None else []
        self.ainfl = ainfl if ainfl is not None else []

    def _new_uid_label(self, prefix="LBL"):
        self.label_uid_counter += 1
        return f"{prefix}{self.label_uid_counter}"

    def _new_string_label(self):
        self.string_label_counter += 1
        return f"STR{self.string_label_counter}"

    def _sanitize_identifier(self, name):
        name = str(name) # Ensure it's a string
        # Replace any non-alphanumeric or non-underscore character with an underscore
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', name)
        # If the name starts with a digit, or is empty after sanitization, prepend an underscore
        if not sanitized or not (sanitized[0].isalpha() or sanitized[0] == '_'):
            sanitized = '_' + sanitized
        
        # Avoid collision with assembly reserved keywords by appending "_var"
        # This list should be comprehensive for your target assembler (e.g., NASM, MASM)
        reserved_keywords = [
            "MOV", "ADD", "SUB", "MUL", "DIV", "CMP", "JMP", "JE", "JNE", "JG", "JL", "JGE", "JLE", 
            "AX", "BX", "CX", "DX", "SI", "DI", "SP", "BP", "CS", "DS", "ES", "SS",
            "PROC", "ENDP", "DW", "DB", "BYTE", "WORD", "DWORD", "QWORD", "OFFSET",
            "LEA", "CALL", "RET", "INT", "PUSH", "POP", "LOOP", "NEG", "NOT", "AND", "OR", "XOR", "SHL", "SHR",
            "MODEL", "STACK", "DATA", "CODE", "INCLUDE", "END", "IF", "ELSE", "ENDIF", "WHILE", "ENDW", 
            "PRINT_STRING_CUSTOM", "PRINT_NUMBER_CUSTOM", "PRINT_NEWLINE_CUSTOM" # Add own proc names
        ]
        if sanitized.upper() in reserved_keywords:
            sanitized += "_var"
        return sanitized

    def _declare_variable(self, var_name_original): # MODIFIED
        # This function uses symbol table info to declare variables correctly.
        sanitized_name = self._sanitize_identifier(var_name_original)

        if not (isinstance(var_name_original, str) and var_name_original != '_' and not var_name_original.isdigit()):
            return None # Not a declarable variable name

        if sanitized_name in self.declared_variables:
            return sanitized_name # Already declared

        # Try to find the variable in the symbol table (synbl)
        symbol_entry = None
        # Search in synbl for the original variable name
        for entry in self.synbl: # Iterate through the provided synbl
            if entry.get('NAME') == var_name_original and entry.get('CAT') == 'v':
                symbol_entry = entry
                break
        
        declaration_line = None

        if symbol_entry: # If found in synbl, use its type information
            type_ptr = symbol_entry.get('TYPE_PTR')
            if type_ptr is not None and 0 <= type_ptr < len(self.typel):
                type_info = self.typel[type_ptr]
                type_kind = type_info.get('KIND')
                
                if type_kind == 'array':
                    ainfl_ptr = type_info.get('AINFL_PTR')
                    if ainfl_ptr is not None and 0 <= ainfl_ptr < len(self.ainfl):
                        array_details = self.ainfl[ainfl_ptr]
                        num_elements = array_details.get('NUM_ELEMENTS', 1)
                        element_size_bytes = 2 # Default to WORD (DW)
                        # Potentially, you could get element_size from ainfl if stored there
                        # For example: element_typel_ptr = array_details.get('ELEMENT_TYPE_PTR')
                        # if element_typel_ptr is not None and 0 <= element_typel_ptr < len(self.typel):
                        #    element_type_info = self.typel[element_typel_ptr]
                        #    element_size_bytes = element_type_info.get('SIZE', 2)
                        
                        directive = "DW" # Assuming WORD elements for now
                        if num_elements > 0:
                           declaration_line = f"    {sanitized_name} {directive} {num_elements} DUP(?)"
                        else: # Should not happen for valid arrays
                           declaration_line = f"    {sanitized_name} {directive} ?" 
                elif type_kind == 'basic':
                    # basic_size_bytes = type_info.get('SIZE', 2) # Get size from typel
                    # directive = "DW" if basic_size_bytes == 2 else "DB" # Example
                    declaration_line = f"    {sanitized_name} DW ?" # Assuming basic types are WORDs
        
        if not declaration_line:
            # Default for temporaries not found in synbl or if type info is missing/basic
            # This will catch compiler-generated temporaries like t0, t1, etc.
            declaration_line = f"    {sanitized_name} DW ?"

        self.data_segment_lines.append(declaration_line)
        self.declared_variables.add(sanitized_name)
        return sanitized_name

    def _get_operand_assembly_str(self, operand_value, is_code_label_name=False):
        # Formats an operand for use in an assembly instruction.
        # Does NOT declare variables; declaration is handled in the pre-pass.
        if isinstance(operand_value, int):
            return str(int(operand_value)) # Immediate value
        elif isinstance(operand_value, float):
            return str(int(operand_value))
        elif isinstance(operand_value, str):
            if operand_value.isdigit() or (operand_value.startswith('-') and operand_value[1:].isdigit()):
                return operand_value # Immediate number represented as a string
            elif operand_value != '_': # Placeholder for unused operands
                sanitized_name = self._sanitize_identifier(operand_value)
                if is_code_label_name:
                    return sanitized_name # It's a code label name, use directly
                else:
                    # It's a variable identifier; wrap in brackets for memory access
                    return f"[{sanitized_name}]"
        return None # Should not happen for valid operands

    def _load_to_reg(self, reg, operand_val_or_mem_str):
        self.code_segment_lines.append(f"    MOV {reg}, {operand_val_or_mem_str}")

    def generate(self, intermediate_code_tuples):
        self.assembly_code = []
        self.data_segment_lines = ["    ; --- Variables ---"]
        self.code_segment_lines = [
            "MAIN PROC",
            "    MOV AX, @DATA",
            "    MOV DS, AX",
            "    ; --- Program Code ---"
        ]
        self.declared_variables.clear()
        self.string_literals.clear()
        self.label_uid_counter = 0
        self.string_label_counter = 0 
        
        # Operations whose 'res' field is a value to be stored (variable or temp)
        value_producing_ops = {'=', '+', '-', '*', '/', '>', '<', '>=', '<=', '==', '!=', '=[]'} # ADDED '=[]'
        # Operations whose 'res' field is a code label name to be defined
        label_definition_ops = {'lb', 'ie'}
        # Operations whose 'res' field is a code label name used as a jump target
        label_target_ops = {'if', 'do', 'gt', 'el', 'we'}

        # Pre-pass 1: Declare all variables defined in the source program (from SYNBL)
        # This ensures arrays and other user-defined variables get correct sizes.
        for symbol in self.synbl:
            if symbol.get('CAT') == 'v': # Only process variables
                self._declare_variable(symbol['NAME'])

        # Pre-pass 2: Declare remaining temporaries from IR and string literals.
        # Variables already declared in Pre-pass 1 will be skipped by _declare_variable.
        for op, arg1, arg2, res in intermediate_code_tuples:
            # Declare string literals if arg1 of 'write' is a string
            if op == 'write' and isinstance(arg1, str) and not (arg1.isdigit() or (arg1.startswith('-') and arg1[1:].isdigit())):
                potential_var_sanitized = self._sanitize_identifier(arg1)
                if potential_var_sanitized not in self.declared_variables and arg1 not in self.string_literals:
                    str_data_label = self._new_string_label() 
                    self.string_literals[arg1] = str_data_label 
                    # Escape single quotes within the string content for assembly syntax
                    escaped_arg1_content = arg1.replace("'", "''") 
                    self.data_segment_lines.append(f"    {str_data_label} DB '{escaped_arg1_content}', '$'")

            # Declare variables from operands (arg1, arg2) if they are identifiers
            # These will likely be temporaries if not caught by Pre-pass 1
            if isinstance(arg1, str) and arg1 != '_' and not arg1.isdigit():
                if not (op == 'write' and arg1 in self.string_literals):
                    self._declare_variable(arg1) 
            
            if isinstance(arg2, str) and arg2 != '_' and not arg2.isdigit():
                self._declare_variable(arg2)

            # Declare variable from result (res) if it's an identifier AND op produces a value in 'res'
            if isinstance(res, str) and res != '_' and not res.isdigit():
                if op in value_producing_ops:
                    self._declare_variable(res)
        
        # Main generation pass: Convert IR to assembly lines
        for op, arg1, arg2, res in intermediate_code_tuples:
            self.code_segment_lines.append(f"    ; {op}, {arg1}, {arg2}, {res}")

            # Determine if 'res' for this op is a code label name (either for definition or target)
            res_is_code_label_name = (op in label_definition_ops or op in label_target_ops)
            
            arg1_asm = self._get_operand_assembly_str(arg1, is_code_label_name=False)
            arg2_asm = self._get_operand_assembly_str(arg2, is_code_label_name=False)
            res_asm = self._get_operand_assembly_str(res, is_code_label_name=res_is_code_label_name)

            if op == '=': # Assignment
                if arg1_asm and res_asm:
                    self._load_to_reg("AX", arg1_asm)
                    self.code_segment_lines.append(f"    MOV {res_asm}, AX")
            elif op in ['+', '-', '*', '/']: # Arithmetic
                if arg1_asm: self._load_to_reg("AX", arg1_asm)
                arg2_for_op = arg2_asm
                if op in ['*', '/'] and arg2_asm and not arg2_asm.startswith('['):
                    self._load_to_reg("BX", arg2_asm)
                    arg2_for_op = "BX"
                if op == '+':
                    if arg2_for_op: self.code_segment_lines.append(f"    ADD AX, {arg2_for_op}")
                elif op == '-':
                    if arg2_for_op: self.code_segment_lines.append(f"    SUB AX, {arg2_for_op}")
                elif op == '*':
                    if arg2_for_op:
                        if arg2_for_op != "BX": self._load_to_reg("BX", arg2_for_op)
                        self.code_segment_lines.append(f"    MUL BX")
                elif op == '/':
                    self.code_segment_lines.append(f"    MOV DX, 0")
                    if arg2_for_op:
                        if arg2_for_op != "BX": self._load_to_reg("BX", arg2_for_op)
                        self.code_segment_lines.append(f"    DIV BX")
                if res_asm: self.code_segment_lines.append(f"    MOV {res_asm}, AX")

            elif op in ['>', '<', '>=', '<=', '==', '!=']: # Relational ops
                # Note: IR uses '=' for comparison, which is fine if distinct from assignment '='
                if arg1_asm: self._load_to_reg("AX", arg1_asm)
                if arg2_asm:
                    if arg2_asm.startswith('['): 
                        self._load_to_reg("BX", arg2_asm)
                        self.code_segment_lines.append(f"    CMP AX, BX")
                    else: 
                        self.code_segment_lines.append(f"    CMP AX, {arg2_asm}")
                true_lbl = self._new_uid_label("TRUE") # Compiler-generated label
                end_lbl = self._new_uid_label("ENDCMP") # Compiler-generated label
                jump_op_code = ""
                if op == '>': jump_op_code = "JG"
                elif op == '<': jump_op_code = "JL"
                elif op == '>=': jump_op_code = "JGE"
                elif op == '<=': jump_op_code = "JLE"
                elif op == '==' or op == '=': jump_op_code = "JE" 
                elif op == '!=': jump_op_code = "JNE"
                self.code_segment_lines.append(f"    {jump_op_code} {true_lbl}")
                self.code_segment_lines.append(f"    MOV AX, 0    ; False")
                self.code_segment_lines.append(f"    JMP {end_lbl}")
                self.code_segment_lines.append(f"{true_lbl}:")
                self.code_segment_lines.append(f"    MOV AX, 1    ; True (boolean)")
                self.code_segment_lines.append(f"{end_lbl}:")
                if res_asm: self.code_segment_lines.append(f"    MOV {res_asm}, AX")

            elif op == 'lb' or op == 'ie': # Label definition (lb or if-end)
                if res_asm: # res_asm is the sanitized label name
                    self.code_segment_lines.append(f"{res_asm}:")
            
            elif op == 'gt' or op == 'el' or op == 'we': # Unconditional Jump
                if res_asm: # res_asm is the sanitized target label name
                    self.code_segment_lines.append(f"    JMP {res_asm}")
            
            elif op == 'if': # (if cond_var, _, FalseTargetLabel)
                if arg1_asm: self._load_to_reg("AX", arg1_asm) # Load condition result
                self.code_segment_lines.append(f"    CMP AX, 0")  # Check if false (0)
                if res_asm: # res_asm is the sanitized target label name for the false path
                    self.code_segment_lines.append(f"    JE {res_asm}") 
            
            elif op == 'do': # (do cond_var, _, FalseTargetLabelForLoopExit)
                if arg1_asm: self._load_to_reg("AX", arg1_asm) # Load condition result
                self.code_segment_lines.append(f"    CMP AX, 0")  # Check if false (0)
                if res_asm: # res_asm is the sanitized target label name for loop exit
                    self.code_segment_lines.append(f"    JE {res_asm}")

            elif op == 'write':
                if arg1 in self.string_literals: 
                    str_data_label = self.string_literals[arg1]
                    self.code_segment_lines.append(f"    LEA DX, {str_data_label}")
                    self.code_segment_lines.append(f"    CALL PRINT_STRING_CUSTOM")
                elif arg1_asm: 
                    self._load_to_reg("AX", arg1_asm)
                    self.code_segment_lines.append(f"    CALL PRINT_NUMBER_CUSTOM")
                self.code_segment_lines.append(f"    CALL PRINT_NEWLINE_CUSTOM")
            
            elif op == 'wh': # While-head marker
                self.code_segment_lines.append(f"    ; While head marker (wh)")
            
            elif op == '[]=': # Array store: array_name[index] = value
                              # IR: ('[]=', value, index, array_name)
                # arg1_asm is value, arg2_asm is index, res_asm is array_name
                if arg1_asm and arg2_asm and res_asm:
                    # Load value to store into AX
                    self._load_to_reg("AX", arg1_asm) # AX = value
                    
                    # Load index into SI
                    self._load_to_reg("SI", arg2_asm) # SI = index
                    
                    # Assuming 1-based indexing and WORD elements (2 bytes)
                    self.code_segment_lines.append(f"    DEC SI")       # Adjust for 0-based: SI = index - 1
                    self.code_segment_lines.append(f"    SHL SI, 1")    # SI = (index - 1) * 2 (byte offset)
                    
                    # Get base address of array into BX
                    # res_asm for array_name will be like '[myArray_var]', we need 'myArray_var' for LEA
                    array_base_name = res.strip('[]') # Get 'myArray_var' from '[myArray_var]'
                    sanitized_array_base_name = self._sanitize_identifier(array_base_name)
                    self.code_segment_lines.append(f"    LEA BX, {sanitized_array_base_name}") # BX = address of array
                    
                    # Store value: MOV [BX+SI], AX
                    self.code_segment_lines.append(f"    MOV [BX+SI], AX")
                else:
                    self.code_segment_lines.append(f"    ; Error generating []= for {arg1}, {arg2}, {res}")

            elif op == '=[]': # Array fetch: result_temp = array_name[index]
                              # IR: ('=[]', array_name, index, result_temp)
                # arg1_asm is array_name, arg2_asm is index, res_asm is result_temp
                if arg1_asm and arg2_asm and res_asm:
                    # Load index into SI
                    self._load_to_reg("SI", arg2_asm) # SI = index

                    # Assuming 1-based indexing and WORD elements (2 bytes)
                    self.code_segment_lines.append(f"    DEC SI")       # Adjust for 0-based: SI = index - 1
                    self.code_segment_lines.append(f"    SHL SI, 1")    # SI = (index - 1) * 2 (byte offset)

                    # Get base address of array into BX
                    # arg1_asm for array_name will be like '[myArray_var]'
                    array_base_name = arg1.strip('[]') 
                    sanitized_array_base_name = self._sanitize_identifier(array_base_name)
                    self.code_segment_lines.append(f"    LEA BX, {sanitized_array_base_name}") # BX = address of array

                    # Fetch value: MOV AX, [BX+SI]
                    self.code_segment_lines.append(f"    MOV AX, [BX+SI]")
                    
                    # Store in result_temp
                    self.code_segment_lines.append(f"    MOV {res_asm}, AX") # result_temp = AX
                else:
                    self.code_segment_lines.append(f"    ; Error generating =[] for {arg1}, {arg2}, {res}")
            
            else: 
                self.code_segment_lines.append(f"    ; TODO: Unhandled op: {op} {arg1} {arg2} {res}")

        # Add program termination code INSIDE MAIN PROC, BEFORE MAIN ENDP
        self.code_segment_lines.append("    ; --- End Program ---")
        self.code_segment_lines.append("    MOV AH, 4CH")
        self.code_segment_lines.append("    INT 21H")
        self.code_segment_lines.append("MAIN ENDP")

        # Assemble the full program structure
        self.assembly_code.append(".MODEL SMALL")
        self.assembly_code.append(".STACK 100H")
        self.assembly_code.append(".DATA")
        unique_data_lines = []
        seen_data_content = set()
        for line in self.data_segment_lines:
            if line.strip() not in seen_data_content:
                unique_data_lines.append(line)
                seen_data_content.add(line.strip())
        self.assembly_code.extend(unique_data_lines)
        
        self.assembly_code.append(".CODE")
        self.assembly_code.extend(self.code_segment_lines)

        # Add custom printing procedures AFTER MAIN ENDP
        self.assembly_code.append("")
        self.assembly_code.append("; --- Custom Print String Procedure ---")
        self.assembly_code.append("PRINT_STRING_CUSTOM PROC")
        self.assembly_code.append("    PUSH AX")
        self.assembly_code.append("    PUSH SI")
        self.assembly_code.append("    MOV SI, DX      ; DX should hold the address of the string")
        self.assembly_code.append("PRINT_STRING_LOOP:")
        self.assembly_code.append("    MOV AL, [SI]")
        self.assembly_code.append("    CMP AL, '$'     ; Check for string terminator")
        self.assembly_code.append("    JE PRINT_STRING_END")
        self.assembly_code.append("    MOV AH, 02h     ; Function to display character")
        self.assembly_code.append("    MOV DL, AL      ; Character to display")
        self.assembly_code.append("    INT 21h")
        self.assembly_code.append("    INC SI")
        self.assembly_code.append("    JMP PRINT_STRING_LOOP")
        self.assembly_code.append("PRINT_STRING_END:")
        self.assembly_code.append("    POP SI")
        self.assembly_code.append("    POP AX")
        self.assembly_code.append("    RET")
        self.assembly_code.append("PRINT_STRING_CUSTOM ENDP")
        self.assembly_code.append("")
        self.assembly_code.append("; --- Custom Print Newline Procedure ---")
        self.assembly_code.append("PRINT_NEWLINE_CUSTOM PROC")
        self.assembly_code.append("    PUSH AX")
        self.assembly_code.append("    PUSH DX")
        self.assembly_code.append("    MOV AH, 02h")
        self.assembly_code.append("    MOV DL, 0DH     ; Carriage Return")
        self.assembly_code.append("    INT 21h")
        self.assembly_code.append("    MOV DL, 0AH     ; Line Feed")
        self.assembly_code.append("    INT 21h")
        self.assembly_code.append("    POP DX")
        self.assembly_code.append("    POP AX")
        self.assembly_code.append("    RET")
        self.assembly_code.append("PRINT_NEWLINE_CUSTOM ENDP")
        self.assembly_code.append("")
        self.assembly_code.append("; --- Custom Print Number Procedure (Signed Word in AX) ---")
        self.assembly_code.append("PRINT_NUMBER_CUSTOM PROC")
        self.assembly_code.append("    PUSH AX")
        self.assembly_code.append("    PUSH BX")
        self.assembly_code.append("    PUSH CX")
        self.assembly_code.append("    PUSH DX")
        self.assembly_code.append("    PUSH SI")
        self.assembly_code.append("    CMP AX, 0")
        self.assembly_code.append("    JGE PRINT_NUM_POSITIVE")
        self.assembly_code.append("    PUSH AX")
        self.assembly_code.append("    MOV AH, 02h")
        self.assembly_code.append("    MOV DL, '-'")
        self.assembly_code.append("    INT 21h")
        self.assembly_code.append("    POP AX")
        self.assembly_code.append("    NEG AX")
        self.assembly_code.append("PRINT_NUM_POSITIVE:")
        self.assembly_code.append("    MOV CX, 0")
        self.assembly_code.append("    MOV BX, 10")
        self.assembly_code.append("PRINT_NUM_DIVLOOP:")
        self.assembly_code.append("    MOV DX, 0")
        self.assembly_code.append("    DIV BX")
        self.assembly_code.append("    PUSH DX")
        self.assembly_code.append("    INC CX")
        self.assembly_code.append("    CMP AX, 0")
        self.assembly_code.append("    JNE PRINT_NUM_DIVLOOP")
        self.assembly_code.append("PRINT_NUM_PRINTLOOP:")
        self.assembly_code.append("    POP DX")
        self.assembly_code.append("    ADD DL, '0'")
        self.assembly_code.append("    MOV AH, 02h")
        self.assembly_code.append("    INT 21h")
        self.assembly_code.append("    LOOP PRINT_NUM_PRINTLOOP")
        self.assembly_code.append("    POP SI")
        self.assembly_code.append("    POP DX")
        self.assembly_code.append("    POP CX")
        self.assembly_code.append("    POP BX")
        self.assembly_code.append("    POP AX")
        self.assembly_code.append("    RET")
        self.assembly_code.append("PRINT_NUMBER_CUSTOM ENDP")
        self.assembly_code.append("")
        
        self.assembly_code.append("END MAIN")

        return self.assembly_code

if __name__ == '__main__':
    # Sample IR based on the new intermediate.py logic
    sample_intermediate_code_new = [
        # total = 5 + 3
        ('=', 5, '_', 't0'),       # Assuming expression 5 is simplified to t0 = 5
        ('=', 3, '_', 't1'),       # Assuming expression 3 is simplified to t1 = 3
        ('+', 't0', 't1', 't2'),    # t2 = t0 + t1
        ('=', 't2', '_', 'total'),  # total = t2

        # isPositive = 10 > 0
        ('=', 10, '_', 't3'),
        ('=', 0, '_', 't4'),
        ('>', 't3', 't4', 'isPositive'), # isPositive gets boolean result (0 or 1)

        # counter = 10
        ('=', 10, '_', 'counter'),

        # while (counter > 0)
        ('wh', '_', '_', '_'),          # While head marker
        ('lb', '_', '_', 'L0'),         # Label for condition evaluation
        ('=', 0, '_', 't5'),           # Temp for 0
        ('>', 'counter', 't5', 't6'),  # t6 = counter > 0
        ('do', 't6', '_', 'L1'),        # If t6 is false, jump to L1 (loop exit)
        
        # Loop body:
        # total = total + counter
        ('+', 'total', 'counter', 't7'),
        ('=', 't7', '_', 'total'),
        # counter = counter - 1
        ('=', 1, '_', 't8'),
        ('-', 'counter', 't8', 't9'),
        ('=', 't9', '_', 'counter'),
        
        ('we', '_', '_', 'L0'),         # Jump back to condition L0
        ('lb', '_', '_', 'L1'),         # Label for loop exit

        # if (isPositive) then ... else ...
        # (if, isPositive, '_', L_ELSE_LABEL_FOR_FALSE_PATH)
        ('if', 'isPositive', '_', 'L3'), # If isPositive is false, jump to L3 (else part)
        
        # Then part:
        ('write', "Total is: ", '_', '_'),
        ('write', 'total', '_', '_'),
        ('el', '_', '_', 'L2'),         # Unconditional jump to end_if (L2)
        
        # Else part:
        ('lb', '_', '_', 'L3'),         # Label for else part
        ('write', "Counter was not positive", '_', '_'),
        # Fall through to L2 (end_if label)
        
        ('ie', '_', '_', 'L2')          # Label definition for end_if
    ]

    generator = TargetCodeGenerator()
    target_asm_code = generator.generate(sample_intermediate_code_new)
    
    print("\n--- Generated 8086 Assembly (with custom print, new IR) ---")
    for line in target_asm_code:
        print(line)

    # To test with ML.EXE, save the output to a .asm file, then:
    # ML.EXE /c yourfile.asm
    # LINK.EXE yourfile.obj;
    # (You might need to set up your environment for ML.EXE and LINK.EXE, e.g., via a VS Developer Command Prompt)
    # For emu8086, ensure 'emu8086.inc' is in the same directory or a known include path.
