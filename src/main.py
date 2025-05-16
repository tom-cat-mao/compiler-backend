import sys
from parser import parse
from semantic import SemanticAnalyzer
from intermediate import IntermediateCodeGenerator

def read_source_file(file_path):
    """Read the source code from a file."""
    with open(file_path, 'r') as file:
        return file.read()

def print_tokens(source_code):
    """Print the token sequence from the lexer."""
    from parser import lexer
    lexer.input(source_code)
    print("Token Sequence:")
    print("---------------")
    for token in lexer:
        print(f"Token(type='{token.type}', value='{token.value}', line={token.lineno})")
    print("\n")

def print_keyword_delimiter_tables():
    """Print keyword and delimiter tables."""
    from parser import tokens, reserved
    print("Keyword Table:")
    print("--------------")
    for keyword in reserved:
        print(f"Keyword: {keyword} -> Token: {reserved[keyword]}")
    print("\nDelimiter Table:")
    print("----------------")
    delimiters = ['SEMICOLON', 'COLON', 'COMMA', 'ASSIGN', 'DOT', 'LPAREN', 'RPAREN']
    for delim in delimiters:
        if delim in tokens:
            print(f"Delimiter: {delim}")
    print("\n")

def main(file_path):
    """Main function to run the compiler frontend."""
    # Read source code
    source_code = read_source_file(file_path)
    
    # Print lexical analysis results
    print_tokens(source_code)
    print_keyword_delimiter_tables()
    
    # Parse the source code to build AST
    ast = parse(source_code)
    if ast is None:
        print("Parsing failed. Exiting.")
        return
    
    print("Abstract Syntax Tree (AST):")
    print("--------------------------")
    print(ast)
    print("\n")
    
    # Perform semantic analysis
    analyzer = SemanticAnalyzer()
    try:
        analyzer.analyze(ast)
        print("Symbol Table (after semantic analysis):")
        print("---------------------------------------")
        symbol_table = analyzer.get_symbol_table()
        for var_name, info in symbol_table.items():
            print(f"Variable: {var_name}, Type: {info['type']}, Initialized: {info['initialized']}")
        print("\n")
    except ValueError as e:
        print(f"Semantic Error: {e}")
        return
    
    # Generate intermediate code
    generator = IntermediateCodeGenerator()
    generator.set_symbol_table(symbol_table)
    code = generator.generate(ast)
    print("Intermediate Code (Four-Tuple Sequence):")
    print("---------------------------------------")
    for i, quad in enumerate(code):
        print(f"{i+1}: {quad}")
    print("\n")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python main.py <source_file>")
        sys.exit(1)
    main(sys.argv[1])
