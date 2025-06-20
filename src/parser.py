import ply.lex as lex
import ply.yacc as yacc

# Lexer Definition
# Defines the tokens for the Pascal language grammar.
# Tokens are the basic building blocks of the input language, such as keywords, identifiers, numbers, and operators.
tokens = (
    'NUMBER',      # Represents numeric values (integers)
    'REAL_NUMBER', # Represents real numeric values (e.g., 3.14)
    'PLUS',        # Represents the '+' operator
    'MINUS',       # Represents the '-' operator
    'TIMES',       # Represents the '*' operator
    'DIVIDE',      # Represents the '/' operator
    'LPAREN',      # Represents the '(' character
    'RPAREN',      # Represents the ')' character
    'ID',          # Represents identifiers (variable names)
    'SEMICOLON',   # Represents the ';' character
    'COLON',       # Represents the ':' character
    'COMMA',       # Represents the ',' character
    'ASSIGN',      # Represents the ':=' operator
    'DOT',         # Represents the '.' character
    'LT',          # Represents the '<' operator
    'GT',          # Represents the '>' operator
    'EQ',          # Represents the '=' operator
    'LE',          # Represents the '<=' operator
    'GE',          # Represents the '>=' operator
    'AND',         # Represents the 'and' keyword
    'PROGRAM',     # Represents the 'program' keyword
    'VAR',         # Represents the 'var' keyword
    'INTEGER',     # Represents the 'integer' keyword
    'BOOLEAN',     # Represents the 'boolean' keyword
    'REAL',        # Represents the 'real' keyword
    'CHAR',        # Represents the 'char' keyword
    'BEGIN',       # Represents the 'begin' keyword
    'END',         # Represents the 'end' keyword
    'IF',          # Represents the 'if' keyword
    'THEN',        # Represents the 'then' keyword
    'ELSE',        # Represents the 'else' keyword
    'WHILE',       # Represents the 'while' keyword
    'DO',          # Represents the 'do' keyword
    'WRITELN',     # Represents the 'writeln' keyword
    'STRING',      # Represents string literals (which can be chars or strings)
    # Array-related tokens
    'ARRAY',       # Represents the 'array' keyword
    'OF',          # Represents the 'of' keyword
    'LSQUARE',     # Represents the '[' character
    'RSQUARE',     # Represents the ']' character
    'DOTDOT',      # Represents the '..' range operator
)

t_PLUS = r'\+'
t_MINUS = r'-'
t_TIMES = r'\*'
t_DIVIDE = r'/'
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_NUMBER = r'\d+'
t_REAL_NUMBER = r'\d+\.\d+' # Matches numbers like 3.14, 0.5 etc.
t_SEMICOLON = r';'
t_COLON = r':'
t_COMMA = r','
t_ASSIGN = r':='
t_DOT = r'\.'
t_LT = r'<'
t_GT = r'>'
t_EQ = r'='
t_LE = r'<='
t_GE = r'>='
# t_STRING = r'\'[^\']*\''  # Matches single-quoted strings
t_STRING = r"\'([^\']|\'\')*\'" # Handles Pascal-style strings with '' for a single quote
# Array-related token rules
t_LSQUARE = r'\['
t_RSQUARE = r'\]'
t_DOTDOT = r'\.\.'


# Reserved keywords mapping
reserved = {
    'and': 'AND',
    'program': 'PROGRAM',
    'var': 'VAR',
    'integer': 'INTEGER',
    'boolean': 'BOOLEAN',
    'real': 'REAL',        # Added
    'char': 'CHAR',        # Added
    'begin': 'BEGIN',
    'end': 'END',
    'if': 'IF',
    'then': 'THEN',
    'else': 'ELSE',
    'while': 'WHILE',
    'do': 'DO',
    'writeln': 'WRITELN',
    # Array-related reserved words
    'array': 'ARRAY',
    'of': 'OF',
}

def t_ID(t):
    r'[a-zA-Z][a-zA-Z0-9]*'
    t.type = reserved.get(t.value.lower(), 'ID')  # Check if it's a reserved keyword
    # print(f"Token: ID, Value: {t.value}, Line: {t.lineno}, Position: {t.lexpos}")
    return t

t_ignore = ' \t'

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)
    # Do not return the token, as it's ignored

def t_error(t):
    print(f"Illegal character '{t.value[0]}' at line {t.lineno}")
    t.lexer.skip(1)

lexer = lex.lex()

# Parser Definition
# Implements the grammar rules for Pascal language constructs.
# The grammar supports program structure, variable declarations, assignments,
# arithmetic and logical expressions, If statements, and While loops.
# Each rule constructs an Abstract Syntax Tree (AST) node.

