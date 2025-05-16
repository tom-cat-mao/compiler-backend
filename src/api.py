from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os

# Adjust the path to import from the same directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from parser import parse, lexer
from semantic import SemanticAnalyzer
from intermediate import IntermediateCodeGenerator

app = Flask(__name__)
CORS(app)  # Enable CORS to allow frontend requests from different origins

@app.route('/compile', methods=['POST'])
def compile():
    data = request.get_json()
    program = data.get('program', '')
    
    if not program:
        return jsonify({'error': 'No program provided'}), 400
    
    try:
        # Step 1: Lexical Analysis - Generate token sequence
        lexer.input(program)
        tokens = []
        for token in lexer:
            tokens.append(f"Token(type='{token.type}', value='{token.value}', line={token.lineno})")
        
        # Step 2: Parse the program to AST
        ast = parse(program)
        if ast is None:
            return jsonify({'error': 'Invalid program syntax'}), 400
        
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
            'tokens': '\n'.join(tokens),
            'symbolTable': '\n'.join(symbol_table_str) if symbol_table_str else 'No symbols defined',
            'intermediate': '\n'.join(intermediate_str) if intermediate_str else 'No intermediate code generated'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
