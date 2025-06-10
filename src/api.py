from intermediate import IntermediateCodeGenerator
from semantic import SemanticAnalyzer
from optimizer import Optimizer 
from parser import parse, lexer, tokens as parser_ply_tokens, reserved as parser_reserved_keywords
from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os
from output_formatter import (
    format_synbl,
    format_typel,
    format_pfinfl,
    format_ainfl,
    format_consl,
    format_keyword_table,
    format_delimiter_table,
    format_identifier_table,
    format_constant_table,
    format_token_sequence,
    format_intermediate_code,
    format_optimized_code
)

# Adjust the path to import from the same directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__)
CORS(app, resources={r"/compile": {"origins": "*"}}, supports_credentials=True)


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
        intermediate_str = format_intermediate_code(code)

        # Step 5: Optimize the intermediate code
        optimizer = Optimizer()
        optimized_code = optimizer.optimize(code) # Pass the original intermediate code
        optimized_intermediate_str = format_optimized_code(optimized_code)


        # Format results for display
        return jsonify({
            'tokens': final_token_sequence_str,
            'keywordTable': final_keyword_table_str,
            'delimiterTable': final_delimiter_table_str,
            'identifierTable': final_identifier_table_str,
            'constantTable': final_constant_table_str,
            'symbolTable': synbl_str,
            'intermediate': intermediate_str,
            'optimizedIntermediate': optimized_intermediate_str,
            'typel': typel_str,
            'pfinfl': pfinfl_str,
            'ainfl': ainfl_str,
            'consl': consl_str
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
