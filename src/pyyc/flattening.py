#!/usr/bin/env python3.10
import ast
from ast import *
from heapify import get_heapify
flattened_prog = []
variable_mapping_dict = {}
used_tmp_vars = []
uniquify_dict ={}
eval_temp_var_names = []
var_type_mapping = {}
box_var_mapping = {}
box_variable_mapping_dict = {}
func_mapping = {}
int_list_mapping = []

closure_list = []


CREATE_LIST = '{target} = create_list({length})'
SET_ELEMENT = '{tgt} = set_subscript({c}, {key}, {val})'
GET_ELEMENT = '{tgt} = get_subscript({c}, {key})'
box_vars = {
    "project" : 0,
    "inject": 0,
    "int_checks" : 0
}

lambda_count = 0
def get_lambda_label():
    global lambda_count
    label = 'lambda_' + str(lambda_count)
    lambda_count += 1
    return label


def get_new_box_is_int():
    var = 'tp_check_type_' + str(box_vars["int_checks"])
    box_vars["int_checks"] += 1
    return var

def get_new_box_proj():
    var = 'tp_proj_' + str(box_vars["project"])
    box_vars["project"] += 1
    return var

def get_new_box_inject():
    var = 'inject_' + str(box_vars["inject"])
    box_vars["inject"] += 1
    return var

def get_op_type(operand):
    if operand in box_var_mapping:
        return box_var_mapping[operand]["type"], operand

    if operand.isdigit():
        return "INT", operand
    elif operand in ['True', 'False']:
        op = '1' if operand == 'True' else '0' 
        return "BOOL", op
    else:
        return "BIG", operand

is_int_dict = {
    "INT": "is_int", "BOOL": "is_bool", "BIG": "is_big"
}

is_project_dict = {
    "INT": "project_int", "BOOL": "project_bool", "BIG": "project_big"
}

is_inject_dict = {
    "INT": "inject_int", "BOOL": "inject_bool", "BIG": "inject_big"
}


"""
Replace the variable names by adding the prefix like <prefix>_<var_name>
"""
def replace_var_names(tree, prefix):
    for node in ast.walk(tree): 
        if isinstance(node, Name):
            if(node.id not in ["print","input","eval", "int"]):
                node.id = prefix + node.id
        


"""
Returns the unique temporary/intermediate variable name
"""
def get_new_temp_var(var = None):
    if var is None:
        new_var = 'temp' + str(len(variable_mapping_dict)) + '_'
        variable_mapping_dict['______'+ new_var] = new_var
        return new_var

    if var == 'eval(input())':
        new_var = 'temp' + str(len(variable_mapping_dict)) + '_'
        eval_temp_var_names.append(new_var)
        variable_mapping_dict[var+ '_' + new_var] = new_var
        return new_var
    elif var.isdigit():
        new_var = 'temp' + str(len(variable_mapping_dict)) + '_'
        variable_mapping_dict['______'+ var] = new_var
        return new_var
    elif var in variable_mapping_dict:
        return variable_mapping_dict[var]
    else:
        new_var = 'temp' + str(len(variable_mapping_dict)) + '_'
        variable_mapping_dict[var] = new_var
        return new_var

def get_new_box_temp_var(var = None):
    if var is None:
        new_var = 'tp_box_' + str(len(box_variable_mapping_dict)) + '_'
        box_variable_mapping_dict['______'+ new_var] = new_var
        return new_var

    if var.isdigit():
        new_var = 'tp_box_' + str(len(box_variable_mapping_dict)) + '_'
        box_variable_mapping_dict['______'+ var] = new_var
        return new_var
    elif var in box_variable_mapping_dict:
        return box_variable_mapping_dict[var]
    else:
        new_var = 'tp_box_' + str(len(box_variable_mapping_dict)) + '_'
        box_variable_mapping_dict[var] = new_var
        return new_var

rest_main_code = []
def add_flat_python(indent, string, func_name = 'main', is_new_var_needed=False, is_ignore = False):
    if is_ignore:
        return string
    # func_name = "ss"
    if func_name == 'main':
        closure_list.append(indent + string)
    else:
        if is_new_var_needed:
            new_var = get_new_temp_var(string)
            flattened_prog.append(indent + new_var + " = " + string)
            string = new_var
        else:
            flattened_prog.append(indent + string)
    return string

"""
flattens the node passed
"""
label_mappings = {
    "if": 0,
    "while": 0
}

def get_if_label():
    label = label_mappings["if"] 
    label_mappings["if"] += 1
    return str(label)

def get_while_label():
    label = label_mappings["while"] 
    label_mappings["while"] += 1
    return str(label)

def get_index(value):
    for i in range(len(flattened_prog)):
        if value in flattened_prog[i]:
            return i
    return 0



def add_expressions(node, indent, string, target_var, func_name):
    if not isinstance(node, Name) and not isinstance(node, Constant)and not isinstance(node, UnaryOp) and not isinstance(node, BinOp):
        if target_var is None:
            add_flat_python(indent, string, func_name, True, False)
        else:
            add_flat_python(indent, target_var + " = " + string, func_name, func_name)


def handle_expr_node(n, indent, target_var, func_name):
    new_str = flattening_using_rec(n.value, indent, None, func_name)
    if target_var is None:
        if 'print' in new_str:
            new_str = add_flat_python(indent, new_str, func_name, func_name)
        else:
            new_str = add_flat_python(indent, new_str, func_name, True, False)
    else:
        new_str = add_flat_python(indent, new_str, func_name)
    return new_str 

def handle_if_node(n, indent, target_var, func_name):
    if_label = get_if_label()
    add_flat_python(indent, "# if" + if_label, func_name)
    if_block, else_block = '' , ''

    condition = flattening_using_rec(n.test, indent, None, func_name)
    is_var_int = get_new_temp_var(None)
    is_var_bool = get_new_temp_var(None)
    is_var_big = get_new_temp_var(None)
    
    to_cmp = get_new_temp_var(None)

    add_flat_python(indent, is_var_int + " = is_int(" + condition + ")",func_name)
    add_flat_python(indent, is_var_bool + " = is_bool(" + condition + ")",func_name)
    add_flat_python(indent, is_var_big + " = is_big(" + condition + ")",func_name)
    add_flat_python(indent, "if(" + is_var_int + "):",func_name)
    add_flat_python(indent, "\t" + to_cmp + " = project_int(" + condition + ")", func_name)
    add_flat_python(indent, "elif(" + is_var_bool + "):", func_name)
    add_flat_python(indent, "\t" + to_cmp + " = project_bool(" + condition + ")", func_name)
    add_flat_python(indent, "elif(" + is_var_big + "):", func_name)
    add_flat_python(indent, "\t" + to_cmp + " = is_true(" + condition + ")",func_name)
   
    add_flat_python(indent, "# if_condition " + if_label, func_name)
    add_flat_python(indent, "if("+ to_cmp +"):", func_name)

    for x in n.body:
        flattening_using_rec(x, indent + '\t', target_var, func_name)

    if len(n.orelse) != 0: 
        add_flat_python(indent, "# else" + if_label, func_name)
        s = add_flat_python(indent, "else:", func_name)

        for x in n.orelse:
            flattening_using_rec(x, indent +'\t', target_var, func_name)
    add_flat_python(indent, "# if_end" + if_label, func_name)    

    return "result_if_str"


def get_indent(string):
    indent = ''
    for a in string:
        if a != '\t':
            break
        indent += '\t'
    return indent


