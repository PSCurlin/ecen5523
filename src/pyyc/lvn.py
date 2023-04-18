#!/usr/bin/env python3.10
import ast
from ast import *
from liveness import *

class LVN_NODE():
    def __init__(self, value, is_constant, is_expr = False):
        self.value = value
        self.is_constant = is_constant
        self.is_expr = is_expr
        self.expr_result = None

    def print_lvn_node(self):
        return "value: "+ self.value+ ", is_constant: "+ str(self.is_constant) + ", is_expr: "+ str(self.expr_result)

        # print("value: ", self.value, ", is_constant: ", self.is_constant, ", is_expr: ", self.is_expr)



class LVN():
    def __init__(self):
        self.var_mapping = {}
        self.var_count = 0

    def is_op_number(self, var):
        return False if '$' in var else True
    
    def get_src_lvn_node(self, op, var_mapping):
        if op in var_mapping:
            return var_mapping[op].value, var_mapping

        is_constant = True if '$' in op else False
        var_mapping[op] = LVN_NODE(str(self.var_count), is_constant)
        if is_constant:
            var_mapping[op].expr_result = int(op.replace('$', ''))
            
        self.var_count += 1
        return var_mapping[op].value, var_mapping

    
    def set_movl_tgt_node(self, tgt_op, var_mapping, value):
        if tgt_op in var_mapping:
            var_mapping[tgt_op].is_constant = var_mapping[value].is_constant
            var_mapping[tgt_op].value = var_mapping[value].value
            if var_mapping[value].is_constant:
                var_mapping[tgt_op].expr_result = var_mapping[value].expr_result
            return var_mapping
        
        var_mapping[tgt_op] = LVN_NODE(var_mapping[value].value, var_mapping[value].is_constant)
        if var_mapping[value].is_constant:
            var_mapping[tgt_op].expr_result = var_mapping[value].expr_result
        return var_mapping

    # def get_key_from_value(self, value, var_mapping):
    #     matching_keys = []
    #     matching_keys = [key for key in var_mapping if var_mapping[key].value == value]        
    #     only_var = None
    #     for key in reversed(matching_keys):
    #         if '+' not in key and '-' not in key:
    #             only_var = key
    #         if '$' in key:
    #             return key
        
    #     return only_var
    
    def get_key_from_value(self, src_key, value, var_mapping):
        matching_keys = []
        matching_keys = [key for key in var_mapping if var_mapping[key].value == value]        
        only_var = None

        for key in reversed(matching_keys):
            if '$' in key:
                return key
        
        for key in reversed(matching_keys):
            if '+' not in key and '-' not in key and src_key != key:
                return key
        
        return None
    
    def get_bin_key(self, op1, op2):
        return op1 + "+" + op2

    def process_line(self, ir_inst, var_mapping):
        keywords = ir_inst.split(' ')
        op = keywords[0]
        src_op, tgt_op = None, None
        if op in "movl":
            
            src_op = keywords[1].split(',')[0]
            src, var_mapping = self.get_src_lvn_node(src_op, var_mapping)
            tgt_op = keywords[2]
            var_mapping = self.set_movl_tgt_node(tgt_op, var_mapping, src_op)


            # if self.is_op_number(src_op) and var_mapping[src_op].is_constant and var_mapping[tgt_op].value == var_mapping[src_op].value:
            if var_mapping[src_op].is_constant and var_mapping[tgt_op].value == var_mapping[src_op].value:
                replacement = self.get_key_from_value(tgt_op, var_mapping[src_op].value, var_mapping)
                ir_inst = ir_inst.replace(src_op, replacement)

        elif op == "addl": 
            
            src_op1 = keywords[1].split(',')[0]
            src1, var_mapping = self.get_src_lvn_node(src_op1, var_mapping)
            src_op2 = keywords[2]
            src2, var_mapping = self.get_src_lvn_node(src_op2, var_mapping)
            new_key = self.get_bin_key(var_mapping[src_op1].value, var_mapping[src_op2].value)
            is_constant = True if var_mapping[src_op1].is_constant and var_mapping[src_op2].is_constant else False

            if is_constant:
                var_mapping[src_op2].expr_result += var_mapping[src_op1].expr_result
                ir_inst = "movl ${result}, {tgt}".format(result = var_mapping[src_op2].expr_result, tgt=src_op2)

            elif new_key in var_mapping:
                replacement = self.get_key_from_value(src_op2, var_mapping[new_key].value, var_mapping)
                ir_inst = "movl {src}, {tgt}".format(src = replacement, tgt = src_op2)  
            else:
                src_replacement = self.get_key_from_value(src_op2, var_mapping[src_op1].value, var_mapping)
                src_replacement = src_op1 if src_replacement is None else src_replacement
                ir_inst = "addl {src}, {tgt}".format(src = src_replacement, tgt = src_op2)

            if new_key in var_mapping:
                var_mapping[src_op2].value = var_mapping[new_key].value
            else:
                var_mapping[src_op2].value = str(self.var_count)
                self.var_count += 1
                var_mapping[src_op2].is_constant = is_constant
                var_mapping[new_key] = LVN_NODE(var_mapping[src_op2].value, is_constant)
                var_mapping[new_key].expr_result = var_mapping[src_op2].expr_result

        elif op == "negl":
            src_op = keywords[1]
            if src_op in var_mapping:
                var_mapping[src_op].value = str(self.var_count)
                abs_result = None
                if var_mapping[src_op].expr_result is None:
                    tgt_node = self.get_key_from_value(src_op, var_mapping[src_op].value, var_mapping)
                    if tgt_node is not None:
                        abs_result = abs(tgt_node.expr_result) if -abs(tgt_node.expr_result) == tgt_node.expr_result else -abs(tgt_node.expr_result)
                else:
                    abs_result = abs(var_mapping[src_op].expr_result) if -abs(var_mapping[src_op].expr_result) == var_mapping[src_op].expr_result else -abs(var_mapping[src_op].expr_result)
                
                var_mapping[src_op].expr_result = abs_result 
                var_mapping[src_op].is_constant = True if abs_result is not None else False
            else:    
                is_constant = True if '$' in src_op else False
                var_mapping[src_op] = LVN_NODE(str(self.var_count), is_constant)
                var_mapping[src_op].expr_result = -abs(int(src_op.replace('$', '')))
            self.var_count += 1
        return ir_inst, var_mapping
    
    


    def block_processing(self, cfg, index):
        bb = cfg[index]
        var_mapping = cfg[index].variable_mapping
        for i in range(len(bb.code_block)):
            bb.code_block[i], var_mapping = self.process_line(bb.code_block[i], var_mapping)
        
        # import ipdb; ipdb.set_trace()
        
        cfg[index].code_block = bb.code_block
        cfg[index].variable_mapping = var_mapping        
        return cfg

    def create_dependency_dict(self, cfg):
        for i in reversed(range(len(cfg))):
            cfg = self.block_processing(cfg, i)

            for k in cfg[i].variable_mapping:
                print(k, cfg[i].variable_mapping[k].print_lvn_node())

        return cfg



