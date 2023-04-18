#!/usr/bin/env python3.10
import sys
import ast
import pathlib
from ast import *
from flattening import gen_flat_python_code

# from box import *


from cfg import *
from lvn import *
from graph import *
from utils import *
from liveness import *
from ir_assembly import *


def save_file(file_content_list, filename):
    prog = "\n".join(file_content_list)
    f = open(filename, "w")
    f.writelines(prog)
    f.close()

def get_target_python_filename():
    if len(sys.argv) <= 1:
        print("Python file is missing.")
        return None
    
    filename = sys.argv[1]
    file_extension = pathlib.Path(filename).suffix
    if file_extension != '.py':
        print("Error: Incorrect file type provided")
        return None    
    return filename

def get_var_mapping(tree):
    stack_var_mapping = {}
    for node in ast.walk(tree): 
        if not isinstance(node, Name):
            continue
        if(node.id in ["print","input","eval"]):
            continue
        if node.id in stack_var_mapping:
            continue
        stack_var_mapping[node.id] = str(-4*(len(stack_var_mapping)+1))
    return stack_var_mapping

def static_vars(**kwargs):
    def decorate(func):
        for k in kwargs:
            setattr(func, k, kwargs[k])
        return func
    return decorate


class REGISTER_ALLOCATION():
    def __init__(self):
        self.irx86_list = [] 
        self.temp_vars = {}
        self.temp_caller_saved_registers = ['%eax', '%ecx', '%edx']
        self.regs_proirity_order = ['%eax', '%ecx', '%edx', '%ebx', '%esi', '%edi']
        self.compare_register_clash = ["%eax"]
        self.tmp_var_dict = {}
        self.next_temp_num = 0
        self.label_mappings = {
            "if": 0,
            "while": 0
        }
        self.liveness_cycle = {}
        self.spill_var = 0

    def get_if_label(self):
        label = self.label_mappings["if"] 
        self.label_mappings["if"] += 1
        return str(label)

    def get_while_label(self):
        label = self.label_mappings["while"] 
        self.label_mappings["while"] += 1
        return str(label)

    def is_stack_loc(self, op):    
        if 'ebp' in op :
            return True
        return False
    
    def gen_new_temp_var(self, var_name, line_num):        
        new_var = '__tp' + str(self.spill_var) + '_'
        self.spill_var += 1
        if line_num in self.tmp_var_dict:
            self.tmp_var_dict[line_num].append({"tmp_var": new_var, "stk_loc": var_name})
        else:
            self.tmp_var_dict[line_num] = [{"tmp_var": new_var, "stk_loc": var_name}]
        return new_var

    def fix_src_var(self, src_var):
        return src_var.split(',')[0] 

    
    def dead_code_elimination(self, block, liveness, block_type):
        if len(liveness) == 1:
            return block
        if 'loop' in block_type or 'then' in block_type or 'else' in block_type:
            return block
        liveness.remove(liveness[0])
        result = []
        for i in range(len(block)):
            keywords = block[i].split(' ')
            op = keywords[0]
            if op == "movl":
                tgt_op = keywords[2]
                
                if tgt_op not in liveness[i]:
                    result.append(i)           
        for i in result:
            block[i] = None
        return block
    
    def per_block_liveness(self, cfg, index, meta_data_dict):
        node = cfg[index]
        if node.block_type is None or not node.block_type or "end_if" in node.block_type or "then" in node.block_type or "else" in node.block_type or "end_while" in node.block_type:
            prev_liveness = set()
            for i in node.links:
                prev_liveness = prev_liveness.union(set(cfg[i].liveness[0]))                   
            node.liveness = get_liveness(node.code_block, prev_liveness) 
        elif "if" in node.block_type:
            prev_liveness = set() 
            for i in node.links:
                if node.block_type.replace("if", "end_if") != cfg[i].block_type:
                    prev_liveness = prev_liveness.union(set(cfg[i].liveness[0]))
            cfg[index].liveness = get_liveness(node.code_block, prev_liveness)
        elif "loop" in node.block_type:
                     
            for ns in reversed(node.loop_dependencies):
                for n in ns:
                    self.per_block_liveness(cfg, n, meta_data_dict)
            prev_liveness = set() 
            for i in node.links:
                prev_liveness = prev_liveness.union(set(cfg[i].liveness[0]))
  
            cfg[index].liveness = get_liveness(node.code_block, prev_liveness)
        elif "while" in node.block_type:
            end_while_block_index = meta_data_dict[node.block_type.replace("while", "end_while")]
            end_while_block_liveness = set(cfg[end_while_block_index].liveness[0])
            cfg[index].liveness = get_liveness(node.code_block, end_while_block_liveness)

            loop_block_index = meta_data_dict[node.block_type.replace("while", "loop")]
            self.per_block_liveness(cfg, loop_block_index, meta_data_dict)
            loop_block_liveness = set(cfg[loop_block_index].liveness[0])

            combined_liveness = end_while_block_liveness.union(loop_block_liveness)
            cfg[index].liveness = get_liveness(node.code_block, combined_liveness)
            while_block_liveness = set(cfg[index].liveness[0])
            while(True):
                self.per_block_liveness(cfg, loop_block_index, meta_data_dict)
                loop_block_liveness = set(cfg[loop_block_index].liveness[0])
                combined_liveness = end_while_block_liveness.union(loop_block_liveness)
                cfg[index].liveness = get_liveness(node.code_block, combined_liveness)
                if while_block_liveness == set(cfg[index].liveness[0]):
                    break
                while_block_liveness = set(cfg[index].liveness[0])



    def club_liveness(self, cfg, meta_data_dict):
        result = []
        ir_code = []
               
        for node in cfg:
            self.per_block_liveness(cfg, node.key, meta_data_dict)

        # for node in cfg:
        #     self.per_block_liveness(cfg, node.key, meta_data_dict)
        #     node.code_block = self.dead_code_elimination(node.code_block, node.liveness, node.block_type)
        #     node.code_block = self.remove_none(node.code_block)
        #     self.per_block_liveness(cfg, node.key, meta_data_dict)
        #     print(node.code_block)

        for node in reversed(cfg):    
            result.extend(node.liveness[0:len(node.liveness)-1])
            ir_code.extend(node.code_block)
        self.irx86_list = ir_code

        result.append([])
        

        return cfg, result

    def generate_liveness_using_blocks(self, ir_assembly):
        control_graph = CFG()
        cfg, meta_data_dict = control_graph.create_cfg(ir_assembly)
        # lvn = LVN()
        # cfg = lvn.create_dependency_dict(cfg)

        blocks, liveness = self.club_liveness(cfg, meta_data_dict)        
        
        print("####################################")
        # for l in liveness:
        #     print(l)

        print(ir_assembly[0], liveness[0])
        print("####################################")
        
        # for b in blocks:
        #     print(b.key, b.code_block, b.links, b.liveness[0], b.loop_dependencies)
        # print("####################################")
        return liveness

    def generate_interference_graph(self, ir_list, liveness_list):
        result = {}
        liveness_list.remove(liveness_list[0])
        for i in range(len(ir_list)):
            inst = ir_list[i]
            op = inst.split(' ')[0]
            if ":" in op or op in ["je", "jmp", "function"]: #'je' in op or 'jmp' in op:
                continue
            live_vars = liveness_list[i]
    
            target_var = inst.split(' ')[-1]
            op = inst.split(' ')[0]
            if target_var not in result:
                result[target_var] = {
                    "target_reg" : None,
                    "neighbors": [],
                    "dont_assign" : []
                }
            
            is_addl_op, is_movl_op, is_compare, is_cmpl = False, False, False, False  
            is_box, is_subscript, is_stack_assign = False, False, False
            is_get_ptr, is_free_vars, is_func_return, is_create_closure = False, False, False, False
            # handle function call too, add registers to the neighbors list
            if op in ['print', 'eval_input', 'create_dict']:
                for live_var in liveness_list[i]:
                    if live_var in result:
                        result[live_var]["dont_assign"].extend(self.temp_caller_saved_registers)
                    else:
                        result[live_var] = {
                            "target_reg" : None,
                            "neighbors": [],
                            "dont_assign" : self.temp_caller_saved_registers
                        }            
                result[target_var]["dont_assign"].extend(self.temp_caller_saved_registers)

            elif op in ["get_fun_ptr"]:
                for live_var in live_vars:
                    if live_var in result:
                        result[live_var]["dont_assign"].extend(self.temp_caller_saved_registers)
                    else:
                        result[live_var] = {
                            "target_reg" : None,
                            "neighbors": [],
                            "dont_assign" : self.temp_caller_saved_registers
                        }            
                result[target_var]["dont_assign"].extend(self.temp_caller_saved_registers)
                is_get_ptr = True          
            elif op in ["get_free_vars"]:
                for live_var in live_vars:
                    if live_var in result:
                        result[live_var]["dont_assign"].extend(self.temp_caller_saved_registers)
                    else:
                        result[live_var] = {
                            "target_reg" : None,
                            "neighbors": [],
                            "dont_assign" : self.temp_caller_saved_registers
                        }            
                result[target_var]["dont_assign"].extend(self.temp_caller_saved_registers)
                is_free_vars = True
            elif op in ["create_closure"]:
                for live_var in live_vars:
                    if live_var in result:
                        result[live_var]["dont_assign"].extend(self.temp_caller_saved_registers)
                    else:
                        result[live_var] = {
                            "target_reg" : None,
                            "neighbors": [],
                            "dont_assign" : self.temp_caller_saved_registers
                        }            
                result[target_var]["dont_assign"].extend(self.temp_caller_saved_registers)
                is_create_closure = True
            elif op in ["function_return"]:
                
                for live_var in live_vars:
                    if live_var in result:
                        result[live_var]["dont_assign"].extend(self.temp_caller_saved_registers)
                    else:
                        result[live_var] = {
                            "target_reg" : None,
                            "neighbors": [],
                            "dont_assign" : self.temp_caller_saved_registers
                        }            
                result[target_var]["dont_assign"].extend(self.temp_caller_saved_registers)
                keywords = inst.split(' ')
                for i in range(1, len(keywords)-1):
                    result[keywords[i]]["neighbors"].append(target_var)
                    result[target_var]["neighbors"].append(keywords[i])

                    result[keywords[i]]["neighbors"].append(var)
                    result[var]["neighbors"].append(keywords[i])

            elif op in ["set_subscript"]:
                for live_var in liveness_list[i]:
                    if live_var in result:
                        result[live_var]["dont_assign"].extend(self.temp_caller_saved_registers)
                    else:
                        result[live_var] = {
                            "target_reg" : None,
                            "neighbors": [],
                            "dont_assign" : self.temp_caller_saved_registers
                        }            
                result[target_var]["dont_assign"].extend(self.temp_caller_saved_registers)
                src1_op = inst.split(' ')[1].split(',')[0]
                if '$' not in src1_op:
                    if src1_op not in result:
                        result[src1_op] = {
                            "target_reg" : None,
                            "neighbors": [],
                            "dont_assign" : self.compare_register_clash
                        }
                    elif src1_op in result:
                        result[src1_op]["dont_assign"].extend(self.compare_register_clash)

                src3_op = inst.split(' ')[3].split(',')[0]
                if '$' not in src3_op:
                    if src3_op not in result:
                        result[src3_op] = {
                            "target_reg" : None,
                            "neighbors": [],
                            "dont_assign" : self.compare_register_clash
                        }
                    elif src3_op in result:
                        result[src3_op]["dont_assign"].extend(self.compare_register_clash)
                
                if '$' not in src1_op or '$' not in src3_op: 
                    is_subscript = True
            elif op in ["equals", "not_equals", "equals_big", "not_equals_big", "get_subscript", "add", "assign_stack"]:
                is_compare = True
                for live_var in liveness_list[i]:
                    if live_var in result:
                        result[live_var]["dont_assign"].extend(self.compare_register_clash)
                    else:
                        result[live_var] = {
                            "target_reg" : None,
                            "neighbors": [],
                            "dont_assign" : self.compare_register_clash
                        }             
                
                middle_op = inst.split(' ')[2]
                if '$' not in middle_op:
                    if middle_op not in result:
                        result[middle_op] = {
                            "target_reg" : None,
                            "neighbors": [],
                            "dont_assign" : self.compare_register_clash
                        }
                    else:
                        result[middle_op]["dont_assign"].extend(self.compare_register_clash)
                result[target_var]["dont_assign"].extend(self.compare_register_clash)

                src_op = inst.split(' ')[1].split(',')[0]
                if src_op not in result and '$' not in src_op:
                    result[src_op] = {
                        "target_reg" : None,
                        "neighbors": [],
                        "dont_assign" : self.compare_register_clash
                    }
                elif src_op in result:
                    result[src_op]["dont_assign"].extend(self.compare_register_clash)
            
            elif op in ['project_int', 'is_int', 'inject_int', 'project_bool', 'is_bool',  'inject_bool', 'project_big', 
                        'is_big', 'inject_big', 'is_true', 'create_list']:
                for live_var in liveness_list[i]:
                    if live_var in result:
                        result[live_var]["dont_assign"].extend(self.temp_caller_saved_registers)
                    else:
                        result[live_var] = {
                            "target_reg" : None,
                            "neighbors": [],
                            "dont_assign" : self.temp_caller_saved_registers
                        }            
                result[target_var]["dont_assign"].extend(self.temp_caller_saved_registers)     
                src_op = inst.split(' ')[1].split(',')[0]
                
                if '$' not in src_op:
                    if src_op not in result:
                        result[src_op] = {
                            "target_reg" : None,
                            "neighbors": [],
                            "dont_assign" : self.temp_caller_saved_registers
                        }
                    else:
                        result[src_op]["dont_assign"].extend(self.temp_caller_saved_registers)
                    is_box = True


            elif op == 'addl':
                src_op = inst.split(' ')[1].split(',')[0]
                if src_op not in result and '$' not in src_op:
                    result[src_op] = {
                        "target_reg" : None,
                        "neighbors": [],
                        "dont_assign" : []
                    }
                    is_addl_op = True
           
            elif op == 'movl':
                src_op = inst.split(' ')[1].split(',')[0]
                if '$' not in src_op:
                    if src_op not in result: 
                        result[src_op] = {
                            "target_reg" : None,
                            "neighbors": [],
                            "dont_assign" : []
                        }
                    is_movl_op = True   
            
            for var in live_vars:
                if var == target_var:
                    continue
                if var not in result: 
                    result[var] = {
                        "target_reg" : None,
                        "neighbors": [],
                        "dont_assign" : []
                    }
                
                result[var]["neighbors"].append(target_var)
                result[target_var]["neighbors"].append(var)                

                if is_create_closure:
                    keywords = inst.split(' ')
                    if '$' not in keywords[1]:
                        result[keywords[1]]["neighbors"].append(target_var)
                        result[target_var]["neighbors"].append(keywords[1])
                        result[keywords[1]]["neighbors"].append(var)
                        result[var]["neighbors"].append(keywords[1])
                    if '$' not in keywords[2]:
                        result[keywords[2]]["neighbors"].append(target_var)
                        result[target_var]["neighbors"].append(keywords[2])
                        result[keywords[2]]["neighbors"].append(var)
                        result[var]["neighbors"].append(keywords[2])
                                

                if is_movl_op:
                    if src_op in result[target_var]["neighbors"]:
                        result[target_var]["neighbors"].remove(src_op)
                    if target_var in result[src_op]["neighbors"]:
                        result[src_op]["neighbors"].remove(target_var)

                if is_subscript:
                    if '$' not in src1_op:
                        result[src1_op]["neighbors"].append(target_var)
                        result[target_var]["neighbors"].append(src1_op)

                        result[src1_op]["neighbors"].append(var)
                        result[var]["neighbors"].append(src1_op)

                    if '$' not in src3_op:
                        result[src3_op]["neighbors"].append(target_var)
                        result[target_var]["neighbors"].append(src3_op)

                        result[src3_op]["neighbors"].append(var)
                        result[var]["neighbors"].append(src3_op)
                        
                if is_addl_op or is_box:
                    result[src_op]["neighbors"].append(target_var)
                    result[target_var]["neighbors"].append(src_op)

                    result[src_op]["neighbors"].append(var)
                    result[var]["neighbors"].append(src_op)

                if is_compare:
                    src_op = inst.split(' ')[1].split(',')[0]
                    if "$" not in src_op:
                        result[src_op]["neighbors"].append(target_var)
                        result[target_var]["neighbors"].append(src_op)
                    
                    if "$" not in src_op and "$" not in middle_op:
                        result[src_op]["neighbors"].append(middle_op)
                        result[middle_op]["neighbors"].append(src_op)

        for key in result:
            result[key]["neighbors"] = list(set(result[key]["neighbors"]))
            if key in result[key]["neighbors"]:
                result[key]["neighbors"].remove(key)
            
            result[key]["dont_assign"] = list(set(result[key]["dont_assign"]))
            if key in result[key]["dont_assign"]:
                result[key]["dont_assign"].remove(key)
        return result
   
    def assign_reg(self, interference_graph, var, stack_mapping):
        no_no_regs = interference_graph[var]["dont_assign"] 
        for reg in self.regs_proirity_order:
            if reg not in no_no_regs:
                interference_graph[var]["target_reg"] = reg
                for nei in interference_graph[var]["neighbors"]:
                    if interference_graph[nei]["target_reg"] == None:
                        interference_graph[nei]["dont_assign"].append(reg)
                break   
        else:
            # use stack
            if var in stack_mapping:
                stack_loc = stack_mapping[var]
            else:
                stack_loc = str(-4*(len(stack_mapping)+1)) + '(%ebp)'
                stack_mapping[var] = stack_loc
            interference_graph[var]["target_reg"] = stack_loc
            for nei in interference_graph[var]["neighbors"]:
                if interference_graph[nei]["target_reg"] == None:
                    interference_graph[nei]["dont_assign"].append(stack_loc)
        return interference_graph

    def get_most_conflicting_var(self, interference_graph, ignore_vars):      
        max_neighbors = 0
        neighbor_to_start = None
        for key in interference_graph:
            if 'tp' in key and key not in ignore_vars:
                return key
            
            if key not in ignore_vars and interference_graph[key]["target_reg"] == None:
                if len(interference_graph[key]["neighbors"]) > max_neighbors:
                    max_neighbors = len(interference_graph[key]["neighbors"])
                    neighbor_to_start = key
        
        if neighbor_to_start == None:
            vars = list(interference_graph.keys())
            for var in vars:
                if var not in ignore_vars:
                    return var
        return neighbor_to_start   

    def coloring_graph(self, interference_graph, stack_prev):
        vars = list(interference_graph.keys())
        ignore_vars = []
        ignore_vars_len = 0
        stack_mapping = {}
        while(len(vars) != ignore_vars_len): 
            conflicting_var = self.get_most_conflicting_var(interference_graph, ignore_vars)
            interference_graph = self.assign_reg(interference_graph, conflicting_var, stack_mapping)
            ignore_vars.append(conflicting_var)
            ignore_vars_len = len(ignore_vars)
        return interference_graph, stack_mapping

    def remove_stack_mov_ops(self, starting_index, stack_loc):
        index = starting_index
        while(index >= 0):
            keywords = self.irx86_list[index].split(' ')
            if keywords[0] == 'movl' and keywords[2] == stack_loc:
                return index, keywords[1].split(',')[0]
            index -= 1
        return None, stack_loc

    def fix_function_calls(self, ir_list):
        for i in range(len(ir_list)):
            if ir_list[i] is None:
                continue
            keywords = ir_list[i].split(' ') 
            op = keywords[0]
            if op in ['print']:
                value = keywords[-1]
                ir_list[i] = 'pushl ' + value + '\n' + 'call print_any' + '\n' + 'addl $4, %esp'
            elif op in ['eval_input']:
                value = keywords[-1]
                ir_list[i] = 'call {op}\nmovl %eax, {value}'.format(value = value, op= "eval_input_pyobj")
            elif op in ['create_dict']:
                value = keywords[-1]
                ir_list[i] = 'call {op}\nmovl %eax, {value}'.format(value = value, op=op)
            elif op in ["assign_stack"]:
                value =  keywords[1].replace('$', '') + "(%ebp)"
                ir_list[i] = 'movl {value}, {var}'.format(value = value, var = keywords[-1])
            elif 'not_equals_big' in ir_list[i]: 
                ir_list[i] = "pushl {y}\npushl {x}\ncall not_equal\nmovl %eax, {z}\naddl $8, %esp".format(x=keywords[1], y=keywords[2], z=keywords[3])
            elif 'equals_big' in ir_list[i]:
                ir_list[i] = "pushl {y}\npushl {x}\ncall equal\nmovl %eax, {z}\naddl $8, %esp".format(x=keywords[1], y=keywords[2], z=keywords[3])
            elif 'not_equals' in ir_list[i]: 
                ir_list[i] = "cmpl {x}, {y}\nsetne %al\nmovzbl %al, {z}".format(x=keywords[1], y=keywords[2], z=keywords[3])
            elif 'equals' in ir_list[i]:
                ir_list[i] = "cmpl {x}, {y}\nsete %al\nmovzbl %al, {z}".format(x=keywords[1], y=keywords[2], z=keywords[3])
            elif op in ["get_subscript", "add", "create_closure"]:
                ir_list[i] = "pushl {y}\npushl {x}\ncall {op}\nmovl %eax, {z}\naddl $8, %esp".format(x=keywords[1], y=keywords[2], z=keywords[3], op=op)
            elif op in ["get_fun_ptr", "get_free_vars"]:
                ir_list[i] = "pushl {x}\ncall {op}\nmovl %eax, {tgt}\naddl $4, %esp".format(x=keywords[1], tgt=keywords[2], op=op)
            elif op in ["function_return"]:
                push_str = ""
                stack_length = 0
                j = len(keywords)-2
                while (j > 1):
                    push_str += "pushl {var}\n".format(var=keywords[j])
                    j -= 1
                    stack_length += 4
                ir_list[i] = push_str + "call *{op}\nmovl %eax, {z}\naddl ${stack_length}, %esp".format(z=keywords[-1], op=keywords[1], stack_length = str(stack_length))                    
            elif op in ['is_int', 'project_int', 'inject_int', 'is_bool', 'project_bool', 'inject_bool', "is_big", "project_big", "inject_big", 
                        "is_true", 'create_list']: 
                src_reg = keywords[1].split(",")[0]
                target_reg = keywords[-1]
                ir_list[i] = 'pushl {src_reg}\ncall {op}\nmovl %eax, {target_reg}\naddl $4, %esp'.format(op=op,target_reg=target_reg,src_reg=src_reg)
            elif op in ['set_subscript']:
                reg = keywords[4]
                value = keywords[3].split(',')[0]
                index = keywords[2].split(',')[0]
                list_name = keywords[1].split(',')[0]
                ir_list[i] = "pushl {value}\npushl {index}\npushl {list}\ncall {op}\nmovl %eax, {reg}\naddl $12, %esp".format(list = list_name, reg = reg, value= value, index=index, op=op )
            elif op in ['function']:
                ir_list[i] = None

    def get_reg(self, reg_var_mapping_dict, var_name):
        for key in reg_var_mapping_dict:
            for i in range(len(reg_var_mapping_dict[key])):
                if reg_var_mapping_dict[key][i]["var"] == var_name:
                    return reg_var_mapping_dict[key][i]["reg"]
        return None

    def set_var(self, reg_var_mapping_dict, var_name, replace_var):
        for key in reg_var_mapping_dict:
            for i in range(len(reg_var_mapping_dict[key])):
                if reg_var_mapping_dict[key][i]["var"] == var_name:
                   
                   reg_var_mapping_dict[key][i]["var"] = replace_var
        return reg_var_mapping_dict
        
    def check_for_spill_code(self, reg_var_mapping, ir_list):
        result = {}
        is_spill_code_present = False   
        for i in range(len(ir_list)):
            line = ir_list[i]
            if line is None:
                continue
            keywords = line.split(" ")
            if keywords[0] in ["je", "jmp"] or len(keywords) <= 1:
                continue
            keywords[1] = keywords[1].split(',')[0]
            operation = keywords[0]
            if operation == "movl" and keywords[1] == keywords[2]:
                reg_var_mapping = self.set_var(reg_var_mapping, reg_var_mapping[i][0]["var"], reg_var_mapping[i][1]["var"]) 
                result[i] = None
            elif operation == "cmpl":
                is_cmpl_spills = False
                ops = []
                if self.is_stack_loc(keywords[1]):
                    is_cmpl_spills = True
                    src1_op = self.gen_new_temp_var(keywords[1], i)
                    ops.append("movl " + keywords[1] + ", " + src1_op)
                else:
                    src1_op = keywords[1]
                
                if self.is_stack_loc(keywords[2]):
                    is_cmpl_spills = True
                    src2_op = self.gen_new_temp_var(keywords[2], i)
                    ops.append("movl " + keywords[2] + ", " + src2_op)
                else:
                    src2_op = keywords[2]
                
                if is_cmpl_spills: 
                    is_spill_code_present = True
                    ops.append(operation + " " + src1_op + ", "+ src2_op)
                    ops_str = "\n".join(ops)
                    result[i] = ops_str
            elif operation in ["equals", "not_equals"]:
                is_cmpl_spills = False
                ops = []
                if self.is_stack_loc(keywords[1]):
                    is_cmpl_spills = True
                    src1_op = self.gen_new_temp_var(keywords[1], i)
                    ops.append("movl " + keywords[1] + ", " + src1_op)
                else:
                    src1_op = keywords[1]
                
                if self.is_stack_loc(keywords[2]):
                    is_cmpl_spills = True
                    src2_op = self.gen_new_temp_var(keywords[2], i)
                    ops.append("movl " + keywords[2] + ", " + src2_op)
                else:
                    src2_op = keywords[2]
                
                is_tgt_on_stack = False
                if self.is_stack_loc(keywords[3]):
                    is_tgt_on_stack = True
                    
                if is_cmpl_spills: 
                    is_spill_code_present = True
                    if is_tgt_on_stack:
                        target_op = self.gen_new_temp_var(keywords[3], i)
                        ops.append(operation + " " + src1_op + " "+ src2_op + " " + target_op) 
                        ops.append("movl " + target_op + ", " + keywords[3])               
                    else:
                        ops.append(operation + " " + src1_op + " "+ src2_op + " " + keywords[3])
                    ops_str = "\n".join(ops)
                    result[i] = ops_str
                elif is_tgt_on_stack:
                    is_spill_code_present = True
                    target_op = self.gen_new_temp_var(keywords[3], i)
                    ops.append(operation + " " + src1_op + " "+ src2_op + " " + target_op) 
                    ops.append("movl " + target_op + ", " + keywords[3]) 
                    ops_str = "\n".join(ops)
                    result[i] = ops_str

            # elif operation in ["assign_stack"] and self.is_stack_loc(keywords[2]):
            #     tgt_op = self.gen_new_temp_var(keywords[2], i)
            #     is_spill_code_present = True
            #     ops = ["assign_stack " + keywords[1] + ", " + tgt_op]
            #     ops.append("movl {src}, {tgt}".format(src = tgt_op, tgt = keywords[2]))
            #     ops_str = "\n".join(ops)
            #     result[i] = ops_str 
                
            elif operation in ["addl", "movl"] and self.is_stack_loc(keywords[1]) and self.is_stack_loc(keywords[2]):                
                src_op = self.gen_new_temp_var(keywords[1], i)
                tgt_op = self.gen_new_temp_var(keywords[2], i)
                is_spill_code_present = True
                ops = ["movl " + keywords[1] + ", " + src_op]
                if operation == "addl":
                    ops.append("movl " + keywords[2] + ", " + tgt_op)
                    ops.append("addl " + src_op + ", " + tgt_op)
                    ops.append("movl " + tgt_op + ", "+ keywords[2])
                else:
                    ops.append("movl " + src_op + ", " + keywords[2])
                ops_str = "\n".join(ops)
                for m in reg_var_mapping[i]:
                    ops_str = ops_str.replace(m["reg"], m["var"])  
                result[i] = ops_str 

        return result, is_spill_code_present            

    def remove_none(self, l):
        while(None in l):
            l.remove(None)

    

    def generate_reg_var_mapping(self, interference_graph, ir_list):
        reg_var_mapping = {}
        for i in range(len(ir_list)):
            keywords = ir_list[i].split(' ')
            if keywords[0] in ["je", "jmp", "function"] or len(keywords) <= 1:
                continue
            reg_var_mapping[i] = []

            if keywords[0] in ['addl', 'movl', 'cmpl', 'is_int', 'project_int', 'inject_int', 'is_bool', 'project_bool', 
                               'inject_bool', 'is_big', 'project_big', 'inject_big', 'is_true', 'create_list', 'assign_stack']:
                
                reg_var_mapping[i].append({
                    "index": 2,
                    "reg" : interference_graph[keywords[-1]]["target_reg"],
                    "var" : keywords[2]
                })  
                keywords = ir_list[i].split(' ')              
                keywords[2] = keywords[2].replace(keywords[2].split(',')[0], interference_graph[keywords[2].split(',')[0]]["target_reg"])
                ir_list[i] = " ".join(keywords)
            
            elif keywords[0] in ["not_equals", "equals", "not_equals_big", "equals_big", "get_subscript", "add"]:
                if '$' not in keywords[2]:
                    reg_var_mapping[i].append({
                        "index": 2,
                        "reg" : interference_graph[keywords[2]]["target_reg"],
                        "var" : keywords[2]
                    })

                    keywords = ir_list[i].split(' ')
                    keywords[2] = keywords[2].replace(keywords[2].split(',')[0], interference_graph[keywords[2].split(',')[0]]["target_reg"])
                    ir_list[i] = " ".join(keywords)

                reg_var_mapping[i].append({
                    "index": 3,
                    "reg" : interference_graph[keywords[3]]["target_reg"],
                    "var" : keywords[3]
                })

                keywords = ir_list[i].split(' ')
                keywords[3] = keywords[3].replace(keywords[3].split(',')[0], interference_graph[keywords[3].split(',')[0]]["target_reg"])
                ir_list[i] = " ".join(keywords)
            
            elif keywords[0] in ["set_subscript"]:
                if '$' not in keywords[3].split(',')[0]:
                    reg_var_mapping[i].append({
                        "index": 3,
                        "reg" : interference_graph[keywords[3].split(',')[0]]["target_reg"],
                        "var" : keywords[3].split(',')[0]
                    })
                    keywords = ir_list[i].split(' ')
                    keywords[3] = keywords[3].replace(keywords[3].split(',')[0], interference_graph[keywords[3].split(',')[0]]["target_reg"])
                    ir_list[i] = " ".join(keywords)

                if '$' not in keywords[2].split(',')[0]:
                    reg_var_mapping[i].append({
                        "index": 2,
                        "reg" : interference_graph[keywords[2].split(',')[0]]["target_reg"],
                        "var" : keywords[2].split(',')[0]
                    })
                    keywords = ir_list[i].split(' ')
                    keywords[2] = keywords[2].replace(keywords[2].split(',')[0], interference_graph[keywords[2].split(',')[0]]["target_reg"])
                    ir_list[i] = " ".join(keywords)

                reg_var_mapping[i].append({
                    "index": 4,
                    "reg" : interference_graph[keywords[4]]["target_reg"],
                    "var" : keywords[4]
                })
                keywords = ir_list[i].split(' ')
                keywords[4] = keywords[4].replace(keywords[4].split(',')[0], interference_graph[keywords[4].split(',')[0]]["target_reg"])
                ir_list[i] = " ".join(keywords)

            elif keywords[0] in ["get_free_vars", "get_fun_ptr"]:
                reg_var_mapping[i].append({
                    "index": 2,
                    "reg" : interference_graph[keywords[2]]["target_reg"],
                    "var" : keywords[2]
                })
                keywords = ir_list[i].split(' ')
                keywords[2] = keywords[2].replace(keywords[2], interference_graph[keywords[2]]["target_reg"])
                ir_list[i] = " ".join(keywords)
            
            elif keywords[0] in ["create_closure"]:
                reg_var_mapping[i].append({
                    "index": 2,
                    "reg" : interference_graph[keywords[2]]["target_reg"],
                    "var" : keywords[2]
                })
                keywords = ir_list[i].split(' ')
                keywords[2] = keywords[2].replace(keywords[2], interference_graph[keywords[2]]["target_reg"])
                ir_list[i] = " ".join(keywords)

                reg_var_mapping[i].append({
                    "index": 3,
                    "reg" : interference_graph[keywords[3]]["target_reg"],
                    "var" : keywords[3]
                })
                keywords = ir_list[i].split(' ')
                keywords[3] = keywords[3].replace(keywords[3], interference_graph[keywords[3]]["target_reg"])
                ir_list[i] = " ".join(keywords)

            elif keywords[0] in ["function_return"]:
                for j in range(2, len(keywords)):
                    reg_var_mapping[i].append({
                        "index": j,
                        "reg" : interference_graph[keywords[j]]["target_reg"],
                        "var" : keywords[j]
                    })
                    keywords = ir_list[i].split(' ')
                    keywords[j] = keywords[j].replace(keywords[j], interference_graph[keywords[j]]["target_reg"])
                    ir_list[i] = " ".join(keywords)

            if '$' not in keywords[1]:
                keywords = ir_list[i].split(' ')
                if "%" not in keywords[1]:
                    reg_var_mapping[i].append({
                        "index": 1,
                        "reg" : interference_graph[keywords[1].split(',')[0]]["target_reg"],
                        "var" : keywords[1].split(',')[0]
                    }) 
                    keywords[1] = keywords[1].replace(keywords[1].split(',')[0], interference_graph[keywords[1].split(',')[0]]["target_reg"])
                    ir_list[i] = " ".join(keywords)       

        return reg_var_mapping
  
    def replace_reg_with_vars(self, reg_var_mapping, stack_mapping, ir_list):
        for i in reg_var_mapping:
            if i >= len(ir_list) or ir_list[i] is None:
                continue
            maps = reg_var_mapping[i]
            for m in maps:
                keywords = ir_list[i].split(' ')
                keywords[m["index"]] = keywords[m["index"]].replace(m["reg"], m["var"])
                
                if '%ebp' in ir_list[i]:
                    for entry in stack_mapping:
                        if stack_mapping[entry] == keywords[1].split(',')[0]:
                            keywords[1] = keywords[1].replace(keywords[1].split(',')[0], entry)
                ir_list[i] = " ".join(keywords)
 

    def remove_same_op_movl(self, ir_list):
        for i in range(len(ir_list)):
            if ir_list[i] is  None:
                continue
            keywords = ir_list[i].split(' ')
            if 'movl' == keywords[0] and keywords[1].split(',')[0] == keywords[2]:
                ir_list[i] = None
            
    def assign_registers(self, flat_tree, stack_var_mapping):
        ir_lists = get_ir_assembly(flat_tree, stack_var_mapping)
        stack_per_fun = {}
        for fun in ir_lists:
            is_spill_code_present = True
            ir_list = ir_lists[fun]
            save_file(ir_list, "demo.s")
            reg_var_mapping = {}
            stack_mapping = {}
            while(is_spill_code_present):
                stack_mapping = {}
                liveness_list = self.generate_liveness_using_blocks(ir_list)  
                save_file(ir_list, "demo1.s")
                interference_graph = self.generate_interference_graph(ir_list, liveness_list)
                
                if 'function' in ir_list[0]:
                    stack_prev = len(ir_list[0].split(' '))
                else:
                    stack_prev = 0

                interference_graph, stack_mapping = self.coloring_graph(interference_graph, stack_prev)
                og_irx86_list = ir_list
                
                vars = list(interference_graph.keys())
                vars.sort()
                
                reg_var_mapping = self.generate_reg_var_mapping(interference_graph, ir_list)
                replacements, is_spill_code_present = self.check_for_spill_code(reg_var_mapping, ir_list)

                for index in replacements:
                    og_irx86_list[index] = replacements[index]
                ir_list = og_irx86_list
                if is_spill_code_present:
                    self.replace_reg_with_vars(reg_var_mapping, stack_mapping, ir_list)
                    self.remove_none(ir_list)
                    reg_var_mapping = {}
                    self.next_temp_num = 0
                    self.tmp_var_dict = dict()
                    self.spill_var = 0
                    ir_list = ("\n".join(ir_list)).split("\n")
                    self.remove_same_op_movl(ir_list)
                    self.remove_none(ir_list)
            self.remove_none(ir_list)
            self.fix_function_calls(ir_list)
            self.remove_none(ir_list)
            
            ir_lists[fun] = "\n".join(ir_list).split("\n")
            # ir_list = "\n".join(ir_list).split("\n")
            
            stack_per_fun[fun] = stack_mapping
        return ir_lists, stack_per_fun

