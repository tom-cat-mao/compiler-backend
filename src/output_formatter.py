def format_synbl(synbl, analyzer_instance):
    lines = []
    if not synbl:
        lines.append("SYNBL is empty.")
        return "\n".join(lines)
    header = f"{'Idx':<3} | {'Name':<15} | {'Cat':<5} | {'Addr/Info':<20}"
    lines.append(header)
    lines.append("-" * len(header))
    for i, entry in enumerate(synbl):
        addr_info_str = str(entry.get('ADDR_PTR'))
        cat = entry.get('CAT')
        addr_ptr = entry.get('ADDR_PTR')
        if cat == 'f' and isinstance(addr_ptr, int):
            addr_info_str = f"PFINFL_IDX:{addr_ptr}"
        elif cat == 'c' and isinstance(addr_ptr, int):
            addr_info_str = f"CONSL_IDX:{addr_ptr}"
        elif cat in ['v', 'p_val', 'p_ref']:
            addr_info_str = str(addr_ptr if addr_ptr is not None else "N/A")
        elif cat == 'program_name' or cat == 't':
            addr_info_str = "N/A"
        lines.append(f"{i:<3} | {str(entry.get('NAME')):<15} | {str(cat):<5} | {addr_info_str:<20}")
    return "\n".join(lines)

def format_typel(typel):
    lines = []
    if not typel:
        lines.append("TYPEL is empty.")
        return "\n".join(lines)
    header = f"{'Idx':<3} | {'Kind':<10} | {'Details':<30}"
    lines.append(header)
    lines.append("-" * len(header))
    for i, entry in enumerate(typel):
        details_str = ""
        if entry.get('KIND') == 'basic':
            details_str = f"Name: {entry.get('NAME')}"
        elif entry.get('KIND') == 'array':
            details_str = f"AINFL_PTR: {entry.get('AINFL_PTR')}"
        lines.append(f"{i:<3} | {str(entry.get('KIND')):<10} | {details_str:<30}")
    return "\n".join(lines)

def format_pfinfl(pfinfl, analyzer_instance):
    lines = []
    if not pfinfl:
        lines.append("PFINFL is empty.")
        return "\n".join(lines)
    header = f"{'Idx':<3} | {'Level':<5} | {'Params':<6} | {'Return Type':<15} | {'Entry Label':<20} | {'Param SYNBL Idxs':<20}"
    lines.append(header)
    lines.append("-" * len(header))
    for i, entry in enumerate(pfinfl):
        ret_type_name = "PROCEDURE"
        if entry.get('RETURN_TYPE_PTR', -1) != -1:
             ret_type_name = analyzer_instance.get_type_name_from_ptr(entry.get('RETURN_TYPE_PTR'))
        param_idxs_str = ", ".join(map(str, entry.get('PARAM_SYNBL_INDICES', [])))
        lines.append(f"{i:<3} | {str(entry.get('LEVEL')):<5} | {str(entry.get('PARAM_COUNT')):<6} | {ret_type_name:<15} | {str(entry.get('ENTRY_LABEL')):<20} | {param_idxs_str:<20}")
    return "\n".join(lines)

def format_ainfl(ainfl, analyzer_instance):
    lines = []
    if not ainfl:
        lines.append("AINFL is empty.")
        return "\n".join(lines)
    header = f"{'Idx':<3} | {'Element Type':<20} | {'LowerB':<6} | {'UpperB':<6} | {'Size':<5}"
    lines.append(header)
    lines.append("-" * len(header))
    for i, entry in enumerate(ainfl):
        el_type_name = analyzer_instance.get_type_name_from_ptr(entry.get('ELEMENT_TYPE_PTR', -1))
        lines.append(f"{i:<3} | {el_type_name:<20} | {str(entry.get('LOWER_BOUND')):<6} | {str(entry.get('UPPER_BOUND')):<6} | {str(entry.get('TOTAL_SIZE')):<5}")
    return "\n".join(lines)

def format_consl(consl, analyzer_instance):
    lines = []
    if not consl:
        lines.append("CONSL is empty.")
        return "\n".join(lines)
    header = f"{'Idx':<3} | {'Value':<20} | {'Type':<20}"
    lines.append(header)
    lines.append("-" * len(header))
    for i, entry in enumerate(consl):
        type_name = analyzer_instance.get_type_name_from_ptr(entry.get('TYPE_PTR', -1))
        lines.append(f"{i:<3} | {str(entry.get('VALUE')):<20} | {type_name:<20}")
    return "\n".join(lines)


