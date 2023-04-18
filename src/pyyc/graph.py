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

    def gen_graph(self, ir_assembly, liveness_list):
        liveness_list.remove(liveness_list[0])
        for i in range(len(ir_assembly)):
            inst = ir_assembly[i]
            op = inst.split(' ')[0]
            if ":" in op or op in ["je", "jmp"]: 
                continue
            live_vars = liveness_list[i]
            keywords = inst.split(' ')
            
            target_var = keywords[-1]
            if op == "movl": 
                # target interfers with everything in live_vars except src_op
                target_node = self.get_node(target_var)
                src_op = keywords[1].split(',')[0]
                for live_var in live_vars:
                    if live_var == target_var or live_var == src_op:
                        continue
                    live_var_node = self.get_node(live_var)
                    live_var_node.neighbors.add(target_var)
                    target_node.neighbors.add(live_var)
                    

            elif op == "addl":
                # target intergeres with everything in live_vars
                target_node = self.get_node(target_var)
                src_op = keywords[1]
                
                for live_var in live_vars:
                    if live_var == target_var:
                        continue
                    live_var_node = self.get_node(live_var)
                    live_var_node.neighbors.add(target_var)
                    target_node.neighbors.add(live_var)
            
            elif op == "negl":
                target_node = self.get_node(target_var)
                
                for live_var in live_vars:
                    if live_var == target_var:
                        continue
                    live_var_node = self.get_node(live_var)
                    live_var_node.neighbors.add(target_var)
                    target_node.neighbors.add(live_var)

            elif op in ['print', 'eval_input']:
                # caller saved registers will interfer with everything in live_vars
                target_node = self.get_node(target_var)
                target_node.dont_assign = target_node.dont_assign.union(self.temp_caller_saved_registers)
                for live_var in live_vars:
                    if live_var == target_var:
                        continue
                    live_var_node = self.get_node(live_var)
                    live_var_node.dont_assign = live_var_node.dont_assign.union(self.temp_caller_saved_registers)
                    target_node.dont_assign = target_node.dont_assign.union(self.temp_caller_saved_registers)
                    live_var_node = self.get_node(live_var)
                    live_var_node.neighbors.add(target_var)
                    target_node.neighbors.add(live_var)
            elif op in ['inject_int', 'project_int', 'inject_bool', 'project_bool' , 'inject_big', 'project_big'  'is_int', 'is_big', 'is_bool', 'is_true']:  
                # caller saved registers will interfer with everything in live_vars               
                target_node = self.get_node(target_var)
                target_node.dont_assign = target_node.dont_assign.union(self.temp_caller_saved_registers)
                src_op =  keywords[1].split(',')[0]
                for live_var in live_vars:
                    if live_var == target_var:
                        continue
                    live_var_node = self.get_node(live_var)
                    live_var_node.dont_assign = live_var_node.dont_assign.union(self.temp_caller_saved_registers)
                    target_node.dont_assign = target_node.dont_assign.union(self.temp_caller_saved_registers)
                    live_var_node.neighbors.add(target_var)
                    target_node.neighbors.add(live_var)
                    
            elif op in ['equals', 'not_equals', "equals_big", "not_equals_big"]:
                # compare saved registers will interfere with live_vars
                target_node = self.get_node(target_var)
                target_node.dont_assign = target_node.dont_assign.union(self.compare_register_clash)
                src_op1 = keywords[1]
                src_op2 = keywords[2]
                for live_var in live_vars:
                    if live_var == target_var: #or live_var == src_op1 or live_var == src_op2:
                        continue
                    live_var_node = self.get_node(live_var)
                    live_var_node.neighbors.add(target_var)
                    target_node.neighbors.add(live_var)
                    live_var_node.dont_assign = live_var_node.dont_assign.union(self.compare_register_clash)
                    target_node.dont_assign = target_node.dont_assign.union(self.compare_register_clash)
                    if '$' not in src_op1:
                        src_op1_node = self.get_node(src_op1)
                        src_op1_node.dont_assign = src_op1_node.dont_assign.union(self.compare_register_clash)

                        target_node.neighbors.add(src_op1)
                        src_op1_node.neighbors.add(target_var)
                    if '$' not in src_op2:
                        src_op2_node = self.get_node(src_op2)
                        src_op2_node.dont_assign = src_op2_node.dont_assign.union(self.compare_register_clash)

                        target_node.neighbors.add(src_op2)
                        src_op2_node.neighbors.add(target_var)

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

    def generate_reg_var_mapping(self, ir_assembly):
        reg_var_mapping = {}
        for i in range(len(ir_assembly)):
            keywords = ir_assembly[i].split(' ')
            if keywords[0] in ["je", "jmp"] or len(keywords) <= 1:
                continue
            reg_var_mapping[i] = []

            if keywords[0] in ['addl', 'movl', 'cmpl', 'is_int', 'project_int', 'inject_int', 'is_bool', 'project_bool', 'inject_bool', 
                               "is_big", "project_big", "inject_big", "is_true"] and '$' not in keywords[-1]:
                
                reg_var_mapping[i].append({
                    "reg" : self.graph[keywords[-1]].target_reg,
                    "var" : keywords[-1]
                })

                ir_assembly[i] = ir_assembly[i].replace(keywords[-1], self.graph[keywords[-1]].target_reg)
            elif keywords[0] in ["not_equals", "equals", "not_equals_big", "equals_big"]:
                if '$' not in keywords[2]:
                    reg_var_mapping[i].append({
                        "reg" : self.graph[keywords[2]].target_reg,
                        "var" : keywords[2]
                    })
                    ir_assembly[i] = ir_assembly[i].replace(keywords[2], self.graph[keywords[2]].target_reg)

                reg_var_mapping[i].append({
                    "reg" : self.graph[keywords[3]].target_reg,
                    "var" : keywords[3]
                })
                ir_assembly[i] = ir_assembly[i].replace(keywords[3], self.graph[keywords[3]].target_reg)

            if '$' not in keywords[1]:
                reg_var_mapping[i].append({
                    "reg" : self.graph[keywords[1].split(',')[0]].target_reg,
                    "var" : keywords[1].split(',')[0]
                })    
                ir_assembly[i] = ir_assembly[i].replace(keywords[1].split(',')[0], self.graph[keywords[1].split(',')[0]].target_reg)
                

        return reg_var_mapping, ir_assembly

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