def handle_while_node(n, indent, target_var, func_name):
    while_label = get_while_label()
    while_block, else_block = '', ''
    add_flat_python(indent, "# while" + while_label, func_name)
    condition = flattening_using_rec(n.test, indent, None, func_name)
       
    if not isinstance(n.test, Constant) and not isinstance(n.test, Name):
        if isinstance(n.test, Call) and n.test.func.id == "int":
            pass
        else:                
            condition = add_flat_python(indent, condition, func_name, True, False)
    is_var_int = get_new_temp_var(None)
    is_var_big = get_new_temp_var(None)
    is_var_bool = get_new_temp_var(None)
    to_cmp = get_new_temp_var(None)

    add_flat_python(indent, is_var_int + " = is_int(" + condition + ")", func_name)
    add_flat_python(indent, is_var_bool + " = is_bool(" + condition + ")", func_name)
    add_flat_python(indent, is_var_big + " = is_big(" + condition + ")", func_name)
    add_flat_python(indent, "if(" + is_var_int + "):", func_name)
    add_flat_python(indent, "\t" + to_cmp + " = project_int(" + condition + ")", func_name)
    add_flat_python(indent, "elif(" + is_var_bool + "):", func_name)
    add_flat_python(indent, "\t" + to_cmp + " = project_bool(" + condition + ")", func_name)
    add_flat_python(indent, "elif(" + is_var_big + "):", func_name)
    add_flat_python(indent, "\t" + to_cmp + " = is_true(" + condition + ")", func_name)

    add_flat_python(indent, "while("+ to_cmp +"):",func_name)
    for x in n.body:
        flattening_using_rec(x, indent + '\t', None, func_name)
           
    if len(n.orelse) != 0: 
        add_flat_python(indent, "# else" + while_label, func_name)
        add_flat_python(indent, "else:", func_name)
        else_block = "\n".join([flattening_using_rec(x, indent +'\t', None, func_name) for x in n.orelse])

    if func_name != 'main':
        get_while_cond_start_index = flattened_prog.index(indent + "# while" + while_label)
        get_while_cond_end_index = flattened_prog.index(indent + "while("+ to_cmp +"):")
        add_flat_python(indent + "\t", "#Condition re-evaluation while" + while_label, func_name)
        for i in range(get_while_cond_start_index+1, get_while_cond_end_index):
            add_flat_python("\t", flattened_prog[i], func_name)

        add_flat_python(indent, "# end_while" + while_label, func_name) 
    else:
        get_while_cond_start_index = closure_list.index(indent + "# while" + while_label)
        get_while_cond_end_index = closure_list.index(indent + "while("+ to_cmp +"):")
        add_flat_python(indent + "\t", "#Condition re-evaluation while" + while_label, func_name)
        for i in range(get_while_cond_start_index+1, get_while_cond_end_index):
            add_flat_python("\t", closure_list[i], func_name)

        add_flat_python(indent, "# end_while" + while_label, func_name) 
    return "RESULT"


def handle_unary_node(n, indent, target_var, func_name):
    op = flattening_using_rec(n.op, indent, None, func_name)
    if op == "not":
        target_var = get_new_temp_var(None) if target_var is None else target_var
        if isinstance(n.operand, Constant):
            temp_var = get_new_temp_var(None)
            value = str(n.operand.value)
            
            if value in ["0", "False"]:
                add_flat_python(indent, target_var + " = 5", func_name)
            else:
                add_flat_python(indent, target_var + " = 1" , func_name)
            return target_var

        elif isinstance(n.operand, Name):
            value = n.operand.id
        else:
            value = flattening_using_rec(n.operand, indent, None, func_name)
            if 'temp' not in value:
                value = add_flat_python(indent, value, func_name, True, False)

        is_var_int = get_new_box_is_int()
        is_var_big = get_new_box_is_int()
        is_var_bool = get_new_box_is_int()
        add_flat_python(indent, is_var_int + " = is_int(" + value + ")", func_name)
        add_flat_python(indent, is_var_bool + " = is_bool(" + value + ")", func_name)
        add_flat_python(indent, is_var_big + " = is_big(" + value + ")", func_name)
        add_flat_python(indent, "if(" + is_var_int + "):", func_name)
        add_flat_python(indent, "\t" + value + " = project_int(" + value + ")", func_name)
        add_flat_python(indent, "elif(" + is_var_bool + "):", func_name)
        add_flat_python(indent, "\t" + value + " = project_bool(" + value + ")", func_name)
        add_flat_python(indent, "elif(" + is_var_big + "):", func_name)
        add_flat_python(indent, "\t" + value + " = is_true(" + value + ")", func_name)
        add_flat_python(indent, "if(" + value + "):", func_name)
        add_flat_python(indent, "\t" + target_var + " = 1", func_name)
        add_flat_python(indent, "else:", func_name)
        add_flat_python(indent, "\t" + target_var + " = 5", func_name)      
        new_var = target_var
    else:
        value = flattening_using_rec(n.operand, indent, None, func_name)
        new_var = get_new_temp_var(value)
        proj_var = get_new_box_proj()
        if isinstance(n.operand, Constant):
            if value in ["True", "False"]:
                value = '1' if value == "True" else '0'

            add_flat_python(indent, proj_var + " = -" + value, func_name)
            add_flat_python(indent, new_var + " = inject_int(" + proj_var + ")", func_name)
        else:
            add_flat_python(indent, proj_var + " = project_int(" + value + ")", func_name)
            add_flat_python(indent, proj_var + " = -" + proj_var, func_name)
            add_flat_python(indent, new_var + " = inject_int(" + proj_var + ")", func_name)
    return new_var 



def handle_call_node(n, indent, target_var, func_name):
    prev_func = func_name
    new_str = ''
    func_name = flattening_using_rec(n.func, indent, target_var, prev_func)
    if '_' == func_name[0]:
        func_name = func_name[1:]
    args_list = []
    arg_param = ''
    target_var = target_var if target_var is not None else get_new_temp_var(None)
    
    for x in n.args:
        if isinstance(x, Name):
            if prev_func != "main" and x.id.replace('_', '') in funcs.function_collection[prev_func].bound_vars:
                x.id = "_" + prev_func + x.id
                arg_param = x.id
            else:
                arg_param = flattening_using_rec(x, indent, None, prev_func)
        else:
            arg_param = flattening_using_rec(x, indent, None, prev_func)
            if isinstance(x, Constant) or isinstance(x, Compare):
                pass
            elif n.func.id in ["eval", "input"] and isinstance(x, Call):
                pass
            elif n.func.id == "int" and not isinstance(x, Constant) and not isinstance(x, Name):
                if isinstance(x, UnaryOp) and (isinstance(x.operand, Name) or isinstance(x.operand, Constant)):
                    pass
                else:
                    arg_param = add_flat_python(indent, arg_param, prev_func, True, False)
            elif isinstance(x, BinOp) or isinstance(x, BoolOp) or isinstance(x, List) or isinstance(x, Dict):
                pass
            elif (n.func.id)[1:] in list(funcs.function_collection.keys()):
                pass
            else:
                arg_param = add_flat_python(indent, arg_param, prev_func, True, False)

        if arg_param.isdigit():
            temp_inject_var = get_new_box_inject()
            add_flat_python(indent, temp_inject_var + " = " + str(int(arg_param)<<2), prev_func)
            arg_param = temp_inject_var
        args_list.append(arg_param)
    
    if func_name not in ["print", "int", "eval", "input"]:
        func_ptr = get_new_temp_var(None)
        free_vars = get_new_temp_var(None)

        if func_name in func_mapping:            
            add_flat_python(indent, free_vars + " = get_free_vars(" + func_mapping[func_name] + ")", prev_func)
            add_flat_python(indent, func_ptr + " = get_fun_ptr(" + func_mapping[func_name] + ")", prev_func)
            if args_list:
                add_flat_python(indent, target_var + " = function_return(" + func_ptr + ", " + free_vars + ", " + ",".join(args_list) + ")", prev_func)
            else:
                add_flat_python(indent, target_var + " = function_return(" + func_ptr + ", " + free_vars + ")", prev_func)
        else:
            if isinstance(n.func, Name):
                add_flat_python(indent, free_vars + " = get_free_vars(" + n.func.id + ")", prev_func)
                add_flat_python(indent, func_ptr + " = get_fun_ptr(" + n.func.id + ")", prev_func)
            else:
                add_flat_python(indent, free_vars + " = get_free_vars(" + func_name + ")", prev_func)
                add_flat_python(indent, func_ptr + " = get_fun_ptr(" + func_name + ")", prev_func)
            if args_list:
                add_flat_python(indent, target_var + " = function_return(" + func_ptr + ", " + free_vars + ", " + ",".join(args_list) + ")", prev_func)
            else:
                add_flat_python(indent, target_var + " = function_return(" + func_ptr + ", " + free_vars + ")", prev_func)   
        
        new_str = target_var
    elif n.func.id == 'int':
        value = "\n".join(args_list) 
        add_flat_python(indent, value + " = project_bool(" + value + ")", prev_func)
        add_flat_python(indent, value + " = inject_int(" + value + ")", prev_func)        
        new_str = value
    else:
        var = ",".join(args_list)
        new_str = func_name + '(' + var + ')'
        if new_str == "eval(input())":
            add_flat_python(indent, target_var + " = " + new_str, prev_func)
            new_str = target_var
    return new_str 

