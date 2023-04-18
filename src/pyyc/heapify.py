#!/usr/bin/env python3.10
import ast
from ast import *


uniquify_dict ={}
lambda_count = 0
def get_lambda_label():
    global lambda_count
    label = 'lambda_' + str(lambda_count)
    lambda_count += 1
    return label
class FUNCTION_DEF_NODES():
    def __init__(self, func_name):
        self.name = func_name
        self.free_vars = set()
        self.bound_vars = set()

    def print_def_node(self):
        print(self.name, self.free_vars, self.bound_vars)

class FUNCTION_DEF():
    def __init__(self):
        self.index = 0
        self.function_collection = {}

    def get_next_name(self):
        index = self.index
        self.index += 1
        return 'lambda_' + str(index)

    def capture_function_def(self, func_name):
        # if 'lambda' in func_name:
        #     func_name = self.get_next_name()

        func_node = FUNCTION_DEF_NODES(func_name)
        self.function_collection[func_name] = func_node
        return func_name

    def print_all(self):
        for p_def in self.function_collection:
            self.function_collection[p_def].print_def_node()

    def updade_bound_var_list(self, func_name, var):
        if func_name in self.function_collection:
            bound_vars = self.function_collection[func_name].bound_vars
            bound_vars.add(var)
            return True
        else:
            print("{var} is not in the collection.".format(var=var))
        return False    

    def updade_free_var_list(self, func_name, var):
        if func_name in self.function_collection:
            if var not in self.function_collection[func_name].bound_vars:
                self.function_collection[func_name].free_vars.add(var)
                return True
        else:
            print("{var} is not in the collection.".format(var=var))
        return False

funcs = FUNCTION_DEF()


def handle_unary_node(n, func_name):
    pass

def handle_call_node(n, func_name):
    if isinstance(n.func, Name):
        if n.func.id == func_name:
            funcs.updade_free_var_list(func_name, n.func.id)    
        else:
            funcs.updade_free_var_list(func_name, n.func.id)
    

    heapify_rec(n.func, func_name)
    for x in n.args:       
        heapify_rec(x, func_name)

def handle_boolop_node(n, func_name):
    heapify_rec(n.op, func_name)
    for x in n.values:
        heapify_rec(x, func_name)
    

def handle_list_node(n, func_name):
    for x in n.elts:
        heapify_rec(x, func_name)

def handle_dict_node(n, func_name):
    for i in n.keys:
        heapify_rec(i, func_name)
    for i in n.values:
        heapify_rec(i, func_name)

def handle_subscript_node(n, func_name):
    heapify_rec(n.slice, func_name)
    heapify_rec(n.value, func_name)

def handle_expr_node(n, func_name):
    heapify_rec(n.value, func_name)

def handle_compare_node(n, func_name):
    heapify_rec(n.left, func_name)
    heapify_rec(n.comparators[0], func_name)

def handle_while_node(n, func_name):
    heapify_rec(n.test, func_name)
    for x in n.body:
        heapify_rec(x, func_name)
    for x in n.orelse:
        heapify_rec(x, func_name)

def handle_if_node(n, func_name):
    heapify_rec(n.test, func_name)
    for x in n.body:
        heapify_rec(x, func_name)
    for x in n.orelse:
        heapify_rec(x, func_name)


def handle_ifexp_node(n, func_name):
    heapify_rec(n.test, func_name)
    heapify_rec(n.body, func_name)
    heapify_rec(n.orelse, func_name)

def update_node_name_id(node, func_name, op_value):
    if func_name in uniquify_dict:
        if op_value in uniquify_dict[func_name]:
            node.id = uniquify_dict[func_name][op_value]

def handle_binop_node(n, func_name):
    if isinstance(n.left, Name):
        funcs.updade_free_var_list(func_name, n.left.id)
        update_node_name_id(n.left, func_name, n.left.id)
        
    if isinstance(n.right, Name):
        funcs.updade_free_var_list(func_name, n.right.id)
        update_node_name_id(n.right, func_name, n.right.id)

    heapify_rec(n.left, func_name)
    heapify_rec(n.right, func_name)

   
        

def handle_assign_node(n, func_name):
    if isinstance(n.targets[0], Name):
        is_bound = funcs.updade_bound_var_list(func_name, n.targets[0].id)
        if is_bound:
            target = n.targets[0].id
            if(target not in ["print","input","eval", "int"]):
                if func_name in uniquify_dict:
                    if target in uniquify_dict[func_name]:
                        n.targets[0].id = uniquify_dict[func_name][target]
                    else:
                        n.targets[0].id = func_name + "_"  + n.targets[0].id
                        uniquify_dict[func_name][target] = func_name + "_"  + n.targets[0].id
                else:
                    n.targets[0].id = func_name + "_"  + n.targets[0].id
                    uniquify_dict[func_name] = {
                        n.targets[0].id : func_name + "_"  + n.targets[0].id
                    }

    elif isinstance(n.targets[0], Subscript):
        funcs.updade_bound_var_list(func_name, heapify_rec(n.targets[0].value, func_name))
    
    if isinstance(n.value, Name):
        funcs.updade_free_var_list(func_name, n.value.id)
    else:
        heapify_rec(n.value, func_name)

