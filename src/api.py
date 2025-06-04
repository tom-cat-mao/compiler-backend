from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os

# Adjust the path to import from the same directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from parser import parse, lexer, tokens as parser_ply_tokens, reserved as parser_reserved_keywords
from semantic import SemanticAnalyzer
from intermediate import IntermediateCodeGenerator

app = Flask(__name__)
CORS(app)  # Enable CORS to allow frontend requests from different origins

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
            elif ast is None: # Tokens might exist but parsing failed
                error_msg = "Invalid program syntax. AST could not be constructed."
            return jsonify({'error': error_msg + ' Please check your Pascal code for correct structure (e.g., program declaration, begin/end blocks).'}), 400

        # --- Prepare maps for the transformed token sequence (similar to main.py) ---
        # Keyword map: keyword string (lowercase) -> pos
        sorted_keywords_list = sorted(parser_reserved_keywords.keys())
        keyword_to_pos = {kw: i + 1 for i, kw in enumerate(sorted_keywords_list)}

        # Delimiter map: symbol string -> pos
        _delimiter_type_to_symbol_map = {
            'SEMICOLON': ';', 'COLON': ':', 'COMMA': ',', 'ASSIGN': ':=', 'DOT': '.',
            'LPAREN': '(', 'RPAREN': ')', 'PLUS': '+', 'MINUS': '-', 'TIMES': '*',
            'DIVIDE': '/', 'LT': '<', 'GT': '>', 'EQ': '=', 'LE': '<=', 'GE': '>='
        }
        active_delimiter_type_to_symbol = {
            k: v for k, v in _delimiter_type_to_symbol_map.items() if k in parser_ply_tokens
        }
        sorted_delimiter_symbols_list = sorted(list(set(active_delimiter_type_to_symbol.values())))
        delimiter_symbol_to_pos = {sym: i + 1 for i, sym in enumerate(sorted_delimiter_symbols_list)}

        # Identifier map: identifier string -> pos (from current program's tokens)
        unique_identifiers_list = sorted(list(set(t.value for t in raw_tokens_from_parser if t.type == 'ID')))
        identifier_to_pos = {ident: i + 1 for i, ident in enumerate(unique_identifiers_list)}

        # Constant map: constant string value -> pos (from current program's tokens)
        unique_constants_list = sorted(list(set(str(t.value) for t in raw_tokens_from_parser if t.type == 'NUMBER' or t.type == 'STRING')))
        constant_to_pos = {const_val: i + 1 for i, const_val in enumerate(unique_constants_list)}
        
        # --- Generate the transformed token sequence string ---
        transformed_token_sequence_output = []
        for token_obj in raw_tokens_from_parser: # Use the collected token objects
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
                transformed_token_sequence_output.append(f"({pos},{type_code})")
            else:
                # Fallback for unmapped tokens
                transformed_token_sequence_output.append(f"(err:{token_obj.type},{token_obj.value})")
        
        final_token_sequence_str = " ".join(transformed_token_sequence_output)

        # Step 3: Semantic Analysis - Build symbol table
        analyzer = SemanticAnalyzer()
        analyzer.analyze(ast)
        symbol_table = analyzer.get_symbol_table()
        symbol_table_str = []
        for var_name, info in symbol_table.items():
            symbol_table_str.append(f"Variable: {var_name}, Type: {info['type']}, Initialized: {info['initialized']}")
        
        # Step 4: Generate intermediate code
        generator = IntermediateCodeGenerator()
        generator.set_symbol_table(symbol_table)
        code = generator.generate(ast)
        intermediate_str = [f"{i+1}: {quad}" for i, quad in enumerate(code)]
        
        # Format results for display
        return jsonify({
            'tokens': final_token_sequence_str,
            'symbolTable': '\n'.join(symbol_table_str) if symbol_table_str else 'No symbols defined',
            'intermediate': '\n'.join(intermediate_str) if intermediate_str else 'No intermediate code generated'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
