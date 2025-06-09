import sys
import os # Added for path operations and directory creation
from parser import parse as parse_source, tokens as parser_tokens, reserved as parser_reserved
from semantic import SemanticAnalyzer
from intermediate import IntermediateCodeGenerator
from optimizer import Optimizer # Import the Optimizer class
from target import TargetCodeGenerator # Import the TargetCodeGenerator class

def read_source_file(file_path):
    """Read the source code from a file."""
    with open(file_path, 'r') as file:
        return file.read()

def print_transformed_token_sequence(
    tokens_list,
    keyword_to_pos_map,
    delimiter_symbol_to_pos_map,
    identifier_to_pos_map,
    constant_to_pos_map,
    # These are needed to correctly categorize tokens from the raw token stream
    language_keywords_map, # e.g., {'program': 'PROGRAM', ...} from parser_reserved
    active_delimiter_type_to_symbol_map # e.g., {'SEMICOLON': ';', ...}
):
    """Print the token sequence as (pos, type_code) tuples."""
    print("Token Sequence (pos, type_code):")
    print("---------------------------------")
    if not tokens_list:
        print("No tokens found.")
        print("\n")
        return

    output_sequence = []
    for token in tokens_list:
        pos = -1
        type_code = '?'  # Default for unknown or unhandled

        # Check for Keyword: token.value is the keyword string (e.g., 'program')
        # token.type is its type (e.g., 'PROGRAM')
        if token.value.lower() in language_keywords_map and \
           language_keywords_map[token.value.lower()] == token.type and \
           token.value.lower() in keyword_to_pos_map:
            type_code = 'k'
            pos = keyword_to_pos_map[token.value.lower()]
        # Check for Delimiter: token.type (e.g., 'SEMICOLON'), token.value (e.g., ';')
        elif token.type in active_delimiter_type_to_symbol_map:
            symbol = active_delimiter_type_to_symbol_map[token.type]
            if symbol in delimiter_symbol_to_pos_map:
                type_code = 'd'
                pos = delimiter_symbol_to_pos_map[symbol]
        # Check for Identifier
        elif token.type == 'ID':
            if token.value in identifier_to_pos_map:
                type_code = 'i'
                pos = identifier_to_pos_map[token.value]
        # Check for Constant (Number or String)
        elif token.type == 'NUMBER' or token.type == 'STRING':
            str_val = str(token.value) # Ensure value is string for map lookup
            if str_val in constant_to_pos_map:
                type_code = 'c'
                pos = constant_to_pos_map[str_val]
        
        if pos != -1:
            output_sequence.append(f"({pos},{type_code})")
        else:
            # Fallback for unmapped tokens - should be rare if maps are comprehensive
            output_sequence.append(f"(err:{token.type},{token.value})")

    # Print the sequence, e.g., 10 items per line for better readability
    for i in range(0, len(output_sequence), 10):
        print(" ".join(output_sequence[i:i+10]))
    print("\n")

