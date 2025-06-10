from intermediate import IntermediateCodeGenerator
from semantic import SemanticAnalyzer
from optimizer import Optimizer # Import the Optimizer
from parser import parse, lexer, tokens as parser_ply_tokens, reserved as parser_reserved_keywords
from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os

# Adjust the path to import from the same directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__)
CORS(app, resources={r"/compile": {"origins": "*"}}, supports_credentials=True)

def format_synbl(synbl, analyzer_instance):
    lines = []
    if not synbl:
        lines.append("SYNBL is empty.")
        return "\n".join(lines)
    header = f"{'Idx':<3} | {'Name':<15} | {'Cat':<5} | {'Addr/Info':<20}"
    lines.append(header)
    lines.append("-" * len(header))
    for i, entry in enumerate(synbl):
        addr_info_str = str(entry.get('ADDR_PTR'))
        cat = entry.get('CAT')
        addr_ptr = entry.get('ADDR_PTR')
        if cat == 'f' and isinstance(addr_ptr, int):
            addr_info_str = f"PFINFL_IDX:{addr_ptr}"
        elif cat == 'c' and isinstance(addr_ptr, int):
            addr_info_str = f"CONSL_IDX:{addr_ptr}"
        elif cat in ['v', 'p_val', 'p_ref']:
            addr_info_str = str(addr_ptr if addr_ptr is not None else "N/A")
        elif cat == 'program_name' or cat == 't':
            addr_info_str = "N/A"
        lines.append(f"{i:<3} | {str(entry.get('NAME')):<15} | {str(cat):<5} | {addr_info_str:<20}")
    return "\n".join(lines)

def format_typel(typel):
    lines = []
    if not typel:
        lines.append("TYPEL is empty.")
        return "\n".join(lines)
    header = f"{'Idx':<3} | {'Kind':<10} | {'Details':<30}"
    lines.append(header)
    lines.append("-" * len(header))
    for i, entry in enumerate(typel):
        details_str = ""
        if entry.get('KIND') == 'basic':
            details_str = f"Name: {entry.get('NAME')}"
        elif entry.get('KIND') == 'array':
            details_str = f"AINFL_PTR: {entry.get('AINFL_PTR')}"
        lines.append(f"{i:<3} | {str(entry.get('KIND')):<10} | {details_str:<30}")
    return "\n".join(lines)

def format_pfinfl(pfinfl, analyzer_instance):
    lines = []
    if not pfinfl:
        lines.append("PFINFL is empty.")
        return "\n".join(lines)
    header = f"{'Idx':<3} | {'Level':<5} | {'Params':<6} | {'Return Type':<15} | {'Entry Label':<20} | {'Param SYNBL Idxs':<20}"
    lines.append(header)
    lines.append("-" * len(header))
    for i, entry in enumerate(pfinfl):
        ret_type_name = "PROCEDURE"
        if entry.get('RETURN_TYPE_PTR', -1) != -1:
             ret_type_name = analyzer_instance.get_type_name_from_ptr(entry.get('RETURN_TYPE_PTR'))
        param_idxs_str = ", ".join(map(str, entry.get('PARAM_SYNBL_INDICES', [])))
        lines.append(f"{i:<3} | {str(entry.get('LEVEL')):<5} | {str(entry.get('PARAM_COUNT')):<6} | {ret_type_name:<15} | {str(entry.get('ENTRY_LABEL')):<20} | {param_idxs_str:<20}")
    return "\n".join(lines)

def format_ainfl(ainfl, analyzer_instance):
    lines = []
    if not ainfl:
        lines.append("AINFL is empty.")
        return "\n".join(lines)
    header = f"{'Idx':<3} | {'Element Type':<20} | {'LowerB':<6} | {'UpperB':<6} | {'Size':<5}"
    lines.append(header)
    lines.append("-" * len(header))
    for i, entry in enumerate(ainfl):
        el_type_name = analyzer_instance.get_type_name_from_ptr(entry.get('ELEMENT_TYPE_PTR', -1))
        lines.append(f"{i:<3} | {el_type_name:<20} | {str(entry.get('LOWER_BOUND')):<6} | {str(entry.get('UPPER_BOUND')):<6} | {str(entry.get('SIZE')):<5}")
    return "\n".join(lines)

def format_consl(consl, analyzer_instance):
    lines = []
    if not consl:
        lines.append("CONSL is empty.")
        return "\n".join(lines)
    header = f"{'Idx':<3} | {'Value':<20} | {'Type':<20}"
    lines.append(header)
    lines.append("-" * len(header))
    for i, entry in enumerate(consl):
        type_name = analyzer_instance.get_type_name_from_ptr(entry.get('TYPE_PTR', -1))
        lines.append(f"{i:<3} | {str(entry.get('VALUE')):<20} | {type_name:<20}")
    return "\n".join(lines)