def handle_ifexp_node(n, indent, target_var, func_name):
    target_var = target_var if target_var is not None else get_new_temp_var(None)
    IF_EXP_STR = "if({cond}):\n{indent}\t{tgt} = {if_value}\n{indent}else:\n{indent}\t{tgt} = {else_value}"

    
    condition = flattening_using_rec(n.test, indent, None, func_name)
    if not isinstance(n.test, Constant) and not isinstance(n.test, Name):
        if isinstance(n.test, Call) and n.test.func.id == "int":
            pass
        # else:                
        #     condition = add_flat_python(indent, condition, func_name, True, False)
    is_var_int = get_new_temp_var(None)
    is_var_big = get_new_temp_var(None)
    is_var_bool = get_new_temp_var(None)
    to_cmp = get_new_temp_var(None)

    add_flat_python(indent, is_var_int + " = is_int(" + condition + ")", func_name)
    add_flat_python(indent, is_var_bool + " = is_bool(" + condition + ")", func_name)
    add_flat_python(indent, is_var_big + " = is_big(" + condition + ")", func_name)
    add_flat_python(indent, "if(" + is_var_int + "):", func_name)
    add_flat_python(indent, "\t" + to_cmp + " = project_int(" + condition + ")", func_name)
    add_flat_python(indent, "elif(" + is_var_bool + "):", func_name)
    add_flat_python(indent, "\t" + to_cmp + " = project_bool(" + condition + ")", func_name)
    add_flat_python(indent, "elif(" + is_var_big + "):", func_name)
    add_flat_python(indent, "\t" + to_cmp + " = is_true(" + condition + ")", func_name)    

    add_flat_python(indent, "if("+ to_cmp +"):", func_name)

    if_block, else_block = '' , ''
    if isinstance(n.body, Constant):
        value = str(n.body.value)
        if value == "True":
            value = "5"
        elif value == "False":
            value = "1"
        else:
            value = str(int(value)<<2)
        add_flat_python(indent+'\t', target_var + " = " + value, func_name)
    else:
        value = flattening_using_rec(n.body, indent+"\t", None, func_name)
        add_flat_python(indent+"\t", target_var + " = " + value, func_name)
    
    add_flat_python(indent, "else:", func_name)
    if isinstance(n.orelse, Constant):
        value = str(n.orelse.value)
        if value == "True":
            value = "5"
        elif value == "False":
            value = "1"
        else:
            value = str(int(value)<<2)      
        add_flat_python(indent+'\t', target_var + " = " + value, func_name)
    else:
        value = flattening_using_rec(n.orelse, indent+"\t", None, func_name)
        add_flat_python(indent+"\t", target_var + " = " + value, func_name)
    return target_var

def handle_assign_node(n, indent, target_var, func_name):
    is_subscript_op = False
    if isinstance(n.targets[0], Name):
        op = n.targets[0].id
        if func_name != 'main' and op.replace('_', '') in funcs.function_collection[func_name].bound_vars:
            op = "_" + func_name + op
    elif isinstance(n.targets[0], Subscript):
        is_subscript_op = True
        op = get_new_temp_var(None)
    if isinstance(n.value, Name):
        if func_name != "main" and n.value.id.replace('_', '') in funcs.function_collection[func_name].bound_vars:
            n.value.id = "_" + func_name + n.value.id
        add_flat_python(indent, op + " = " + n.value.id, func_name)
    elif isinstance(n.value, IfExp) or isinstance(n.value, BoolOp) or isinstance(n.value, List) or isinstance(n.value, Dict):
        value = flattening_using_rec(n.value, indent, op, func_name)
    elif isinstance(n.value, BinOp):
        value = flattening_using_rec(n.value, indent, op, func_name)
        if value.isdigit():
            int_list_mapping.append(op)
            temp_var = get_new_temp_var(None)
            temp_target = get_new_temp_var(None)
            add_flat_python(indent, CREATE_LIST.format(target = temp_target, length = 4), func_name) # injected length
            add_flat_python(indent, temp_target + " = inject_big(" + temp_target + ")", func_name)
            add_flat_python(indent, SET_ELEMENT.format(tgt=temp_var, c=temp_target, key=0, val=value), func_name)
            add_flat_python(indent, GET_ELEMENT.format(tgt=op, key=0, c=temp_target), func_name)
        elif value != op and '+' in value:
            add_boxing_layer(indent, value.split('+')[0], value.split('+')[1], op)
        elif '+' not in value and op != value:
            add_flat_python(indent, op + " = "+ value, func_name)
    elif isinstance(n.value, UnaryOp):
        value = flattening_using_rec(n.value, indent, op, func_name)
        if op == "not":
            pass
        else:                  
            add_flat_python(indent, op + ' = ' + value, func_name)      
    else:
        value = flattening_using_rec(n.value, indent, op, func_name)
        if op == value:
            pass
        elif isinstance(n.value, Constant):
            if value == "True":
                value = "5"
            elif value == "False":
                value = "1"
            else:
                value = str(int(value)<<2)
            temp_var = get_new_temp_var(None)
            temp_target = get_new_temp_var(None)

            add_flat_python(indent, CREATE_LIST.format(target = temp_target, length = 4), func_name) # injected length
            add_flat_python(indent, temp_target + " = inject_big(" + temp_target + ")", func_name)
            add_flat_python(indent, SET_ELEMENT.format(tgt=temp_var, c=temp_target, key=0, val=value), func_name)
            add_flat_python(indent, GET_ELEMENT.format(tgt=op, key=0, c=temp_target), func_name)
        elif isinstance(n.value, Name):
            add_flat_python(indent, op + ' = ' + value, func_name)
        elif value == 'eval(input())':
            # temp_var = get_new_temp_var(None)
            add_flat_python(indent, op + " = " + value, func_name)
        else:
            add_flat_python(indent, op + ' = ' + value, func_name)
        int_list_mapping.append(op)

    if is_subscript_op:
        value = flattening_using_rec(n.targets[0].value, indent, target_var, func_name)
        index = flattening_using_rec(n.targets[0].slice, indent, target_var, func_name)
        if index.isdigit():
            temp_var = get_new_box_proj()
            add_flat_python(indent, temp_var + " = " + str(int(index)<<2), func_name )
            index = temp_var
        temp_var = get_new_temp_var(None)
        add_flat_python(indent, SET_ELEMENT.format(tgt=temp_var, c=value, key=index, val=op), func_name)
    return op




