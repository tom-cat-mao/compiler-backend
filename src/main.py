import sys
import os 
from parser import parse as parse_source, tokens as parser_tokens, reserved as parser_reserved
from semantic import SemanticAnalyzer
from intermediate import IntermediateCodeGenerator
from optimizer import Optimizer 
from target import TargetCodeGenerator
from output_formatter import (
    format_token_sequence,
    format_keyword_table,
    format_delimiter_table,
    format_identifier_table,
    format_constant_table,
    format_synbl,
    format_typel,
    format_pfinfl,
    format_ainfl,
    format_consl,
    format_intermediate_code,
    format_optimized_code
)

def read_source_file(file_path):
    """Read the source code from a file."""
    with open(file_path, 'r') as file:
        return file.read()

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
        'DIVIDE': '/', 'LT': '<', 'GT': '>', 'EQ': '=', 'LE': '<=', 'GE': '>=',
        # Add array-related delimiters
        'LSQUARE': '[', 'RSQUARE': ']', 'DOTDOT': '..'
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
    unique_constants_list = sorted(list(set(str(t.value) for t in collected_tokens if t.type == 'NUMBER' or t.type == 'STRING' or t.type == 'REAL_NUMBER')))
    constant_to_pos = {const_val: i + 1 for i, const_val in enumerate(unique_constants_list)}
    
    # --- Print all tables ---
    # First, print the definition tables that pos refers to
    print("Keyword Table (k):")
    print("---------------------------------")
    print(format_keyword_table(parser_reserved),"\n")

    print("Delimiter Table (d):")
    print("---------------------------------")
    print(format_delimiter_table(_delimiter_type_to_symbol_map, parser_tokens),"\n")

    print("Identifier Table (i):")
    print("---------------------------------")
    print(format_identifier_table(unique_identifiers_list),"\n")

    print("Constant Table (c):")
    print("---------------------------------")
    print(format_constant_table(unique_constants_list),"\n")

    # Then, print the transformed token sequence
    transformed_token_sequence_output = []
    for token_obj in collected_tokens:
        pos = -1
        type_code = '?'
        if token_obj.value.lower() in parser_reserved and \
            parser_reserved[token_obj.value.lower()] == token_obj.type and \
            token_obj.value.lower() in keyword_to_pos:
            type_code = 'k'
            pos = keyword_to_pos[token_obj.value.lower()]
        elif token_obj.type in active_delimiter_type_to_symbol:
            symbol = active_delimiter_type_to_symbol[token_obj.type]
            if symbol in delimiter_symbol_to_pos:
                type_code = 'd'
                pos = delimiter_symbol_to_pos[symbol]
        elif token_obj.type == 'ID':
            if token_obj.value in identifier_to_pos:
                type_code = 'i'
                pos = identifier_to_pos[token_obj.value]
        elif token_obj.type == 'NUMBER' or token_obj.type == 'STRING' or token_obj.type == 'REAL_NUMBER':
            str_val = str(token_obj.value)
            if str_val in constant_to_pos:
                type_code = 'c'
                pos = constant_to_pos[str_val]
        if pos != -1:
            transformed_token_sequence_output.append(f"({pos},{type_code})")
        else:
            transformed_token_sequence_output.append(f"(err:{token_obj.type},{token_obj.value})")

    print("\nToken Sequence (pos, type_code):")
    print("---------------------------------")
    print(format_token_sequence(transformed_token_sequence_output)+"\n")
    
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
        
        print(format_synbl(all_symbol_tables.get("SYNBL", []), analyzer))
        print(format_typel(all_symbol_tables.get("TYPEL", [])))
        print(format_pfinfl(all_symbol_tables.get("PFINFL", []), analyzer))
        print(format_ainfl(all_symbol_tables.get("AINFL", []), analyzer))
        print(format_consl(all_symbol_tables.get("CONSL", []), analyzer))

        print("\n")
    except ValueError as e:
        print(f"Semantic Error: {e}")
        return # Stop if semantic errors occur
    
    # Generate intermediate code
    generator = IntermediateCodeGenerator()
    generator.set_symbol_table(all_symbol_tables.get("SYNBL"))
    
    code = generator.generate(ast)
    print("Intermediate Code (Four-Tuple Sequence):")
    print("---------------------------------------")
    print(format_intermediate_code(code))
            
    print("\n")

    # Optimize the intermediate code
    optimizer = Optimizer()
    optimized_code = optimizer.optimize(code) # Pass the original code
    print("Optimized Intermediate Code (Four-Tuple Sequence):")
    print("-------------------------------------------------")
    print(format_optimized_code(optimized_code))
    print("\n")

    # Generate Target Code (Assembly)
    if optimized_code: # Proceed only if there's optimized code
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