def format_keyword_table(keywords_map):
    lines = []
    if not keywords_map:
        lines.append("No keywords defined.")
        return "\n".join(lines)
    
    sorted_keywords = sorted(keywords_map.keys())
    max_idx_len = len(str(len(sorted_keywords)))
    max_keyword_len = max(len(kw) for kw in sorted_keywords) if sorted_keywords else 10
    max_token_len = max(len(keywords_map[kw]) for kw in sorted_keywords) if sorted_keywords else 10
    
    header = f"{'Pos':<{max_idx_len}} | {'Keyword':<{max_keyword_len}} | {'Token Type':<{max_token_len}}"
    lines.append(header)
    lines.append("-" * len(header))
    for i, keyword in enumerate(sorted_keywords):
        pos = i + 1
        lines.append(f"{str(pos):<{max_idx_len}} | {keyword:<{max_keyword_len}} | {keywords_map[keyword]:<{max_token_len}}")
    return "\n".join(lines)

def format_delimiter_table(delimiter_map, available_tokens):
    lines = []
    active_delimiters = {k: v for k, v in delimiter_map.items() if k in available_tokens}
    sorted_symbols = sorted(list(set(active_delimiters.values())))
    
    if not sorted_symbols:
        lines.append("No delimiters defined.")
        return "\n".join(lines)

    symbol_to_types = {sym: [] for sym in sorted_symbols}
    for token_type, sym in active_delimiters.items():
        symbol_to_types[sym].append(token_type)

    max_idx_len = len(str(len(sorted_symbols)))
    max_symbol_len = max(len(sym) for sym in sorted_symbols)
    max_type_len = max(len(", ".join(types)) for types in symbol_to_types.values())

    header = f"{'Pos':<{max_idx_len}} | {'Symbol':<{max_symbol_len}} | {'Token Type(s)':<{max_type_len}}"
    lines.append(header)
    lines.append("-" * len(header))
    for i, symbol in enumerate(sorted_symbols):
        pos = i + 1
        type_names = ", ".join(symbol_to_types[symbol])
        lines.append(f"{str(pos):<{max_idx_len}} | {symbol:<{max_symbol_len}} | {type_names:<{max_type_len}}")
    return "\n".join(lines)

def format_identifier_table(identifiers):
    lines = []
    if not identifiers:
        lines.append("No identifiers found.")
        return "\n".join(lines)
    
    max_idx_len = len(str(len(identifiers)))
    max_id_len = max(len(identifier) for identifier in identifiers) if identifiers else 10
    
    header = f"{'Pos':<{max_idx_len}} | {'Identifier':<{max_id_len}}"
    lines.append(header)
    lines.append("-" * len(header))
    for i, identifier in enumerate(identifiers):
        pos = i + 1
        lines.append(f"{str(pos):<{max_idx_len}} | {identifier:<{max_id_len}}")
    return "\n".join(lines)

def format_constant_table(constants):
    lines = []
    if not constants:
        lines.append("No constants found.")
        return "\n".join(lines)
        
    max_idx_len = len(str(len(constants)))
    max_const_len = max(len(constant) for constant in constants) if constants else 10

    header = f"{'Pos':<{max_idx_len}} | {'Constant':<{max_const_len}}"
    lines.append(header)
    lines.append("-" * len(header))
    for i, constant in enumerate(constants):
        pos = i + 1
        lines.append(f"{str(pos):<{max_idx_len}} | {constant:<{max_const_len}}")
    return "\n".join(lines)


def format_token_sequence(sequence):
    lines = []
    if not sequence:
        lines.append("No token sequence generated.")
        return "\n".join(lines)
    
    for i in range(0, len(sequence), 10):
        lines.append(" ".join(sequence[i:i+10]))
    return "\n".join(lines)