def format_keyword_table(keywords_map):
    lines = []
    if not keywords_map:
        lines.append("No keywords defined.")
        return "\n".join(lines)
    
    sorted_keywords = sorted(keywords_map.keys())
    max_idx_len = len(str(len(sorted_keywords)))
    max_keyword_len = max(len(kw) for kw in sorted_keywords) if sorted_keywords else 10
    max_token_len = max(len(keywords_map[kw]) for kw in sorted_keywords) if sorted_keywords else 10
    
    header = f"{'Pos':<{max_idx_len}} | {'Keyword':<{max_keyword_len}} | {'Token Type':<{max_token_len}}"
    lines.append(header)
    lines.append("-" * len(header))
    for i, keyword in enumerate(sorted_keywords):
        pos = i + 1
        lines.append(f"{str(pos):<{max_idx_len}} | {keyword:<{max_keyword_len}} | {keywords_map[keyword]:<{max_token_len}}")
    return "\n".join(lines)

def format_delimiter_table(delimiter_map, available_tokens):
    lines = []
    active_delimiters = {k: v for k, v in delimiter_map.items() if k in available_tokens}
    sorted_symbols = sorted(list(set(active_delimiters.values())))
    
    if not sorted_symbols:
        lines.append("No delimiters defined.")
        return "\n".join(lines)

    symbol_to_types = {sym: [] for sym in sorted_symbols}
    for token_type, sym in active_delimiters.items():
        symbol_to_types[sym].append(token_type)

    max_idx_len = len(str(len(sorted_symbols)))
    max_symbol_len = max(len(sym) for sym in sorted_symbols)
    max_type_len = max(len(", ".join(types)) for types in symbol_to_types.values())

    header = f"{'Pos':<{max_idx_len}} | {'Symbol':<{max_symbol_len}} | {'Token Type(s)':<{max_type_len}}"
    lines.append(header)
    lines.append("-" * len(header))
    for i, symbol in enumerate(sorted_symbols):
        pos = i + 1
        type_names = ", ".join(symbol_to_types[symbol])
        lines.append(f"{str(pos):<{max_idx_len}} | {symbol:<{max_symbol_len}} | {type_names:<{max_type_len}}")
    return "\n".join(lines)

def format_identifier_table(identifiers):
    lines = []
    if not identifiers:
        lines.append("No identifiers found.")
        return "\n".join(lines)
    
    max_idx_len = len(str(len(identifiers)))
    max_id_len = max(len(identifier) for identifier in identifiers) if identifiers else 10
    
    header = f"{'Pos':<{max_idx_len}} | {'Identifier':<{max_id_len}}"
    lines.append(header)
    lines.append("-" * len(header))
    for i, identifier in enumerate(identifiers):
        pos = i + 1
        lines.append(f"{str(pos):<{max_idx_len}} | {identifier:<{max_id_len}}")
    return "\n".join(lines)

def format_constant_table(constants):
    lines = []
    if not constants:
        lines.append("No constants found.")
        return "\n".join(lines)
        
    max_idx_len = len(str(len(constants)))
    max_const_len = max(len(constant) for constant in constants) if constants else 10

    header = f"{'Pos':<{max_idx_len}} | {'Constant':<{max_const_len}}"
    lines.append(header)
    lines.append("-" * len(header))
    for i, constant in enumerate(constants):
        pos = i + 1
        lines.append(f"{str(pos):<{max_idx_len}} | {constant:<{max_const_len}}")
    return "\n".join(lines)


def format_token_sequence(sequence):
    lines = []
    if not sequence:
        lines.append("No token sequence generated.")
        return "\n".join(lines)
    
    for i in range(0, len(sequence), 10):
        lines.append(" ".join(sequence[i:i+10]))
    return "\n".join(lines)


def format_intermediate_code(code):
    lines = []
    if not code:
        lines.append("No intermediate code generated.")
        return "\n".join(lines)
    
    for i, quad in enumerate(code):
        op, arg1, arg2, res = quad
        op_str = str(op)
        arg1_str = str(arg1)
        arg2_str = str(arg2)
        res_str = str(res)
        lines.append(f"({op_str}, {arg1_str}, {arg2_str}, {res_str})")
    return "\n".join(lines)


def format_optimized_code(optimized_code):
    lines = []
    if not optimized_code:
        lines.append("No optimized code generated.")
        return "\n".join(lines)
    
    for i, quad in enumerate(optimized_code):
        op, arg1, arg2, res = quad
        op_str = str(op)
        arg1_str = str(arg1)
        arg2_str = str(arg2)
        res_str = str(res)
        lines.append(f"({op_str}, {arg1_str}, {arg2_str}, {res_str})")
    return "\n".join(lines)
