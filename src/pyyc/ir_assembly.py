import ast
from ast import *


ir_assembly = []
assembly_prog = {}
temp_vars = {}
label_mappings = {
    "if": 0,
    "while": 0
}

def update_assembly_instruction(func_name, inst):
    if func_name in assembly_prog:
        assembly_prog[func_name].append(inst)
    else:
        assembly_prog[func_name] = [inst]

def get_if_label():
    label = label_mappings["if"] 
    label_mappings["if"] += 1
    return str(label)

def get_while_label():
    label = label_mappings["while"] 
    label_mappings["while"] += 1
    return str(label)

MOVL_STR = "movl {src}, {tgt}"
ADDL_STR = "addl {src}, {tgt}"
NEGL_STR = "negl {var}"
FUNCTION_DEF_STR = "function {func}"
RETURN_STR = "return {var}"
IF_STR = "if{label}:"
THEN_STR = "then{label}:"
ELSE_STR = "else{label}:"
WHILE_STR = "while{label}:"
LOOP_STR = "loop{label}:"
END_IF_STR = "end_if{label}:"
END_WHILE_STR = "end_while{label}:"
WHILE_ELSE_STR = "while_else{label}:"
JE_ELSE_STR = "je else{label}"
JE_END_IF_STR = "je end_if{label}"
JE_END_WHILE_STR = "je end_while{label}"
DATA_TYPE_STR = "{func} {src}, {tgt}"
JMP_END_IF_STR = "jmp end_if{label}"
JMP_END_WHILE_STR = "jmp end_while{label}"
JMP_WHILE_STR = "jmp while{label}"
CMPL_0_STR = "cmpl $0, {value}" 
CREATE_LIST_STR = "{func} ${len} {var}" 
CREATE_DICT_STR = "create_dict {var}"
EQUALS_STR = "{func} {arg1} {arg2} {tgt}"
SET_SUBSCIPT_FUNC_STR = "{func} {arg1} {arg2} {arg3} {tgt}"
GET_SUBSCRIPT_FUNC_STR = "{func} {arg1} {arg2} {tgt}"
PRINT_STR = "print {var}"
EVAL_INPUT_STR = "eval_input {var}"
INT_STR = "{op} {left_op} {right_op} {tgt}"
CREATE_CLOSURE_STR = "create_closure ${func_ptr} {free_vars} {tgt}"
GET_FREE_VARS_STR = "get_free_vars {func_ptr}"

RETURN_FUNCTION_STR = "function_return {args} {tgt}"

