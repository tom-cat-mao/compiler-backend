import ply.lex as lex
import ply.yacc as yacc

# Lexer
tokens = (
    'NUMBER',
    'PLUS',
    'TIMES',
    'LPAREN',
    'RPAREN',
)

t_PLUS = r'\+'
t_TIMES = r'\*'
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_NUMBER = r'\d+'

t_ignore = ' \t\n'

def t_error(t):
    print(f"Illegal character '{t.value[0]}'")
    t.lexer.skip(1)

lexer = lex.lex()

# Parser
def p_expression_plus(p):
    'expression : expression PLUS term'
    p[0] = ('+', p[1], p[3])

def p_expression_term(p):
    'expression : term'
    p[0] = p[1]

def p_term_times(p):
    'term : term TIMES factor'
    p[0] = ('*', p[1], p[3])

def p_term_factor(p):
    'term : factor'
    p[0] = p[1]

def p_factor_expr(p):
    'factor : LPAREN expression RPAREN'
    p[0] = p[2]

def p_factor_number(p):
    'factor : NUMBER'
    p[0] = int(p[1])

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
