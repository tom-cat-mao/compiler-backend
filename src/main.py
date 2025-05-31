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
    symbol_table = None # Initialize symbol_table
    try:
        analyzer.analyze(ast)
        print("Symbol Table (after semantic analysis):")
        print("---------------------------------------")
        symbol_table = analyzer.get_symbol_table()
        if not symbol_table:
            print("Symbol table is empty.")
        else:
            max_var_len = max(len(var_name) for var_name in symbol_table) if symbol_table else 10
            max_type_len_sym = max(len(info['type']) for info in symbol_table.values()) if symbol_table else 10
            header_sym = f"{'Variable':<{max_var_len}} | {'Type':<{max_type_len_sym}} | Initialized"
            print(header_sym)
            print("-" * len(header_sym))
            for var_name, info in sorted(symbol_table.items()):
                print(f"{var_name:<{max_var_len}} | {info['type']:<{max_type_len_sym}} | {info['initialized']}")
        print("\n")
    except ValueError as e:
        print(f"Semantic Error: {e}")
        return # Stop if semantic errors occur
    
    # Generate intermediate code
    generator = IntermediateCodeGenerator()
    if symbol_table: # Ensure symbol_table is available
        generator.set_symbol_table(symbol_table) 
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


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python main.py <source_file_path>")
        sys.exit(1)
    main(sys.argv[1])