def handle_boolop_node(n, indent, target_var, func_name):
    op = flattening_using_rec(n.op, indent, None, func_name)
    new_var = get_new_temp_var(None) if target_var is None else target_var
    inst = []
    cache_values = []
    op_values = []
    for i in range(0, len(n.values)):
        value = flattening_using_rec(n.values[i], indent, None, func_name)
        cache_values.append(value)
        if isinstance(n.values[i], Constant):
            if value == "True":
                value = "5"
            elif value == "False":
                value = "1"
            else:
                value = str(int(value)<<2)
            op_values.append(value)
        else:
            op_values.append(value)
    
    is_all_constant = True
    for cache_value in cache_values:
        if not cache_value.isdigit():
            is_all_constant = False
    
    if is_all_constant:
        if op == "and":
            add_flat_python(indent, new_var + " = " + str(int(cache_values[-1])<<2), func_name)
        elif op == "or":
            add_flat_python(indent, new_var + " = "+ str(int(cache_values[0])<<2), func_name)
        return new_var
    elif len(list(set(cache_values))) == 1:
        return cache_values[0] 


    indent_level = indent
    if op == "and":
        for i in range(len(op_values)-1):
            is_left_var_int = get_new_box_is_int()
            is_left_var_big = get_new_box_is_int()
            is_left_var_bool = get_new_box_is_int()

            to_cmp = get_new_box_proj()
            add_flat_python(indent_level, is_left_var_int + " = is_int(" + op_values[i] + ")", func_name)
            add_flat_python(indent_level, is_left_var_bool + " = is_bool(" + op_values[i] + ")", func_name)
            add_flat_python(indent_level, is_left_var_big + " = is_big(" + op_values[i] + ")", func_name)
            add_flat_python(indent_level, "if(" + is_left_var_int + "):", func_name)
            add_flat_python(indent_level +"\t", to_cmp + " = project_int(" + op_values[i] + ")", func_name)
            add_flat_python(indent_level, "elif(" + is_left_var_bool + "):", func_name)
            add_flat_python(indent_level + "\t", to_cmp + " = project_bool(" + op_values[i] + ")", func_name)
            add_flat_python(indent_level, "elif(" + is_left_var_big + "):", func_name)
            add_flat_python(indent_level + "\t", to_cmp + " = is_true(" + op_values[i] + ")", func_name)
            add_flat_python(indent_level, "if(" + to_cmp + "):", func_name)
            indent_level += '\t'
        add_flat_python(indent_level, new_var + " = " + op_values[-1], func_name)
        for i in reversed(range(len(op_values) - 1)):
            indent_level = indent_level[1:]
            add_flat_python(indent_level, "else:", func_name)
            add_flat_python(indent_level + '\t', new_var + " = " + op_values[i], func_name)

    elif op == "or":    
        for i in range(len(op_values)-1):
            is_left_var_int = get_new_box_is_int()
            is_left_var_big = get_new_box_is_int()
            is_left_var_bool = get_new_box_is_int()
            to_cmp = get_new_box_proj()
            add_flat_python(indent_level, is_left_var_int + " = is_int(" + op_values[i] + ")", func_name)
            add_flat_python(indent_level, is_left_var_big + " = is_bool(" + op_values[i] + ")", func_name)
            add_flat_python(indent_level, is_left_var_bool + " = is_big(" + op_values[i] + ")", func_name)
            add_flat_python(indent_level, "if(" + is_left_var_int + "):", func_name)
            add_flat_python(indent_level + "\t", to_cmp + " = project_int(" + op_values[i] + ")", func_name)
            add_flat_python(indent_level, "elif(" + is_left_var_bool + "):", func_name)
            add_flat_python(indent_level + "\t", to_cmp + " = project_bool(" + op_values[i] + ")", func_name)
            add_flat_python(indent_level, "elif(" + is_left_var_big + "):", func_name)
            add_flat_python(indent_level + "\t", to_cmp + " = is_true(" + op_values[i] + ")", func_name)
            add_flat_python(indent_level, "if(" + to_cmp + "):", func_name)
            add_flat_python(indent_level + "\t", new_var + " = " + op_values[i], func_name)
            add_flat_python(indent_level, "else:", func_name)
            indent_level += '\t'
        add_flat_python(indent_level, new_var + " = " + op_values[-1], func_name)

    return new_var

def add_boxing_layer(indent, left_operand, right_operand, target_var, func_name):
    target_var = get_new_temp_var(None) if target_var is None else target_var
    temp_project_l = get_new_box_proj()
    is_left_var_int = get_new_box_is_int()
    is_left_var_bool = get_new_box_is_int()
    is_left_var_big = get_new_box_is_int()
    if left_operand == right_operand:
        add_flat_python(indent, is_left_var_int +' = is_int(' + left_operand + ")", func_name)
        add_flat_python(indent, is_left_var_big +' = is_big(' + left_operand + ")", func_name)
        add_flat_python(indent, is_left_var_bool +' = is_bool(' + left_operand + ")", func_name)
        add_flat_python(indent, 'if(' + is_left_var_int + "):", func_name)
        add_flat_python(indent, "\t" + temp_project_l + " = project_int(" + left_operand + ")", func_name)
        add_flat_python(indent, "\t" + temp_project_l + " = " + temp_project_l + " + " + temp_project_l, func_name)
        add_flat_python(indent, "\t" + target_var + " = inject_int(" + temp_project_l + ")", func_name)
        add_flat_python(indent, 'elif(' + is_left_var_bool + "):", func_name)
        add_flat_python(indent, "\t" + temp_project_l + " = project_bool(" + left_operand + ")", func_name)
        add_flat_python(indent, "\t" + temp_project_l + " = " + temp_project_l + " + " + temp_project_l, func_name)
        add_flat_python(indent, "\t" + target_var + " = inject_bool(" + temp_project_l + ")", func_name)
        add_flat_python(indent, 'elif(' + is_left_var_big + "):", func_name)
        add_flat_python(indent, "\t" + temp_project_l + " = project_big(" + left_operand + ")", func_name)
        add_flat_python(indent, "\t" + temp_project_l + " = add(" + temp_project_l + ", " + temp_project_l + ")", func_name)
        add_flat_python(indent, "\t" + target_var + " = inject_big(" + temp_project_l + ")", func_name)
    else:
        is_right_var_int = get_new_box_is_int()
        is_right_var_big = get_new_box_is_int()
        is_right_var_bool = get_new_box_is_int()
        temp_project_r = get_new_box_proj() 

        add_flat_python(indent, is_left_var_int +' = is_int(' + left_operand + ")", func_name)
        add_flat_python(indent, is_left_var_big +' = is_big(' + left_operand + ")", func_name)
        add_flat_python(indent, is_left_var_bool +' = is_bool(' + left_operand + ")", func_name)
        add_flat_python(indent, 'if(' + is_left_var_int + "):", func_name)
        add_flat_python(indent + "\t", is_right_var_int +' = is_int(' + right_operand + ")", func_name)
        # add_flat_python(indent + "\t", is_right_var_big +' = is_big(' + right_operand + ")", func_name)
        add_flat_python(indent + "\t", is_right_var_bool +' = is_bool(' + right_operand + ")", func_name)
        add_flat_python(indent + "\t", 'if(' + is_right_var_int + "):", func_name)
        add_flat_python(indent, "\t\t" + temp_project_l + " = project_int(" + left_operand + ")", func_name)
        add_flat_python(indent, "\t\t" + temp_project_r + " = project_int(" + right_operand + ")", func_name)
        add_flat_python(indent, "\t\t" + temp_project_l + " = " + temp_project_l + " + " + temp_project_r, func_name)
        add_flat_python(indent, "\t\t" + target_var + " = inject_int(" + temp_project_l + ")", func_name)
        add_flat_python(indent + "\t", 'if(' + is_right_var_bool + "):", func_name)
        add_flat_python(indent, "\t\t" + temp_project_l + " = project_int(" + left_operand + ")", func_name)
        add_flat_python(indent, "\t\t" + temp_project_r + " = project_bool(" + right_operand + ")", func_name)
        add_flat_python(indent, "\t\t" + temp_project_l + " = " + temp_project_l + " + " + temp_project_r, func_name)
        add_flat_python(indent, "\t\t" + target_var + " = inject_int(" + temp_project_l + ")", func_name)

        add_flat_python(indent, 'elif(' + is_left_var_bool + "):", func_name)
        add_flat_python(indent + "\t", is_right_var_int +' = is_int(' + right_operand + ")", func_name)
        # add_flat_python(indent + "\t", is_right_var_big +' = is_big(' + right_operand + ")", func_name)
        add_flat_python(indent + "\t", is_right_var_bool +' = is_bool(' + right_operand + ")", func_name)
        add_flat_python(indent + "\t", 'if(' + is_right_var_int + "):", func_name)
        add_flat_python(indent, "\t\t" + temp_project_l + " = project_bool(" + left_operand + ")", func_name)
        add_flat_python(indent, "\t\t" + temp_project_r + " = project_int(" + right_operand + ")", func_name)
        add_flat_python(indent, "\t\t" + temp_project_l + " = " + temp_project_l + " + " + temp_project_r, func_name)
        add_flat_python(indent, "\t\t" + target_var + " = inject_int(" + temp_project_l + ")", func_name)
        add_flat_python(indent + "\t", 'if(' + is_right_var_bool + "):", func_name)
        add_flat_python(indent, "\t\t" + temp_project_l + " = project_bool(" + left_operand + ")", func_name)
        add_flat_python(indent, "\t\t" + temp_project_r + " = project_bool(" + right_operand + ")", func_name)
        add_flat_python(indent, "\t\t" + temp_project_l + " = " + temp_project_l + " + " + temp_project_r, func_name)
        add_flat_python(indent, "\t\t" + target_var + " = inject_int(" + temp_project_l + ")", func_name)

        add_flat_python(indent, 'elif(' + is_left_var_big + "):", func_name)
        # add_flat_python(indent + "\t", is_right_var_int +' = is_int(' + right_operand + ")", func_name)
        add_flat_python(indent + "\t", is_right_var_big +' = is_big(' + right_operand + ")", func_name)
        # add_flat_python(indent + "\t", is_right_var_bool +' = is_bool(' + right_operand + ")", func_name)
        add_flat_python(indent + "\t", 'if(' + is_right_var_big + "):", func_name)
        add_flat_python(indent, "\t\t" + temp_project_l + " = project_big(" + left_operand + ")", func_name)
        add_flat_python(indent, "\t\t" + temp_project_r + " = project_big(" + right_operand + ")", func_name)
        add_flat_python(indent, "\t\t" + temp_project_l + " = add(" + temp_project_l + ", " + temp_project_r + ")", func_name)
        add_flat_python(indent, "\t\t" + target_var + " = inject_big(" + temp_project_l + ")", func_name)
        
    return target_var