def handle_function_node(n, func_name):
    func_name = n.name
    func_name = funcs.capture_function_def(func_name)
    for arg in n.args.args:
        funcs.updade_bound_var_list(func_name, arg.arg)
        if func_name not in uniquify_dict:
            uniquify_dict[func_name] = {
                arg.arg: func_name + "_" + arg.arg
            }
        else:
            uniquify_dict[func_name][arg.arg] = func_name + "_" + arg.arg
        arg.arg = '_' + func_name + "_" + arg.arg
    for node in n.body:
        if isinstance(node, Name):
            funcs.updade_bound_var_list(func_name, node.id)
        heapify_rec(node, func_name)

def handle_lambda_node(n, func_name):
    func_name = get_lambda_label()
    n.name = func_name
    func_name = funcs.capture_function_def(func_name)
    for arg in n.args.args:
        funcs.updade_bound_var_list(func_name, arg.arg)
        if func_name not in uniquify_dict:
            uniquify_dict[func_name] = {
                arg.arg: func_name + "_" + arg.arg
            }
        else:
            uniquify_dict[func_name][arg.arg] = func_name + "_" + arg.arg
        arg.arg = '_' + func_name + "_" + arg.arg
    
    if isinstance(n.body, Name):
        n.body.id = func_name + "_" + n.body.id
        funcs.updade_bound_var_list(func_name, n.body.id)
    else:
        heapify_rec(n.body, func_name)


def handle_return_node(n, func_name):
    if isinstance(n.value, Name):
        if n.value.id in funcs.function_collection[func_name].bound_vars:
            n.value.id = func_name + "_" + n.value.id
        else:
            funcs.updade_free_var_list(func_name, n.value.id)
            heapify_rec(n.value, func_name)
    else:
        heapify_rec(n.value, func_name)

def heapify_rec(n, func_name):
    if isinstance(n, Module):
        result = []
        for x in n.body:
            line = heapify_rec(x, None)
            result.append(line)
        return ''
    elif isinstance(n, Assign):
        return handle_assign_node(n, func_name)
    elif isinstance(n, Expr):
        return handle_expr_node(n, func_name)
    elif isinstance(n, Compare):
        return handle_compare_node(n, func_name)
    elif isinstance(n, While):
        return handle_while_node(n, func_name)
    elif isinstance(n, If):
        return handle_if_node(n, func_name)
    elif isinstance(n, IfExp):
        return handle_ifexp_node(n, func_name)    
    elif isinstance(n, BinOp):
        return handle_binop_node(n, func_name)
    elif isinstance(n, UnaryOp):
        return handle_unary_node(n, func_name)
    elif isinstance(n, Call):
        return handle_call_node(n, func_name)
    elif isinstance(n, BoolOp):    
        return handle_boolop_node(n, func_name)
    elif isinstance(n, List):
        return handle_list_node(n, func_name)
    elif isinstance(n, Dict):
        return handle_dict_node(n, func_name)
    elif isinstance(n, Subscript):
        return handle_subscript_node(n, func_name)
    elif isinstance(n, FunctionDef):
        return handle_function_node(n, func_name)
    elif isinstance(n, Lambda):
        return handle_lambda_node(n, func_name)
    elif isinstance(n, Return):
        return handle_return_node(n, func_name)
    elif isinstance(n, Constant):
        return str(n.value)
    elif isinstance(n, Name):
        return str(n.id)
    elif isinstance(n, And):
        return 'and'
    elif isinstance(n, Or):
        return 'or'    
    elif isinstance(n, Not):
        return 'not'    
    elif isinstance(n, Add):
        return '+'
    elif isinstance(n, USub):
        return '-'
    elif isinstance(n, Load):
        return '++'
    elif isinstance(n, Store):
        return '--'
    elif isinstance(n, Eq):
        return '=='
    elif isinstance(n, NotEq):
        return "!="
    elif isinstance(n, Is):
        return "is"
    elif isinstance(n, IsNot):
        return "isnot"
    elif isinstance(n, Gt):
        return '>'
    elif isinstance(n, Lt):
        return '<'
    elif isinstance(n, Name):
        return n.id
    else:
        print(n._fields)
        raise Exception('Error in recreate_program_from_ast: unrecognized AST node')
    

def get_heapify(tree):
    global funcs
    global uniquify_dict
    heapify_rec(tree, None)
    return funcs, uniquify_dict


# PYTHON_FILENAME = "test.py"
# TEST_DIR = 'test_cases'
# with open(PYTHON_FILENAME) as f:
#     prog = f.read()
#     tree = ast.parse(prog)
# print(ast.dump(tree,indent=4))

# heapify = get_heapify(tree)
# print(ast.dump(tree,indent=4))
# print("#######################################")
# funcs.print_all()
# print("#######################################")
# print(uniquify_dict)
# print("#######################################")
