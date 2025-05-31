import collections

class DagNode:
    def __init__(self, node_id, op, value=None, children=None, captured_child_markers=None): # Added captured_child_markers
        self.id = node_id
        self.op = op
        self.value = value # For 'CONST' nodes
        self.children = children if children else []
        self.markers = set()
        self.main_marker = None
        self.additional_markers = []
        self.captured_child_markers = captured_child_markers if captured_child_markers else [] # Store captured markers

    def __repr__(self):
        child_ids = [c.id for c in self.children]
        # Optionally include captured_child_markers in repr for debugging
        return f"Node(id={self.id}, op='{self.op}', val={self.value}, main='{self.main_marker}', markers={sorted(list(str(m) for m in self.markers))}, children={child_ids}, captured_operands={self.captured_child_markers})"


    def _is_temporary(self, var_name):
        return isinstance(var_name, str) and var_name.startswith('t') and var_name[1:].isdigit()

    def _get_marker_priority(self, marker):
        if not isinstance(marker, str):  # Constant
            return 0
        if not self._is_temporary(marker):  # Non-temporary variable
            return 1
        return 2  # Temporary variable

    def prioritize_markers(self):
        if not self.markers:
            self.main_marker = None
            self.additional_markers = []
            return

        sorted_markers = sorted(list(self.markers), key=lambda m: (self._get_marker_priority(m), str(m)))
        
        self.main_marker = sorted_markers[0]
        self.additional_markers = [m for m in sorted_markers[1:] if m != self.main_marker]


