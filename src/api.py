from intermediate import IntermediateCodeGenerator
from semantic import SemanticAnalyzer
from optimizer import Optimizer # Import the Optimizer
from parser import parse, lexer, tokens as parser_ply_tokens, reserved as parser_reserved_keywords
from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os
import traceback # For detailed error logging

# Adjust the path to import from the same directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

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
        raw_tokens_from_parser, ast = parse(program)

        if ast is None:
            error_msg = "Invalid program syntax."
            # ... (error handling for parsing failure as before)
            if not raw_tokens_from_parser and ast is None:
                error_msg = "Parsing failed: No tokens generated and no AST."
            elif ast is None:
                error_msg = "Invalid program syntax. AST could not be constructed."
            return jsonify({'error': error_msg + ' Please check your Pascal code for correct structure (e.g., program declaration, begin/end blocks).'}), 400

        # --- Prepare maps for the transformed token sequence (similar to main.py) ---
        # (This part remains largely the same, generating token-based tables like keyword, delimiter, identifier)
        sorted_keywords_list = sorted(parser_reserved_keywords.keys())
        keyword_to_pos = {kw: i + 1 for i, kw in enumerate(sorted_keywords_list)}
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
        unique_identifiers_list = sorted(list(set(t.value for t in raw_tokens_from_parser if t.type == 'ID')))
        identifier_to_pos = {ident: i + 1 for i, ident in enumerate(unique_identifiers_list)}
        
        # Note: The original token-based constant_to_pos and unique_constants_list are no longer directly used for the main 'constantTable' output,
        # as CONSL from semantic analysis will replace it. However, it's still needed for the transformed token sequence.
        unique_constants_literals_list = sorted(list(set(str(t.value) for t in raw_tokens_from_parser if t.type == 'NUMBER' or t.type == 'STRING')))
        constant_literal_to_pos = {const_val: i + 1 for i, const_val in enumerate(unique_constants_literals_list)}


        # --- Generate the transformed token sequence string ---
        transformed_token_sequence_output = []
        for token_obj in raw_tokens_from_parser:
            pos = -1
            type_code = '?'
            # Check for Keyword:
            if isinstance(token_obj.value, str) and \
               token_obj.value.lower() in parser_reserved_keywords and \
               parser_reserved_keywords.get(token_obj.value.lower()) == token_obj.type and \
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
                if str_val in constant_literal_to_pos: # Use the literal map here
                    type_code = 'c'
                    pos = constant_literal_to_pos[str_val]
            if pos != -1:
                transformed_token_sequence_output.append(f"({pos},{type_code})")
            else:
                transformed_token_sequence_output.append(f"(err:{token_obj.type},{token_obj.value})")
        formatted_token_lines = [" ".join(transformed_token_sequence_output[i:i+10]) for i in range(0, len(transformed_token_sequence_output), 10)]
        final_token_sequence_str = "\n".join(formatted_token_lines)

        # --- Generate Keyword Table String ---
        keyword_table_str_lines = [f"{'Pos':<5} | {'Keyword':<15} | {'Token Type':<15}", "-" * 39]
        keyword_table_str_lines.extend([f"{i+1:<5} | {kw:<15} | {parser_reserved_keywords[kw]:<15}" for i, kw in enumerate(sorted_keywords_list)])
        final_keyword_table_str = "\n".join(keyword_table_str_lines)
        
        # --- Generate Delimiter Table String ---
        delimiter_table_str_lines = [f"{'Pos':<5} | {'Symbol':<10} | {'Token Type(s)':<20}", "-" * 40]
        symbol_to_types_map = {sym: [] for sym in sorted_delimiter_symbols_list}
        for token_type, sym in active_delimiter_type_to_symbol.items(): symbol_to_types_map[sym].append(token_type)
        delimiter_table_str_lines.extend([f"{i+1:<5} | {sym:<10} | {', '.join(symbol_to_types_map[sym]):<20}" for i, sym in enumerate(sorted_delimiter_symbols_list)])
        final_delimiter_table_str = "\n".join(delimiter_table_str_lines)

        # --- Generate Identifier Table String (from tokens) ---
        identifier_table_str_lines = [f"{'Pos':<5} | {'Identifier':<20}", "-" * 28]
        identifier_table_str_lines.extend([f"{identifier_to_pos[val]:<5} | {val:<20}" for val in unique_identifiers_list])
        final_identifier_table_str = "\n".join(identifier_table_str_lines)

        # --- Old Constant Literal Table String (from tokens, for reference or if needed separately) ---
        # This is what used to be 'constantTable'. We'll call it 'literalConstantTable' if we want to keep it.
        # For now, the main 'constantTable' will be CONSL from semantic analysis.
        # Let's create it for completeness, maybe the UI wants it.
        literal_constant_table_str_lines = ["Literal Constant Table (from Tokens):", "------------------------------------"]
        if not unique_constants_literals_list:
            literal_constant_table_str_lines.append("No literal constants found in tokens.")
        else:
            header_l_const = f"{'Pos':<5} | {'Constant Literal':<30}"
            literal_constant_table_str_lines.append(header_l_const)
            literal_constant_table_str_lines.append("-" * len(header_l_const))
            for const_val_str in unique_constants_literals_list:
                pos = constant_literal_to_pos[const_val_str]
                literal_constant_table_str_lines.append(f"{str(pos):<5} | {const_val_str:<30}")
        final_literal_constant_table_str = "\n".join(literal_constant_table_str_lines)


        # Step 3: Semantic Analysis - Build symbol table and other tables
        analyzer = SemanticAnalyzer()
        analyzer.analyze(ast) 

        synbl_entries = analyzer.get_symbol_table_entries()
        tval_entries = analyzer.get_type_table()
        consl_entries = analyzer.get_constant_table() # This is the new CONSL
        lenl_entries = analyzer.get_length_table()
        vall_entries = analyzer.get_activity_record_table()

        # --- Format Symbol Table (SYNBL) String ---
        synbl_str_lines = ["Symbol Table (SYNBL):", "---------------------"]
        if not synbl_entries: synbl_str_lines.append("No symbols found.")
        else:
            header_synbl = f"{'NEME':<15} | {'TYP (idx)':<10} | {'CAT':<5} | {'ADDR (VALL_idx)':<15} | {'SCOPE':<15} | {'INIT':<5}"
            synbl_str_lines.append(header_synbl); synbl_str_lines.append("-" * len(header_synbl))
            for entry in synbl_entries:
                typ_display = str(entry.get('TYP', 'N/A'))
                addr_display = str(entry.get('ADDR', 'N/A')) # ADDR now points to VALL index for vars
                synbl_str_lines.append(f"{entry.get('NEME', ''):<15} | {typ_display:<10} | {entry.get('CAT', ''):<5} | "
                                       f"{addr_display:<15} | {entry.get('scope', ''):<15} | {str(entry.get('initialized', '')):<5}")
        final_synbl_str = "\n".join(synbl_str_lines)

        # --- Format Type Table (TVAL) String ---
        tval_str_lines = ["Type Table (TVAL):", "------------------"]
        if not tval_entries: tval_str_lines.append("No types defined.")
        else:
            header_tval = f"{'IDX':<5} | {'ID (val)':<8} | {'TVAL_CAT':<10} | {'TPOINT':<10} | {'NAME':<15}"
            tval_str_lines.append(header_tval); tval_str_lines.append("-" * len(header_tval))
            for i, entry in enumerate(tval_entries):
                tval_str_lines.append(f"{str(i):<5} | {str(entry.get('id','N/A')):<8} | {entry.get('TVAL_CAT', ''):<10} | "
                                      f"{str(entry.get('TPOINT', '')):<10} | {entry.get('name', ''):<15}")
        final_tval_str = "\n".join(tval_str_lines)

        # --- Format Constant Table (CONSL) String ---
        consl_str_lines = ["Constant Value Table (CONSL):", "-----------------------------"]
        if not consl_entries: consl_str_lines.append("No constants recorded.")
        else:
            header_consl = f"{'IDX':<5} | {'ID (val)':<8} | {'VALUE':<20} | {'TYPE_PTR (TVAL_idx)':<18}"
            consl_str_lines.append(header_consl); consl_str_lines.append("-" * len(header_consl))
            for i, entry in enumerate(consl_entries):
                consl_str_lines.append(f"{str(i):<5} | {str(entry.get('id','N/A')):<8} | {str(entry.get('value', '')):<20} | "
                                       f"{str(entry.get('type_ptr', '')):<18}")
        final_consl_str = "\n".join(consl_str_lines)
        
        # --- Format Length Table (LENL) String ---
        lenl_str_lines = ["Length Table (LENL):", "--------------------"]
        if not lenl_entries: lenl_str_lines.append("No length information.")
        else:
            header_lenl = f"{'TYPE_PTR (TVAL_idx)':<20} | {'SIZE':<10}"
            lenl_str_lines.append(header_lenl); lenl_str_lines.append("-" * len(header_lenl))
            for entry in lenl_entries:
                type_name = tval_entries[entry['type_ptr']]['name'] if entry['type_ptr'] < len(tval_entries) else 'UnknownType'
                lenl_str_lines.append(f"{str(entry.get('type_ptr', '')) + f' ({type_name})':<20} | {str(entry.get('size', '')):<10}")
        final_lenl_str = "\n".join(lenl_str_lines)

        # --- Format Activity Record Table (VALL) String ---
        vall_str_lines = ["Activity Record Table (VALL):", "-------------------------------"]
        if not vall_entries: vall_str_lines.append("No activity records.")
        else:
            for i, entry in enumerate(vall_entries):
                vall_str_lines.append(f"--- VALL Record IDX: {i} (Scope ID: {entry.get('scope_id', 'N/A')}) ---")
                vall_str_lines.append(f"  Return Address: {entry.get('return_address', 'N/A')}")
                vall_str_lines.append(f"  Dynamic Link:   {entry.get('dynamic_link', 'N/A')}")
                vall_str_lines.append(f"  Static Link:    {entry.get('static_link', 'N/A')}")
                vall_str_lines.append(f"  Formal Params:  {str(entry.get('formal_params', [])):<30}")
                vall_str_lines.append(f"  Local Variables ({len(entry.get('local_variables', []))}):")
                for lv in entry.get('local_variables', []):
                    lv_type_name = tval_entries[lv['type_ptr']]['name'] if lv['type_ptr'] < len(tval_entries) else 'UnknownType'
                    vall_str_lines.append(f"    - Name: {lv.get('name', ''):<15} (Type: {lv_type_name} [TVAL_idx:{lv.get('type_ptr','')}])")
                vall_str_lines.append(f"  Temp Units:     {entry.get('temp_units', 'N/A')}")
                vall_str_lines.append(f"  Internal Vector:{entry.get('internal_vector', 'N/A')}")
                vall_str_lines.append("") 
        final_vall_str = "\n".join(vall_str_lines)

        # Step 4: Generate intermediate code
        generator = IntermediateCodeGenerator()
        # The set_symbol_table in IntermediateCodeGenerator might need adjustment
        # if it expects the old dictionary format. analyzer.get_symbol_table() now returns SYNBL list.
        # For now, we pass what get_symbol_table() returns, which is the list of symbol entries.
        # This might require IntermediateCodeGenerator to be updated.
        current_symbol_table_for_gen = analyzer.get_symbol_table() # This is List[Dict]
        generator.set_symbol_table(current_symbol_table_for_gen) 
        code = generator.generate(ast)
        intermediate_str_lines = [f"({quad[0]}, {str(quad[1]) if quad[1] is not None else '_'}, {str(quad[2]) if quad[2] is not None else '_'}, {str(quad[3]) if quad[3] is not None else '_'})" for quad in code]
        final_intermediate_str = "\n".join(intermediate_str_lines)

        # Step 5: Optimize the intermediate code
        optimizer = Optimizer()
        optimized_code = optimizer.optimize(code) 
        optimized_intermediate_str_lines = [f"({quad[0]}, {str(quad[1]) if quad[1] is not None else '_'}, {str(quad[2]) if quad[2] is not None else '_'}, {str(quad[3]) if quad[3] is not None else '_'})" for quad in optimized_code]
        final_optimized_intermediate_str = "\n".join(optimized_intermediate_str_lines)

        return jsonify({
            'tokens': final_token_sequence_str,
            'keywordTable': final_keyword_table_str,
            'delimiterTable': final_delimiter_table_str,
            'identifierTable': final_identifier_table_str, # From tokens
            'literalConstantTable': final_literal_constant_table_str, # Old constant table from tokens
            'symbolTable': final_synbl_str,          # New SYNBL
            'typeTable': final_tval_str,             # New TVAL
            'constantTable': final_consl_str,        # New CONSL (replaces old 'constantTable' key)
            'lengthTable': final_lenl_str,           # New LENL
            'activityRecordTable': final_vall_str,   # New VALL
            'intermediate': final_intermediate_str if final_intermediate_str else 'No intermediate code generated.',
            'optimizedIntermediate': final_optimized_intermediate_str if final_optimized_intermediate_str else 'No optimized intermediate code generated.'
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
