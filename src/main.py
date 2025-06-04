import sys
import os # Added for path operations and directory creation
import traceback # For printing stack traces on error
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
    constant_literal_to_pos_map, # Changed from constant_to_pos_map
    language_keywords_map, 
    active_delimiter_type_to_symbol_map
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
        type_code = '?' 
        if isinstance(token.value, str) and \
           token.value.lower() in language_keywords_map and \
           language_keywords_map[token.value.lower()] == token.type and \
           token.value.lower() in keyword_to_pos_map:
            type_code = 'k'
            pos = keyword_to_pos_map[token.value.lower()]
        elif token.type in active_delimiter_type_to_symbol_map:
            symbol = active_delimiter_type_to_symbol_map[token.type]
            if symbol in delimiter_symbol_to_pos_map:
                type_code = 'd'
                pos = delimiter_symbol_to_pos_map[symbol]
        elif token.type == 'ID':
            if token.value in identifier_to_pos_map:
                type_code = 'i'
                pos = identifier_to_pos_map[token.value]
        elif token.type == 'NUMBER' or token.type == 'STRING':
            str_val = str(token.value) 
            if str_val in constant_literal_to_pos_map: # Use the literal map
                type_code = 'c'
                pos = constant_literal_to_pos_map[str_val]
        
        if pos != -1:
            output_sequence.append(f"({pos},{type_code})")
        else:
            output_sequence.append(f"(err:{token.type},{token.value})")

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
    active_delimiters = {k: v for k, v in delimiter_type_to_symbol_map.items() if k in parser_tokens}
    sorted_delimiter_symbols = sorted(list(set(active_delimiters.values())))
    if not sorted_delimiter_symbols:
        print("No delimiters defined or found in parser tokens.")
    else:
        max_idx_len = len(str(len(sorted_delimiter_symbols)))
        symbol_to_types = {sym: [] for sym in sorted_delimiter_symbols}
        for token_type, sym in active_delimiters.items(): symbol_to_types[sym].append(token_type)
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
    print("Identifier Table (i - from tokens):") # Clarified origin
    print("-----------------------------------")
    if not identifiers:
        print("No identifiers found in tokens.")
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

def print_synbl_table(synbl_entries):
    print("Symbol Table (SYNBL):")
    print("---------------------")
    if not synbl_entries: print("SYNBL is empty.")
    else:
        header = f"{'NEME':<15} | {'TYP (idx)':<10} | {'CAT':<5} | {'ADDR (VALL_idx)':<15} | {'SCOPE':<15} | {'INIT':<5}"
        print(header); print("-" * len(header))
        for entry in synbl_entries:
            typ_display = str(entry.get('TYP', 'N/A'))
            addr_display = str(entry.get('ADDR', 'N/A'))
            print(f"{entry.get('NEME', ''):<15} | {typ_display:<10} | {entry.get('CAT', ''):<5} | "
                  f"{addr_display:<15} | {entry.get('scope', ''):<15} | {str(entry.get('initialized', '')):<5}")
    print("\n")

def print_tval_table(tval_entries):
    print("Type Table (TVAL):")
    print("------------------")
    if not tval_entries: print("TVAL is empty.")
    else:
        header = f"{'IDX':<5} | {'ID (val)':<8} | {'TVAL_CAT':<10} | {'TPOINT':<10} | {'NAME':<15}"
        print(header); print("-" * len(header))
        for i, entry in enumerate(tval_entries):
            print(f"{str(i):<5} | {str(entry.get('id','N/A')):<8} | {entry.get('TVAL_CAT', ''):<10} | "
                  f"{str(entry.get('TPOINT', '')):<10} | {entry.get('name', ''):<15}")
    print("\n")