def p_program(p):
    'program : PROGRAM ID SEMICOLON var_declarations BEGIN statements END DOT'
    p[0] = ('program', p[2], p[4], p[6])

def p_var_declarations(p):
    '''var_declarations : VAR var_list
                        | '''
    if len(p) > 1:
        p[0] = ('var_declarations', p[2])
    else:
        p[0] = ('var_declarations', [])

def p_var_list(p):
    '''var_list : var_list var_declaration
                | var_declaration'''
    if len(p) > 2:
        p[0] = p[1] + [p[2]]
    else:
        p[0] = [p[1]]

def p_var_declaration(p):
    'var_declaration : id_list COLON type SEMICOLON'
    p[0] = ('var', p[1], p[3])

def p_id_list(p):
    '''id_list : id_list COMMA ID
               | ID'''
    if len(p) > 2:
        p[0] = p[1] + [p[3]]
    else:
        p[0] = [p[1]]

# New rule for 'variable' which can be an ID or an array access
def p_variable(p):
    '''variable : ID
                | ID LSQUARE expression RSQUARE'''
    if len(p) == 2:  # Matched ID
        p[0] = ('ID', p[1])  # AST node for simple variable
    else:  # Matched ID LSQUARE expression RSQUARE
        p[0] = ('array_access', p[1], p[3])  # AST node for array access

def p_type(p):
    '''type : INTEGER
            | BOOLEAN
            | REAL
            | CHAR
            | array_type_definition''' # Added array type
    p[0] = p[1]

# New rule for array type definition
def p_array_type_definition(p):
    '''array_type_definition : ARRAY LSQUARE index_range RSQUARE OF type'''
    # p[3] is the index_range tuple (low_bound_node, high_bound_node)
    # p[6] is the base_type_node
    p[0] = ('array_type', p[3][0], p[3][1], p[6])

# New rule for index range (assuming integer number literals for now)
def p_index_range(p):
    '''index_range : NUMBER DOTDOT NUMBER'''
    # For simplicity, we directly use the NUMBER token's value.
    # In a more complex scenario, these could be constant expressions.
    p[0] = (('NUMBER', int(p[1])), ('NUMBER', int(p[3])))


def p_statements(p):
    '''statements : statements statement SEMICOLON
                  | statement SEMICOLON
                  | statements statement
                  | statement'''
    if len(p) > 2:
        if isinstance(p[1], list):
            p[0] = p[1] + [p[2]]
        else:
            p[0] = [p[1], p[2]]
    else:
        p[0] = [p[1]]

def p_statement(p):
    '''statement : assignment
                 | if_statement
                 | while_statement
                 | writeln_statement'''
    p[0] = p[1]

def p_assignment(p):
    'assignment : variable ASSIGN expression' # Use 'variable' for the left-hand side
    # p[1] is the AST node from p_variable (e.g., ('ID', 'name') or ('array_access', 'name', index_expr))
    # p[3] is the AST node for the expression on the right-hand side
    p[0] = ('assign', p[1], p[3])

def p_if_statement(p):
    '''if_statement : IF expression THEN BEGIN statements END
                    | IF expression THEN BEGIN statements END ELSE BEGIN statements END
                    | IF expression THEN statement
                    | IF expression THEN statement ELSE statement'''
    if len(p) > 7:
        p[0] = ('if', p[2], p[5], p[9])
    elif len(p) == 7:
        p[0] = ('if', p[2], p[5], None)
    elif len(p) == 6:
        p[0] = ('if', p[2], p[4], p[5])
    else:
        p[0] = ('if', p[2], p[4], None)

def p_while_statement(p):
    'while_statement : WHILE expression DO BEGIN statements END'
    p[0] = ('while', p[2], p[5])

# Updated writeln to use a general expression_list
def p_expression_list(p):
    '''expression_list : expression_list COMMA expression
                       | expression'''
    if len(p) > 2: # list COMMA expr
        p[0] = p[1] + [p[3]] # Corrected: p[3] is the expression after the comma
    else: # single expr
        p[0] = [p[1]]

def p_writeln_statement(p):
    '''writeln_statement : WRITELN LPAREN expression_list RPAREN'''
    p[0] = ('writeln', p[3]) # p[3] is the list of expressions

# Removed p_string_expression_list and p_string_expression as expression_list covers them

def p_expression(p):
    '''expression : simple_expression
                  | simple_expression relop simple_expression'''
    if len(p) > 2:
        p[0] = (p[2], p[1], p[3])
    else:
        p[0] = p[1]

def p_simple_expression(p):
    '''simple_expression : term
                         | simple_expression addop term'''
    if len(p) > 2:
        p[0] = (p[2], p[1], p[3])
    else:
        p[0] = p[1]