def print_keyword_delimiter_tables():
    """Print keyword and delimiter tables in a table-like format."""
    print("Keyword Table (k):")
    print("------------------")
    if not parser_reserved:
        print("No keywords defined.")
    else:
        sorted_keywords = sorted(parser_reserved.keys())
        max_idx_len = len(str(len(sorted_keywords)))
        max_keyword_len = max(len(kw) for kw in sorted_keywords) if sorted_keywords else 10
        max_token_len = max(len(parser_reserved[kw]) for kw in sorted_keywords) if sorted_keywords else 10
        
        header_kw = f"{'Pos':<{max_idx_len}} | {'Keyword':<{max_keyword_len}} | {'Token Type':<{max_token_len}}"
        print(header_kw)
        print("-" * len(header_kw))
        for i, keyword in enumerate(sorted_keywords):
            pos = i + 1
            print(f"{str(pos):<{max_idx_len}} | {keyword:<{max_keyword_len}} | {parser_reserved[keyword]:<{max_token_len}}")
    print("\n")

    print("Delimiter Table (d):")
    print("--------------------")
    delimiter_type_to_symbol_map = {
        'SEMICOLON': ';', 'COLON': ':', 'COMMA': ',', 'ASSIGN': ':=', 'DOT': '.',
        'LPAREN': '(', 'RPAREN': ')', 'PLUS': '+', 'MINUS': '-', 'TIMES': '*',
        'DIVIDE': '/', 'LT': '<', 'GT': '>', 'EQ': '=', 'LE': '<=', 'GE': '>='
    }
    active_delimiters = {
        k: v for k, v in delimiter_type_to_symbol_map.items() if k in parser_tokens
    }
    # Sort by symbol for consistent positioning
    sorted_delimiter_symbols = sorted(list(set(active_delimiters.values())))

    if not sorted_delimiter_symbols:
        print("No delimiters defined or found in parser tokens.")
    else:
        max_idx_len = len(str(len(sorted_delimiter_symbols)))
        # Find the longest token type name for a given symbol (could be multiple types for same symbol, though not typical here)
        symbol_to_types = {}
        for token_type, sym in active_delimiters.items():
            if sym not in symbol_to_types:
                symbol_to_types[sym] = []
            symbol_to_types[sym].append(token_type)
        
        max_type_len_delim = max(len(", ".join(symbol_to_types[sym])) for sym in sorted_delimiter_symbols) if sorted_delimiter_symbols else 15
        max_symbol_len_delim = max(len(sym) for sym in sorted_delimiter_symbols) if sorted_delimiter_symbols else 10

        header_delim = f"{'Pos':<{max_idx_len}} | {'Symbol':<{max_symbol_len_delim}} | {'Token Type(s)':<{max_type_len_delim}}"
        print(header_delim)
        print("-" * len(header_delim))
        for i, symbol in enumerate(sorted_delimiter_symbols):
            pos = i + 1
            type_names = ", ".join(symbol_to_types[symbol])
            print(f"{str(pos):<{max_idx_len}} | {symbol:<{max_symbol_len_delim}} | {type_names:<{max_type_len_delim}}")
    print("\n")

def print_identifier_table(tokens_list):
    """Print the identifier table from a list of tokens in a table-like format."""
    identifiers = sorted(list(set(token.value for token in tokens_list if token.type == 'ID')))
    
    print("Identifier Table (i):")
    print("---------------------")
    if not identifiers:
        print("No identifiers found.")
    else:
        max_idx_len = len(str(len(identifiers)))
        max_id_len = max(len(identifier) for identifier in identifiers) if identifiers else 10
        header = f"{'Pos':<{max_idx_len}} | {'Identifier':<{max_id_len}}"
        print(header)
        print("-" * len(header))
        for i, identifier in enumerate(identifiers):
            pos = i + 1
            print(f"{str(pos):<{max_idx_len}} | {identifier:<{max_id_len}}")
    print("\n")

def print_constant_table(tokens_list):
    """Print the constant table from a list of tokens in a table-like format."""
    constants = sorted(list(set(str(token.value) for token in tokens_list if token.type == 'NUMBER' or token.type == 'STRING')))
            
    print("Constant Table (c):")
    print("-------------------")
    if not constants:
        print("No constants found.")
    else:
        max_idx_len = len(str(len(constants)))
        max_const_len = max(len(constant) for constant in constants) if constants else 10
        header = f"{'Pos':<{max_idx_len}} | {'Constant':<{max_const_len}}"
        print(header)
        print("-" * len(header))
        for i, constant in enumerate(constants):
            pos = i + 1
            print(f"{str(pos):<{max_idx_len}} | {constant:<{max_const_len}}")
    print("\n")

