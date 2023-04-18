

def add_liveness_var(line_liveness, var):
    if '$' not in var:
        line_liveness.add(var.split(',')[0])
    return line_liveness


def get_liveness(block, starting_liveness = set()):
    result = []
    prev_live_vars = starting_liveness
    result.append(list(prev_live_vars))
    for inst in reversed(block):
        line_liveness = prev_live_vars
        keywords = inst.split(' ')
        if keywords[0] == 'movl':
            if keywords[2] in line_liveness:
                line_liveness.remove(keywords[2])
            line_liveness = add_liveness_var(line_liveness, keywords[1])
        elif keywords[0] in ['negl', 'return']:
            line_liveness = add_liveness_var(line_liveness, keywords[1])
        elif keywords[0] == 'addl':
            line_liveness = add_liveness_var(line_liveness, keywords[1]) 
            line_liveness = add_liveness_var(line_liveness, keywords[2])  
        elif keywords[0] == 'print':
            line_liveness = add_liveness_var(line_liveness, keywords[1])
        elif keywords[0] in ['eval_input', 'create_dict']:
            if keywords[1] in line_liveness:
                line_liveness.remove(keywords[1])
        elif keywords[0] == "cmpl":
            line_liveness = add_liveness_var(line_liveness, keywords[1])
            line_liveness = add_liveness_var(line_liveness, keywords[2])
        elif keywords[0] in ['is_int', 'project_int', 'inject_int', 'is_bool', 'project_bool', 'inject_bool', 'is_big', 'project_big', 
                             'inject_big', 'is_true', 'create_list', 'assign_stack']:
            if keywords[2] in line_liveness:
                line_liveness.remove(keywords[2]) 
            line_liveness = add_liveness_var(line_liveness, keywords[1].split(",")[0])
        elif keywords[0] in ["equals", "not_equals", "equals_big", "not_equals_big", "get_subscript", "add", "set_free_var"]:
            if keywords[3] in line_liveness:
                line_liveness.remove(keywords[3])
            line_liveness = add_liveness_var(line_liveness, keywords[1])
            line_liveness = add_liveness_var(line_liveness, keywords[2])
        elif keywords[0] in ["set_subscript"]:
            if keywords[4] in line_liveness:
                line_liveness.remove(keywords[4])
            line_liveness = add_liveness_var(line_liveness, keywords[1])
            line_liveness = add_liveness_var(line_liveness, keywords[2])
            line_liveness = add_liveness_var(line_liveness, keywords[3])
        elif keywords[0] in ["function"]:
            for i in range(2, len(keywords)):
                if keywords[i] in line_liveness:
                    line_liveness.remove(keywords[i])
        elif keywords[0] in ["return"]:
            for i in range(1, len(keywords)):
                line_liveness = add_liveness_var(line_liveness, keywords[i])
        elif keywords[0] in ["get_fun_ptr", "get_free_vars"]:
            if keywords[2] in line_liveness:
                line_liveness.remove(keywords[2])
            line_liveness = add_liveness_var(line_liveness, keywords[1])       
        elif keywords[0] in ["create_closure"]:
            if keywords[3] in line_liveness:
                line_liveness.remove(keywords[3])
            line_liveness = add_liveness_var(line_liveness, keywords[2])
        elif keywords[0] in ["function_return"]:
            if keywords[-1] in line_liveness:
                line_liveness.remove(keywords[-1])
            for i in range(1, len(keywords)-1):
                line_liveness = add_liveness_var(line_liveness, keywords[i])

        elif keywords[0] == "je" or keywords[0] == "jmp":
            pass
        prev_live_vars = line_liveness
        result.append(list(line_liveness))
    result.reverse()
    return result