def get_prev_occurance(operand):
    if operand in variable_mapping_dict:
        operand = variable_mapping_dict[operand]  
    elif operand == 'eval(input())':
        operand = eval_temp_var_names[0]
        eval_temp_var_names.remove(operand)
    return operand


def handle_binop_node(n, indent, target_var, func_name):
    BIN_OP_STR = "{src_op}+{tgt_op}"

    left_operand = flattening_using_rec(n.left, indent, None, func_name)
    right_operand = flattening_using_rec(n.right, indent, None, func_name)

    if left_operand.isdigit() and right_operand.isdigit(): 
        return str(int(left_operand) + int(right_operand))
    else:
        if isinstance(n.left, Constant):
            left_var = get_new_box_inject()
            if left_operand in ["True", "False"]:
                left_operand = "1" if left_operand == "True" else "0"
            add_flat_python(indent, left_var + " = inject_int(" + left_operand + ")", func_name)
            left_operand = left_var
        elif isinstance(n.left, Name):
            if func_name != 'main' and left_operand.replace("_", "") in funcs.function_collection[func_name].bound_vars:
                left_operand = '_' + func_name + left_operand


        if isinstance(n.right, Constant):
            right_var = get_new_box_inject()
            if right_operand in ["True", "False"]:
                right_operand = "1" if right_operand == "True" else "0"
            add_flat_python(indent, right_var + " = inject_int(" + right_operand + ")", func_name)
            right_operand = right_var
        elif isinstance(n.right, Name):
            if func_name != 'main' and right_operand.replace("_", "") in funcs.function_collection[func_name].bound_vars:
                right_operand = '_' + func_name + right_operand

        add_expressions(n.left, indent, left_operand, None, func_name)
        add_expressions(n.right, indent, right_operand, None, func_name)
        if right_operand.isdigit():
            left_operand, right_operand = right_operand, left_operand

        if target_var == right_operand:
            temp_var = get_new_temp_var(None)
            target_var = add_boxing_layer(indent, left_operand, right_operand, temp_var, func_name)
        else:
            target_var = add_boxing_layer(indent, left_operand, right_operand, target_var, func_name)
        
        return target_var 



