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
            'DIVIDE': '/', 'LT': '<', 'GT': '>', 'EQ': '=', 'LE': '<=', 'GE': '>='
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
        formatted_token_lines = []
        for i in range(0, len(transformed_token_sequence_output), 10):
            formatted_token_lines.append(
                " ".join(transformed_token_sequence_output[i:i+10]))
        final_token_sequence_str = "\n".join(formatted_token_lines)

        # --- Generate Keyword Table String ---
        keyword_table_str_lines = []
        if not parser_reserved_keywords:
            keyword_table_str_lines.append("No keywords defined.")
        else:
            sorted_keywords = sorted(parser_reserved_keywords.keys())
            # Basic formatting, can be enhanced with padding like in main.py if needed
            header_kw = f"{'Pos':<5} | {'Keyword':<15} | {'Token Type':<15}"
            keyword_table_str_lines.append(header_kw)
            keyword_table_str_lines.append("-" * len(header_kw))
            for i, keyword in enumerate(sorted_keywords):
                pos = i + 1
                keyword_table_str_lines.append(f"{str(pos):<5} | {keyword:<15} | {
                                               parser_reserved_keywords[keyword]:<15}")
        final_keyword_table_str = "\n".join(keyword_table_str_lines)

        # --- Generate Delimiter Table String ---
        delimiter_table_str_lines = []
        active_delimiters_for_table = {
            k: v for k, v in _delimiter_type_to_symbol_map.items() if k in parser_ply_tokens
        }
        sorted_delimiter_symbols_for_table = sorted(
            list(set(active_delimiters_for_table.values())))

        if not sorted_delimiter_symbols_for_table:
            delimiter_table_str_lines.append(
                "No delimiters defined or found in parser tokens.")
        else:
            symbol_to_types_map = {}
            for token_type, sym in active_delimiters_for_table.items():
                if sym not in symbol_to_types_map:
                    symbol_to_types_map[sym] = []
                symbol_to_types_map[sym].append(token_type)

            header_delim = f"{'Pos':<5} | {
                'Symbol':<10} | {'Token Type(s)':<20}"
            delimiter_table_str_lines.append(header_delim)
            delimiter_table_str_lines.append("-" * len(header_delim))
            for i, symbol in enumerate(sorted_delimiter_symbols_for_table):
                pos = i + 1
                type_names = ", ".join(symbol_to_types_map[symbol])
                delimiter_table_str_lines.append(
                    f"{str(pos):<5} | {symbol:<10} | {type_names:<20}")
        final_delimiter_table_str = "\n".join(delimiter_table_str_lines)

        # --- Generate Identifier Table String ---
        # unique_identifiers_list is already available from token sequence generation
        identifier_table_str_lines = []
        if not unique_identifiers_list:  # This was sorted list of unique ID values
            identifier_table_str_lines.append("No identifiers found.")
        else:
            # Basic formatting
            header_id = f"{'Pos':<5} | {'Identifier':<20}"
            identifier_table_str_lines.append(header_id)
            identifier_table_str_lines.append("-" * len(header_id))
            # identifier_to_pos gives us the position directly
            # We need to iterate through unique_identifiers_list to maintain the sorted order
            # and get the position from identifier_to_pos
            for i, identifier_value in enumerate(unique_identifiers_list):
                # Get the pre-calculated position
                pos = identifier_to_pos[identifier_value]
                identifier_table_str_lines.append(
                    f"{str(pos):<5} | {identifier_value:<20}")
        final_identifier_table_str = "\n".join(identifier_table_str_lines)

        # --- Generate Constant Table String ---
        # unique_constants_list is already available from token sequence generation
        constant_table_str_lines = []
        # This was sorted list of unique constant values (as strings)
        if not unique_constants_list:
            constant_table_str_lines.append("No constants found.")
        else:
            # Basic formatting
            # Increased width for constants
            header_const = f"{'Pos':<5} | {'Constant':<30}"
            constant_table_str_lines.append(header_const)
            constant_table_str_lines.append("-" * len(header_const))
            # constant_to_pos gives us the position directly
            # We need to iterate through unique_constants_list to maintain the sorted order
            # and get the position from constant_to_pos
            for i, const_value in enumerate(unique_constants_list):
                # Get the pre-calculated position
                pos = constant_to_pos[const_value]
                constant_table_str_lines.append(
                    f"{str(pos):<5} | {const_value:<30}")
        final_constant_table_str = "\n".join(constant_table_str_lines)

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