class Optimizer:
    def __init__(self):
        self.node_id_counter = 0
        self.dag_nodes = {}
        self.var_to_node_id = {}
        self.expr_to_node_id = {}
        self.ordered_nodes_for_codegen = []

        # Operator categories (can be class level or initialized here)
        self.arithmetic_ops = ['+', '-', '*', '/']
        self.relational_ops = ['<', '>', '=', '<=', '>=']
        self.logical_ops = ['and', 'or']
        self.computational_ops = self.arithmetic_ops + self.relational_ops + self.logical_ops
        # Add 'wh', 'el', 'ie' to control_flow_ops
        self.control_flow_ops = ['lb', 'gt', 'if', 'do', 'we', 'wh', 'el', 'ie'] 
        self.io_ops = ['write']
        self.control_io_ops = self.control_flow_ops + self.io_ops
        self.commutative_ops = ['+', '*', '=', 'and', 'or']


    def _new_node_id(self):
        self.node_id_counter += 1
        return self.node_id_counter

    def _is_temporary(self, var_name):
        return isinstance(var_name, str) and var_name.startswith('t') and var_name[1:].isdigit()

    def _is_non_temporary(self, var_name):
        return isinstance(var_name, str) and not self._is_temporary(var_name) and var_name != '_'


    def _get_or_create_leaf_node(self, operand_val):
        if operand_val == '_': return None
        if operand_val in self.var_to_node_id:
            return self.dag_nodes[self.var_to_node_id[operand_val]]

        node_id = self._new_node_id()
        op_type = 'CONST' if not isinstance(operand_val, str) else 'ID'
        # Leaf nodes don't have 'captured_child_markers' in the same way op nodes do
        node = DagNode(node_id, op_type, value=operand_val if op_type == 'CONST' else None)
        node.markers.add(operand_val)
        node.prioritize_markers()
        self.dag_nodes[node_id] = node
        self.var_to_node_id[operand_val] = node_id
        return node

    def _update_variable_association(self, var_name, new_node_for_var):
        if var_name == '_': return
        if var_name in self.var_to_node_id:
            old_node_id = self.var_to_node_id[var_name]
            if old_node_id != new_node_for_var.id: # Check if it's actually a different node
                old_node = self.dag_nodes[old_node_id]
                if var_name in old_node.markers:
                    old_node.markers.remove(var_name)
                    old_node.prioritize_markers()
        new_node_for_var.markers.add(var_name)
        new_node_for_var.prioritize_markers()
        self.var_to_node_id[var_name] = new_node_for_var.id

    def _identify_basic_blocks(self, code_tuples):
        if not code_tuples:
            return []

        leaders = {0}
        branch_causing_ops = {'gt', 'if', 'do', 'we', 'el'} # 'el' is also an unconditional jump

        for i, (op, _, _, res) in enumerate(code_tuples):
            if op == 'wh' or op == 'lb': 
                leaders.add(i)

            if op in branch_causing_ops:
                if op in ['if', 'do', 'gt', 'we', 'el'] and res != '_' and isinstance(res, str): # Targets of jumps
                    for j, (inner_op, _, _, inner_res_label) in enumerate(code_tuples):
                        if inner_op == 'lb' and inner_res_label == res:
                            leaders.add(j)
                            break
                if i + 1 < len(code_tuples): # Instruction following a branch
                    leaders.add(i + 1)
            # 'ie' does not inherently define a leader, it's a marker.

        unique_sorted_leaders = sorted(list(leaders))
        # Further ensure uniqueness if multiple conditions make the same index a leader
        if not unique_sorted_leaders: return []
        
        final_leaders = [unique_sorted_leaders[0]]
        for k in range(1, len(unique_sorted_leaders)):
            if unique_sorted_leaders[k] > final_leaders[-1]:
                 final_leaders.append(unique_sorted_leaders[k])
        
        blocks = []
        for i in range(len(final_leaders)):
            start_index = final_leaders[i]
            end_index = final_leaders[i+1] if i + 1 < len(final_leaders) else len(code_tuples)
            if start_index < end_index: 
                blocks.append(code_tuples[start_index:end_index])
        
        return blocks

    def _optimize_block(self, block_code_tuples):
        self.node_id_counter = 0 
        self.dag_nodes.clear()
        self.var_to_node_id.clear()
        self.expr_to_node_id.clear()
        self.ordered_nodes_for_codegen.clear()

        for op, arg1_val, arg2_val, res_var in block_code_tuples:
            node_arg1 = self._get_or_create_leaf_node(arg1_val) if arg1_val != '_' else None
            node_arg2 = self._get_or_create_leaf_node(arg2_val) if arg2_val != '_' else None
            current_op_node = None

            # Capture operand markers *before* potential modification by res_var assignment
            # These will be stored in the DagNode if it's an operation node
            captured_arg1_marker = node_arg1.main_marker if node_arg1 else '_'
            captured_arg2_marker = node_arg2.main_marker if node_arg2 else '_'

            if op == '=':
                if node_arg1:
                    self._update_variable_association(res_var, node_arg1)
            elif op in self.computational_ops:
                folded_value = None
                if node_arg1 and node_arg1.op == 'CONST' and \
                   (not node_arg2 or (node_arg2 and node_arg2.op == 'CONST')):
                    val1, val2 = node_arg1.value, node_arg2.value if node_arg2 else None
                    try:
                        if op == '+': folded_value = val1 + val2
                        elif op == '-': folded_value = val1 - val2
                        elif op == '*': folded_value = val1 * val2
                        elif op == '/' and val2 != 0:
                            folded_value = val1 // val2 if isinstance(val1, int) and isinstance(val2, int) else val1 / val2
                        elif op == '<': folded_value = val1 < val2
                        elif op == '>': folded_value = val1 > val2
                        elif op == '=': folded_value = val1 == val2 # Comparison
                        elif op == '<=': folded_value = val1 <= val2
                        elif op == '>=': folded_value = val1 >= val2
                        elif op == 'and': folded_value = val1 and val2
                        elif op == 'or': folded_value = val1 or val2
                    except (TypeError, ZeroDivisionError): folded_value = None
                
                if folded_value is not None:
                    current_op_node = self._get_or_create_leaf_node(folded_value)
                else: # Common Subexpression or new operation
                    if not node_arg1 or (arg2_val != '_' and not node_arg2 and op not in ['not']): # 'not' is unary
                        print(f"Warning (opt_block): Missing operand node for op {op}, arg1={arg1_val}, arg2={arg2_val}")
                        continue
                    child1_id, child2_id = node_arg1.id, node_arg2.id if node_arg2 else None
                    if op in self.commutative_ops and node_arg2 and child1_id > child2_id:
                        child1_id, child2_id = child2_id, child1_id
                    expr_key = (op, child1_id, child2_id)

                    if expr_key in self.expr_to_node_id:
                        current_op_node = self.dag_nodes[self.expr_to_node_id[expr_key]]
                    else:
                        new_node_id = self._new_node_id()
                        op_children_nodes = []
                        op_captured_markers = []
                        if node_arg1: 
                            op_children_nodes.append(node_arg1)
                            op_captured_markers.append(captured_arg1_marker)
                        if node_arg2: # Only add if it's a binary op and node_arg2 exists
                            op_children_nodes.append(node_arg2)
                            op_captured_markers.append(captured_arg2_marker)
                        
                        current_op_node = DagNode(new_node_id, op, children=op_children_nodes, captured_child_markers=op_captured_markers)
                        self.dag_nodes[new_node_id] = current_op_node
                        self.expr_to_node_id[expr_key] = new_node_id
                        if current_op_node not in self.ordered_nodes_for_codegen:
                             self.ordered_nodes_for_codegen.append(current_op_node)
                if res_var != '_' and current_op_node:
                    self._update_variable_association(res_var, current_op_node)

            elif op in self.control_io_ops:
                new_node_id = self._new_node_id()
                op_children_nodes = []
                op_captured_markers = []
                if node_arg1: 
                    op_children_nodes.append(node_arg1)
                    op_captured_markers.append(captured_arg1_marker)
                # arg2 is usually '_' for these, but handle if it exists
                if node_arg2: 
                    op_children_nodes.append(node_arg2)
                    op_captured_markers.append(captured_arg2_marker)

                current_op_node = DagNode(new_node_id, op, children=op_children_nodes, captured_child_markers=op_captured_markers)
                self.dag_nodes[new_node_id] = current_op_node
                if current_op_node not in self.ordered_nodes_for_codegen:
                    self.ordered_nodes_for_codegen.append(current_op_node)
                if res_var != '_': 
                    current_op_node.markers.add(res_var)
                    current_op_node.prioritize_markers()
                    self.var_to_node_id[res_var] = current_op_node.id
            else: # Unhandled ops
                print(f"Warning (opt_block): Unhandled op '{op}'")
                new_node_id = self._new_node_id()
                op_children_nodes = []
                op_captured_markers = []
                if node_arg1: 
                    op_children_nodes.append(node_arg1)
                    op_captured_markers.append(captured_arg1_marker)
                if node_arg2: 
                    op_children_nodes.append(node_arg2)
                    op_captured_markers.append(captured_arg2_marker)
                current_op_node = DagNode(new_node_id, op, children=op_children_nodes, captured_child_markers=op_captured_markers)
                self.dag_nodes[new_node_id] = current_op_node
                if current_op_node not in self.ordered_nodes_for_codegen:
                    self.ordered_nodes_for_codegen.append(current_op_node)
                if res_var != '_':
                     self._update_variable_association(res_var, current_op_node)

        # --- Regenerate Optimized Code for this block ---
        block_optimized_code = []
        assigned_non_temps_in_block = set()

        for node in self.ordered_nodes_for_codegen:
            op_to_emit = node.op
            
            # Use captured markers for operands
            arg1_to_emit = node.captured_child_markers[0] if len(node.captured_child_markers) > 0 else '_'
            arg2_to_emit = '_'
            if len(node.captured_child_markers) > 1:
                arg2_to_emit = node.captured_child_markers[1]
            
            res_to_emit = '_'
            # For computational ops, result is the node's own main_marker
            if op_to_emit not in self.control_io_ops and op_to_emit not in ['ID', 'CONST']: 
                res_to_emit = node.main_marker
            # For control flow ops, result is often a label, also from node's main_marker
            elif op_to_emit in self.control_flow_ops: 
                res_to_emit = node.main_marker # Label name or '_'
            # 'write' op's res_to_emit is '_', handled by the condition below
            # 'el', 'ie' might have '_' as main_marker if no res_var, which is fine.
            
            # Emit if it's a meaningful operation
            # Control flow ops always emitted. Write always emitted.
            # Others emitted if they have a result.
            if op_to_emit in self.control_flow_ops or \
               op_to_emit == 'write' or \
               (op_to_emit not in self.control_io_ops and res_to_emit != '_'):
                block_optimized_code.append((op_to_emit, arg1_to_emit, arg2_to_emit, res_to_emit))
                if self._is_non_temporary(res_to_emit):
                    assigned_non_temps_in_block.add(res_to_emit)

        sorted_all_nodes_in_block = sorted(self.dag_nodes.values(), key=lambda n: n.id)
        for node in sorted_all_nodes_in_block:
            if node.main_marker is not None: # Node has a value
                for marker in node.additional_markers:
                    if self._is_non_temporary(marker) and \
                       marker != node.main_marker and \
                       marker not in assigned_non_temps_in_block:
                        # Ensure the source of assignment (node.main_marker) is not '_'
                        if node.main_marker != '_':
                             block_optimized_code.append(('=', node.main_marker, '_', marker))
                             assigned_non_temps_in_block.add(marker)
        
        final_clean_block_code = []
        for quad_op, quad_arg1, quad_arg2, quad_res in block_optimized_code:
            if quad_op == '=' and quad_arg1 == quad_res and quad_arg2 == '_':
                continue
            final_clean_block_code.append((quad_op, quad_arg1, quad_arg2, quad_res))
        
        return final_clean_block_code

    def optimize(self, code_tuples):
        if not code_tuples:
            return []
            
        basic_blocks = self._identify_basic_blocks(code_tuples)
        
        all_optimized_code = []
        for i, block in enumerate(basic_blocks):
            # print(f"\n--- Optimizing Basic Block {i+1} ---") # Debug
            # for instr_idx, instr in enumerate(block): print(f"  {instr_idx}: {instr}") # Debug
            optimized_block_code = self._optimize_block(block)
            all_optimized_code.extend(optimized_block_code)

        return all_optimized_code