def p_term(p):
    '''term : factor
            | term mulop factor'''
    if len(p) > 2:
        p[0] = (p[2], p[1], p[3])
    else:
        p[0] = p[1]

def p_factor(p):
    '''factor : LPAREN expression RPAREN
              | NUMBER
              | REAL_NUMBER
              | STRING
              | variable'''  # Use 'variable' for ID or array access as r-value
    
    # Check the type of the first token in the slice to determine the rule matched
    # For 'variable', p[1] will already be the AST tuple from p_variable.
    # For literals, p[1] is the token value.
    # For LPAREN, p[1] is '('.

    # Check if the first symbol is LPAREN for (expression)
    if p.slice[1].type == 'LPAREN':
        p[0] = p[2]  # p[2] is the expression node
    # Check if p[1] is a tuple, which means it came from 'variable' rule
    elif isinstance(p[1], tuple) and (p[1][0] == 'ID' or p[1][0] == 'array_access'): # This means 'variable' was matched
        p[0] = p[1] # p[1] is already the AST node from p_variable
    # Otherwise, it must be one of the direct literals
    else:
        token_type = p.slice[1].type # Get type of the token (NUMBER, REAL_NUMBER, STRING)
        token_value = p[1]           # Get value of the token

        if token_type == 'NUMBER':
            p[0] = ('NUMBER', int(token_value))
        elif token_type == 'REAL_NUMBER':
            p[0] = ('REAL_NUMBER', float(token_value))
        elif token_type == 'STRING':
            content = token_value[1:-1]
            processed_value = content.replace("''", "'")
            if len(processed_value) == 1:
                p[0] = ('CHAR_LITERAL', processed_value)
            else:
                p[0] = ('STRING_LITERAL', processed_value)
        # Note: A plain 'ID' token without brackets is now handled by 'variable'

def p_addop(p):
    '''addop : PLUS
             | MINUS'''
    p[0] = p[1]

def p_mulop(p):
    '''mulop : TIMES
             | DIVIDE'''
    p[0] = p[1]

def p_relop(p):
    '''relop : LT
             | GT
             | EQ
             | LE
             | GE'''
    p[0] = p[1]

def p_expression_logical(p):
    'expression : expression AND expression'
    p[0] = ('and', p[1], p[3])

def p_error(p):
    if p:
        print(f"Syntax error in input at token '{p.value}' (type: {p.type}, line: {p.lineno})")
        # Consider adding parser.errok() or other recovery mechanisms if needed
    else:
        print("Syntax error in input at EOF!")

parser = yacc.yacc(debug=False) # You can control debug logging here or via a parameter

def parse(input_string, debug_parser=False):
    """
    Performs lexical analysis and parsing of the input string.

    Args:
        input_string (str): The source code to parse.
        debug_parser (bool): Flag to enable YACC debugging.

    Returns:
        tuple: (list_of_tokens, abstract_syntax_tree)
               Returns (None, None) if parsing fails at a very early stage or input is empty.
    """
    if not input_string:
        return [], None # Return empty tokens and no AST for empty input

    # 1. Lexical Analysis: Collect all tokens
    lexer.input(input_string)
    collected_tokens = []
    while True:
        tok = lexer.token()
        if not tok:
            break
        collected_tokens.append(tok)

    # 2. Syntactic Analysis: Parse the tokens to build AST
    # Reset lexer for the parser. PLY's yacc.parse() will use this lexer instance.
    lexer.input(input_string) 
    ast = parser.parse(input_string, lexer=lexer, debug=debug_parser)
    # print(f"AST: {ast}") #if debug_parser else None  # Print AST if debugging is enabled
    return collected_tokens, ast

if __name__ == "__main__":
    # This block is for testing parser.py independently
    def print_ast_json(ast_node):
        import json
        try:
            print(json.dumps(ast_node, indent=2))
        except TypeError:
            print(ast_node) # Fallback for non-serializable parts

    while True:
        try:
            s = input('parser_test > ')
            if not s or s.lower() == 'exit':
                break
            
            tokens, ast_result = parse(s) # Call the modified parse function
            
            print("\n--- Collected Tokens ---")
            if tokens:
                for token in tokens:
                    print(f"  {token}")
            else:
                print("  No tokens collected.")
            
            print("\n--- Abstract Syntax Tree (AST) ---")
            if ast_result is not None:
                print_ast_json(ast_result)
            else:
                print("  Parsing failed or no AST generated.")
            print("-" * 30 + "\n")

        except EOFError:
            break
        except Exception as e:
            print(f"An error occurred during parsing test: {e}")
