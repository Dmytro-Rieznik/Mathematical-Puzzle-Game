import pygame
import sys
import os
import json
import math
import random

# Define all combinator types in order of levels.json structure
COMBINATOR_TYPES = [
    "plus",
    "minus",
    "multiply",
    "divide",
    "degree",
    "root",
    "degree_3",
    "root_3"
]

# Color Palette (Elegant Dark Slate/Sky theme)
COLOR_BG = (15, 23, 42)            # Slate 900
COLOR_PANEL_BG = (30, 41, 59)       # Slate 800
COLOR_BORDER = (71, 85, 105)        # Slate 600
COLOR_TEXT = (241, 245, 249)        # Slate 100
COLOR_TEXT_MUTED = (148, 163, 184)   # Slate 400

COLOR_PRIMARY = (14, 165, 233)       # Sky 500 (Blue)
COLOR_PRIMARY_HOVER = (56, 189, 248) # Sky 400
COLOR_SUCCESS = (34, 197, 94)       # Green 500
COLOR_SUCCESS_HOVER = (74, 222, 128) # Green 400
COLOR_DANGER = (239, 68, 68)        # Red 500
COLOR_DANGER_HOVER = (248, 113, 113) # Red 400

# Editor state
levels = []
selected_level_index = None
editor_inputs = {}  # {(col, row): value_str}
editor_output = None  # {"x": col, "y": row, "target_value": value_str}
editor_bridge = 0
editor_combinators = {op: 0 for op in COMBINATOR_TYPES}
editor_solution_layout = {}  # {(col, row): (type_str, val_or_op)}
active_editing_cell = None  # (col, row, type) e.g. type is 'input' or 'output'
validation_state = 'unverified'  # 'unverified', 'solvable', 'unsolvable'
validation_result_str = ""
generation_difficulty = 'Medium'
level_list_scroll = 0

def load_levels_file():
    global levels
    try:
        with open('levels.json', 'r') as f:
            data = json.load(f)
            levels = data.get('levels', [])
    except (FileNotFoundError, json.JSONDecodeError):
        levels = []

def save_levels_file():
    # Update ids to match list order
    for idx, lvl in enumerate(levels):
        lvl['id'] = idx
        
    with open('levels.json', 'w') as f:
        json.dump({"levels": levels}, f, indent=2)

def load_level_to_editor(idx):
    global editor_inputs, editor_output, editor_bridge, editor_combinators, editor_solution_layout
    global active_editing_cell, validation_state, validation_result_str
    
    editor_solution_layout = {}
    active_editing_cell = None
    validation_state = 'unverified'
    validation_result_str = ""
    
    if idx is None or idx < 0 or idx >= len(levels):
        # Reset to default empty level
        editor_inputs = {}
        editor_output = None
        editor_bridge = 0
        editor_combinators = {op: 0 for op in COMBINATOR_TYPES}
        return
        
    lvl_data = levels[idx]
    
    # Load inputs
    editor_inputs = {}
    for inp in lvl_data.get('inputs', []):
        editor_inputs[(inp['x'], inp['y'])] = str(inp['value'])
        
    # Load output
    out = lvl_data.get('output', {})
    if out:
        editor_output = {"x": out['x'], "y": out['y'], "target_value": str(out['target_value'])}
    else:
        editor_output = None
        
    # Load bridge
    editor_bridge = lvl_data.get('bridge', 0)
    
    # Load combinators
    editor_combinators = {op: 0 for op in COMBINATOR_TYPES}
    for comb in lvl_data.get('combinators', []):
        editor_combinators[comb['type']] = comb['count']

def get_level_dict_from_editor():
    # Convert inputs
    inputs_list = []
    for (x, y), val_str in editor_inputs.items():
        try:
            val = int(val_str)
        except ValueError:
            val = 0
        inputs_list.append({"x": x, "y": y, "value": val})
        
    # Convert output
    if editor_output:
        try:
            t_val = int(editor_output['target_value'])
        except ValueError:
            t_val = 0
        out_dict = {"x": editor_output['x'], "y": editor_output['y'], "target_value": t_val}
    else:
        out_dict = {"x": 5, "y": 0, "target_value": 0}
        
    # Convert combinators
    combinators_list = []
    for op in COMBINATOR_TYPES:
        combinators_list.append({"type": op, "count": editor_combinators.get(op, 0)})
        
    return {
        "id": selected_level_index if selected_level_index is not None else len(levels),
        "combinators": combinators_list,
        "output": out_dict,
        "inputs": inputs_list,
        "bridge": editor_bridge,
        "mapSize": {"rows": 12, "columns": 12}
    }