def print_consl_table(consl_entries):
    print("Constant Value Table (CONSL):")
    print("-----------------------------")
    if not consl_entries: print("CONSL is empty.")
    else:
        header = f"{'IDX':<5} | {'ID (val)':<8} | {'VALUE':<20} | {'TYPE_PTR (TVAL_idx)':<18}"
        print(header); print("-" * len(header))
        for i, entry in enumerate(consl_entries):
            print(f"{str(i):<5} | {str(entry.get('id','N/A')):<8} | {str(entry.get('value', '')):<20} | "
                  f"{str(entry.get('type_ptr', '')):<18}")
    print("\n")

def print_lenl_table(lenl_entries, tval_entries_for_names):
    print("Length Table (LENL):")
    print("--------------------")
    if not lenl_entries: print("LENL is empty.")
    else:
        header = f"{'TYPE_PTR (TVAL_idx)':<20} | {'SIZE':<10}"
        print(header); print("-" * len(header))
        for entry in lenl_entries:
            type_name = 'UnknownType'
            type_ptr = entry.get('type_ptr')
            if type_ptr is not None and type_ptr < len(tval_entries_for_names):
                type_name = tval_entries_for_names[type_ptr].get('name', 'UnknownType')
            type_display = f"{str(type_ptr) if type_ptr is not None else 'N/A'} ({type_name})"
            print(f"{type_display:<20} | {str(entry.get('size', '')):<10}")
    print("\n")

def print_vall_table(vall_entries, tval_entries_for_names):
    print("Activity Record Table (VALL):")
    print("-------------------------------")
    if not vall_entries: print("VALL is empty.")
    else:
        for i, entry in enumerate(vall_entries):
            print(f"--- VALL Record IDX: {i} (Scope ID: {entry.get('scope_id', 'N/A')}) ---")
            print(f"  Return Address: {entry.get('return_address', 'N/A')}")
            print(f"  Dynamic Link:   {entry.get('dynamic_link', 'N/A')}")
            print(f"  Static Link:    {entry.get('static_link', 'N/A')}")
            print(f"  Formal Params:  {str(entry.get('formal_params', [])):<30}")
            print(f"  Local Variables ({len(entry.get('local_variables', []))}):")
            for lv in entry.get('local_variables', []):
                lv_type_name = 'UnknownType'
                lv_type_ptr = lv.get('type_ptr')
                if lv_type_ptr is not None and lv_type_ptr < len(tval_entries_for_names):
                    lv_type_name = tval_entries_for_names[lv_type_ptr].get('name', 'UnknownType')
                print(f"    - Name: {lv.get('name', ''):<15} (Type: {lv_type_name} [TVAL_idx:{str(lv_type_ptr)}])")
            print(f"  Temp Units:     {entry.get('temp_units', 'N/A')}")
            print(f"  Internal Vector:{entry.get('internal_vector', 'N/A')}")
            print("") 
    print("\n")