def handle_compare_node(n, indent, target_var, func_name):
    target_var = get_new_temp_var(None) if target_var is None else target_var
    left_op = flattening_using_rec(n.left, indent, None, func_name)
    is_left_op_constant, is_right_op_constant = False, False
    if isinstance(n.left, Constant):
        if left_op == "True":
            left_op = "5"
        elif left_op == "False":
            left_op = "1"
        else:
            is_left_op_constant = True
            left_op = left_op
    elif isinstance(n.left, Name):
        if left_op in int_list_mapping:
            left_op = left_op
        
        if func_name != 'main' and left_op.replace("_", "") in funcs.function_collection[func_name].bound_vars:
            left_op = '_' + func_name + left_op

    value = flattening_using_rec(n.comparators[0], indent, None, func_name)
    if isinstance(n.comparators[0], Constant):
        if value == "True":
            value = "5"
        elif value == "False":
            value = "1"
        else:
            is_right_op_constant = True
            value = str(int(value))
    elif isinstance(n.comparators[0], Name):
        if value in int_list_mapping:
            value = value 

        if func_name != 'main' and value.replace("_", "")  in funcs.function_collection[func_name].bound_vars:
            value = '_' + func_name + value

    if is_left_op_constant and is_right_op_constant:
        if left_op == value:
            is_equal = True
        else:
            is_equal = False
        if isinstance(n.ops[0], Eq) or isinstance(n.ops[0], Is):
            if is_equal:
                add_flat_python(indent, target_var + " = 5", func_name)
            else:
                add_flat_python(indent, target_var + " = 1", func_name)
        elif isinstance(n.ops[0], NotEq) or isinstance(n.ops[0], IsNot):
            if is_equal:
                add_flat_python(indent, target_var + " = 1", func_name)
            else:
                add_flat_python(indent, target_var + " = 5", func_name)
    
    elif is_right_op_constant:
        is_left_var_int = get_new_box_is_int()
        project_l = get_new_box_proj()
        add_flat_python(indent, is_left_var_int + " = is_int("+ left_op +")", func_name)
        add_flat_python(indent, "if(" + is_left_var_int + "):", func_name)
        add_flat_python(indent + '\t', target_var + " = project_int(" + left_op + ")", func_name)
        if isinstance(n.ops[0], Eq) or isinstance(n.ops[0], Is):
            add_flat_python(indent + '\t', target_var + " = equals(" + value + ", " + target_var + ")", func_name)
            add_flat_python(indent + '\t', target_var + " = inject_bool(" + target_var + ")", func_name)
        elif isinstance(n.ops[0], NotEq) or isinstance(n.ops[0], IsNot):
            add_flat_python(indent + '\t', target_var + " = not_equals(" + value + ", " + target_var + ")", func_name)
            add_flat_python(indent + '\t', target_var + " = inject_bool(" + target_var + ")", func_name)
        add_flat_python(indent, "else:", func_name)
        if isinstance(n.ops[0], Eq) or isinstance(n.ops[0], Is):
            add_flat_python(indent + '\t', target_var + " = 1", func_name)
        elif isinstance(n.ops[0], NotEq) or isinstance(n.ops[0], IsNot):
            add_flat_python(indent + '\t', target_var + " = 5", func_name)
    
    elif is_left_op_constant:
        left_op, value = value, left_op
        is_left_var_int = get_new_box_is_int()
        project_l = get_new_box_proj()
        
        add_flat_python(indent, is_left_var_int + " = is_int("+ left_op +")", func_name)
        add_flat_python(indent, "if(" + is_left_var_int + "):", func_name)
        add_flat_python(indent + '\t', project_l + " = project_int(" + left_op + ")", func_name)
        if isinstance(n.ops[0], Eq) or isinstance(n.ops[0], Is):
            add_flat_python(indent + '\t', target_var + " = equals(" + value + ", " + project_l + ")", func_name)
            add_flat_python(indent + '\t', target_var + " = inject_bool(" + target_var + ")", func_name)
        elif isinstance(n.ops[0], NotEq) or isinstance(n.ops[0], IsNot):
            add_flat_python(indent + '\t', target_var + " = not_equals(" + value + ", " + project_l + ")", func_name)
            add_flat_python(indent + '\t', target_var + " = inject_bool(" + target_var + ")", func_name)
        add_flat_python(indent, "else:", func_name)
        if isinstance(n.ops[0], Eq) or isinstance(n.ops[0], Is):
            add_flat_python(indent + '\t', target_var + " = 1", func_name)
        elif isinstance(n.ops[0], NotEq) or isinstance(n.ops[0], IsNot):
            add_flat_python(indent + '\t', target_var + " = 5", func_name)
    else:
        is_left_var_int = get_new_box_is_int()
        is_left_var_bool = get_new_box_is_int()
        is_left_var_big = get_new_box_is_int()
        is_right_var_int = get_new_box_is_int()
        is_right_var_bool = get_new_box_is_int()
        is_right_var_big = get_new_box_is_int()
        project_l = get_new_box_proj()
        project_r = get_new_box_proj()

        add_flat_python(indent, is_left_var_int + " = is_int("+ left_op +")", func_name)
        add_flat_python(indent, is_left_var_big + " = is_big("+ left_op +")", func_name)
        add_flat_python(indent, is_left_var_bool + " = is_bool("+ left_op +")", func_name)
        add_flat_python(indent, "if(" + is_left_var_int + "):", func_name)
        add_flat_python(indent + '\t', is_right_var_int + " = is_int("+ value +")", func_name)
        add_flat_python(indent + '\t', is_right_var_bool + " = is_bool("+ value +")", func_name)
        add_flat_python(indent + '\t', "if(" + is_right_var_int + "):", func_name)
        add_flat_python(indent + '\t\t', project_l + " = project_int(" + left_op + ")", func_name)
        add_flat_python(indent + '\t\t', project_r + " = project_int(" + value + ")", func_name)
        if isinstance(n.ops[0], Eq) or isinstance(n.ops[0], Is):
            add_flat_python(indent + '\t\t', project_l + " = equals(" + project_l + ", " + project_r + ")", func_name)
            add_flat_python(indent + '\t\t', target_var + " = inject_bool(" + project_l + ")", func_name)
        elif isinstance(n.ops[0], NotEq) or isinstance(n.ops[0], IsNot):
            add_flat_python(indent + '\t\t', project_l + " = not_equals(" + project_l + ", " + project_r + ")", func_name)
            add_flat_python(indent + '\t\t', target_var + " = inject_bool(" + project_l + ")", func_name)
        add_flat_python(indent + '\t', "elif(" + is_right_var_bool + "):", func_name)
        add_flat_python(indent + '\t\t', project_l + " = project_int(" + left_op + ")", func_name)
        add_flat_python(indent + '\t\t', project_r + " = project_bool(" + value + ")", func_name)
        if isinstance(n.ops[0], Eq):
            add_flat_python(indent + '\t\t', project_l + " = equals(" + project_l + ", " + project_r + ")", func_name)
            add_flat_python(indent + '\t\t', target_var + " = inject_bool(" + project_l + ")", func_name)
        elif isinstance(n.ops[0], NotEq):
            add_flat_python(indent + '\t\t', project_l + " = not_equals(" + project_l + ", " + project_r + ")", func_name)
            add_flat_python(indent + '\t\t', target_var + " = inject_bool(" + project_l + ")", func_name)
        elif isinstance(n.ops[0], Is):
            add_flat_python(indent + '\t\t', target_var + " = 1", func_name)
        elif isinstance(n.ops[0], IsNot):
            add_flat_python(indent + '\t\t', target_var + " = 5", func_name)
        add_flat_python(indent + '\t', "else:", func_name)
        if isinstance(n.ops[0], Eq) or isinstance(n.ops[0], Is):
            add_flat_python(indent + '\t\t', target_var + " = 1", func_name)
        elif isinstance(n.ops[0], NotEq) or isinstance(n.ops[0], IsNot):
            add_flat_python(indent + '\t\t', target_var + " = 5", func_name)
        add_flat_python(indent, "elif(" + is_left_var_bool + "):", func_name)
        add_flat_python(indent + '\t', is_right_var_int + " = is_int("+ value +")", func_name)
        add_flat_python(indent + '\t', is_right_var_bool + " = is_bool("+ value +")", func_name)
        add_flat_python(indent + '\t', "if(" + is_right_var_bool + "):", func_name)
        add_flat_python(indent + '\t\t', project_l + " = project_bool(" + left_op + ")", func_name)
        add_flat_python(indent + '\t\t', project_r + " = project_bool(" + value + ")", func_name)
        if isinstance(n.ops[0], Eq) or isinstance(n.ops[0], Is):
            add_flat_python(indent + '\t\t', project_l + " = equals(" + project_l + ", " + project_r + ")", func_name)
            add_flat_python(indent + '\t\t', target_var + " = inject_bool(" + project_l + ")", func_name)
        elif isinstance(n.ops[0], NotEq) or isinstance(n.ops[0], IsNot):
            add_flat_python(indent + '\t\t', project_l + " = not_equals(" + project_l + ", " + project_r + ")", func_name)
            add_flat_python(indent + '\t\t', target_var + " = inject_bool(" + project_l + ")", func_name)
        add_flat_python(indent + '\t', "elif(" + is_right_var_int + "):", func_name)
        add_flat_python(indent + '\t\t', project_l + " = project_bool(" + left_op + ")", func_name)
        add_flat_python(indent + '\t\t', project_r + " = project_int(" + value + ")", func_name)
        if isinstance(n.ops[0], Eq):
            add_flat_python(indent + '\t\t', project_l + " = equals(" + project_l + ", " + project_r + ")", func_name)
            add_flat_python(indent + '\t\t', target_var + " = inject_bool(" + project_l + ")", func_name)
        elif isinstance(n.ops[0], NotEq):
            add_flat_python(indent + '\t\t', project_l + " = not_equals(" + project_l + ", " + project_r + ")", func_name)
            add_flat_python(indent + '\t\t', target_var + " = inject_bool(" + project_l + ")", func_name)
        elif isinstance(n.ops[0], Is):
            add_flat_python(indent + '\t\t', target_var + " = 1", func_name)
        elif isinstance(n.ops[0], IsNot):
            add_flat_python(indent + '\t\t', target_var + " = 5", func_name)
        add_flat_python(indent + '\t', "else:", func_name)
        if isinstance(n.ops[0], Eq) or isinstance(n.ops[0], Is):
            add_flat_python(indent + '\t\t', target_var + " = 1", func_name)
        elif isinstance(n.ops[0], NotEq) or isinstance(n.ops[0], IsNot):
            add_flat_python(indent + '\t\t', target_var + " = 5 ", func_name)
        add_flat_python(indent, "elif(" + is_left_var_big + "):", func_name)
        add_flat_python(indent + '\t', is_right_var_big + " = is_big("+ value +")", func_name)
        add_flat_python(indent + '\t', "if(" + is_right_var_big + "):", func_name)
        add_flat_python(indent + '\t\t', project_l + " = project_big(" + left_op + ")", func_name)
        add_flat_python(indent + '\t\t', project_r + " = project_big(" + value + ")", func_name)
        if isinstance(n.ops[0], Eq):
            add_flat_python(indent + '\t\t', project_l + " = equals_big(" + project_l + ", " + project_r + ")", func_name)
            add_flat_python(indent + '\t\t', target_var + " = inject_bool(" + project_l + ")", func_name)
        elif isinstance(n.ops[0], NotEq):
            add_flat_python(indent + '\t\t', project_l + " = not_equals_big(" + project_l + ", " + project_r + ")", func_name)
            add_flat_python(indent + '\t\t', target_var + " = inject_bool(" + project_l + ")", func_name)
        elif isinstance(n.ops[0], Is):
            add_flat_python(indent + '\t\t', project_l + " = equals(" + project_l + ", " + project_r + ")", func_name)
            add_flat_python(indent + '\t\t', target_var + " = inject_bool(" + project_l + ")", func_name)
        elif isinstance(n.ops[0], IsNot):
            add_flat_python(indent + '\t\t', project_l + " = not_equals(" + project_l + ", " + project_r + ")", func_name)
            add_flat_python(indent + '\t\t', target_var + " = inject_bool(" + project_l + ")", func_name)
        add_flat_python(indent + '\t', "else:", func_name)
        if isinstance(n.ops[0], Eq) or isinstance(n.ops[0], Is):
            add_flat_python(indent + '\t\t', target_var + " = 1", func_name)
        elif isinstance(n.ops[0], NotEq) or isinstance(n.ops[0], IsNot):
            add_flat_python(indent + '\t\t', target_var + " = 5", func_name)
    return target_var



def handle_subscript_node(n, indent, target_var, func_name):
    value = flattening_using_rec(n.value, indent, target_var, func_name)
    index = flattening_using_rec(n.slice, indent, target_var, func_name)

    if isinstance(n.slice, Constant):
        index = str(int(index)<<2)

    temp_var = get_new_temp_var(None)
    add_flat_python(indent, temp_var + " = get_subscript(" + value + ", " + index + ")", func_name)
    return temp_var