# Solver/Validator
def solve_level(inputs, target_value, combinators_counts):
    memo = set()
    # initial_nums format: (val, (expr_str, ast_node))
    # where ast_node is ("input", val, idx)
    initial_nums = tuple(sorted((val, (str(val), ("input", val, idx))) for idx, val in enumerate(inputs)))
    initial_comb = tuple(sorted((k, v) for k, v in combinators_counts.items() if v > 0))
    
    def search(nums, combs):
        # Memoize by values only
        vals_only = tuple(sorted(val for val, (expr, ast) in nums))
        state = (vals_only, combs)
        if state in memo:
            return None
        memo.add(state)
        
        # Check if target is in nums
        for val, (expr, ast) in nums:
            if abs(val - target_value) < 1e-9:
                return expr, ast
                
        combs_dict = dict(combs)
        
        # Try binary combinators
        for op in ['plus', 'minus', 'multiply', 'divide']:
            if combs_dict.get(op, 0) > 0:
                n = len(nums)
                if n >= 2:
                    new_combs_dict = combs_dict.copy()
                    new_combs_dict[op] -= 1
                    next_combs = tuple(sorted((k, v) for k, v in new_combs_dict.items() if v > 0))
                    
                    for i in range(n):
                        for j in range(n):
                            if i == j:
                                continue
                            x_val, (x_expr, x_ast) = nums[i]
                            y_val, (y_expr, y_ast) = nums[j]
                            
                            rem_nums = list(nums)
                            rem_nums.remove((x_val, (x_expr, x_ast)))
                            rem_nums.remove((y_val, (y_expr, y_ast)))
                            
                            results = []
                            if op == 'plus':
                                results.append((x_val + y_val, (f"({x_expr} + {y_expr})", (op, x_ast, y_ast))))
                            elif op == 'minus':
                                results.append((x_val - y_val, (f"({x_expr} - {y_expr})", (op, x_ast, y_ast))))
                            elif op == 'multiply':
                                results.append((x_val * y_val, (f"({x_expr} * {y_expr})", (op, x_ast, y_ast))))
                            elif op == 'divide':
                                if y_val != 0 and x_val % y_val == 0:
                                    results.append((x_val // y_val, (f"({x_expr} / {y_expr})", (op, x_ast, y_ast))))
                                    
                            for res_val, res_info in results:
                                if abs(res_val) > 100000:
                                    continue
                                next_nums = tuple(sorted(rem_nums + [(res_val, res_info)], key=lambda item: item[0]))
                                sol = search(next_nums, next_combs)
                                if sol is not None:
                                    return sol
                                    
        # Try unary combinators
        for op in ['degree', 'root', 'degree_3', 'root_3']:
            if combs_dict.get(op, 0) > 0:
                n = len(nums)
                new_combs_dict = combs_dict.copy()
                new_combs_dict[op] -= 1
                next_combs = tuple(sorted((k, v) for k, v in new_combs_dict.items() if v > 0))
                
                for i in range(n):
                    x_val, (x_expr, x_ast) = nums[i]
                    rem_nums = list(nums)
                    rem_nums.remove((x_val, (x_expr, x_ast)))
                    
                    results = []
                    if op == 'degree':
                        results.append((x_val ** 2, (f"({x_expr})^2", (op, x_ast))))
                    elif op == 'root':
                        if x_val >= 0:
                            r = int(math.isqrt(x_val))
                            if r * r == x_val:
                                results.append((r, (f"sqrt({x_expr})", (op, x_ast))))
                    elif op == 'degree_3':
                        results.append((x_val ** 3, (f"({x_expr})^3", (op, x_ast))))
                    elif op == 'root_3':
                        r = int(round(math.cbrt(x_val)))
                        if r ** 3 == x_val:
                            results.append((r, (f"cbrt({x_expr})", (op, x_ast))))
                            
                    for res_val, res_info in results:
                        if abs(res_val) > 100000:
                            continue
                        next_nums = tuple(sorted(rem_nums + [(res_val, res_info)], key=lambda item: item[0]))
                        sol = search(next_nums, next_combs)
                        if sol is not None:
                            return sol
                            
    final_sol = search(initial_nums, initial_comb)
    return final_sol

def clear_solution():
    global editor_solution_layout
    editor_solution_layout = {}

def layout_solution(ast, inp_positions, output_pos, max_bridges=0):
    # 1. Assign ideal coordinates using barycentric relaxation
    ideal = {}

    # Initialize with default center values
    def init_ideal(node):
        if node[0] == "input":
            ideal[node] = inp_positions[node[2]]
            return
        if len(node) == 3:
            init_ideal(node[1])
            init_ideal(node[2])
        else:
            init_ideal(node[1])
        ideal[node] = (6.0, 6.0)

    init_ideal(ast)

    # Run a few iterations to let operator positions settle
    for _ in range(10):
        def calc_ideal(node, parent_coord=None):
            if node[0] == "input":
                return

            if len(node) == 3:
                calc_ideal(node[1], ideal.get(node))
                calc_ideal(node[2], ideal.get(node))
                c_coords = [ideal[node[1]], ideal[node[2]]]
            else:
                calc_ideal(node[1], ideal.get(node))
                c_coords = [ideal[node[1]]]

            p_coord = parent_coord if parent_coord else output_pos
            coords = c_coords + [p_coord]
            avg_x = sum(c[0] for c in coords) / len(coords)
            avg_y = sum(c[1] for c in coords) / len(coords)
            ideal[node] = (avg_x, avg_y)

        calc_ideal(ast)

    # 2. Map operators to unique central cells (1 to 10)
    central_cells = [(c, r) for c in range(1, 11) for r in range(1, 11)]
    assigned_positions = {}
    occupied_ops = set(inp_positions) | {output_pos}

    operators_in_tree = []
    def collect_ops(node):
        if node[0] == "input":
            return
        collect_ops(node[1])
        if len(node) == 3:
            collect_ops(node[2])
        operators_in_tree.append(node)

    collect_ops(ast)

    # Assign starting from leaves to root, enforcing at least 1 cell of spacing
    for op_node in operators_in_tree:
        ideal_coord = ideal[op_node]
        best_cell = None
        min_dist = float('inf')
        
        # Enforce Manhattan distance >= 2 between any two combinators to prevent adjacent clusters
        for cell in central_cells:
            if cell in occupied_ops:
                continue
            if any(abs(cell[0] - pos[0]) + abs(cell[1] - pos[1]) < 2 for pos in assigned_positions.values()):
                continue
            dist = abs(cell[0] - ideal_coord[0]) + abs(cell[1] - ideal_coord[1])
            if dist < min_dist:
                min_dist = dist
                best_cell = cell
                
        # If no cell satisfies the non-adjacency constraint, relax it and pick any available cell
        if not best_cell:
            min_dist = float('inf')
            for cell in central_cells:
                if cell in occupied_ops:
                    continue
                dist = abs(cell[0] - ideal_coord[0]) + abs(cell[1] - ideal_coord[1])
                if dist < min_dist:
                    min_dist = dist
                    best_cell = cell

        if best_cell:
            assigned_positions[op_node] = best_cell
            occupied_ops.add(best_cell)
        else:
            # fallback
            assigned_positions[op_node] = (6, 6)

    # 3. We collect the connections we need to route
    # Format of connections: (start_pos, end_pos, is_order_dep, conn_type)
    connections = []

    def collect_connections(node):
        if node[0] == "input":
            return

        parent_pos = assigned_positions[node]
        op_type = node[0]
        is_order_dep = op_type in ['minus', 'divide']

        if len(node) == 3:
            left_child = node[1]
            right_child = node[2]

            left_pos = inp_positions[left_child[2]] if left_child[0] == "input" else assigned_positions[left_child]
            right_pos = inp_positions[right_child[2]] if right_child[0] == "input" else assigned_positions[right_child]

            connections.append((left_pos, parent_pos, is_order_dep, 1)) # left is type 1 if order-dependent
            connections.append((right_pos, parent_pos, is_order_dep, 0)) # right is type 0

            collect_connections(left_child)
            collect_connections(right_child)
        else:
            child = node[1]
            child_pos = inp_positions[child[2]] if child[0] == "input" else assigned_positions[child]

            connections.append((child_pos, parent_pos, False, 0))
            collect_connections(child)

    collect_connections(ast)
    # Output connection
    root_pos = assigned_positions[ast]
    connections.append((root_pos, output_pos, False, 0))

    # 4. Route connections using Pathfinder with Bridge support
    placed = {} # {coord: (type_str, val_or_op, conn_directions)}
    # Add combinators first so pathfinder knows they are blocked
    for node, coord in assigned_positions.items():
        placed[coord] = ("combinator", node[0], set())

    bridges_used = 0

    def check_neighbors_grid(c, r, placed_grid, path_cells, start, end):
        # We only check internal cells
        if not (1 <= c <= 10 and 1 <= r <= 10):
            return True

        # Build customization type map: 0 = connector, 1 = bridge, 2 = combinator
        customization = {}
        for pos, info in placed_grid.items():
            type_str = info[0]
            if type_str == "combinator":
                customization[pos] = 2
            elif type_str == "bridge":
                customization[pos] = 1
            elif type_str == "connector":
                customization[pos] = 0

        for pos in path_cells:
            # We only count them as connector if they are in the internal grid and not start/end
            if pos != start and pos != end and (1 <= pos[0] <= 10 and 1 <= pos[1] <= 10):
                if pos not in customization:
                    customization[pos] = 0

        up_2 = False
        left_up = False
        up = False
        right_up = False
        left_2 = False
        left = False
        right = False
        right_2 = False
        down_left = False
        down = False
        down_right = False
        down_2 = False

        offsets = [
            (0, -2),   # up_2
            (-1, -1),  # left_up
            (0, -1),   # up
            (1, -1),   # right_up
            (-2, 0),   # left_2
            (-1, 0),   # left
            (1, 0),    # right
            (2, 0),    # right_2
            (-1, 1),   # down_left
            (0, 1),    # down
            (1, 1),    # down_right
            (0, 2)     # down_2
        ]

        for dc, dr in offsets:
            nc, nr = c + dc, r + dr
            if (nc, nr) in customization:
                type_id = customization[(nc, nr)]

                # Bridge diagonal check:
                if type_id == 1 and (dc, dr) in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
                    return False

                # If neighbor is combinator or bridge, return True immediately (game logic)
                if type_id != 0:
                    return True

                match (dc, dr):
                    case (0, -2): up_2 = True
                    case (-1, -1): left_up = True
                    case (0, -1): up = True
                    case (1, -1): right_up = True
                    case (-2, 0): left_2 = True
                    case (-1, 0): left = True
                    case (1, 0): right = True
                    case (2, 0): right_2 = True
                    case (-1, 1): down_left = True
                    case (0, 1): down = True
                    case (1, 1): down_right = True
                    case (0, 2): down_2 = True

        if (left_up and up and up_2) or (left_2 and left and left_up):
            return False
        if (right_up and up and up_2) or (right_2 and right and right_up):
            return False
        if (left_2 and left and down_left) or (down_left and down and down_2):
            return False
        if (down_right and down and down_2) or (down_right and right and right_2):
            return False
        if (left_up and left and down_left) or (left_up and up and right_up) or (right_up and right and down_right) or (down_right and down and down_left):
            return False
        if (left and left_up and up) or (right and right_up and up) or (left and down_left and down) or (right and down_right and down):
            return False

        return True

    def check_bridge_grid(c, r, placed_grid, path_cells):
        # 1. No adjacent bridges
        for dc, dr in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nc, nr = c + dc, r + dr
            if (nc, nr) in placed_grid:
                if placed_grid[(nc, nr)][0] == "bridge":
                    return False

        # 2. No diagonal customized cells (placed or current path)
        custom_positions = set(placed_grid.keys()) | set(path_cells)
        for dc, dr in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
            nc, nr = c + dc, r + dr
            if (nc, nr) in custom_positions:
                return False

        return True

    # Define a local pathfinder helper
    def find_path(start, end, max_bridges_allowed):
        # BFS search
        queue = [([start], 0)]
        visited = {} # {(coord, bridges): path_len}

        # Blocked cells: all inputs, output, and combinators, except start/end
        blocked = (set(inp_positions) | {output_pos} | set(assigned_positions.values())) - {start, end}

        while queue:
            path, b_count = queue.pop(0)
            curr = path[-1]

            if curr == end:
                return path, b_count

            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nxt = (curr[0] + dx, curr[1] + dy)
                # Only allow moving inside the 10x10 internal grid, unless nxt is the final destination (border input/output)
                is_valid_cell = (nxt == end) or (1 <= nxt[0] <= 10 and 1 <= nxt[1] <= 10)
                if not is_valid_cell:
                    continue
                if nxt in blocked:
                    continue

                cell_info = placed.get(nxt)
                can_enter = False
                nxt_b_count = b_count

                if nxt == end:
                    can_enter = True
                elif cell_info is None:
                    # Enforce check_neighbors constraint
                    if check_neighbors_grid(nxt[0], nxt[1], placed, path, start, end):
                        can_enter = True
                elif cell_info[0] == "connector" and cell_info[1] != 1: # don't cross input type 1 connectors
                    # Check if we can place a bridge
                    if b_count < max_bridges_allowed:
                        if check_bridge_grid(nxt[0], nxt[1], placed, path):
                            is_horiz = (dx != 0)
                            has_up = placed.get((nxt[0], nxt[1] - 1)) is not None
                            has_down = placed.get((nxt[0], nxt[1] + 1)) is not None
                            has_left = placed.get((nxt[0] - 1, nxt[1])) is not None
                            has_right = placed.get((nxt[0] + 1, nxt[1])) is not None

                            if is_horiz and (has_up or has_down) and not (has_left or has_right):
                                can_enter = True
                                nxt_b_count = b_count + 1
                            elif not is_horiz and (has_left or has_right) and not (has_up or has_down):
                                can_enter = True
                                nxt_b_count = b_count + 1

                if can_enter:
                    state = (nxt, nxt_b_count)
                    if state not in visited or len(path) + 1 < visited[state]:
                        visited[state] = len(path) + 1
                        queue.append((path + [nxt], nxt_b_count))

        return None, 0

    # Route each connection
    for start, end, is_order_dep, conn_type in connections:
        # Pathfinder with remaining bridge count limit
        path, path_bridges = find_path(start, end, max_bridges - bridges_used)

        # Fallback if no bridge path was found
        if not path:
            # First try: respect neighbor constraints
            queue = [[start]]
            visited = {start}
            blocked = (set(inp_positions) | {output_pos} | set(assigned_positions.values())) - {start, end}
            while queue:
                p = queue.pop(0)
                curr = p[-1]
                if curr == end:
                    path = p
                    break
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nxt = (curr[0] + dx, curr[1] + dy)
                    is_valid_cell = (nxt == end) or (1 <= nxt[0] <= 10 and 1 <= nxt[1] <= 10)
                    if is_valid_cell and nxt not in visited and nxt not in blocked:
                        if nxt == end or check_neighbors_grid(nxt[0], nxt[1], placed, p, start, end):
                            visited.add(nxt)
                            queue.append(p + [nxt])

        # Second fallback: ignore neighbor constraints to guarantee connection is made
        if not path:
            queue = [[start]]
            visited = {start}
            blocked = (set(inp_positions) | {output_pos} | set(assigned_positions.values())) - {start, end}
            while queue:
                p = queue.pop(0)
                curr = p[-1]
                if curr == end:
                    path = p
                    break
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nxt = (curr[0] + dx, curr[1] + dy)
                    is_valid_cell = (nxt == end) or (1 <= nxt[0] <= 10 and 1 <= nxt[1] <= 10)
                    if is_valid_cell and nxt not in visited and nxt not in blocked:
                        visited.add(nxt)
                        queue.append(p + [nxt])
            path_bridges = 0

        if path:
            bridges_used += path_bridges
            # Place path cells
            for idx, cell in enumerate(path[1:-1]):
                if cell in placed and placed[cell][0] == "connector":
                    placed[cell] = ("bridge", None, set())
                elif cell not in placed:
                    # Set connector type (0 or 1) next to parent combinator for order-dependent calculations
                    is_adjacent_to_combinator = (idx == len(path[1:-1]) - 1)
                    if is_adjacent_to_combinator and is_order_dep:
                        placed[cell] = ("connector", conn_type, set())
                    else:
                        placed[cell] = ("connector", 0, set())

            # Trace and record explicit connection directions for connector cells
            for i in range(len(path) - 1):
                curr = path[i]
                nxt = path[i+1]

                if nxt[0] == curr[0] + 1:
                    d_curr, d_nxt = "right", "left"
                elif nxt[0] == curr[0] - 1:
                    d_curr, d_nxt = "left", "right"
                elif nxt[1] == curr[1] + 1:
                    d_curr, d_nxt = "down", "up"
                elif nxt[1] == curr[1] - 1:
                    d_curr, d_nxt = "up", "down"
                else:
                    continue

                if curr in placed and placed[curr][0] == "connector":
                    placed[curr][2].add(d_curr)
                if nxt in placed and placed[nxt][0] == "connector":
                    placed[nxt][2].add(d_nxt)

    return placed

# Border spacing helper
def get_spaced_border_positions(count, min_spacing=3):
    """Pick `count` border positions with at least `min_spacing` manhattan distance between each pair."""
    all_border = []
    for i in range(1, 11):
        all_border.append((i, 0))    # Top
    for i in range(1, 11):
        all_border.append((11, i))   # Right
    for i in range(10, 0, -1):
        all_border.append((i, 11))   # Bottom
    for i in range(10, 0, -1):
        all_border.append((0, i))    # Left

    for attempt in range(200):
        random.shuffle(all_border)
        selected = []
        for pos in all_border:
            if all(abs(pos[0] - s[0]) + abs(pos[1] - s[1]) >= min_spacing for s in selected):
                selected.append(pos)
            if len(selected) == count:
                return selected
    # Fallback: just pick evenly spaced
    step = max(1, len(all_border) // count)
    return [all_border[i * step % len(all_border)] for i in range(count)]

# Procedural Generator
def generate_random_level(difficulty):
    if difficulty == "Easy":
        num_ops = random.randint(1, 2)
        num_inputs = random.randint(2, 3)
        max_target = 100
        allowed_ops = ['plus', 'minus', 'multiply']
        decoy_combs_count = 0
        bridge_count = 0
        min_spacing = 4
    elif difficulty == "Medium":
        num_ops = random.randint(2, 4)
        num_inputs = random.randint(3, 4)
        max_target = 500
        allowed_ops = ['plus', 'minus', 'multiply', 'divide', 'degree', 'root']
        decoy_combs_count = random.randint(0, 2)
        bridge_count = random.choice([0, 1])
        min_spacing = 3
    else: # Hard
        num_ops = random.randint(4, 6)
        num_inputs = random.randint(4, 6)
        max_target = 2000
        allowed_ops = ['plus', 'minus', 'multiply', 'divide', 'degree', 'root', 'degree_3', 'root_3']
        decoy_combs_count = random.randint(2, 4)
        bridge_count = random.randint(1, 3)
        min_spacing = 3

    attempts = 0
    while attempts < 300:
        attempts += 1
        inputs_vals = []
        for _ in range(num_inputs):
            if 'root_3' in allowed_ops and random.random() < 0.2:
                inputs_vals.append(random.choice([1, 8, 27, 64]))
            elif 'root' in allowed_ops and random.random() < 0.3:
                inputs_vals.append(random.choice([1, 4, 9, 16, 25, 36, 49, 64]))
            else:
                inputs_vals.append(random.randint(2, 15))

        pool = [{"val": v, "used_inputs": [i]} for i, v in enumerate(inputs_vals)]
        used_ops = {op: 0 for op in COMBINATOR_TYPES}

        success = True
        for _ in range(num_ops):
            if not pool:
                success = False
                break

            op = random.choice(allowed_ops)
            is_binary = op in ['plus', 'minus', 'multiply', 'divide']

            if is_binary:
                if len(pool) < 2:
                    new_val = random.randint(2, 15)
                    inputs_vals.append(new_val)
                    pool.append({"val": new_val, "used_inputs": [len(inputs_vals) - 1]})

                node1 = random.choice(pool)
                pool.remove(node1)
                node2 = random.choice(pool)
                pool.remove(node2)

                val1, val2 = node1["val"], node2["val"]
                res = None
                if op == 'plus':
                    res = val1 + val2
                elif op == 'minus':
                    res = max(val1, val2) - min(val1, val2)
                elif op == 'multiply':
                    res = val1 * val2
                elif op == 'divide':
                    if val2 != 0 and val1 % val2 == 0:
                        res = val1 // val2
                    elif val1 != 0 and val2 % val1 == 0:
                        res = val2 // val1

                if res is None or abs(res) > max_target or res <= 0:
                    pool.append(node1)
                    pool.append(node2)
                    continue

                used_ops[op] += 1
                merged_used = list(set(node1["used_inputs"] + node2["used_inputs"]))
                pool.append({"val": res, "used_inputs": merged_used})

            else:
                node = random.choice(pool)
                pool.remove(node)
                val = node["val"]
                res = None
                if op == 'degree':
                    res = val ** 2
                elif op == 'degree_3':
                    res = val ** 3
                elif op == 'root':
                    if val >= 0:
                        r = int(math.isqrt(val))
                        if r * r == val:
                            res = r
                elif op == 'root_3':
                    r = int(round(math.cbrt(val)))
                    if r ** 3 == val:
                        res = r

                if res is None or abs(res) > max_target or res <= 0:
                    pool.append(node)
                    continue

                used_ops[op] += 1
                pool.append({"val": res, "used_inputs": node["used_inputs"]})

        while len(pool) > 1 and success:
            node1 = pool.pop(0)
            node2 = pool.pop(0)
            op = random.choice(['plus', 'minus', 'multiply'])
            res = None
            if op == 'plus':
                res = node1["val"] + node2["val"]
            elif op == 'minus':
                res = max(node1["val"], node2["val"]) - min(node1["val"], node2["val"])
            elif op == 'multiply':
                res = node1["val"] * node2["val"]

            if res is None or abs(res) > max_target * 1.5 or res <= 0:
                success = False
                break

            used_ops[op] += 1
            merged_used = list(set(node1["used_inputs"] + node2["used_inputs"]))
            pool.append({"val": res, "used_inputs": merged_used})

        if not success or not pool:
            continue

        final_node = pool[0]
        target_val = final_node["val"]
        used_indices = sorted(final_node["used_inputs"])
        if len(used_indices) < 2:
            continue

        final_inputs_vals = [inputs_vals[i] for i in used_indices]

        # Grid placement with guaranteed spacing
        needed = len(final_inputs_vals) + 1  # +1 for output
        positions = get_spaced_border_positions(needed, min_spacing)
        if len(positions) < needed:
            continue

        out_x, out_y = positions[0]
        inputs_list = []
        for k, val in enumerate(final_inputs_vals):
            ix, iy = positions[k + 1]
            inputs_list.append({"x": ix, "y": iy, "value": val})

        # Add decoys
        for _ in range(decoy_combs_count):
            decoy_op = random.choice(COMBINATOR_TYPES)
            used_ops[decoy_op] += 1

        # Verify
        sol_info = solve_level(final_inputs_vals, target_val, used_ops)
        if sol_info is not None:
            sol, _ = sol_info
            return {
                "combinators": [{"type": op, "count": used_ops[op]} for op in COMBINATOR_TYPES],
                "output": {"x": out_x, "y": out_y, "target_value": target_val},
                "inputs": inputs_list,
                "bridge": bridge_count,
                "mapSize": {"rows": 12, "columns": 12}
            }

    # Fallback default level
    return {
        "combinators": [{"type": op, "count": 1 if op == 'plus' else 0} for op in COMBINATOR_TYPES],
        "output": {"x": 5, "y": 0, "target_value": 10},
        "inputs": [
            {"x": 1, "y": 0, "value": 4},
            {"x": 10, "y": 11, "value": 6}
        ],
        "bridge": 0,
        "mapSize": {"rows": 12, "columns": 12}
    }

# Helper UI functions
def draw_text(screen, text, pos, color=(255, 255, 255), font_size=20, center=False):
    font = pygame.font.Font(None, font_size)
    text_surf = font.render(text, True, color)
    rect = text_surf.get_rect()
    if center:
        rect.center = pos
    else:
        rect.topleft = pos
    screen.blit(text_surf, rect)
    return rect

def draw_button(screen, text, rect, normal_color, hover_color, text_color=(255, 255, 255), font_size=20, active=False, active_color=None):
    mouse_pos = pygame.mouse.get_pos()
    is_hovered = rect.collidepoint(mouse_pos)
    
    color = hover_color if is_hovered else normal_color
    if active and active_color:
        color = active_color
        
    pygame.draw.rect(screen, color, rect, border_radius=4)
    pygame.draw.rect(screen, COLOR_BORDER, rect, width=1, border_radius=4)
    
    draw_text(screen, text, rect.center, text_color, font_size, center=True)
    return is_hovered

def load_and_scale(path, size):
    img = pygame.image.load(path)
    return pygame.transform.scale(img, size)

def main():
    global selected_level_index, editor_inputs, editor_output, editor_bridge, editor_combinators, editor_solution_layout
    global active_editing_cell, validation_state, validation_result_str, generation_difficulty, level_list_scroll
    
    pygame.init()
    screen = pygame.display.set_mode((1280, 720))
    pygame.display.set_caption("Mathematical Puzzle - Level Generator & Editor")
    clock = pygame.time.Clock()
    
    # Load levels
    load_levels_file()
    selected_level_index = 0 if levels else None
    load_level_to_editor(selected_level_index)
    
    # Load grid textures
    cell_size = 45
    map_images = {}
    try:
        map_images['cell'] = load_and_scale('images/cell_map.png', (cell_size, cell_size))
        map_images['input'] = load_and_scale('images/input_map.png', (cell_size, cell_size))
        map_images['output'] = load_and_scale('images/output_map.png', (cell_size, cell_size))
        map_images['up'] = load_and_scale('images/up_map_end.png', (cell_size, cell_size))
        map_images['down'] = load_and_scale('images/down_map_end.png', (cell_size, cell_size))
        map_images['left'] = load_and_scale('images/left_map_end.png', (cell_size, cell_size))
        map_images['right'] = load_and_scale('images/right_map_end.png', (cell_size, cell_size))
        map_images['void'] = load_and_scale('images/void_map_end.png', (cell_size, cell_size))
    except pygame.error:
        print("Warning: Game image assets not found. Using fallback shapes/colors.")
        
    # Load combinator icons
    combinator_icons = {}
    for op in COMBINATOR_TYPES:
        try:
            img = pygame.image.load(f"images/textures_for_frame/{op}.png")
            combinator_icons[op] = pygame.transform.scale(img, (24, 24))
        except pygame.error:
            combinator_icons[op] = None
            
    try:
        bridge_img = pygame.image.load("images/textures_for_frame/bridge.png")
        bridge_icon = pygame.transform.scale(bridge_img, (24, 24))
    except pygame.error:
        bridge_icon = None

    # Load scaled grid textures for solution display (from textures_for_map to align with the game grid)
    grid_combinator_images = {}
    for op in COMBINATOR_TYPES:
        try:
            img = pygame.image.load(f"images/textures_for_map/{op}.png")
            grid_combinator_images[op] = pygame.transform.scale(img, (cell_size, cell_size))
        except pygame.error:
            grid_combinator_images[op] = None
            
    try:
        bridge_map_img = pygame.image.load("images/textures_for_map/bridge.png")
        grid_combinator_images['bridge'] = pygame.transform.scale(bridge_map_img, (cell_size, cell_size))
    except pygame.error:
        grid_combinator_images['bridge'] = None

    try:
        map_connector = pygame.image.load("images/textures_for_map/connector.png")
    except pygame.error:
        map_connector = None

    try:
        map_connector_turn = pygame.image.load("images/textures_for_map/connector_turn.png")
    except pygame.error:
        map_connector_turn = None

    try:
        map_connector_input = pygame.image.load("images/textures_for_map/connector_input.png")
    except pygame.error:
        map_connector_input = None

    try:
        map_connector_turn_input = pygame.image.load("images/textures_for_map/connector_turn_input.png")
    except pygame.error:
        map_connector_turn_input = None

    def get_solution_connector_image(c, r, conn_type=0, conn_directions=None):
        if conn_directions is None:
            conn_directions = set()

        if conn_type == 1:
            base_conn = map_connector_input
            base_turn = map_connector_turn_input
        else:
            base_conn = map_connector
            base_turn = map_connector_turn

        if not base_conn or not base_turn:
            return None

        # Determine connections in each direction using explicit conn_directions
        left = "left" in conn_directions
        right = "right" in conn_directions
        up = "up" in conn_directions
        down = "down" in conn_directions

        if right and down:
            img = base_turn
        elif right and up:
            img = pygame.transform.rotate(base_turn, 90)
        elif left and up:
            img = pygame.transform.rotate(base_turn, 180)
        elif left and down:
            img = pygame.transform.rotate(base_turn, 270)
        elif left or right:
            img = base_conn
        elif up or down:
            img = pygame.transform.rotate(base_conn, 90)
        else:
            img = base_conn

        return pygame.transform.scale(img, (cell_size, cell_size))

    # Panel definitions
    left_panel_rect = pygame.Rect(10, 10, 220, 700)
    grid_panel_rect = pygame.Rect(240, 10, 640, 700)
    right_panel_rect = pygame.Rect(890, 10, 380, 700)
    
    grid_x = 240 + (640 - 12 * cell_size) // 2
    grid_y = 10 + (700 - 12 * cell_size) // 2

    # Keyboard editing state helper
    cursor_timer = 0
    show_cursor = True
    
    running = True
    while running:
        dt = clock.tick(60)
        cursor_timer += dt
        if cursor_timer >= 500:
            show_cursor = not show_cursor
            cursor_timer = 0
            
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False
                
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                
                # Check grid clicks
                if grid_x <= mx < grid_x + 12 * cell_size and grid_y <= my < grid_y + 12 * cell_size:
                    clear_solution()
                    col = (mx - grid_x) // cell_size
                    row = (my - grid_y) // cell_size
                    
                    # Exclude corners
                    is_corner = (col == 0 and row == 0) or (col == 0 and row == 11) or (col == 11 and row == 0) or (col == 11 and row == 11)
                    is_border = col == 0 or col == 11 or row == 0 or row == 11
                    
                    if is_border and not is_corner:
                        # Cycle node: Empty -> Input -> Output -> Empty
                        if (col, row) in editor_inputs:
                            # It is an input. Change it to Output.
                            editor_inputs.pop((col, row))
                            editor_output = {"x": col, "y": row, "target_value": "10"}
                            active_editing_cell = (col, row, 'output')
                            validation_state = 'unverified'
                        elif editor_output and editor_output['x'] == col and editor_output['y'] == row:
                            # It is the output. Clear it.
                            editor_output = None
                            active_editing_cell = None
                            validation_state = 'unverified'
                        else:
                            # It was empty. Make it an Input.
                            editor_inputs[(col, row)] = "5"
                            active_editing_cell = (col, row, 'input')
                            validation_state = 'unverified'
                    else:
                        # Click on non-border cell cancels editing
                        active_editing_cell = None
                
                else:
                    # Cancel cell editing if clicking outside the grid (unless clicking textboxes)
                    # Let's keep editing active unless explicitly cleared, or click outside panels
                    pass

                # Check Left Panel - Levels list selection
                if left_panel_rect.collidepoint(mx, my):
                    # Level items bounds
                    for i in range(14):
                        idx = level_list_scroll + i
                        if idx < len(levels):
                            item_rect = pygame.Rect(20, 50 + i * 40, 200, 32)
                            if item_rect.collidepoint(mx, my):
                                selected_level_index = idx
                                load_level_to_editor(idx)
                                active_editing_cell = None
                                
                    # Scroll buttons
                    scroll_up_rect = pygame.Rect(20, 610, 95, 30)
                    scroll_dn_rect = pygame.Rect(125, 610, 95, 30)
                    if scroll_up_rect.collidepoint(mx, my) and level_list_scroll > 0:
                        level_list_scroll -= 1
                    if scroll_dn_rect.collidepoint(mx, my) and level_list_scroll + 14 < len(levels):
                        level_list_scroll += 1
                        
                    # New Level button
                    new_lvl_rect = pygame.Rect(20, 650, 200, 40)
                    if new_lvl_rect.collidepoint(mx, my):
                        selected_level_index = None
                        load_level_to_editor(None)
                        
                # Check Right Panel - Actions and Quantity adjustments
                if right_panel_rect.collidepoint(mx, my):
                    active_editing_cell = None  # click on panels cancels editing
                    
                    # Bridges adjustment
                    y_off = 70
                    btn_minus = pygame.Rect(1020, y_off, 24, 24)
                    btn_plus = pygame.Rect(1080, y_off, 24, 24)
                    if btn_minus.collidepoint(mx, my) and editor_bridge > 0:
                        clear_solution()
                        editor_bridge -= 1
                        validation_state = 'unverified'
                    if btn_plus.collidepoint(mx, my) and editor_bridge < 10:
                        clear_solution()
                        editor_bridge += 1
                        validation_state = 'unverified'
                        
                    # Combinators adjustment
                    for op_idx, op in enumerate(COMBINATOR_TYPES):
                        y_off = 110 + op_idx * 32
                        btn_minus = pygame.Rect(1020, y_off, 24, 24)
                        btn_plus = pygame.Rect(1080, y_off, 24, 24)
                        if btn_minus.collidepoint(mx, my) and editor_combinators[op] > 0:
                            clear_solution()
                            editor_combinators[op] -= 1
                            validation_state = 'unverified'
                        if btn_plus.collidepoint(mx, my) and editor_combinators[op] < 99:
                            clear_solution()
                            editor_combinators[op] += 1
                            validation_state = 'unverified'
                            
                    # Difficulty buttons (must match draw coordinates exactly)
                    diff_y = 385
                    diffs = [("Easy", 1065, 60), ("Medium", 1130, 65), ("Hard", 1200, 60)]
                    for d_name, d_x, d_w in diffs:
                        d_rect = pygame.Rect(d_x, diff_y, d_w, 26)
                        if d_rect.collidepoint(mx, my):
                            generation_difficulty = d_name
                            
                    # Procedural Generate button
                    gen_rect = pygame.Rect(905, 420, 350, 36)
                    if gen_rect.collidepoint(mx, my):
                        clear_solution()
                        # Generate random level!
                        gen_lvl = generate_random_level(generation_difficulty)
                        # Load generated level
                        editor_inputs = {}
                        for inp in gen_lvl['inputs']:
                            editor_inputs[(inp['x'], inp['y'])] = str(inp['value'])
                        editor_output = {
                            "x": gen_lvl['output']['x'],
                            "y": gen_lvl['output']['y'],
                            "target_value": str(gen_lvl['output']['target_value'])
                        }
                        editor_bridge = gen_lvl['bridge']
                        for op in COMBINATOR_TYPES:
                            editor_combinators[op] = 0
                        for comb in gen_lvl['combinators']:
                            editor_combinators[comb['type']] = comb['count']
                            
                        validation_state = 'unverified'
                        
                    # Verify Level & Show Solution buttons side-by-side
                    ver_rect = pygame.Rect(905, 480, 170, 36)
                    show_sol_rect = pygame.Rect(1085, 480, 170, 36)
                    
                    if ver_rect.collidepoint(mx, my):
                        # Convert editor to inputs/outputs
                        inp_vals = []
                        for val_str in editor_inputs.values():
                            try:
                                inp_vals.append(int(val_str))
                            except ValueError:
                                inp_vals.append(0)
                                
                        if not editor_output:
                            validation_state = 'unsolvable'
                            validation_result_str = "Error: Level needs one output cell!"
                        elif len(inp_vals) < 2:
                            validation_state = 'unsolvable'
                            validation_result_str = "Error: Need at least 2 input values!"
                        else:
                            try:
                                t_val = int(editor_output['target_value'])
                            except ValueError:
                                t_val = 0
                            sol_info = solve_level(inp_vals, t_val, editor_combinators)
                            if sol_info is not None:
                                sol, _ = sol_info
                                validation_state = 'solvable'
                                validation_result_str = f"Solvable! Formula: {sol}"
                            else:
                                validation_state = 'unsolvable'
                                validation_result_str = "Unsolvable with current combinators!"
                                
                    elif show_sol_rect.collidepoint(mx, my):
                        # Convert editor to inputs/outputs
                        inp_vals = []
                        inp_positions = []
                        for pos, val_str in editor_inputs.items():
                            try:
                                inp_vals.append(int(val_str))
                                inp_positions.append(pos)
                            except ValueError:
                                pass
                                
                        if not editor_output:
                            validation_state = 'unsolvable'
                            validation_result_str = "Error: Level needs one output cell!"
                        elif len(inp_vals) < 2:
                            validation_state = 'unsolvable'
                            validation_result_str = "Error: Need at least 2 input values!"
                        else:
                            try:
                                t_val = int(editor_output['target_value'])
                            except ValueError:
                                t_val = 0
                            sol_info = solve_level(inp_vals, t_val, editor_combinators)
                            if sol_info is not None:
                                sol, ast = sol_info
                                validation_state = 'solvable'
                                validation_result_str = f"Solvable! Formula: {sol}"
                                # layout and place solution
                                editor_solution_layout = layout_solution(ast, inp_positions, (editor_output['x'], editor_output['y']), editor_bridge)
                            else:
                                validation_state = 'unsolvable'
                                validation_result_str = "Unsolvable with current combinators!"
                                editor_solution_layout = {}
                                
                    # Save Level button
                    save_rect = pygame.Rect(905, 590, 350, 36)
                    if save_rect.collidepoint(mx, my):
                        lvl_dict = get_level_dict_from_editor()
                        if selected_level_index is not None:
                            levels[selected_level_index] = lvl_dict
                        else:
                            levels.append(lvl_dict)
                            selected_level_index = len(levels) - 1
                        save_levels_file()
                        load_levels_file()  # reload
                        load_level_to_editor(selected_level_index)
                        
                    # Delete Selected button
                    if selected_level_index is not None:
                        del_rect = pygame.Rect(905, 635, 170, 36)
                        if del_rect.collidepoint(mx, my):
                            levels.pop(selected_level_index)
                            save_levels_file()
                            load_levels_file()  # reload
                            selected_level_index = 0 if levels else None
                            load_level_to_editor(selected_level_index)
                            
                    # Clear Grid button
                    clear_rect = pygame.Rect(1085, 635, 170, 36)
                    if clear_rect.collidepoint(mx, my):
                        editor_inputs = {}
                        editor_output = None
                        editor_bridge = 0
                        for op in COMBINATOR_TYPES:
                            editor_combinators[op] = 0
                        validation_state = 'unverified'
                        validation_result_str = ""
                        clear_solution()
            
            elif event.type == pygame.KEYDOWN:
                if active_editing_cell is not None:
                    col, row, c_type = active_editing_cell
                    clear_solution()
                    
                    if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_ESCAPE):
                        active_editing_cell = None
                    elif event.key == pygame.K_BACKSPACE:
                        if c_type == 'input':
                            curr = editor_inputs.get((col, row), "")
                            editor_inputs[(col, row)] = curr[:-1]
                        elif c_type == 'output' and editor_output:
                            curr = editor_output['target_value']
                            editor_output['target_value'] = curr[:-1]
                        validation_state = 'unverified'
                    else:
                        char = event.unicode
                        if char.isdigit():
                            if c_type == 'input':
                                curr = editor_inputs.get((col, row), "")
                                if len(curr) < 5:
                                    editor_inputs[(col, row)] = curr + char
                            elif c_type == 'output' and editor_output:
                                curr = editor_output['target_value']
                                if len(curr) < 5:
                                    editor_output['target_value'] = curr + char
                            validation_state = 'unverified'
                            
        # DRAWING
        screen.fill(COLOR_BG)
        
        # 1. Left Panel (Levels List)
        pygame.draw.rect(screen, COLOR_PANEL_BG, left_panel_rect, border_radius=8)
        pygame.draw.rect(screen, COLOR_BORDER, left_panel_rect, width=1, border_radius=8)
        draw_text(screen, "Levels List", (20, 20), COLOR_TEXT, font_size=24)
        
        for i in range(14):
            idx = level_list_scroll + i
            if idx < len(levels):
                item_rect = pygame.Rect(20, 50 + i * 40, 200, 32)
                is_sel = (idx == selected_level_index)
                bg_color = COLOR_PRIMARY if is_sel else (47, 55, 71)
                text_color = COLOR_TEXT if is_sel else COLOR_TEXT_MUTED
                
                pygame.draw.rect(screen, bg_color, item_rect, border_radius=4)
                draw_text(screen, f"Level {idx + 1}", item_rect.center, text_color, font_size=20, center=True)
                
        # Scroll & Add buttons
        scroll_up_rect = pygame.Rect(20, 610, 95, 30)
        scroll_dn_rect = pygame.Rect(125, 610, 95, 30)
        draw_button(screen, "^", scroll_up_rect, (51, 65, 85), (71, 85, 105), COLOR_TEXT, font_size=20)
        draw_button(screen, "v", scroll_dn_rect, (51, 65, 85), (71, 85, 105), COLOR_TEXT, font_size=20)
        
        new_lvl_rect = pygame.Rect(20, 650, 200, 40)
        draw_button(screen, "+ New Level", new_lvl_rect, COLOR_PRIMARY, COLOR_PRIMARY_HOVER, COLOR_TEXT, font_size=20)
        
        # 2. Central Panel (Grid Editor)
        pygame.draw.rect(screen, COLOR_PANEL_BG, grid_panel_rect, border_radius=8)
        pygame.draw.rect(screen, COLOR_BORDER, grid_panel_rect, width=1, border_radius=8)
        draw_text(screen, "Grid Map Editor", (250, 20), COLOR_TEXT, font_size=24)
        
        # Render the 12x12 Grid
        for r in range(12):
            for c in range(12):
                cx = grid_x + c * cell_size
                cy = grid_y + r * cell_size
                cell_rect = pygame.Rect(cx, cy, cell_size, cell_size)
                
                is_corner = (c == 0 and r == 0) or (c == 0 and r == 11) or (c == 11 and r == 0) or (c == 11 and r == 11)
                
                # Determine cell image/type
                cell_img = None
                fallback_color = (40, 50, 65)
                
                if (c, r) in editor_inputs:
                    cell_img = map_images.get('input')
                    fallback_color = (30, 64, 175) # blue
                elif editor_output and editor_output['x'] == c and editor_output['y'] == r:
                    cell_img = map_images.get('output')
                    fallback_color = (185, 28, 28) # red
                elif is_corner:
                    cell_img = map_images.get('void')
                    fallback_color = COLOR_BG
                elif (c, r) in editor_solution_layout:
                    layout_data = editor_solution_layout[(c, r)]
                    type_str = layout_data[0]
                    val_or_op = layout_data[1]
                    conn_directions = layout_data[2] if len(layout_data) > 2 else set()
                    if type_str == "combinator":
                        cell_img = grid_combinator_images.get(val_or_op)
                        fallback_color = (16, 185, 129) # green
                    elif type_str == "connector":
                        cell_img = get_solution_connector_image(c, r, val_or_op, conn_directions)
                        fallback_color = (107, 114, 128) # gray
                    elif type_str == "bridge":
                        cell_img = grid_combinator_images.get('bridge')
                        fallback_color = (107, 114, 128) # gray
                elif r == 0:
                    cell_img = map_images.get('up')
                elif r == 11:
                    cell_img = map_images.get('down')
                elif c == 0:
                    cell_img = map_images.get('left')
                elif c == 11:
                    cell_img = map_images.get('right')
                else:
                    cell_img = map_images.get('cell')
                    fallback_color = (55, 65, 81)
                    
                if cell_img:
                    screen.blit(cell_img, (cx, cy))
                else:
                    pygame.draw.rect(screen, fallback_color, cell_rect)
                    pygame.draw.rect(screen, COLOR_BORDER, cell_rect, width=1)
                    
                # Render values
                if (c, r) in editor_inputs:
                    val_str = editor_inputs[(c, r)]
                    # Draw value text
                    editing_this = (active_editing_cell == (c, r, 'input'))
                    display_text = val_str
                    if editing_this:
                        display_text += "|" if show_cursor else " "
                    draw_text(screen, display_text, cell_rect.center, (255, 255, 255), font_size=20, center=True)
                    
                elif editor_output and editor_output['x'] == c and editor_output['y'] == r:
                    val_str = editor_output['target_value']
                    editing_this = (active_editing_cell == (c, r, 'output'))
                    display_text = val_str
                    if editing_this:
                        display_text += "|" if show_cursor else " "
                    draw_text(screen, display_text, cell_rect.center, (255, 255, 255), font_size=20, center=True)
                    
                # Highlight active cell
                if active_editing_cell and active_editing_cell[0] == c and active_editing_cell[1] == r:
                    pygame.draw.rect(screen, (234, 179, 8), cell_rect, width=2) # Golden border
                    
        # 3. Right Panel (Sidebar Controls)
        pygame.draw.rect(screen, COLOR_PANEL_BG, right_panel_rect, border_radius=8)
        pygame.draw.rect(screen, COLOR_BORDER, right_panel_rect, width=1, border_radius=8)
        
        # Level Details
        label_text = f"Editing: Level {selected_level_index + 1}" if selected_level_index is not None else "Editing: New Level"
        draw_text(screen, label_text, (905, 20), COLOR_TEXT, font_size=24)
        draw_text(screen, "Map Size: 12 x 12 (Border cells only for I/O)", (905, 45), COLOR_TEXT_MUTED, font_size=16)
        
        # Bridges control
        y_off = 70
        if bridge_icon:
            screen.blit(bridge_icon, (905, y_off - 4))
        draw_text(screen, f"Bridges count:", (940, y_off), COLOR_TEXT, font_size=18)
        
        btn_minus = pygame.Rect(1020, y_off, 24, 24)
        btn_plus = pygame.Rect(1080, y_off, 24, 24)
        draw_button(screen, "-", btn_minus, (71, 85, 105), (100, 116, 139), COLOR_TEXT, font_size=20)
        draw_button(screen, "+", btn_plus, (71, 85, 105), (100, 116, 139), COLOR_TEXT, font_size=20)
        draw_text(screen, str(editor_bridge), (1060, y_off + 2), COLOR_TEXT, font_size=18, center=True)
        
        # Combinators list controls
        for op_idx, op in enumerate(COMBINATOR_TYPES):
            y_off = 110 + op_idx * 32
            icon = combinator_icons[op]
            if icon:
                screen.blit(icon, (905, y_off - 4))
            draw_text(screen, op.replace('_', ' ').capitalize() + ":", (940, y_off), COLOR_TEXT, font_size=18)
            
            btn_minus = pygame.Rect(1020, y_off, 24, 24)
            btn_plus = pygame.Rect(1080, y_off, 24, 24)
            draw_button(screen, "-", btn_minus, (71, 85, 105), (100, 116, 139), COLOR_TEXT, font_size=20)
            draw_button(screen, "+", btn_plus, (71, 85, 105), (100, 116, 139), COLOR_TEXT, font_size=20)
            draw_text(screen, str(editor_combinators[op]), (1060, y_off + 2), COLOR_TEXT, font_size=18, center=True)
            
        # Procedural Generator Panel
        pygame.draw.line(screen, COLOR_BORDER, (890, 370), (1270, 370))
        draw_text(screen, "Procedural Generator", (905, 385), COLOR_TEXT, font_size=20)
        
        diff_y = 385
        draw_button(screen, "Easy", pygame.Rect(1065, diff_y, 60, 26), 
                    (51, 65, 85), (71, 85, 105), COLOR_TEXT, font_size=16,
                    active=(generation_difficulty == 'Easy'), active_color=COLOR_PRIMARY)
        draw_button(screen, "Medium", pygame.Rect(1130, diff_y, 65, 26), 
                    (51, 65, 85), (71, 85, 105), COLOR_TEXT, font_size=16,
                    active=(generation_difficulty == 'Medium'), active_color=COLOR_PRIMARY)
        draw_button(screen, "Hard", pygame.Rect(1200, diff_y, 60, 26), 
                    (51, 65, 85), (71, 85, 105), COLOR_TEXT, font_size=16,
                    active=(generation_difficulty == 'Hard'), active_color=COLOR_PRIMARY)
                    
        gen_rect = pygame.Rect(905, 420, 350, 36)
        draw_button(screen, "Generate Random Solvable Level", gen_rect, COLOR_PRIMARY, COLOR_PRIMARY_HOVER, COLOR_TEXT, font_size=18)
        
        # Validator Panel
        pygame.draw.line(screen, COLOR_BORDER, (890, 468), (1270, 468))
        ver_rect = pygame.Rect(905, 480, 170, 36)
        show_sol_rect = pygame.Rect(1085, 480, 170, 36)
        draw_button(screen, "Verify Level", ver_rect, (107, 114, 128), (156, 163, 175), COLOR_TEXT, font_size=18)
        draw_button(screen, "Show Solution", show_sol_rect, COLOR_PRIMARY, COLOR_PRIMARY_HOVER, COLOR_TEXT, font_size=18)
        
        status_y = 525
        if validation_state == 'unverified':
            draw_text(screen, "Status: Not Verified", (905, status_y), COLOR_TEXT_MUTED, font_size=18)
        elif validation_state == 'solvable':
            draw_text(screen, "Status: SOLVABLE!", (905, status_y), COLOR_SUCCESS, font_size=18)
            # Render formula string, split if too long
            f_str = validation_result_str
            if len(f_str) > 42:
                # split
                draw_text(screen, f_str[:42], (905, status_y + 22), COLOR_SUCCESS, font_size=16)
                draw_text(screen, f_str[42:], (905, status_y + 40), COLOR_SUCCESS, font_size=16)
            else:
                draw_text(screen, f_str, (905, status_y + 22), COLOR_SUCCESS, font_size=16)
        else:
            draw_text(screen, "Status: UNSOLVABLE", (905, status_y), COLOR_DANGER, font_size=18)
            draw_text(screen, validation_result_str, (905, status_y + 22), COLOR_DANGER, font_size=16)
            
        # File Action Panel
        pygame.draw.line(screen, COLOR_BORDER, (890, 580), (1270, 580))
        save_rect = pygame.Rect(905, 590, 350, 36)
        draw_button(screen, "Save to levels.json", save_rect, COLOR_SUCCESS, COLOR_SUCCESS_HOVER, COLOR_TEXT, font_size=18)
        
        if selected_level_index is not None:
            del_rect = pygame.Rect(905, 635, 170, 36)
            draw_button(screen, "Delete Level", del_rect, COLOR_DANGER, COLOR_DANGER_HOVER, COLOR_TEXT, font_size=18)
            
        clear_rect = pygame.Rect(1085, 635, 170, 36)
        draw_button(screen, "Clear Grid", clear_rect, (100, 116, 139), (148, 163, 184), COLOR_TEXT, font_size=18)

        pygame.display.flip()
        
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