def main(file_path):
    source_code = read_source_file(file_path)
    collected_tokens, ast = parse_source(source_code)

    if collected_tokens is None and ast is None:
        print("Failed to tokenize and parse the source code.")
        return

    # --- Prepare maps for the transformed token sequence ---
    # Keyword map: keyword string (lowercase) -> pos
    sorted_keywords_list = sorted(parser_reserved.keys())
    keyword_to_pos = {kw: i + 1 for i, kw in enumerate(sorted_keywords_list)}

    # Delimiter map: symbol string -> pos
    # Also need active_delimiter_type_to_symbol for categorization
    _delimiter_type_to_symbol_map = {
        'SEMICOLON': ';', 'COLON': ':', 'COMMA': ',', 'ASSIGN': ':=', 'DOT': '.',
        'LPAREN': '(', 'RPAREN': ')', 'PLUS': '+', 'MINUS': '-', 'TIMES': '*',
        'DIVIDE': '/', 'LT': '<', 'GT': '>', 'EQ': '=', 'LE': '<=', 'GE': '>='
    }
    active_delimiter_type_to_symbol = {
        k: v for k, v in _delimiter_type_to_symbol_map.items() if k in parser_tokens
    }
    sorted_delimiter_symbols_list = sorted(list(set(active_delimiter_type_to_symbol.values())))
    delimiter_symbol_to_pos = {sym: i + 1 for i, sym in enumerate(sorted_delimiter_symbols_list)}

    # Identifier map: identifier string -> pos
    unique_identifiers_list = sorted(list(set(t.value for t in collected_tokens if t.type == 'ID')))
    identifier_to_pos = {ident: i + 1 for i, ident in enumerate(unique_identifiers_list)}

    # Constant map: constant string value -> pos
    unique_constants_list = sorted(list(set(str(t.value) for t in collected_tokens if t.type == 'NUMBER' or t.type == 'STRING')))
    constant_to_pos = {const_val: i + 1 for i, const_val in enumerate(unique_constants_list)}
    
    # --- Print all tables ---
    # First, print the definition tables that pos refers to
    print_keyword_delimiter_tables()
    print_identifier_table(collected_tokens)
    print_constant_table(collected_tokens)

    # Then, print the transformed token sequence
    print_transformed_token_sequence(
        collected_tokens,
        keyword_to_pos,
        delimiter_symbol_to_pos,
        identifier_to_pos,
        constant_to_pos,
        parser_reserved, # Original map like {'program': 'PROGRAM'}
        active_delimiter_type_to_symbol # Map like {'SEMICOLON': ';'}
    )
    
    if ast is None:
        print("Parsing failed (AST is None). Exiting.")
        return
    
    # Perform semantic analysis
    analyzer = SemanticAnalyzer()
    all_symbol_tables = None # Initialize
    try:
        analyzer.analyze(ast)
        print("Semantic Analysis Complete. Symbol Tables:")
        print("==========================================")
        all_symbol_tables = analyzer.get_symbol_tables_snapshot()
        
        print_synbl(all_symbol_tables.get("SYNBL", []), analyzer) # Pass analyzer for type name resolution
        print_typel(all_symbol_tables.get("TYPEL", []))
        print_pfinfl(all_symbol_tables.get("PFINFL", []), analyzer)
        print_ainfl(all_symbol_tables.get("AINFL", []), analyzer)
        print_consl(all_symbol_tables.get("CONSL", []), analyzer)
        # print_scope_stack(all_symbol_tables.get("SCOPE_STACK_SNAPSHOT", [])) # Optional: for debugging scope

        print("\n")
    except ValueError as e:
        print(f"Semantic Error: {e}")
        return # Stop if semantic errors occur
    
    # Generate intermediate code
    generator = IntermediateCodeGenerator()
    # The IntermediateCodeGenerator might need access to the semantic analyzer 
    # or specific tables for its operations.
    # For now, we assume it can work with the AST or might need an update.
    # If it used the old symbol_table format, this part needs adjustment.
    # Example: generator.set_semantic_analyzer(analyzer) or generator.set_synbl(all_symbol_tables.get("SYNBL"))
    
    code = generator.generate(ast)
    print("Intermediate Code (Four-Tuple Sequence):")
    print("---------------------------------------")
    if not code:
        print("No intermediate code generated.")
    else:        
        # New format: (op, arg1, arg2, res)
        for i, quad in enumerate(code):
            op, arg1, arg2, res = quad
            # Ensure string representations for all parts, especially for None or non-string values
            op_str = str(op)
            arg1_str = str(arg1)
            arg2_str = str(arg2)
            res_str = str(res)
            print(f"({op_str}, {arg1_str}, {arg2_str}, {res_str})")
            
    print("\n")

    # Optimize the intermediate code
    optimizer = Optimizer()
    optimized_code = optimizer.optimize(code) # Pass the original code
    print("Optimized Intermediate Code (Four-Tuple Sequence):")
    print("-------------------------------------------------")
    if not optimized_code:
        print("No optimized code generated (or code was empty).")
    else:
        for i, quad in enumerate(optimized_code):
            op, arg1, arg2, res = quad
            op_str = str(op)
            arg1_str = str(arg1)
            arg2_str = str(arg2)
            res_str = str(res)
            print(f"({op_str}, {arg1_str}, {arg2_str}, {res_str})")
    print("\n")

    # Generate Target Code (Assembly)
    if optimized_code: # Proceed only if there's optimized code
        target_generator = TargetCodeGenerator()
        assembly_code_lines = target_generator.generate(optimized_code)
        
        # Define the result directory
        result_dir = "result"
        if not os.path.exists(result_dir):
            os.makedirs(result_dir)
            print(f"Created directory: {result_dir}")

        # Determine output filename
        base_filename = os.path.splitext(os.path.basename(file_path))[0]
        asm_filename = f"{base_filename}.asm"
        output_asm_path = os.path.join(result_dir, asm_filename)

        try:
            with open(output_asm_path, 'w') as asm_file:
                for line in assembly_code_lines:
                    asm_file.write(line + "\n")
            print(f"Target assembly code saved to: {output_asm_path}")
        except IOError as e:
            print(f"Error writing assembly file {output_asm_path}: {e}")
    else:
        print("Skipping target code generation as optimized code is empty.")
    print("\n")


