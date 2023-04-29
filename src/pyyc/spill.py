def set_var(reg_var_mapping_dict, var_name, replace_var):
    for key in reg_var_mapping_dict:
        for i in range(len(reg_var_mapping_dict[key])):
            if reg_var_mapping_dict[key][i]["var"] == var_name:
                reg_var_mapping_dict[key][i]["var"] = replace_var
    return reg_var_mapping_dict

def is_stack_loc(op):    
    if '(sp)' in op :
        return True
    return False

spill_var = 0 
tmp_var_dict ={}
def gen_new_temp_var(var_name, line_num):        
    new_var = '__tp' + str(spill_var) + '_'
    spill_var += 1
    if line_num in tmp_var_dict:
        tmp_var_dict[line_num].append({"tmp_var": new_var, "stk_loc": var_name})
    else:
        tmp_var_dict[line_num] = [{"tmp_var": new_var, "stk_loc": var_name}]
    return new_var


LD_SPILL_VAR = "ld {tgt}, {src}"

def replace_spill_inst(var, string, i):
    ops = ''
    if is_stack_loc(var): 
        temp_var = gen_new_temp_var(var, i)
        ops = LD_SPILL_VAR.format(tgt=temp_var, src=var)
        string = string.replace(var, temp_var)
    return ops, string

def check_for_spill_code(reg_var_mapping, ir_list):
    result = {}
    is_spill_code_present = False   
    for i in range(len(ir_list)):
        if ir_list[i] is None:
            continue
        keywords = ir_list[i].split(" ")

        for j in range(len(keywords)):
            keywords[j] = keywords[j].split(',')[0]
        
        if keywords[0] in ["j", "function"] or len(keywords) <= 1:
            continue
        
        if keywords[0] in ['li', 'return', 'eval_input', 'create_dict', 'print', 'nez', 'beqz']:
            if is_stack_loc(keywords[1]):
                is_spill_code_present = True
                ops_str, ir_list[i] = replace_spill_inst(keywords[1], ir_list[i], i)
                ops_str = ops_str + "\n" + ir_list[i]
                for m in reg_var_mapping[i]:
                    ops_str = ops_str.replace(m["reg"], m["var"])  
                result[i] = ops_str
        elif keywords[0] in ['neg', 'mv', 'addi','is_int', 'project_int', 'inject_int', 'is_bool', 'project_bool', 'inject_bool', 'is_big', 'project_big',
                             'inject_big', 'is_true', 'create_list', 'assign_stack', 'xori','snez', 'seqz', "get_fun_ptr", "get_free_vars", 'beq', 'bne', 
                             'bge', 'ble', 'bgt', 'blt']:
            
            ops_str = ''
            if is_stack_loc(keywords[1]):
                ops_str1, ir_list[i] = replace_spill_inst(keywords[1], ir_list[i], i)
                ops_str += ops_str1 + "\n"
            if is_stack_loc(keywords[2]):
                ops_str2, ir_list[i] = replace_spill_inst(keywords[2], ir_list[i], i)
                ops_str += ops_str2 + "\n"
            
            if is_stack_loc(keywords[1]) or is_stack_loc(keywords[2]):
                is_spill_code_present = True
                ops_str = ops_str + ir_list[i]
                for m in reg_var_mapping[i]:
                    ops_str = ops_str.replace(m["reg"], m["var"])  
                result[i] = ops_str
            
        elif keywords[0] in ['xor', "equals", "not_equals", "equals_big", "not_equals_big", "get_subscript", "list_add", "set_free_var", 'add']:
            ops_str = ''
            if is_stack_loc(keywords[1]):
                ops_str1, ir_list[i] = replace_spill_inst(keywords[1], ir_list[i], i)
                ops_str += ops_str1 + "\n"
            if is_stack_loc(keywords[2]):
                ops_str2, ir_list[i] = replace_spill_inst(keywords[2], ir_list[i], i)
                ops_str += ops_str2 + "\n"
            if is_stack_loc(keywords[3]):
                ops_str2, ir_list[i] = replace_spill_inst(keywords[3], ir_list[i], i)
                ops_str += ops_str2 + "\n"
            
            if is_stack_loc(keywords[1]) or is_stack_loc(keywords[2]) or is_stack_loc(keywords[3]):
                is_spill_code_present = True
                ops_str = ops_str + ir_list[i]
                for m in reg_var_mapping[i]:
                    ops_str = ops_str.replace(m["reg"], m["var"])  
                result[i] = ops_str
          
        elif keywords[0] in ["set_subscript", "list_add"]:
            ops_str = ''
            if is_stack_loc(keywords[1]):
                ops_str1, ir_list[i] = replace_spill_inst(keywords[1], ir_list[i], i)
                ops_str += ops_str1 + "\n"
            if is_stack_loc(keywords[2]):
                ops_str2, ir_list[i] = replace_spill_inst(keywords[2], ir_list[i], i)
                ops_str += ops_str2 + "\n"
            if is_stack_loc(keywords[3]):
                ops_str2, ir_list[i] = replace_spill_inst(keywords[3], ir_list[i], i)
                ops_str += ops_str2 + "\n"
            if is_stack_loc(keywords[4]):
                ops_str2, ir_list[i] = replace_spill_inst(keywords[4], ir_list[i], i)
                ops_str += ops_str2 + "\n"
            
            if is_stack_loc(keywords[1]) or is_stack_loc(keywords[2]) or is_stack_loc(keywords[3]) or is_stack_loc(keywords[4]):
                is_spill_code_present = True
                ops_str = ops_str + ir_list[i]
                for m in reg_var_mapping[i]:
                    ops_str = ops_str.replace(m["reg"], m["var"])  
                result[i] = ops_str
            
        
        elif keywords[0] in ["create_closure"]:
            ops_str = ''
            if is_stack_loc(keywords[1]):
                ops_str1, ir_list[i] = replace_spill_inst(keywords[1], ir_list[i], i)
                ops_str += ops_str1 + "\n"
            if is_stack_loc(keywords[3]):
                ops_str2, ir_list[i] = replace_spill_inst(keywords[3], ir_list[i], i)
                ops_str += ops_str2 + "\n"
            
            if is_stack_loc(keywords[1]) or is_stack_loc(keywords[3]):
                is_spill_code_present = True
                ops_str = ops_str + ir_list[i]
                for m in reg_var_mapping[i]:
                    ops_str = ops_str.replace(m["reg"], m["var"])  
                result[i] = ops_str
        elif keywords[0] in ["function_return"]:
            ops_str = ''
            for j in range(1, range(len(keywords))):
                if is_stack_loc(keywords[1]):
                    is_spill_code_present = True
                    ops_str1, ir_list[i] = replace_spill_inst(keywords[1], ir_list[i], i)
                    ops_str += ops_str1 + "\n"
            
            if is_spill_code_present:
                is_spill_code_present = True
                ops_str = ops_str + ir_list[i]
                for m in reg_var_mapping[i]:
                    ops_str = ops_str.replace(m["reg"], m["var"])  
                result[i] = ops_str
    return result, is_spill_code_present      
        