@app.route('/compile', methods=['POST'])
def compile():
    data = request.get_json()
    program = data.get('program', '')

    if not program:
        return jsonify({'error': 'No program provided. Please enter a valid Pascal program in the textarea.'}), 400

    print(f"Received program for compilation:\n{program}")
    try:
        # Step 1 & 2: Lexical Analysis and Parsing
        # The parse function from parser.py returns both collected tokens and the AST.
        raw_tokens_from_parser, ast = parse(program)

        if ast is None:
            error_msg = "Invalid program syntax."
            if not raw_tokens_from_parser and ast is None:
                error_msg = "Parsing failed: No tokens generated and no AST."
            elif ast is None:  # Tokens might exist but parsing failed
                error_msg = "Invalid program syntax. AST could not be constructed."
            return jsonify({'error': error_msg + ' Please check your Pascal code for correct structure (e.g., program declaration, begin/end blocks).'}), 400

        # --- Prepare maps for the transformed token sequence (similar to main.py) ---
        # Keyword map: keyword string (lowercase) -> pos
        sorted_keywords_list = sorted(parser_reserved_keywords.keys())
        keyword_to_pos = {kw: i + 1 for i,
                          kw in enumerate(sorted_keywords_list)}

        # Delimiter map: symbol string -> pos
        _delimiter_type_to_symbol_map = {
            'SEMICOLON': ';', 'COLON': ':', 'COMMA': ',', 'ASSIGN': ':=', 'DOT': '.',
            'LPAREN': '(', 'RPAREN': ')', 'PLUS': '+', 'MINUS': '-', 'TIMES': '*',
            'DIVIDE': '/', 'LT': '<', 'GT': '>', 'EQ': '=', 'LE': '<=', 'GE': '>=',
            'LSQUARE': '[', 'RSQUARE': ']', 'DOTDOT': '..'
        }
        active_delimiter_type_to_symbol = {
            k: v for k, v in _delimiter_type_to_symbol_map.items() if k in parser_ply_tokens
        }
        sorted_delimiter_symbols_list = sorted(
            list(set(active_delimiter_type_to_symbol.values())))
        delimiter_symbol_to_pos = {
            sym: i + 1 for i, sym in enumerate(sorted_delimiter_symbols_list)}

        # Identifier map: identifier string -> pos (from current program's tokens)
        unique_identifiers_list = sorted(
            list(set(t.value for t in raw_tokens_from_parser if t.type == 'ID')))
        identifier_to_pos = {ident: i + 1 for i,
                             ident in enumerate(unique_identifiers_list)}

        # Constant map: constant string value -> pos (from current program's tokens)
        unique_constants_list = sorted(list(set(str(
            t.value) for t in raw_tokens_from_parser if t.type == 'NUMBER' or t.type == 'STRING')))
        constant_to_pos = {const_val: i + 1 for i,
                           const_val in enumerate(unique_constants_list)}

        # --- Generate the transformed token sequence string ---
        transformed_token_sequence_output = []
        for token_obj in raw_tokens_from_parser:  # Use the collected token objects
            pos = -1
            type_code = '?'

            if token_obj.value.lower() in parser_reserved_keywords and \
               parser_reserved_keywords[token_obj.value.lower()] == token_obj.type and \
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
            elif token_obj.type == 'NUMBER' or token_obj.type == 'STRING':
                str_val = str(token_obj.value)
                if str_val in constant_to_pos:
                    type_code = 'c'
                    pos = constant_to_pos[str_val]

            if pos != -1:
                transformed_token_sequence_output.append(
                    f"({pos},{type_code})")
            else:
                # Fallback for unmapped tokens
                transformed_token_sequence_output.append(
                    f"(err:{token_obj.type},{token_obj.value})")

        # Format the token sequence string with newlines (e.g., 10 tokens per line)
        final_token_sequence_str = format_token_sequence(transformed_token_sequence_output)

        # --- Generate Keyword Table String ---
        final_keyword_table_str = format_keyword_table(parser_reserved_keywords)

        # --- Generate Delimiter Table String ---
        final_delimiter_table_str = format_delimiter_table(_delimiter_type_to_symbol_map, parser_ply_tokens)

        # --- Generate Identifier Table String ---
        final_identifier_table_str = format_identifier_table(unique_identifiers_list)

        # --- Generate Constant Table String ---
        final_constant_table_str = format_constant_table(unique_constants_list)

        # Step 3: Semantic Analysis - Build symbol table
        analyzer = SemanticAnalyzer()
        analyzer.analyze(ast)
        symbol_tables = analyzer.get_symbol_tables_snapshot()
        
        synbl_str = format_synbl(symbol_tables.get("SYNBL", []), analyzer)
        typel_str = format_typel(symbol_tables.get("TYPEL", []))
        pfinfl_str = format_pfinfl(symbol_tables.get("PFINFL", []), analyzer)
        ainfl_str = format_ainfl(symbol_tables.get("AINFL", []), analyzer)
        consl_str = format_consl(symbol_tables.get("CONSL", []), analyzer)

        # Step 4: Generate intermediate code
        generator = IntermediateCodeGenerator()
        generator.set_symbol_table(symbol_tables.get("SYNBL", []))
        code = generator.generate(ast)
        intermediate_str = [f"{i+1}: {quad}" for i, quad in enumerate(code)]

        # Step 5: Optimize the intermediate code
        optimizer = Optimizer()
        optimized_code = optimizer.optimize(code) # Pass the original intermediate code
        optimized_intermediate_str = [f"{i+1}: {quad}" for i, quad in enumerate(optimized_code)]


        # Format results for display
        return jsonify({
            'tokens': final_token_sequence_str,
            'keywordTable': final_keyword_table_str,
            'delimiterTable': final_delimiter_table_str,
            'identifierTable': final_identifier_table_str,
            'constantTable': final_constant_table_str,
            'symbolTable': synbl_str,
            'intermediate': '\n'.join(intermediate_str) if intermediate_str else 'No intermediate code generated',
            'optimizedIntermediate': '\n'.join(optimized_intermediate_str) if optimized_intermediate_str else 'No optimized intermediate code generated',
            'typel': typel_str,
            'pfinfl': pfinfl_str,
            'ainfl': ainfl_str,
            'consl': consl_str
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