def print_synbl(synbl, analyzer_instance): # analyzer_instance might not be needed if type name is removed
    print("\nSYNBL (Symbol Table):")
    print("---------------------")
    if not synbl:
        print("SYNBL is empty.")
        return
    # Updated header to only include Idx, Name, Cat, Addr/Info
    header = f"{'Idx':<3} | {'Name':<15} | {'Cat':<5} | {'Addr/Info':<20}"
    print(header)
    print("-" * len(header))
    for i, entry in enumerate(synbl):
        # type_name = analyzer_instance.get_type_name_from_ptr(entry.get('TYPE_PTR', -1)) # Type is removed
        addr_info_str = str(entry.get('ADDR_PTR')) # Default ADDR_PTR
        
        # Logic for specific categories for Addr/Info
        cat = entry.get('CAT')
        addr_ptr = entry.get('ADDR_PTR')

        if cat == 'f' and isinstance(addr_ptr, int):
            addr_info_str = f"PFINFL_IDX:{addr_ptr}"
        elif cat == 'c' and isinstance(addr_ptr, int):
            addr_info_str = f"CONSL_IDX:{addr_ptr}"
        elif cat in ['v', 'p_val', 'p_ref']: # For variables and parameters, ADDR_PTR is usually offset or address
            addr_info_str = str(addr_ptr if addr_ptr is not None else "N/A")
        elif cat == 'program_name' or cat == 't': # Program name or type name might not have a typical ADDR_PTR
            addr_info_str = "N/A"


        # Updated print statement to match the new header
        print(f"{i:<3} | {str(entry.get('NAME')):<15} | {str(cat):<5} | {addr_info_str:<20}")

