class GRAPH_NODE():
    def __init__(self):
        self.neighbors = set()
        self.dont_assign = set()
        self.target_reg = None

    def print_graph_node(self):
        print(self.target_reg, self.neighbors, self.dont_assign)
    
    def get_neighbors(self):
        return self.neighbors
    
    def get_dont_assign_regs(self):
        return self.dont_assign
    
    def set_target_reg(self, reg):
        self.target_reg = reg


def get_var(var):
    return var.split(',')[0]

class GRAPH():
    def __init__(self):
        self.temp_caller_saved_registers = {'%eax', '%ecx', '%edx'}
        self.regs_proirity_order = ['%eax', '%ecx', '%edx', '%ebx', '%esi', '%edi']
        self.compare_register_clash = {"%eax"}
        self.graph = {}

    def get_node(self, key):
        if key not in self.graph:  
            self.graph[key] = GRAPH_NODE()
        return self.graph[key]

    def add_neighbors(self, var1, var2):
        if var1 != var2:
            var1_node = self.get_node(var1)
            var2_node = self.get_node(var2)
            var1_node.neighbors.add(var2)
            var2_node.neighbors.add(var1)


    def gen_graph(self, ir_assembly, liveness_list):
        liveness_list.remove(liveness_list[0])
        for i in range(len(ir_assembly)):
            inst = ir_assembly[i]
            op = inst.split(' ')[0]
            if ":" in op or op in ["j"]: 
                continue
            live_vars = liveness_list[i]
            keywords = inst.split(' ')

            for i in range(len(keywords)):
                keywords[i] = get_var(keywords[i])

            target_var = get_var(keywords[1])
            if op == "li":
                for live_var in live_vars:
                    if live_var == target_var or live_var == src_op:
                        continue
                    self.add_neighbors(live_var, target_var)
                    
            elif op in ["add", "addi"]:
                src1_op = get_var(keywords[2])
                src2_op = get_var(keywords[3]) 
                for live_var in live_vars:
                    if live_var == target_var or live_var == src_op:
                        continue
                    self.add_neighbors(live_var, target_var)
                    if not src2_op.isdigit():
                        self.add_neighbors(src2_op, target_var)
                        self.add_neighbors(live_var, src2_op)
                    if not src1_op.isdigit() and src1_op != 'x0':
                        self.add_neighbors(src1_op, target_var)
                        self.add_neighbors(live_var, src1_op)
                    if (not src1_op.isdigit() and src1_op != 'x0') and (not src2_op.isdigit()):
                        self.add_neighbors(src1_op, src2_op)
            elif op == "neg":
                for live_var in live_vars:
                    if live_var == target_var or live_var == src_op:
                        continue
                    self.add_neighbors(live_var, target_var)
            elif op in ['print', 'eval_input', 'create_dict', "get_fun_ptr", "get_free_vars"]:
                # caller saved registers will interfer with everything in live_vars
                target_node = self.get_node(target_var)
                target_node.dont_assign = target_node.dont_assign.union(self.temp_caller_saved_registers)
                for live_var in live_vars:
                    if live_var == target_var:
                        continue
                    live_var_node = self.get_node(live_var)
                    live_var_node.dont_assign = live_var_node.dont_assign.union(self.temp_caller_saved_registers)
                    self.add_neighbors(live_var, target_var)
            elif op in ["function_return"]:
                target_node = self.get_node(target_var)
                target_node.dont_assign = target_node.dont_assign.union(self.temp_caller_saved_registers)
                for live_var in live_vars:
                    if live_var == target_var:
                        continue
                    live_var_node = self.get_node(live_var)
                    live_var_node.dont_assign = live_var_node.dont_assign.union(self.temp_caller_saved_registers)
                    self.add_neighbors(live_var, target_var)
                
                    for i in range(2, len(keywords)):
                        var = get_var(keywords[i])
                        self.add_neighbors(live_var, var)
                        self.add_neighbors(var, target_var)
                
            elif op in ["set_subscript"]:
                target_node = self.get_node(target_var)
                target_node.dont_assign = target_node.dont_assign.union(self.temp_caller_saved_registers)
                list_var = get_var(keywords[2])
                value_var = get_var(keywords[4])

                self.add_neighbors(list_var, target_var)
                self.add_neighbors(value_var, target_var)
                self.add_neighbors(value_var, list_var)
                for live_var in live_vars:
                    if live_var == target_var:
                        continue
                    self.add_neighbors(live_var, target_var)
                    live_var_node = self.get_node(live_var)
                    live_var_node.dont_assign = live_var_node.dont_assign.union(self.temp_caller_saved_registers)
                    self.add_neighbors(live_var, list_var)
                    self.add_neighbors(live_var, value_var)
            
            elif op in ["create_closure"]:
                target_node = self.get_node(target_var)
                target_node.dont_assign = target_node.dont_assign.union(self.temp_caller_saved_registers)
                
                tgt_var = get_var(keywords[2])
                free_var = get_var(keywords[3])
                self.add_neighbors(tgt_var, free_var)
                self.add_neighbors(tgt_var, target_var)
                self.add_neighbors(target_var, free_var)
                for live_var in live_vars:
                    if live_var == target_var:
                        continue
                    self.add_neighbors(live_var, target_var)
                    live_var_node = self.get_node(live_var)
                    live_var_node.dont_assign = live_var_node.dont_assign.union(self.temp_caller_saved_registers)

                    self.add_neighbors(tgt_var, target_var)
                    self.add_neighbors(live_var, tgt_var)

                    self.add_neighbors(free_var, target_var)
                    self.add_neighbors(live_var, free_var)

            elif op in ["bez"]:
                target_node = self.get_node(target_var)
                for live_var in live_vars:
                    if live_var == target_var:
                        continue
                    self.add_neighbors(live_var, target_var)

            elif op in ["beq"]:
                target_node = self.get_node(target_var)
                src_op1 = get_var(keywords[1])
                src_op2 = get_var(keywords[2])
                for live_var in live_vars:
                    if live_var != src_op1 and not src_op1.isdigit():
                        self.add_neighbors(live_var, src_op1)
                        self.add_neighbors(src_op1, target_var)
                    if live_var != src_op2 and not src_op2.isdigit():
                        self.add_neighbors(live_var, src_op2)
                        self.add_neighbors(src_op2, target_var)
            
            elif op in ["xori"]:
                target_node = self.get_node(target_var)
                src_op1 = get_var(keywords[2])
                src_op2 = get_var(keywords[3])
                for live_var in live_vars:
                    if live_var == target_var:
                        continue
                    self.add_neighbors(live_var, target_var)
                    if not src_op1.isdigit():
                        self.add_neighbors(live_var, src_op1)
                        self.add_neighbors(src_op1, target_var)
                    if not src_op2.isdigit():
                        self.add_neighbors(live_var, src_op2)
                        self.add_neighbors(src_op2, target_var)

            elif op in ['project_int', 'is_int', 'inject_int', 'project_bool', 'is_bool',  'inject_bool', 'project_big', 'is_big', 'inject_big', 'is_true', 'create_list']:  
                # caller saved registers will interfer with everything in live_vars               
                target_node = self.get_node(target_var)
                target_node.dont_assign = target_node.dont_assign.union(self.temp_caller_saved_registers)
                src_op =  get_var(keywords[1])
                for live_var in live_vars:
                    if live_var == target_var:
                        continue
                    live_var_node = self.get_node(live_var)
                    live_var_node.dont_assign = live_var_node.dont_assign.union(self.temp_caller_saved_registers)
                    self.add_neighbors(live_var, target_var)

                    if not src_op.isdigit():
                        self.add_neighbors(live_var, src_op)
                        self.add_neighbors(target_var, src_op)

                    
            elif op in ["equals", "not_equals", "equals_big", "not_equals_big", "get_subscript", "add", "assign_stack"]:
                # compare saved registers will interfere with live_vars
                target_node = self.get_node(target_var)
                target_node.dont_assign = target_node.dont_assign.union(self.compare_register_clash)
                src_op1 = get_var(keywords[1])
                src_op2 = get_var(keywords[2])
                for live_var in live_vars:
                    if live_var == target_var: 
                        continue
                    self.add_neighbors(target_var, live_var)
                    live_var_node = self.get_node(live_var)
                    live_var_node.dont_assign = live_var_node.dont_assign.union(self.compare_register_clash)
                    if not src_op1.isdigit():
                        src_op1_node = self.get_node(src_op1)
                        src_op1_node.dont_assign = src_op1_node.dont_assign.union(self.compare_register_clash)                        
                        self.add_neighbors(target_var, src_op1)
                        self.add_neighbors(src_op1, live_var)
                    if not src_op2.isdigit():
                        src_op2_node = self.get_node(src_op2)
                        src_op2_node.dont_assign = src_op2_node.dont_assign.union(self.compare_register_clash)                        
                        self.add_neighbors(target_var, src_op2)
                        self.add_neighbors(src_op2, live_var)

    def assign_reg(self, var, stack_mapping):
        no_no_regs = self.graph[var].dont_assign
        for reg in self.regs_proirity_order:
            if reg not in no_no_regs:
                self.graph[var].target_reg = reg
                for nei in self.graph[var].neighbors:
                    if self.graph[nei].target_reg == None:
                        self.graph[nei].dont_assign.add(reg)
                break   
        else:
            # use stack
            if var in stack_mapping:
                stack_loc = stack_mapping[var]
            else:
                stack_loc = str(-4*(len(stack_mapping)+1)) + '(%ebp)'
                stack_mapping[var] = stack_loc

            self.graph[var].target_reg = stack_loc
            for nei in self.graph[var].neighbors:
                if self.graph[nei].target_reg == None:
                    self.graph[nei].dont_assign.add(stack_loc)


    def get_most_conflicting_var(self, ignore_vars):      
        max_neighbors = 0
        neighbor_to_start = None
        for key in self.graph:
            if 'tp' in key and key not in ignore_vars:
                return key
            
            if key not in ignore_vars and self.graph[key].target_reg == None:
                if len(self.graph[key].neighbors) > max_neighbors:
                    max_neighbors = len(self.graph[key].neighbors)
                    neighbor_to_start = key
        
        if neighbor_to_start == None:
            vars = list(self.graph.keys())
            for var in vars:
                if var not in ignore_vars:
                    return var
        return neighbor_to_start 
        
    def coloring_graph(self):
        vars = list(self.graph.keys())
        ignore_vars = []
        ignore_vars_len = 0
        stack_mapping = {}
        while(len(vars) != ignore_vars_len): 
            conflicting_var = self.get_most_conflicting_var(ignore_vars)
            self.assign_reg(conflicting_var, stack_mapping)
            ignore_vars.append(conflicting_var)
            ignore_vars_len = len(ignore_vars)
        return stack_mapping

    def update_reg_var(self, reg_var_mapping, index, var, ir_str, i):
        if not var.isdigit() and '-' not in var: 
            target_reg = self.graph[get_var(var)].target_reg
            reg_var_mapping[i].append({
                "index": index,
                "reg" : target_reg,
                "var" : var
            })
            keywords = ir_str.split(' ')              
            keywords[index] = keywords[index].replace(var, target_reg)
            ir_str = " ".join(keywords)
        return reg_var_mapping, ir_str

    def generate_reg_var_mapping(self, ir_list):
        reg_var_mapping = {}
        for i in range(len(ir_list)):
            keywords = ir_list[i].split(' ')
            if keywords[0] in ["j", "function"] or len(keywords) <= 1:
                continue
            reg_var_mapping[i] = []
            if keywords[0] in ['li', 'neg' 'cmpl', 'is_int', 'project_int', 'inject_int', 'is_bool', 'project_bool', 'inject_bool', 'is_big', 'project_big', 'inject_big', 'is_true', 'create_list', 'assign_stack']:
                reg_var_mapping, ir_list[i] = self.update_reg_var(reg_var_mapping, 1, get_var(keywords[1]), ir_list[i], i)
                reg_var_mapping, ir_list[i] = self.update_reg_var(reg_var_mapping, 2, get_var(keywords[2]), ir_list[i], i)           
            elif keywords[0] in ["not_equals", "equals", "not_equals_big", "equals_big", "get_subscript", "add", "xori", "add", "list_add", "create_closure"]:
                reg_var_mapping, ir_list[i] = self.update_reg_var(reg_var_mapping, 1, get_var(keywords[1]), ir_list[i], i)
                reg_var_mapping, ir_list[i] = self.update_reg_var(reg_var_mapping, 2, get_var(keywords[2]), ir_list[i], i) 
                reg_var_mapping, ir_list[i] = self.update_reg_var(reg_var_mapping, 3, get_var(keywords[1]), ir_list[i], i)
            elif keywords[0] in ["set_subscript"]:
                reg_var_mapping, ir_list[i] = self.update_reg_var(reg_var_mapping, 1, get_var(keywords[1]), ir_list[i], i)
                reg_var_mapping, ir_list[i] = self.update_reg_var(reg_var_mapping, 2, get_var(keywords[2]), ir_list[i], i) 
                # reg_var_mapping, ir_list[i] = self.update_reg_var(reg_var_mapping, 3, self.graph[get_var(keywords[3])].target_reg, get_var(keywords[1]), ir_list[i], i)
                reg_var_mapping, ir_list[i] = self.update_reg_var(reg_var_mapping, 4, get_var(keywords[2]), ir_list[i], i) 
            elif keywords[0] in ["get_free_vars", "get_fun_ptr", "beq"]:
                reg_var_mapping, ir_list[i] = self.update_reg_var(reg_var_mapping, 1, get_var(keywords[1]), ir_list[i], i)
                reg_var_mapping, ir_list[i] = self.update_reg_var(reg_var_mapping, 2, get_var(keywords[2]), ir_list[i], i) 
            elif keywords[0] in ["function_return", "bez"]:
                reg_var_mapping, ir_list[i] = self.update_reg_var(reg_var_mapping, 1, get_var(keywords[1]), ir_list[i], i)
                for j in range(2, len(keywords)):
                    reg_var_mapping, ir_list[i] = self.update_reg_var(reg_var_mapping, j, get_var(keywords[1]), ir_list[i], i)
        return reg_var_mapping, ir_list



    def get_reg_var_mapping(self, ir_assembly, liveness_list):
        self.gen_graph(ir_assembly, liveness_list)
        stack_mapping = self.coloring_graph()
        vars = list(self.graph.keys())
        vars.sort()
        
        reg_var_mapping, ir_assembly = self.generate_reg_var_mapping(ir_assembly)

        print(":::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::")
        # import ipdb; ipdb.set_trace()
        for k in self.graph:
            print(k, self.graph[k].target_reg, self.graph[k].neighbors, self.graph[k].dont_assign)

        print(":::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::")

        return reg_var_mapping, ir_assembly, stack_mapping