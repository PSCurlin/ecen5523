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
from compile_utils import *
from spill import *

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

        for node in reversed(cfg):    
            result.extend(node.liveness[0:len(node.liveness)-1])
            ir_code.extend(node.code_block)
        self.irx86_list = ir_code

        result.append([])
        

        return cfg, result

    def generate_liveness_using_blocks(self, ir_assembly):
        control_graph = CFG()
        cfg, meta_data_dict = control_graph.create_cfg(ir_assembly)
        blocks, liveness = self.club_liveness(cfg, meta_data_dict)        
        
        print("####################################")
        # for l in liveness:
        #     print(l)

        print(ir_assembly[0], liveness[0])
        print("####################################")
        
        # for b in blocks:
        #     print(b.key, b.code_block, b.liveness)
        # print("####################################")
        return liveness

    def remove_stack_mov_ops(self, starting_index, stack_loc):
        index = starting_index
        while(index >= 0):
            keywords = self.irx86_list[index].split(' ')
            if keywords[0] == 'movl' and keywords[2] == stack_loc:
                return index, keywords[1].split(',')[0]
            index -= 1
        return None, stack_loc

    def get_inst(self, value, reg):
        if value.isdigit():
            return "li {reg}, {value}".format(reg=reg, value=value)
        else:
            return "add {reg}, x0, {value}".format(reg=reg, value=value)


    def fix_function_calls(self, ir_list):
        for i in range(len(ir_list)):
            if ir_list[i] is None:
                continue
            keywords = ir_list[i].split(' ') 

            for j in range(len(keywords)):
                keywords[j] = get_var(keywords[j])

            op = keywords[0]
            if op in ['print']:
                value = keywords[1]
                ir_list[i] = PRINT_STR.format(push = self.get_inst(value, 'a0'))
            elif op in ['eval_input']:
                value = keywords[1]
                ir_list[i] = EVAL_INPUT.format(value = value, op= "eval_input_pyobj")
            elif op in ['list_add']:
                ir_list[i] = FUNCTION_CALL_2_args.format(push_y = self.get_inst(keywords[3], 'a1'), push_x = self.get_inst(keywords[2], 'a0'),z=keywords[1],  op="add")
            elif op in ['create_dict']:
                value = keywords[1]
                ir_list[i] = CREATE_DICT.format(value = value, op=op)
            elif op in ["assign_stack"]:
                value =  keywords[2].replace('$', '') + "(%ebp)"
                ir_list[i] = ASSIGN_STACK.format(value = value, var = keywords[1])
            elif 'not_equals_big' in ir_list[i]:  
                ir_list[i] = NOT_EQUALS_BIG.format(push_y = self.get_inst(keywords[3], 'a1'), push_x = self.get_inst(keywords[2], 'a0'),z=keywords[1])
            elif 'equals_big' in ir_list[i]:
                ir_list[i] = EQUALS_BIG.format(push_y = self.get_inst(keywords[3], 'a1'), push_x = self.get_inst(keywords[2], 'a0'),z=keywords[1])
            elif 'not_equals' in ir_list[i]: 
                if keywords[2].isdigit():
                    ir_list[i] = "xori {tgt}, {src1}, {src2}\nsnez{tgt}, {tgt}".format(tgt=keywords[1], src1=keywords[2], src2=keywords[3])
                else:
                    ir_list[i] = "xor {tgt}, {src1}, {src2}\nsnez{tgt}, {tgt}".format(tgt=keywords[1], src1=keywords[2], src2=keywords[3])
            elif 'equals' in ir_list[i]:
                if keywords[2].isdigit():
                    ir_list[i] = "xori {tgt}, {src1}, {src2}\nseqz{tgt}, {tgt}".format(tgt=keywords[1], src1=keywords[2], src2=keywords[3])
                else:
                    ir_list[i] = "xor {tgt}, {src1}, {src2}\nseqz{tgt}, {tgt}".format(tgt=keywords[1], src1=keywords[2], src2=keywords[3])
            elif op in ["get_subscript", "create_closure"]:
                ir_list[i] = FUNCTION_CALL_2_args.format(push_y = self.get_inst(keywords[3], 'a1'), push_x = self.get_inst(keywords[2], 'a0'),z=keywords[1],  op=op)
            elif op in ["get_fun_ptr", "get_free_vars"]:
                ir_list[i] = FUNCTION_CALL_1_args.format(push_x = self.get_inst(keywords[2], 'a0'),z=keywords[1],  op=op)
            elif op in ["function_return"]:
                push_str = ""
                stack_length = 0
                j = len(keywords)-1
                while (j > 1):
                    push_str += self.get_inst(keywords[j], 'a' + str(j-2)) + "\n"
                    j -= 1
                    stack_length += 4
                ir_list[i] = push_str + "call *{op}\nmovl a1, {z}".format(z=keywords[2], op=keywords[1])                    
            elif op in ['is_int', 'project_int', 'inject_int', 'is_bool', 'project_bool', 'inject_bool', "is_big", "project_big", "inject_big", 
                        "is_true", 'create_list']: 
                ir_list[i] = FUNCTION_CALL_1_args.format(push_x = self.get_inst(keywords[2], 'a0'),z=keywords[1],  op=op)
                
            elif op in ['set_subscript']:
                ir_list[i] = FUNCTION_CALL_3_args.format(push_z = self.get_inst(keywords[4], 'a2'), push_y = self.get_inst(keywords[3], 'a1'), push_x = self.get_inst(keywords[2], 'a0'),z=keywords[1],  op=op)
            elif op in ['function']:
                ir_list[i] = None


    def set_var(self, reg_var_mapping_dict, var_name, replace_var):
        for key in reg_var_mapping_dict:
            for i in range(len(reg_var_mapping_dict[key])):
                if reg_var_mapping_dict[key][i]["var"] == var_name:
                   reg_var_mapping_dict[key][i]["var"] = replace_var
        return reg_var_mapping_dict
    
    def is_stack_loc(self, op):    
        if 'sp' in op :
            return True
        return False

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

    def replace_reg_with_vars(self, reg_var_mapping, stack_mapping, ir_list):
        for i in reg_var_mapping:
            if i >= len(ir_list) or ir_list[i] is None:
                continue
            maps = reg_var_mapping[i]
            for m in maps:
                keywords = ir_list[i].split(' ')
                keywords[m["index"]] = keywords[m["index"]].replace(m["reg"], m["var"])
                
                if '(sp)' in ir_list[i]:
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
                
                og_irx86_list = ir_list
                graph = GRAPH()
                reg_var_mapping, ir_list, stack_mapping  = graph.get_reg_var_mapping(ir_list, liveness_list)
                replacements, is_spill_code_present = check_for_spill_code(reg_var_mapping, ir_list)
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
                    save_file(ir_list, "demo1.s")
                # import ipdb; ipdb.set_trace()
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
            end_assembly = end_assembly.format(var_space = str(var_space))
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

        assembly_program = "\n".join(HEADER_ASSEMBLY) + starter_assembly + "\n" + "\n".join(assembly_program) + "\n" + end_assembly
        irx86_list.extend(assembly_program)

    if len(assembly_prog) == 0:
        irx86_list = "\n".join(EMPTY_FILE)

    f = open(assembly_filename, "w")
    f.writelines(irx86_list)
    f.close()