def print_typel(typel):
    print("\nTYPEL (Type Table):")
    print("-------------------")
    if not typel:
        print("TYPEL is empty.")
        return
    header = f"{'Idx':<3} | {'Kind':<10} | {'Details':<30}"
    print(header)
    print("-" * len(header))
    for i, entry in enumerate(typel):
        details_str = ""
        if entry.get('KIND') == 'basic':
            details_str = f"Name: {entry.get('NAME')}"
        elif entry.get('KIND') == 'array':
            details_str = f"AINFL_PTR: {entry.get('AINFL_PTR')}"
        # Add other kinds if any
        print(f"{i:<3} | {str(entry.get('KIND')):<10} | {details_str:<30}")

def print_pfinfl(pfinfl, analyzer_instance):
    print("\nPFINFL (Function/Procedure Info Table):")
    print("---------------------------------------")
    if not pfinfl:
        print("PFINFL is empty.")
        return
    header = f"{'Idx':<3} | {'Level':<5} | {'Params':<6} | {'Return Type':<15} | {'Entry Label':<20} | {'Param SYNBL Idxs':<20}"
    print(header)
    print("-" * len(header))
    for i, entry in enumerate(pfinfl):
        ret_type_name = "PROCEDURE"
        if entry.get('RETURN_TYPE_PTR', -1) != -1:
             ret_type_name = analyzer_instance.get_type_name_from_ptr(entry.get('RETURN_TYPE_PTR'))
        param_idxs_str = ", ".join(map(str, entry.get('PARAM_SYNBL_INDICES', [])))
        print(f"{i:<3} | {str(entry.get('LEVEL')):<5} | {str(entry.get('PARAM_COUNT')):<6} | {ret_type_name:<15} | {str(entry.get('ENTRY_LABEL')):<20} | {param_idxs_str:<20}")

def print_ainfl(ainfl, analyzer_instance):
    print("\nAINFL (Array Info Table):")
    print("-------------------------")
    if not ainfl:
        print("AINFL is empty.")
        return
    header = f"{'Idx':<3} | {'Element Type':<20} | {'LowerB':<6} | {'UpperB':<6} | {'Size':<5}"
    print(header)
    print("-" * len(header))
    for i, entry in enumerate(ainfl):
        el_type_name = analyzer_instance.get_type_name_from_ptr(entry.get('ELEMENT_TYPE_PTR', -1))
        print(f"{i:<3} | {el_type_name:<20} | {str(entry.get('LOWER_BOUND')):<6} | {str(entry.get('UPPER_BOUND')):<6} | {str(entry.get('SIZE')):<5}")

def print_consl(consl, analyzer_instance):
    print("\nCONSL (Constant Table):")
    print("-----------------------")
    if not consl:
        print("CONSL is empty.")
        return
    header = f"{'Idx':<3} | {'Value':<20} | {'Type':<20}"
    print(header)
    print("-" * len(header))
    for i, entry in enumerate(consl):
        type_name = analyzer_instance.get_type_name_from_ptr(entry.get('TYPE_PTR', -1))
        print(f"{i:<3} | {str(entry.get('VALUE')):<20} | {type_name:<20}")

def print_scope_stack(scope_stack): # Optional debug helper
    print("\nScope Stack Snapshot:")
    print("---------------------")
    if not scope_stack:
        print("Scope stack is empty or not captured.")
        return
    header = f"{'Idx':<3} | {'Level':<5} | {'Scope ID':<8} | {'Next Offset':<10}"
    print(header)
    print("-" * len(header))
    for i, entry in enumerate(scope_stack):
        level, scope_id, next_offset = entry
        print(f"{i:<3} | {level:<5} | {scope_id:<8} | {next_offset:<10}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python main.py <source_file_path>")
        sys.exit(1)
    main(sys.argv[1])
