def add_liveness_var(line_liveness, var):
    var = var.split(',')[0]
    if var == 'x0':
        pass
    elif not var.isdigit():
        line_liveness.add(var)
    return line_liveness

def remove_var(line_liveness, var):
    var = var.split(',')[0]
    if var in line_liveness:
        line_liveness.remove(var)
    return line_liveness

def get_liveness(block, starting_liveness = set()):
    result = []
    prev_live_vars = starting_liveness
    result.append(list(prev_live_vars))
    for inst in reversed(block):
        line_liveness = prev_live_vars
        keywords = inst.split(' ')
        
        if keywords[0] in ['li', 'return', 'eval_input', 'create_dict']:
            line_liveness = remove_var(line_liveness, keywords[1])
        elif keywords[0] in ['neg', 'mv', 'addi','is_int', 'project_int', 'inject_int', 'is_bool', 'project_bool', 'inject_bool', 'is_big', 'project_big',
                             'inject_big', 'is_true', 'create_list', 'xori','snez', 'seqz', "get_fun_ptr", "get_free_vars", "ld", "assign_stack"]:
            line_liveness = remove_var(line_liveness, keywords[1])
            line_liveness = add_liveness_var(line_liveness, keywords[2])
        elif keywords[0] in ['sd']:
            line_liveness = remove_var(line_liveness, keywords[2])
            line_liveness = add_liveness_var(line_liveness, keywords[1])
        elif keywords[0] in ['xor', "equals", "not_equals", "equals_big", "not_equals_big", "get_subscript", "list_add", "set_free_var", 'add']:
            line_liveness = remove_var(line_liveness, keywords[1])
            line_liveness = add_liveness_var(line_liveness, keywords[2])
            line_liveness = add_liveness_var(line_liveness, keywords[3])
        elif keywords[0] in ['print', 'nez', 'beqz']:
            line_liveness = add_liveness_var(line_liveness, keywords[1])
        elif keywords[0] in ['beq', 'bne', 'bge', 'ble', 'bgt', 'blt']:
            line_liveness = add_liveness_var(line_liveness, keywords[1])
            line_liveness = add_liveness_var(line_liveness, keywords[2])            
        elif keywords[0] in ["set_subscript"]:
            line_liveness = remove_var(line_liveness, keywords[1])
            line_liveness = add_liveness_var(line_liveness, keywords[2])
            line_liveness = add_liveness_var(line_liveness, keywords[3])
            line_liveness = add_liveness_var(line_liveness, keywords[4])
        elif keywords[0] in ["list_add"]:
            line_liveness = remove_var(line_liveness, keywords[1])
            line_liveness = add_liveness_var(line_liveness, keywords[2])
            line_liveness = add_liveness_var(line_liveness, keywords[3])
        elif keywords[0] in ["create_closure"]:
            #Keywords 2 would be a function pointer
            line_liveness = remove_var(line_liveness, keywords[1])
            line_liveness = add_liveness_var(line_liveness, keywords[3])
        elif keywords[0] in ["function_return"]:
            line_liveness = remove_var(line_liveness, keywords[1])
            for i in range(2, len(keywords)):
                line_liveness = add_liveness_var(line_liveness, keywords[i])
        elif keywords[0] == "j": 
            pass
        prev_live_vars = line_liveness
        result.append(list(line_liveness))
    result.reverse()
    return result