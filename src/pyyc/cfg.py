
class CFG_NODE():
    def __init__(self, key_index):
        self.key = key_index
        self.code_block = []
        self.links = []
        self.liveness = [[]]
        self.block_type = []
        self.loop_dependencies = []
        self.variable_mapping = {}
        self.reverse_links = []
    

    def get_parent_nodes(self):
        return self.reverse_links.reverse()

    def get_child_nodes(self):
        return self.links
    
    def is_while_node(self):
        if self.block_type is not None and "while" in self.block_type and "end_while" not in self.block_type:
            return True
        return False

    def is_last_block(self):
        if len(self.reverse_links) == 0:
            return True
        return False
    
    def is_loop_node(self):
        if self.block_type is not None and "loop" in self.block_type:
            return True
        return False

    def is_then_node(self):
        if self.block_type is not None and "then" in self.block_type:
            return True
        return False
    
    def is_else_node(self):
        if self.block_type is not None and "else" in self.block_type:
            return True
        return False

    def is_end_if_node(self):
        if self.block_type is not None and "end_if" in self.block_type:
            return True
        return False

    def print_node(self):
        print(self.key, ":", self.code_block, self.links, self.reverse_links, self.loop_dependencies, self.liveness)

class CFG():
    def __init__(self):
        self.key = 0
        self.cfg = []
        self.meta_data_dict = {}
        self.fixes = {}
        self.if_fixes = {}
        self.loop_node_dependencies = {}
    
    def get_key(self):
        key = self.key
        self.key += 1
        return key

    def get_new_node(self):
        key_index = self.get_key()
        return CFG_NODE(key_index)

    def get_loop_block_dependencies(self, loop_key):
        loop_index = self.meta_data_dict[loop_key]
        while_index = self.meta_data_dict["while" + loop_key.replace("loop", "")]
        dependency_blocks = []
        current_index = loop_index
        
        while(True):
            if while_index in self.cfg[current_index].links:
                return dependency_blocks
            else:
                if len(self.cfg[current_index].links) > 0:
                    dependency_blocks.append(self.cfg[current_index].links)
                    current_index = self.cfg[current_index].links[0]
                else:
                    print("ERRRRR: find_end_to_loop_block: No links in the block with key: {key}".format(current_index))
        return dependency_blocks
        

    def create_cfg(self, ir_assembly):
        node = self.get_new_node()
        last_block_index = 0

        for inst in reversed(ir_assembly):
            keywords = inst.split(" ") 
            op = keywords[0]  
            node.code_block.append(inst)
            if op in ['movl', 'addl', 'print', 'eval_input', 'cmpl', 'equals', 'not_equals', 'negl']:
                pass
            
            elif op == 'je':
                if 'else' in inst or 'end_if' in inst:
                    connects_to = keywords[1] + ":" 
                    if connects_to not in self.meta_data_dict:
                        if node.key not in self.if_fixes:
                            self.if_fixes[node.key] = [connects_to]
                        else:
                            self.if_fixes[node.key].append(connects_to)
                    else:
                        node.links.append(self.meta_data_dict[connects_to])

                elif 'while' in inst:
                    connects_to = keywords[1] + ":" 
                    if connects_to not in self.meta_data_dict:
                        if node.key not in self.fixes:
                            self.fixes[node.key] = [connects_to]
                        else:
                            self.fixes[node.key].append(connects_to)
                    else:
                        node.links.append(self.meta_data_dict[connects_to])

            elif op in 'jmp':
                if 'end_if' in inst:
                    connects_to = keywords[1] + ":"
                    if connects_to not in self.meta_data_dict:
                        if node.key not in self.if_fixes:
                            self.if_fixes[node.key] = [connects_to]
                        else:
                            self.if_fixes[node.key].append(connects_to)
                    else:
                        node.links.append(self.meta_data_dict[connects_to])

                elif 'while' in inst:
                    connects_to = keywords[1] + ":"
                    if connects_to not in self.meta_data_dict:
                        if node.key not in self.fixes:
                            self.fixes[node.key] = [connects_to]
                        else:
                            self.fixes[node.key].append(connects_to)
                    else:
                        node.links.append(self.meta_data_dict[connects_to])

            elif "end_if" in op or "end_while" in op:
                node.block_type = inst
                node.code_block.reverse()

                self.meta_data_dict[inst] = node.key
                self.cfg.append(node)
                node = self.get_new_node()
            elif 'if' in op:
                node.block_type = inst
                node.code_block.reverse()
                then_index = "then" + inst.replace("if", "")
                node.links.append(self.meta_data_dict[then_index])
                self.meta_data_dict[inst] = node.key              
                self.cfg.append(node)
                node = self.get_new_node()
            elif 'while' in op:
                node.block_type = inst
                node.code_block.reverse()
                loop_index = "loop" + inst.replace("while", "")
                end_while_index = "end_while" + inst.replace("while", "")
                self.meta_data_dict[inst] = node.key
                node.links.append(self.meta_data_dict[loop_index])

                self.cfg.append(node)
                node = self.get_new_node()
            elif "then" in op :
                node.block_type = inst
                node.code_block.reverse()

                self.meta_data_dict[inst] = node.key
                self.cfg.append(node)
                node = self.get_new_node()
            elif "else" in op:
                node.block_type = inst
                node.code_block.reverse()
                # import ipdb; ipdb.set_trace()
                # s= 9
                # end_if_key = self.meta_data_dict["end_if" + inst.replace("else", "")]
                self.meta_data_dict[inst] = node.key
                self.cfg.append(node)
                node = self.get_new_node()
            elif "loop" in op:
                self.meta_data_dict[inst] = node.key
                node.block_type = inst
                node.code_block.reverse()
                
                node.loop_dependencies = []
                self.loop_node_dependencies[node.key] = inst
                self.cfg.append(node)
                node = self.get_new_node()

        node.code_block.reverse()
        self.cfg.append(node) 
        
        for node_id in self.fixes:
            for label in self.fixes[node_id]:
                index = self.meta_data_dict[label]
                self.cfg[node_id].links.append(index)
        
        for node_id in self.if_fixes:
            for label in self.if_fixes[node_id]:
                try:
                    index = self.meta_data_dict[label]
                except:
                    import ipdb; ipdb.set_trace()
                    s= 9
                self.cfg[node_id].links.append(index)

        for bb in reversed(self.cfg):
            if not bb.links and bb.key != 0:
                bb.links = [bb.key-1]

        for bb in reversed(self.cfg):
            for index in bb.links:    
                self.cfg[index].reverse_links.append(bb.key)

        for loop_index in self.loop_node_dependencies:
            self.cfg[loop_index].loop_dependencies = self.get_loop_block_dependencies(self.loop_node_dependencies[loop_index])

        return self.cfg, self.meta_data_dict
                

                
                