def reformat_assembly(assembly_prog):
    for func in assembly_prog:
        assembly_list = assembly_prog[func]
        for i in range(len(assembly_list)):
            if ':' not in assembly_list[i]: #and 'return' not in assembly_list[i] and 'function' not in assembly_list[i]:
                assembly_list[i] = "\t" + assembly_list[i]

    return assembly_prog


if __name__ == "__main__":
    is_spill_code_present = True
    stack_mapping  ={}
    # get the python filename from the command line argument
    filename = get_target_python_filename()
    if filename == None:
        raise Exception("Python file is missing")

    # genrate AST for the python file
    prog = ''
    with open(filename) as f:
        prog = f.read()
        tree = ast.parse(prog)

    #flatten the python code
    flat_python = gen_flat_python_code(tree, 'rec')

    print("#####################")
    print(flat_python)
    print("#####################")

    # make a tree from the python code (flattened) and cache all the variables in the dictionary with an offset(memory location from ebp)
    flat_tree = ast.parse(flat_python)

    stack_var_mapping = get_var_mapping(flat_tree)
    register_allocation = REGISTER_ALLOCATION()  
    assembly_prog, stack_mapping = register_allocation.assign_registers(flat_tree, stack_var_mapping)
    
    for fun in assembly_prog:
        ir_list = assembly_prog[fun]
        assembly_prog[fun] = ("\n".join(ir_list)).split("\n")
    assembly_prog = reformat_assembly(assembly_prog)

    assembly_filename = filename.split('.py')[0] + '.s'

    irx86_list = []
    for func in assembly_prog:
        var_space = 4*len(stack_mapping[func]) if len(stack_mapping[func]) != 0 else 4
        if func == "main":
            starter_assembly = "\n".join(MAIN_STARTER_ASSEMBLY)
            starter_assembly = starter_assembly.format(var_space = str(var_space))
            end_assembly = "\n".join(MAIN_END_OF_ASSEMBLY_FILE)
        else:
            start = "\n".join(FUNC_STARTER_ASSEMBLY)
            start = start.format(func=func, var_space = str(var_space))
            starter_assembly = start

            for i in range(len(assembly_prog[func])):
                if 'return' in assembly_prog[func][i]:
                    return_value = assembly_prog[func][i].split(' ')[-1]
                    assembly_prog[func][i] = "\tmovl {val}, %eax  # return ".format(val= return_value)                

            end = "\n".join(FUNC_END_OF_ASSEMBLY_FILE)
            end_assembly = end

        assembly_program = assembly_prog[func]

        assembly_program = starter_assembly + "\n" + "\n".join(assembly_program) + "\n" + end_assembly
        irx86_list.extend(assembly_program)

    if len(assembly_prog) == 0:
        irx86_list = "\n".join(EMPTY_FILE)

    f = open(assembly_filename, "w")
    f.writelines(irx86_list)
    f.close()