def main(file_path):
    source_code = read_source_file(file_path)
    collected_tokens, ast = parse_source(source_code)

    if collected_tokens is None and ast is None:
        print("Failed to tokenize and parse the source code.")
        return

    # --- Prepare maps for the transformed token sequence (Token-based tables) ---
    sorted_keywords_list = sorted(parser_reserved.keys())
    keyword_to_pos = {kw: i + 1 for i, kw in enumerate(sorted_keywords_list)}
    _delimiter_type_to_symbol_map = {
        'SEMICOLON': ';', 'COLON': ':', 'COMMA': ',', 'ASSIGN': ':=', 'DOT': '.',
        'LPAREN': '(', 'RPAREN': ')', 'PLUS': '+', 'MINUS': '-', 'TIMES': '*',
        'DIVIDE': '/', 'LT': '<', 'GT': '>', 'EQ': '=', 'LE': '<=', 'GE': '>='
    }
    active_delimiter_type_to_symbol = {k: v for k, v in _delimiter_type_to_symbol_map.items() if k in parser_tokens}
    sorted_delimiter_symbols_list = sorted(list(set(active_delimiter_type_to_symbol.values())))
    delimiter_symbol_to_pos = {sym: i + 1 for i, sym in enumerate(sorted_delimiter_symbols_list)}
    
    unique_identifiers_list = sorted(list(set(t.value for t in collected_tokens if t.type == 'ID')))
    identifier_to_pos = {ident: i + 1 for i, ident in enumerate(unique_identifiers_list)}
    
    unique_constant_literals_list = sorted(list(set(str(t.value) for t in collected_tokens if t.type == 'NUMBER' or t.type == 'STRING')))
    constant_literal_to_pos = {const_val: i + 1 for i, const_val in enumerate(unique_constant_literals_list)}
    
    # --- Print Token-Based Tables ---
    print_keyword_delimiter_tables()
    print_identifier_table(collected_tokens) 

    # --- Print Transformed Token Sequence ---
    print_transformed_token_sequence(
        collected_tokens,
        keyword_to_pos,
        delimiter_symbol_to_pos,
        identifier_to_pos,
        constant_literal_to_pos, 
        parser_reserved, 
        active_delimiter_type_to_symbol
    )
    
    if ast is None:
        print("Parsing failed (AST is None). Exiting.")
        return
    
    # --- Perform Semantic Analysis ---
    analyzer = SemanticAnalyzer()
    synbl_entries, tval_entries, consl_entries, lenl_entries, vall_entries = [], [], [], [], []
    try:
        analyzer.analyze(ast)
        synbl_entries = analyzer.get_symbol_table_entries()
        tval_entries = analyzer.get_type_table()
        consl_entries = analyzer.get_constant_table()
        lenl_entries = analyzer.get_length_table()
        vall_entries = analyzer.get_activity_record_table()

        print_synbl_table(synbl_entries)
        print_tval_table(tval_entries)
        print_consl_table(consl_entries)
        print_lenl_table(lenl_entries, tval_entries) 
        print_vall_table(vall_entries, tval_entries)

    except ValueError as e:
        print(f"Semantic Error: {e}")
        traceback.print_exc()
        return 
    
    # --- Generate Intermediate Code ---
    generator = IntermediateCodeGenerator()
    # Pass the symbol table (SYNBL entries) to the generator.
    # The generator's set_symbol_table might need to be adapted if it expects the old dict format.
    generator.set_symbol_table(synbl_entries) 
    code = generator.generate(ast)
    print("Intermediate Code (Four-Tuple Sequence):")
    print("---------------------------------------")
    if not code:
        print("No intermediate code generated.")
    else:        
        for i, quad in enumerate(code):
            op, arg1, arg2, res = quad
            op_str = str(op)
            arg1_str = str(arg1) if arg1 is not None else '_'
            arg2_str = str(arg2) if arg2 is not None else '_'
            res_str = str(res) if res is not None else '_'
            print(f"({op_str}, {arg1_str}, {arg2_str}, {res_str})")
            
    print("\n")

    # Optimize the intermediate code
    optimizer = Optimizer()
    optimized_code = optimizer.optimize(code) 
    print("Optimized Intermediate Code (Four-Tuple Sequence):")
    print("-------------------------------------------------")
    if not optimized_code:
        print("No optimized code generated (or code was empty).")
    else:
        for i, quad in enumerate(optimized_code):
            op, arg1, arg2, res = quad
            op_str = str(op)
            arg1_str = str(arg1) if arg1 is not None else '_'
            arg2_str = str(arg2) if arg2 is not None else '_'
            res_str = str(res) if res is not None else '_'
            print(f"({op_str}, {arg1_str}, {arg2_str}, {res_str})")
    print("\n")

    # Generate Target Code (Assembly)
    if optimized_code: 
        target_generator = TargetCodeGenerator()
        assembly_code_lines = target_generator.generate(optimized_code)
        
        result_dir = "result"
        if not os.path.exists(result_dir):
            os.makedirs(result_dir)
            print(f"Created directory: {result_dir}")

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
