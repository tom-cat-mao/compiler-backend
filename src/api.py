from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os

# Adjust the path to import from the same directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from parser import parse
from intermediate import IntermediateCodeGenerator
from optimizer import Optimizer
from target import TargetCodeGenerator

app = Flask(__name__)
CORS(app)  # Enable CORS to allow frontend requests from different origins

@app.route('/compile', methods=['POST'])
def compile():
    data = request.get_json()
    expression = data.get('expression', '')
    
    if not expression:
        return jsonify({'error': 'No expression provided'}), 400
    
    try:
        # Step 1: Parse the expression to AST
        ast = parse(expression)
        if ast is None:
            return jsonify({'error': 'Invalid expression'}), 400
        
        # Step 2: Generate intermediate code
        generator = IntermediateCodeGenerator()
        generator.generate(ast)
        intermediate = generator.get_code()
        
        # Step 3: Optimize the intermediate code
        optimizer = Optimizer()
        optimized = optimizer.optimize(intermediate)
        
        # Step 4: Generate target code
        generator = TargetCodeGenerator()
        target = generator.generate(optimized)
        
        # Format results for display
        return jsonify({
            'ast': str(ast),
            'intermediate': '\n'.join(intermediate),
            'optimized': '\n'.join(optimized),
            'target': '\n'.join(target)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