def handle_list_node(n, indent, target_var, func_name):  
    CREATE_LIST = '{target} = create_list({length})'
    SET_ELEMENT = '{tgt} = set_subscript({c}, {key}, {val})'
    target_var = get_new_temp_var(None) if target_var is None else target_var
    temp_list_var = get_new_temp_var(None)

    add_flat_python(indent, CREATE_LIST.format(target = temp_list_var, length = str(len(n.elts)<<2)), func_name)
    add_flat_python(indent, target_var + " = inject_big(" + temp_list_var + ")", func_name)
    
    for i in range(len(n.elts)):
        temp_index_var = get_new_temp_var(None)
        index_temp_var = (i<<2) | 0
        if isinstance(n.elts[i], Constant):
            value = str(n.elts[i].value)
            if value == "True":
                value = " 5"
            elif value == "False":
                value = "1"
            else:
               value = str(int(value)<<2)
            temp_var = get_new_temp_var()
            int_list_mapping.append(temp_var)
            add_flat_python(indent, temp_var + " = " + value, func_name)
            add_flat_python(indent, SET_ELEMENT.format(tgt=temp_index_var, c=target_var, key=index_temp_var, val=temp_var), func_name, func_name)
        elif isinstance(n.elts[i], Name):
            value = flattening_using_rec(n.elts[i], indent, None, func_name)
            if value in int_list_mapping:
                value = value
            add_flat_python(indent, SET_ELEMENT.format(tgt=temp_index_var, c=target_var, key=index_temp_var, val=value), func_name, func_name)
        else:
            value = flattening_using_rec(n.elts[i], indent, None, func_name)
            if value.isdigit():
                temp_value = get_new_temp_var(None)
                temp_var = get_new_temp_var()
                int_list_mapping.append(temp_var)
                add_flat_python(indent, temp_var + " = " + str(int(value)<<2), func_name)
                add_flat_python(indent, temp_value + " = " + temp_var, func_name)
                value = temp_value
            add_flat_python(indent, SET_ELEMENT.format(tgt=temp_index_var, c=target_var, key=index_temp_var, val=value), func_name)
    return target_var



def handle_dict_node(n, indent, target_var, func_name):
    target_var = get_new_temp_var(None) if target_var is None else target_var
    temp_var = get_new_temp_var(None)
    add_flat_python(indent, temp_var + " = create_dict()", func_name)
    add_flat_python(indent, target_var +" = inject_big(" + temp_var + ")", func_name)

    for i in range(len(n.keys)):
        key = flattening_using_rec(n.keys[i], indent, None, func_name)
        value = flattening_using_rec(n.values[i], indent, None, func_name)
        if isinstance(n.keys[i], Constant):
            if key == "True":
                key = "5"
            elif key == "False":
                key = "1"
            else:
                key = str(int(key)<<2)
        else:
            key = flattening_using_rec(n.keys[i], indent, None, func_name)
            if key.isdigit():
                temp_value = get_new_temp_var(None)
                add_flat_python(indent, temp_value + " = inject_int(" + key + ")", func_name)
                key = temp_value

        if isinstance(n.values[i], Constant):
            if value == "True":
                value = "5"
            elif value == "False":
                value = "1"
            else:
               value = str(int(value)<<2)
        else:
            value = flattening_using_rec(n.values[i], indent, None, func_name)
            if value.isdigit():
                temp_value = get_new_temp_var(None)
                add_flat_python(indent, temp_value + " = inject_int(" + value + ")", func_name)
                value = temp_value

        temp_subscipt = get_new_temp_var(None)
        add_flat_python(indent, temp_subscipt + " = set_subscript(" + target_var + ", " + key + ", "+ value + ")", func_name)
    return target_var


function_closure_map = {}
def handle_function_node(n, indent, target_var, func_name):
    prev_func = func_name
    func_name = n.name 
    
    free_var_list = get_new_temp_var(None)
    func_ptr = get_new_temp_var(None)

    if prev_func == 'main':
        closure_list.append(indent + free_var_list + " = create_list(" + str(len(funcs.function_collection[func_name].free_vars)<<2) + ")")
        closure_list.append(indent + free_var_list + " = inject_big(" + free_var_list + ")")
        
        closure_list.append(indent + func_ptr + " = create_closure(" + func_name + ", " + free_var_list + ")")
        func_pyobj = get_new_temp_var(None)
        closure_list.append(indent + func_pyobj + " = inject_big(" + func_ptr + ")")
        i = 0
        for value in funcs.function_collection[func_name].free_vars:
            temp_index_var = get_new_temp_var(None)
            closure_list.append(indent + SET_ELEMENT.format(tgt=temp_index_var, c=free_var_list, key=str(i<<2), val='_'+value))
            i += 1
    else:
        flattened_prog.append("" +"\t"+ free_var_list + " = create_list(" + str(len(funcs.function_collection[func_name].free_vars)<<2) + ")")
        flattened_prog.append("" +"\t"+ free_var_list + " = inject_big(" + free_var_list + ")")
        flattened_prog.append("" +"\t"+ func_ptr + " = create_closure(" + func_name + ", " + free_var_list + ")")
        func_pyobj = get_new_temp_var(None)
        flattened_prog.append("" +"\t"+ func_pyobj + " = inject_big(" + func_ptr + ")")
        i = 0
        for value in funcs.function_collection[func_name].free_vars:
            temp_index_var = get_new_temp_var(None)
            flattened_prog.append("" +"\t"+ SET_ELEMENT.format(tgt=temp_index_var, c=free_var_list, key=str(i<<2), val='_'+value))
            i += 1
    func_mapping[func_name] = func_pyobj

    args_list = []
    bound_vars = args_list
    for arg in n.args.args:
        args_list.append(arg.arg)
    
    if args_list:
        add_flat_python("", "def {func}({free_vars}, {args}):".format(func=func_name, args=",".join(args_list), free_vars=func_name + "_free_vars"), func_name)
    else:
        add_flat_python("", "def {func}({free_vars}):".format(func=func_name, free_vars=func_name + "_free_vars"), func_name)
    
    if len(funcs.function_collection[func_name].free_vars) != 0:
        add_flat_python("" + "\t", func_name + "_free_vars" + " = assign_stack("+ str(8) +")", func_name)
    i = 0
    for arg in n.args.args:
        tp_var = get_new_box_temp_var(None)
        add_flat_python("" + "\t", tp_var + " = assign_stack("+ str((i+1)*4+8) +")", func_name)
        add_flat_python("" + "\t", arg.arg + " = " + tp_var, func_name)
        i += 1
    i = 0
    for value in funcs.function_collection[func_name].free_vars:
        if value in func_mapping:
            add_flat_python(""+ "\t", func_mapping[value] + " = get_subscript(" + func_name + "_free_vars" + ", " + str(i<<2) + ")", func_name)
        else:
            add_flat_python(""+ "\t", "_" +value + " = get_subscript(" + func_name + "_free_vars" + ", " + str(i<<2) + ")", func_name)
        i += 1
    for node in n.body:
        if isinstance(node, Assign):
            bound_vars.append(node.targets[0].id)
        flattening_using_rec(node, ""+"\t", None, func_name)

    return func_pyobj

