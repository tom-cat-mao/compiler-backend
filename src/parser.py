import ply.lex as lex
import ply.yacc as yacc

# Lexer Definition
# Defines the tokens for the Pascal language grammar.
# Tokens are the basic building blocks of the input language, such as keywords, identifiers, numbers, and operators.
tokens = (
    'NUMBER',      # Represents numeric values (integers)
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
    'BEGIN',       # Represents the 'begin' keyword
    'END',         # Represents the 'end' keyword
    'IF',          # Represents the 'if' keyword
    'THEN',        # Represents the 'then' keyword
    'ELSE',        # Represents the 'else' keyword
    'WHILE',       # Represents the 'while' keyword
    'DO',          # Represents the 'do' keyword
    'WRITELN',     # Represents the 'writeln' keyword
    'STRING',      # Represents string literals
)

t_PLUS = r'\+'
t_MINUS = r'-'
t_TIMES = r'\*'
t_DIVIDE = r'/'
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_NUMBER = r'\d+'
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
t_STRING = r'\'[^\']*\''  # Matches single-quoted strings

# Reserved keywords mapping
reserved = {
    'and': 'AND',
    'program': 'PROGRAM',
    'var': 'VAR',
    'integer': 'INTEGER',
    'boolean': 'BOOLEAN',
    'begin': 'BEGIN',
    'end': 'END',
    'if': 'IF',
    'then': 'THEN',
    'else': 'ELSE',
    'while': 'WHILE',
    'do': 'DO',
    'writeln': 'WRITELN',
}

def t_ID(t):
    r'[a-zA-Z][a-zA-Z0-9]*'
    t.type = reserved.get(t.value.lower(), 'ID')  # Check if it's a reserved keyword
    return t

t_ignore = ' \t\n'

def t_error(t):
    print(f"Illegal character '{t.value[0]}'")
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

def p_type(p):
    '''type : INTEGER
            | BOOLEAN'''
    p[0] = p[1]

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
    'assignment : ID ASSIGN expression'
    p[0] = ('assign', p[1], p[3])

def p_if_statement(p):
    '''if_statement : IF expression THEN BEGIN statements END
                    | IF expression THEN BEGIN statements END ELSE BEGIN statements END'''
    if len(p) > 7:
        p[0] = ('if', p[2], p[5], p[9])
    else:
        p[0] = ('if', p[2], p[5], None)

def p_while_statement(p):
    'while_statement : WHILE expression DO BEGIN statements END'
    p[0] = ('while', p[2], p[5])

def p_writeln_statement(p):
    '''writeln_statement : WRITELN LPAREN expression RPAREN
                         | WRITELN LPAREN string_expression_list RPAREN'''
    if len(p) == 5:
        p[0] = ('writeln', p[3])
    else:
        p[0] = ('writeln', p[3])

def p_string_expression_list(p):
    '''string_expression_list : string_expression_list COMMA string_expression
                              | string_expression'''
    if len(p) > 2:
        p[0] = p[1] + [p[3]]
    else:
        p[0] = [p[1]]

def p_string_expression(p):
    '''string_expression : expression
                         | STRING'''
    p[0] = p[1]

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
              | ID'''
    if len(p) > 2:
        p[0] = p[2]
    else:
        p[0] = p[1] if isinstance(p[1], int) else p[1]

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
    print("Syntax error in input!")

parser = yacc.yacc()

def parse(input_string):
    return parser.parse(input_string, lexer=lexer)

if __name__ == "__main__":
    while True:
        try:
            s = input('calc > ')
            if s == 'exit':
                break
            result = parse(s)
            print(result)
        except EOFError:
            break