if __name__ == "__main__":
    optimizer = Optimizer()
    code = [
        # total := total + counter; counter := counter - 1;
        ('=', 10, '_', 'counter'),      # Initial counter
        ('=', 0, '_', 'total'),        # Initial total
        # Block 1 (loop pre-header or first part of loop)
        ('lb', '_', '_', 'L_WHILE_COND'),
        ('>', 'counter', 0, 't1'),     # while counter > 0
        ('do', 't1', '_', 'L_WHILE_END'), # if not t1 (counter <=0) goto end
        # Block 2 (loop body)
        ('lb', '_', '_', 'L_WHILE_BODY_START'), # Often merged with prev if no other entry
        ('+', 'total', 'counter', 'total'), # total := total + counter
        ('-', 'counter', 1, 'counter'),   # counter := counter - 1
        ('we', '_', '_', 'L_WHILE_COND'), # goto L_WHILE_COND
        # Block 3 (loop exit)
        ('lb', '_', '_', 'L_WHILE_END'),
        ('write', 'total', '_', '_')
    ]
    # Simpler test for x = x + y
    # code = [
    #     ('=', 10, '_', 'x'),
    #     ('=', 5, '_', 'y'),
    #     ('+', 'x', 'y', 'x'), # x = x + y
    #     ('write', 'x', '_', '_')
    # ]


    print("--- Original Code ---")
    for line_num, line_code in enumerate(code):
        print(f"{line_num}: {line_code}")

    optimized_code = optimizer.optimize(code)
    print("\n--- Optimized Code ---")
    for line_num, line_code in enumerate(optimized_code):
        print(f"{line_num}: {line_code}")