def handle_lambda_node(n, indent, target_var, func_name):
    prev_func = func_name
    func_name = get_lambda_label() 
    
    args_list = []
    bound_vars = args_list
    for arg in n.args.args:
        args_list.append(arg.arg)
    
    indent = indent[1:] if len(indent) else ""
    free_var_list = get_new_temp_var(None)
    func_ptr = get_new_temp_var(None)
    if prev_func == "main":
        closure_list.append(indent+ free_var_list + " = create_list(" + str(len(funcs.function_collection[func_name].free_vars)<<2) + ")")
        closure_list.append(indent+ free_var_list + " = inject_big(" + free_var_list + ")")
        closure_list.append(indent+ func_ptr + " = create_closure(" + func_name + ", " + free_var_list + ")")
        closure_func_ptr = get_new_temp_var(None)
        closure_list.append(indent+ closure_func_ptr + " = inject_big(" + func_ptr + ")")
        func_mapping[func_name] = closure_func_ptr
        i = 0
        for value in funcs.function_collection[func_name].free_vars:
            temp_index_var = get_new_temp_var(None)
            closure_list.append(indent+ SET_ELEMENT.format(tgt=temp_index_var, c=free_var_list, key=str(i<<2), val= "_" + func_name + "_" + value))
            i += 1
    else:
        flattened_prog.append("" +"\t" + free_var_list + " = create_list(" + str(len(funcs.function_collection[func_name].free_vars)<<2) + ")")
        flattened_prog.append("" +"\t"+ free_var_list + " = inject_big(" + free_var_list + ")")
        flattened_prog.append("" +"\t"+ func_ptr + " = create_closure(" + func_name + ", " + free_var_list + ")")
        closure_func_ptr = get_new_temp_var(None)
        flattened_prog.append("" +"\t"+ closure_func_ptr + " = inject_big(" + func_ptr + ")")
        func_mapping[func_name] = closure_func_ptr
        i = 0
        for value in funcs.function_collection[func_name].free_vars:
            temp_index_var = get_new_temp_var(None)
            flattened_prog.append("" +"\t"+ SET_ELEMENT.format(tgt=temp_index_var, c=free_var_list, key=str(i<<2), val= "_"+prev_func+"_"+ value))
            i += 1


    if args_list:
        add_flat_python("", "def {func}({free_vars}, {args}):".format(func=func_name, args=",".join(args_list), free_vars =free_var_list), func_name)
    else:
        add_flat_python("", "def {func}({free_vars}):".format(func=func_name, free_vars =free_var_list), func_name)
    
    if len(funcs.function_collection[func_name].free_vars) != 0:
        add_flat_python("" + "\t", free_var_list + " = assign_stack("+ str(8) +")", func_name)
    
    i = 0
    for arg in n.args.args:
        tp_var = get_new_box_temp_var(None)
        add_flat_python("" + "\t", tp_var + " = assign_stack("+ str((i+1)*4+8) +")", func_name)
        add_flat_python('' + "\t", arg.arg + " = " + tp_var, func_name)
        i += 1
    
    i = 0
    for value in funcs.function_collection[func_name].free_vars:
        if prev_func == "main":
            add_flat_python(""+ "\t", "_" + value + " = get_subscript(" + free_var_list + ", " + str(i<<2) + ")", func_name)
        else:
            add_flat_python(""+ "\t", "_" + value + " = get_subscript(" + free_var_list + ", " + str(i<<2) + ")", func_name)
            # add_flat_python(indent+ "\t", "_" +prev_func+ "_" + value + " = get_subscript(" + free_var_list + ", " + str(i<<2) + ")", func_name)
        i += 1

    if isinstance(n.body, Assign):
        bound_vars.append(n.body.targets[0].id)
    
    if isinstance(n.body, Lambda):
        original_func_return_index = len(flattened_prog) + 5
        v = flattening_using_rec(n.body, "", target_var, func_name)
        if v.isdigit():
            v = str(int(value)<<2)
        elif v in ["True", "False"]:
            v = "5" if value == "True" else "1"
        add_flat_python("", "HAHAHA_{index}_return {val}".format(val = v, index=original_func_return_index), func_name)
    else:
        v = flattening_using_rec(n.body, indent+"\t", None, func_name)

    if isinstance(n.body, Constant):
        add_flat_python(""+'\t', "return {val}".format(val=str(int(v)<<2)), func_name)
    else:
        add_flat_python(""+'\t', "return {val}".format(val=v), func_name)
    return closure_func_ptr


def handle_return_node(n, indent, target_var, func_name):
    if isinstance(n.value, Lambda):
        original_func_return_index = len(flattened_prog) + 5
        value = flattening_using_rec(n.value, indent, target_var, func_name)
        if value.isdigit():
            value = str(int(value)<<2)
        elif value in ["True", "False"]:
            value = "5" if value == "True" else "1"
        add_flat_python(indent, "HAHAHA_{index}_return {val}".format(val = value, index=original_func_return_index), func_name)
    else:
        value = flattening_using_rec(n.value, indent, target_var, func_name)
        if value.isdigit():
            value = str(int(value)<<2)
        elif value in ["True", "False"]:
            value = "5" if value == "True" else "1"
        add_flat_python(indent, "return {val}".format(val = value), func_name)
    return value

def flattening_using_rec(n, indent, target_var, func_name):
    if isinstance(n, Module):
        result = []
        for x in n.body:
            line = flattening_using_rec(x, indent, None, func_name)
            result.append(line)
        return ''
    elif isinstance(n, Assign):
        return handle_assign_node(n, indent, target_var, func_name)
    elif isinstance(n, Expr):
        return handle_expr_node(n, indent, target_var, func_name)
    elif isinstance(n, Compare):
        return handle_compare_node(n, indent, target_var, func_name)
    elif isinstance(n, While):
        return handle_while_node(n, indent, target_var, func_name)
    elif isinstance(n, If):
        return handle_if_node(n, indent, target_var, func_name)
    elif isinstance(n, IfExp):
        return handle_ifexp_node(n, indent, target_var, func_name)    
    elif isinstance(n, BinOp):
        return handle_binop_node(n, indent, target_var, func_name)
    elif isinstance(n, UnaryOp):
        return handle_unary_node(n, indent, target_var, func_name)
    elif isinstance(n, Call):
        return handle_call_node(n, indent, target_var, func_name)
    elif isinstance(n, BoolOp):    
        return handle_boolop_node(n, indent, target_var, func_name)
    elif isinstance(n, List):
        return handle_list_node(n, indent, target_var, func_name)
    elif isinstance(n, Dict):
        return handle_dict_node(n, indent, target_var, func_name)
    elif isinstance(n, Subscript):
        return handle_subscript_node(n, indent, target_var, func_name)
    elif isinstance(n, FunctionDef):
        return handle_function_node(n, indent, target_var, func_name)
    elif isinstance(n, Return):
        return handle_return_node(n, indent, target_var, func_name)
    elif isinstance(n, Lambda):
        return handle_lambda_node(n, indent, target_var, func_name)
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


"""
Returns the flattened python code using the passed method type
"""
def gen_flat_python_code(tree, method_type='rec'):
    global flattened_prog
    global funcs
    global uniquify_dict
    # add '_' as prefix to all variable names
    funcs, uniquify_dict = get_heapify(tree)

    print("#######################################")
    for k in funcs.function_collection:
        funcs.function_collection[k].print_def_node()
    print("#######################################")
    print(ast.dump(tree,indent=4))
    replace_var_names(tree, '_')
    if method_type.lower() == 'rec':
        flattening_using_rec(tree, '', None, 'main')
        append_at_end = []
        for i in range(len(closure_list)):
            for func in func_mapping:
                if '_' + func + ')' in closure_list[i]:
                    closure_list[i] = closure_list[i].replace('_' + func, func_mapping[func])
        
        while '' in closure_list:
            closure_list.remove('')
        
        rearrange_code = {}
        for i in range(len(flattened_prog)):
            if "HAHAHA_" in flattened_prog[i]:
                index = int(flattened_prog[i].split('_')[1])
                rearrange_code[index] = flattened_prog[i].split('_')[2]
                flattened_prog[i] = ''
        
        while '' in flattened_prog:
            flattened_prog.remove('')
        
        if len(flattened_prog) > 2: 
            if 'return' in flattened_prog[-1] and 'return' in flattened_prog[-2]:
                flattened_prog[-1] = ''

        for index in rearrange_code:
            flattened_prog.insert(index, '\t' + rearrange_code[index] + "_")

        flattened_prog = closure_list + append_at_end + flattened_prog



        return "\n".join(flattened_prog)
    else:
        print("Error: Wrong Traversal Method passed. Use either of rec/visit")
        return None

# PYTHON_FILENAME = "test.py"
# TEST_DIR = 'test_cases'
# with open(PYTHON_FILENAME) as f:
#     prog = f.read()
#     tree = ast.parse(prog)
# print(ast.dump(tree,indent=4))
# flattened_file_name = PYTHON_FILENAME.split('.py')[0] + '_flat.py'
# flattened_python_code = gen_flat_python_code(tree, 'rec')
# print("#######################################")
# print(flattened_python_code)
# print("#######################################")
# f = open(flattened_file_name, "w")
# f.writelines(flattened_python_code)
# f.close()