def gen_ir_assembly(n, stack_var_mapping, func_name):
    if isinstance(n, Module):
        for x in n.body:
            gen_ir_assembly(x, stack_var_mapping, func_name) 
    elif isinstance(n, Assign):
        value = ''
        if isinstance(n.value, Constant):
            value = '$' + str(n.value.value)
            update_assembly_instruction(func_name, MOVL_STR.format(src=value, tgt=n.targets[0].id))
        elif isinstance(n.value, Name):
            update_assembly_instruction(func_name, MOVL_STR.format(src=n.value.id, tgt=n.targets[0].id))
        elif isinstance(n.value, UnaryOp) or isinstance(n.value, BinOp) or isinstance(n.value, Expr) or isinstance(n.value, Call):  
            gen_ir_assembly(n.value, n.targets[0].id, func_name)
        else:
            print("Assign node failed", n._fields, n.value) 
    
    elif isinstance(n, If):
        if_label = get_if_label()
        is_else = True if len(n.orelse) > 0 else False
        update_assembly_instruction(func_name, IF_STR.format(label=if_label))
        if isinstance(n.test, Name):
            cmp_to = str(n.test.id)
        elif isinstance(n.test, Constant):
            cmp_to = '$' + str(n.test.value)
            update_assembly_instruction(func_name, MOVL_STR.format(src=cmp_to, tgt='const_var' +  str(len(temp_vars))))
            cmp_to = 'const_var' +  str(len(temp_vars))
            temp_vars['const_var' +  str(len(temp_vars))] = str(n.test.value)
        else:
            print("ERRRRRRRRRRRRRRR")  

        update_assembly_instruction(func_name, CMPL_0_STR.format(value=cmp_to))
        if is_else:
            update_assembly_instruction(func_name, JE_ELSE_STR.format(label=if_label))
        else:
            update_assembly_instruction(func_name, JE_END_IF_STR.format(label=if_label))
            
        update_assembly_instruction(func_name, THEN_STR.format(label=if_label))
        for x in n.body:
            gen_ir_assembly(x, None, func_name)

        update_assembly_instruction(func_name, JMP_END_IF_STR.format(label=if_label))

        if len(n.orelse) > 0:
            update_assembly_instruction(func_name, ELSE_STR.format(label=if_label))
            for x in n.orelse:
                gen_ir_assembly(x, None, func_name)
            update_assembly_instruction(func_name, JMP_END_IF_STR.format(label=if_label))
        update_assembly_instruction(func_name, END_IF_STR.format(label=if_label))

    elif isinstance(n, While):
        while_label = get_while_label()
        update_assembly_instruction(func_name, WHILE_STR.format(label=while_label))
        if isinstance(n.test, Name):
            cmp_to = str(n.test.id)
        else:
            cmp_to = '$' + str(n.test.value)
        update_assembly_instruction(func_name, CMPL_0_STR.format(value=cmp_to))
        update_assembly_instruction(func_name, JE_END_WHILE_STR.format(label=while_label))
        update_assembly_instruction(func_name, LOOP_STR.format(label=while_label))        
        for x in n.body:
            gen_ir_assembly(x, None, func_name)        
        # update_assembly_instruction(func_name, JMP_END_WHILE_STR.format(label=while_label)) 
        update_assembly_instruction(func_name, JMP_WHILE_STR.format(label=while_label))

        if len(n.orelse) > 0:
            update_assembly_instruction(func_name, WHILE_ELSE_STR.format(label=while_label))
            for x in n.orelse:
                gen_ir_assembly(x, None, func_name)
            update_assembly_instruction(func_name, JMP_END_WHILE_STR.format(label=while_label))

        update_assembly_instruction(func_name, END_WHILE_STR.format(label=while_label)) 
    elif isinstance(n, Expr):
        gen_ir_assembly(n.value, stack_var_mapping, func_name)
    elif isinstance(n, Constant) or isinstance(n, Name) or isinstance(n, Add) or isinstance(n, USub) or isinstance(n, Load) or isinstance(n, Store):
        pass 
    
    elif isinstance(n, BinOp):
        is_both_operand_constant = 0
        left_val, right_val = '',''

        if isinstance(n.left, Constant):
            is_both_operand_constant += 1
            left_val = '$' + str(n.left.value)
        elif isinstance(n.left, Name):
            left_val = n.left.id
        else:
            print("Unknown Left Node")
        
        if isinstance(n.right, Constant):
            is_both_operand_constant += 1
            right_val = '$' + str(n.right.value)
        elif isinstance(n.right, Name):
            right_val = n.right.id
        else:
            print("Unknown Right Node")
        if type(stack_var_mapping) != dict:
            is_processed = False
            if isinstance(n.left, Name):
                if n.left.id == stack_var_mapping:
                    update_assembly_instruction(func_name, ADDL_STR.format(src=right_val, tgt=left_val))
                    is_processed = True
            if not is_processed and isinstance(n.right, Name):
                if n.right.id == stack_var_mapping:
                    update_assembly_instruction(func_name, ADDL_STR.format(tgt=right_val, src=left_val))
                    is_processed = True
            if not is_processed:
                update_assembly_instruction(func_name, MOVL_STR.format(src=left_val, tgt=stack_var_mapping))   
                update_assembly_instruction(func_name, ADDL_STR.format(src=right_val, tgt=stack_var_mapping)) 
    elif isinstance(n, UnaryOp):
        if isinstance(n.operand, Name):
            update_assembly_instruction(func_name, MOVL_STR.format(src=n.operand.id, tgt=stack_var_mapping)) 
            update_assembly_instruction(func_name, NEGL_STR.format(var=stack_var_mapping))
        elif isinstance(n.operand, Constant):
            update_assembly_instruction(func_name, MOVL_STR.format(src='$-' + str(n.operand.value), tgt=stack_var_mapping))
        else:
            print("IR_GEN: Unary operand unknown")
    elif isinstance(n, FunctionDef):
        func_name = n.name 
        args_list = []
        for arg in n.args.args:
            args_list.append(arg.arg)

        func_str = FUNCTION_DEF_STR.format(func=func_name)
        
        args = " " + " ".join(args_list) if args_list else ''
        update_assembly_instruction(func_name, func_str+args)
        for node in n.body:
            gen_ir_assembly(node, stack_var_mapping, func_name)
    elif isinstance(n, Return):
        return_value = n.value.id if isinstance(n.value, Name) else '$' + str(n.value.value)
        update_assembly_instruction(func_name, RETURN_STR.format(var=return_value))

    elif isinstance(n, Call):
        # handle args
        if n.func.id in ['print']:
            gen_ir_assembly(n.args[0], stack_var_mapping, func_name)
            if isinstance(n.args[0], Constant):
                update_assembly_instruction(func_name, MOVL_STR.format(src= "$"+str(n.args[0].value), tgt='const_var' +  str(len(temp_vars)))) 
                update_assembly_instruction(func_name, PRINT_STR.format(var= 'const_var' +  str(len(temp_vars))))
                temp_vars['const_var' +  str(len(temp_vars))] = str(n.args[0].value)
            elif isinstance(n.args[0], Name):
                update_assembly_instruction(func_name, PRINT_STR.format(var= str(n.args[0].id)))
        elif n.func.id in ['eval']: 
            if type(stack_var_mapping) != dict:
                if stack_var_mapping is None:
                    stack_var_mapping = 'const_var' + str(len(temp_vars))
                    temp_vars['const_var' +  str(len(temp_vars))] = str("HAHAHAH")
                update_assembly_instruction(func_name, EVAL_INPUT_STR.format(var= stack_var_mapping))
        elif n.func.id in ['create_dict']: 
            update_assembly_instruction(func_name, CREATE_DICT_STR.format(var= stack_var_mapping))
        elif n.func.id in ["equals", "not_equals"]:   
            value1 = n.args[0].id if isinstance(n.args[0], Name) else '$' + str(n.args[0].value) 
            value2 = n.args[1].id if isinstance(n.args[1], Name) else '$' + str(n.args[1].value)
            update_assembly_instruction(func_name, EQUALS_STR.format(func=n.func.id, arg1=value1, arg2=value2, tgt=stack_var_mapping))
        elif n.func.id in ["equals_big", "not_equals_big"]:        
            value1 = n.args[0].id if isinstance(n.args[0], Name) else '$' + str(n.args[0].value) 
            value2 = n.args[1].id if isinstance(n.args[1], Name) else '$' + str(n.args[1].value)   
            update_assembly_instruction(func_name, EQUALS_STR.format(func=n.func.id, arg1=value1, arg2=value2, tgt=stack_var_mapping))
        elif n.func.id == "int":
            if isinstance(n.args[0].comparators[0], Constant):
                right_op = 'const_var' +  str(len(temp_vars))
                update_assembly_instruction(func_name, MOVL_STR.format(src= "$"+str(n.args[0].comparators[0].value), tgt=right_op))
                temp_vars['const_var' +  str(len(temp_vars))] = str(n.args[0].comparators[0].value)
            else:
                right_op = n.args[0].comparators[0].id
            left_op = n.args[0].left.id if isinstance(n.args[0].left, Name) else "$" + str(n.args[0].left.value)
            ops = 'equals ' if isinstance(n.args[0].ops[0], Eq) else 'not_equals '
            update_assembly_instruction(func_name, INT_STR.format(op=ops, left_op=left_op, right_op=right_op, tgt=stack_var_mapping))       
        elif n.func.id in ["is_int", "project_int", "inject_int"]:
            entity = n.args[0].id if isinstance(n.args[0], Name) else '$' + str(n.args[0].value)
            update_assembly_instruction(func_name, DATA_TYPE_STR.format(func=n.func.id, src=entity, tgt=stack_var_mapping)) 
            
        elif n.func.id in ["is_bool", "project_bool", "inject_bool"]: 
            if isinstance(n.args[0], Name):
                entity = n.args[0].id 
            else:
                entity = '$'+ str(n.args[0].value)
            update_assembly_instruction(func_name, DATA_TYPE_STR.format(func=n.func.id, src=entity, tgt=stack_var_mapping))

        elif n.func.id in ["is_big", "project_big", "inject_big", "is_true"]: 
            if isinstance(n.args[0], Name):
                entity = n.args[0].id 
            else:
                entity = '$'+ str(n.args[0].value)
            update_assembly_instruction(func_name, DATA_TYPE_STR.format(func=n.func.id, src=entity, tgt=stack_var_mapping))

        elif n.func.id in ["create_list"]: 
            update_assembly_instruction(func_name, CREATE_LIST_STR.format(func=n.func.id, len=str(n.args[0].value), var=stack_var_mapping))
        elif n.func.id in ["set_subscript"]:
            value1 = n.args[0].id if isinstance(n.args[0], Name) else '$' + str(n.args[0].value) 
            value2 = n.args[1].id if isinstance(n.args[1], Name) else '$' + str(n.args[1].value)
            value3 = n.args[2].id if isinstance(n.args[2], Name) else '$' + str(n.args[2].value)
            update_assembly_instruction(func_name, SET_SUBSCIPT_FUNC_STR.format(func=n.func.id, arg1=value1, arg2=value2, arg3=value3, tgt=stack_var_mapping))       
        elif n.func.id in ["get_subscript", "add"]:
            value1 = n.args[0].id if isinstance(n.args[0], Name) else '$' + str(n.args[0].value) 
            value2 = n.args[1].id if isinstance(n.args[1], Name) else '$' + str(n.args[1].value)

            update_assembly_instruction(func_name, GET_SUBSCRIPT_FUNC_STR.format(func = n.func.id, arg1=value1, arg2=value2, tgt=stack_var_mapping))       
        elif n.func.id in ["create_closure"]:
            update_assembly_instruction(func_name, CREATE_CLOSURE_STR.format(func_ptr = n.args[0].id, free_vars=n.args[1].id, tgt= stack_var_mapping))  
        elif n.func.id in ["function_return"]:
            args_list = []
            for arg in n.args:
                args_list.append(arg.id)
            update_assembly_instruction(func_name, RETURN_FUNCTION_STR.format(args = " ".join(args_list), tgt = stack_var_mapping))
        elif n.func.id in ["get_free_vars"]:
            update_assembly_instruction(func_name, "get_free_vars " + n.args[0].id + " " + stack_var_mapping)
        elif n.func.id in ["get_fun_ptr"]:
            update_assembly_instruction(func_name, "get_fun_ptr " + n.args[0].id + " " + stack_var_mapping)
        elif n.func.id in ["function_ptr"]:
            update_assembly_instruction(func_name, "function_ptr " + n.args[0].id + " " + n.args[1].id + " " + stack_var_mapping)
        elif n.func.id in ["assign_stack"]:
            update_assembly_instruction(func_name, "assign_stack $" + str(n.args[0].value) + " " + stack_var_mapping)
        elif "temp" in n.func.id:
            update_assembly_instruction(func_name, "call " + n.func.id + " " + n.args[0].id) 
        else:
            print("unknown func", n.func.id) 
    else:
        print(n._fields)
        raise Exception('Error in gen IR: unrecognized AST node')
    

def get_ir_assembly(flat_tree, stack_var_mapping):
    global assembly_prog
    gen_ir_assembly(flat_tree, stack_var_mapping, "main")
    return assembly_prog