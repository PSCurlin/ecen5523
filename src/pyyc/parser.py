import ast
from ast import *
import ply.yacc as yacc

import ply.lex as lex



reserved = {
    'if' : 'IF',
    'then' : 'THEN',
    'else' : 'ELSE',
    'while' : 'WHILE',
    'print' : 'PRINT',
    'eval' : 'EVAL',
    'input' : 'INPUT'
 }


tokens = ('PRINT','INT','PLUS','LPAR','RPAR','MINUS','ID','EQUALS','COMMENT', 'EVAL', 'INPUT')
t_PRINT = r'print'
t_PLUS = r'\+'
t_LPAR = r'\('
t_RPAR = r'\)'
t_MINUS = r'\-'
t_EQUALS = r'\='
t_EVAL = r'eval'
t_INPUT = r'input'

def t_COMMENT(t):
    r'\#.*'
    pass
     # No return value. Token discarded    
def t_ID(t):
    r'[a-zA-Z_][a-zA_Z_0-9]*'
    try:
        t.type = reserved.get(t.value,'ID')    # Check for reserved words
    except:
        print("############ error #####################")
    return t   
def t_INT(t):
    r'\d+'
    try:
        t.value = int(t.value)
    except ValueError:
        print("integer value too large", t.value)
        t.value = 0
    return t
t_ignore = ' \t'

def t_newline(t):
    r'\n+'
    t.lexer.lineno += t.value.count("\n")
def t_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)



precedence = (
    ('nonassoc','PRINT'),
    ('left','PLUS')
)

def p_start(t):
    'start : statements'
    t[0] = t[1]
    
def p_statements(t):
    'statements : statement statement'

    if type(t[2]) == list:
        t[0] = [t[1]] + t[2]
    else:
        t[0] =  [t[1], t[2]]

    
def p_statement_statements(t):
    'statement : statements'
    t[0] = t[1]

def p_statement_expression(t):
    'statement : expression'
    t[0] = t[1] 

def p_print_statement(t):
    'statement : PRINT LPAR expression RPAR'
    t[0] = Expr(value = Call(Name("print",Load()),[t[3]], []))

def p_assign_id(t):
    'statement : ID EQUALS expression'
    t[0] = Assign(
            targets=[
                Name(id=t[1], ctx=Store())],
            value= t[3])

def p_id_expression(t):
    'expression : ID'
    t[0] = Name(id=t[1], ctx=Load())

def p_plus_expression(t):
    'expression : expression PLUS expression'
    t[0] = BinOp(t[1], Add(), t[3])

def p_comments(t):
    'statement :'
    pass

def p_nested_expression(t): 
    'expression : LPAR expression RPAR'
    t[0] = Expr(value = t[2])

def p_int_expression(t):
    'expression : INT'
    t[0] = Constant(t[1])

def p_unary_expression(t):
    'expression : MINUS expression'
    t[0] = UnaryOp(op = USub(), operand = t[2])


def p_eval_expression(t):
    'expression : EVAL LPAR INPUT LPAR RPAR RPAR'
    t[0] = Call(Name('eval', ctx=Load()), [Call(Name('input', ctx=Load()), [], [])])

def p_error(t):
    print("####: ", t)
    print("Syntax error at '%s'" % t.value)

lexer = lex.lex()
parser = yacc.yacc()

def parse_tree(filename):
    prog = ''
    tree = Module(body = [], type_ignores=[])
    with open(filename) as f:
        prog = f.read()
        tree_branch = yacc.parse(prog, lexer = lexer) # alt. parser.parse(prog)
        if tree_branch != None:
            tree.body.extend(tree_branch)

    while None in tree.body:
        tree.body.remove(None)
    return tree