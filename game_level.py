import pygame
import math
from load_level import LoadLevel

class GameLevel:
    def __init__(self, screen, screen_width, screen_height, level_id):
        self.screen = screen
        self.screen_width = screen_width
        self.screen_height = screen_height

        self.level_data = LoadLevel(level_id) #создания экземпляра класса с данными об уровне

        self.font_back = pygame.font.Font(None, 46)
        self.font_status = pygame.font.Font(None, 24)
        self.back = 'Back'
        self.back_position = ()

        self.position_map_cell = []
        self.font_value = pygame.font.Font(None, 36)

        self.position_frame = []
        self.combinators_in_frame = []
        self.font_combinators_quantity = pygame.font.Font(None, 46)
        self.position_map_cell_customization = []
        self.type_map_texture = []

        self.level_passed = False

        self.frame_initialized = False
        self.map_initialized = False

        self.background = pygame.image.load('images/background.png')
        self.object_frame = pygame.image.load('images/frame.png')

        self.cell_map = pygame.image.load('images/cell_map.png')
        self.input_map = pygame.image.load('images/input_map.png')
        self.output_map = pygame.image.load('images/output_map.png')
        self.up_map_end = pygame.image.load('images/up_map_end.png')
        self.left_map_end = pygame.image.load('images/left_map_end.png')
        self.right_map_end = pygame.image.load('images/right_map_end.png')
        self.down_map_end = pygame.image.load('images/down_map_end.png')
        self.void_map_end = pygame.image.load('images/void_map_end.png')
        self.frame = pygame.image.load('images/frame.png')
        self.frame_active = pygame.image.load('images/frame_active.png')

        self.combinators_sprite_frame = []
        self.combinators_sprite_map = []
        self.combinators_quantity = []
        self.connector = None
        self.connector_turn = None
        self.connector_input = None
        self.connector_inputXY = None
        self.connector_turn_input = None
        self.load_combinators_data()

        # Drag to draw variables
        self.dragging = False
        self.drag_button = None
        self.last_placed_cell = None

        # Animation & Evaluation visualization variables
        self.anim_frame_count = 0
        self.trace_active = False
        self.trace_steps = []
        self.trace_index = 0
        self.trace_timer = 0
        self.trace_step_delay = 2  # snappy frame delay (approx 33ms)

        self.active_search_cells = set()
        self.cell_values = {}
        self.previous_cell_values = {}
        self.fail_cells = set()
        self.evaluation_result = None
        self.eval_finished = False

        self.start_x = 0
        self.start_y = 0
        self.cell_width = 65
        self.cell_height = 65

    def draw(self):
        self.update_animations()
        self.draw_button_back()
        self.draw_map()
        self.draw_frames()
        self.draw_animations_overlay()

    def handle_event(self, event):
        if self.level_passed:
            return self.level_data.level_id + 2
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return 'level_selection'
            
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = event.pos
            if event.button == 1:
                # Check back button
                if isinstance(self.back_position, pygame.Rect) and self.back_position.collidepoint(mouse_pos):
                    return 'level_selection'
                self.handle_frame(mouse_pos)  # Handle clicking frames
                
            if event.button in (1, 3):
                self.dragging = True
                self.drag_button = event.button
                self.draw_at_pos(mouse_pos, event.button, is_drag=False)
                
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button in (1, 3):
                self.dragging = False
                self.drag_button = None
                self.last_placed_cell = None
                
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging and self.drag_button in (1, 3):
                self.draw_at_pos(event.pos, self.drag_button, is_drag=True)
                
        return 'game'

    def draw_button_back(self):
        self.screen.blit(self.background, (0, 0))
        self.back_position = (0, 0)   # Очистка переменной прямоугольника перед отрисовкой

        mouse_pos = pygame.mouse.get_pos()  # Получение позиции курсора мыши

        color = (255, 255, 255)  # Белый цвет по умолчанию
        text = self.font_back.render(self.back, True, (color))  # Белый цвет по умолчанию
        text_pos = self.screen.blit(text, (self.screen_width // 2 - text.get_width() // 2, (self.screen_height // 1.15 - text.get_height())))

        if text_pos.collidepoint(mouse_pos):
            color = (255, 0, 0)  # Изменение цвета на красный, если курсор наведен

        text = self.font_back.render(self.back, True, color)
        self.screen.blit(text, text_pos)
        self.back_position = text_pos

    def draw_map(self):
        if not self.map_initialized:
            map_size = self.level_data.map_size
            self.cell_width = self.cell_map.get_width()
            self.cell_height = self.cell_map.get_height()
            rows, cols = map_size['rows'], map_size['columns']

            self.start_x = (self.screen_width - cols * self.cell_width) // 2
            self.start_y = (self.screen_height - rows * self.cell_height) // 2.5
            start_x = self.start_x
            start_y = self.start_y

            for row in range(rows):
                for col in range(cols):
                    x = start_x + col * self.cell_width
                    y = start_y + row * self.cell_height
                    if (row == 0 and col == 0) or (row == 0 and col == cols - 1) or (row == rows - 1 and col == 0) or (row == rows - 1 and col == cols - 1):
                        self.position_map_cell.append((x, y, self.void_map_end, None))
                    elif row == 0:
                        self.position_map_cell.append((x, y, self.up_map_end, None))
                    elif col == 0:
                        self.position_map_cell.append((x, y, self.left_map_end, None))
                    elif col == cols - 1:
                        self.position_map_cell.append((x, y, self.right_map_end, None))
                    elif row == rows - 1:
                        self.position_map_cell.append((x, y, self.down_map_end, None))
                    else:
                        self.position_map_cell.append((x, y, self.cell_map, None))

            for i in range(len(self.position_map_cell)):
                self.position_map_cell_customization.append((None, None))
                self.type_map_texture.append(0)

            for input_data in self.level_data.inputs:
                x = start_x + input_data['x'] * self.cell_width
                y = start_y + input_data['y'] * self.cell_height
                for i, (px, py, _, _) in enumerate(self.position_map_cell):
                    if px == x and py == y:
                        self.position_map_cell[i] = (x, y, self.input_map, str(input_data['value']))
                        self.position_map_cell_customization[i] = (self.input_map, 'input')

            output_data = self.level_data.output
            x = start_x + output_data['x'] * self.cell_width
            y = start_y + output_data['y'] * self.cell_height
            for i, (px, py, _, _) in enumerate(self.position_map_cell):
                if px == x and py == y:
                    self.position_map_cell[i] = (x, y, self.output_map, str(output_data['target_value']))
                    self.position_map_cell_customization[i] = (self.output_map, 'output')

            self.map_initialized = True  # Установка флага инициализации карты

        for i, (x, y, sprite, value) in enumerate(self.position_map_cell):
            self.screen.blit(sprite, (x, y))
            if self.position_map_cell_customization[i][0] is not None:
                customization_sprite, _ = self.position_map_cell_customization[i]
                self.screen.blit(customization_sprite, (x, y))
            if value:
                color = (0, 0, 255) if sprite == self.input_map else (255, 0, 0)
                text = self.font_value.render(value, True, color)
                text_pos = text.get_rect(center=(x + self.cell_width // 2, y + self.cell_height // 2))
                self.screen.blit(text, text_pos)

    def draw_frames(self):
        if not self.frame_initialized:
            self.position_frame = []

            frame_width = self.frame.get_width()
            frame_height = self.frame.get_height()

            left_frame_width = frame_width * 2
            left_frame_height = frame_height * 2

            left_x = self.screen_width // 4 - left_frame_width // 1.3
            left_start_y = (self.screen_height - 2 * left_frame_height) // 2.25

            for i in range(2):
                y = left_start_y + i * (left_frame_height + 10)
                pos = pygame.Rect(left_x, y, left_frame_width, left_frame_height)
                self.position_frame.append((False, pos))

            right_x_start = 3 * self.screen_width // 4 - frame_width // 2.1
            right_start_y = (self.screen_height - 4 * frame_height) // 2.4

            for i in range(4):
                for j in range(2):
                    x = right_x_start + j * (frame_width + 10)
                    y = right_start_y + i * (frame_height + 10)
                    pos = pygame.Rect(x, y, frame_width, frame_height)
                    self.position_frame.append((False, pos))

            for i, (status, pos) in enumerate(self.position_frame):
                sprite_width = pos.width - 1
                sprite_height = pos.height - 1
                sprite = pygame.transform.scale(self.combinators_sprite_frame[i], (sprite_width, sprite_height))

                temp_surface = pygame.Surface((sprite_width - 1, sprite_height - 1))
                temp_surface.blit(sprite, (0, 0), pygame.Rect(1, 1, sprite_width, sprite_height))

                sprite_x = pos.left + (pos.width - sprite_width)
                sprite_y = pos.top + (pos.height - sprite_height)
                self.combinators_in_frame.append((temp_surface, (sprite_x, sprite_y)))

            self.frame_initialized = True

        for i, (status, pos) in enumerate(self.position_frame):
            if status:
                # Pulsing 3D floating animation for the active frame
                pulse_offset = int(3 * math.sin(self.anim_frame_count * 0.04))
                pulsed_pos = pygame.Rect(pos.left - pulse_offset, pos.top - pulse_offset, pos.width + pulse_offset * 2, pos.height + pulse_offset * 2)
                self.screen.blit(pygame.transform.scale(self.frame_active, (pulsed_pos.width, pulsed_pos.height)), pulsed_pos.topleft)
            else:
                self.screen.blit(pygame.transform.scale(self.frame, (pos.width, pos.height)), pos.topleft)

            sprite, ather_pos = self.combinators_in_frame[i]
            self.screen.blit(sprite, ather_pos)

            if self.combinators_quantity[i] is not None:  # Проверяем, что количество задано
                text = self.font_combinators_quantity.render(str(self.combinators_quantity[i]), True,(255, 255, 255))
                text_pos = text.get_rect(bottomright=(pos.right - 5, pos.bottom - 5))
                self.screen.blit(text, text_pos)

    def handle_frame(self, mouse_pos):
        for i, (status, pos) in enumerate(self.position_frame):
            if pos.collidepoint(mouse_pos):
                if status:
                    self.position_frame[i] = (False, pos)
                    break
                else:
                    for j, (other_status, other_pos) in enumerate(self.position_frame):
                        if other_status:
                            self.position_frame[j] = (False, other_pos)
                    self.position_frame[i] = (True, pos)
                break

    def load_combinators_data(self):
        self.connector = pygame.image.load('images/textures_for_map/connector.png')
        self.connector_turn = pygame.image.load('images/textures_for_map/connector_turn.png')
        self.connector_input = pygame.image.load('images/textures_for_map/connector_input.png')
        self.connector_inputXY = pygame.image.load('images/textures_for_map/connector_inputXY.png')
        self.connector_turn_input = pygame.image.load('images/textures_for_map/connector_turn_input.png')

        self.combinators_sprite_frame.append(pygame.image.load('images/textures_for_frame/connector.png'))
        self.combinators_sprite_frame.append(pygame.image.load('images/textures_for_frame/bridge.png'))
        textures = self.level_data.textures_for_frame
        for texture in textures:
            sprite = pygame.image.load(texture['sprite'])
            self.combinators_sprite_frame.append(sprite)

        self.combinators_sprite_map.append(pygame.image.load('images/textures_for_map/connectorXY.png'))
        self.combinators_sprite_map.append(pygame.image.load('images/textures_for_map/bridge.png'))
        textures = self.level_data.textures_for_map
        for texture in textures:
            sprite = pygame.image.load(texture['sprite'])
            self.combinators_sprite_map.append(sprite)

        self.combinators_quantity.append(None)
        self.combinators_quantity.append(self.level_data.bridge)
        for combinator in self.level_data.combinators:
            count = combinator.get('count')  # Получаем количество, используя ключ 'count'
            self.combinators_quantity.append(count)

    def draw_at_pos(self, pos, button, is_drag):
        if self.is_border_cell_at(pos):
            return

        target_idx = None
        for i, (x, y, sprite, _) in enumerate(self.position_map_cell):
            if sprite.get_rect(topleft=(x, y)).collidepoint(pos):
                target_idx = i
                break

        if target_idx is None:
            return

        if is_drag and target_idx == self.last_placed_cell:
            return
            
        self.last_placed_cell = target_idx
        
        # Reset trace animation since user is editing
        self.reset_trace()

        x, y, sprite, _ = self.position_map_cell[target_idx]

        if button == 1:  # Left mouse button
            selected_combinator_index = self.get_selected_combinator_index()
            if selected_combinator_index is not None:
                # Check if cell is empty
                if self.position_map_cell_customization[target_idx][0] is None:
                    # Place Connector
                    if self.combinators_quantity[selected_combinator_index] is None:
                        if self.check_neighbors(x, y):
                            self.position_map_cell_customization[target_idx] = (
                                self.combinators_sprite_map[selected_combinator_index],
                                selected_combinator_index
                            )
                    # Place Combinator / Bridge
                    elif self.combinators_quantity[selected_combinator_index] > 0:
                        if selected_combinator_index == 1:  # Bridge
                            if self.check_bridge(x, y):
                                self.position_map_cell_customization[target_idx] = (
                                    self.combinators_sprite_map[selected_combinator_index],
                                    selected_combinator_index
                                )
                                self.combinators_quantity[selected_combinator_index] -= 1
                        else:  # Combinator
                            self.position_map_cell_customization[target_idx] = (
                                self.combinators_sprite_map[selected_combinator_index],
                                selected_combinator_index
                            )
                            self.combinators_quantity[selected_combinator_index] -= 1
                
                # If cell is not empty, and we clicked (not dragging)
                elif not is_drag:
                    # Toggle connector type
                    if selected_combinator_index == 0:
                        if self.position_map_cell_customization[target_idx][1] == 0:
                            match self.type_map_texture[target_idx]:
                                case 0:
                                    self.type_map_texture[target_idx] = 1
                                case 1:
                                    self.type_map_texture[target_idx] = 0
                    # Place bridge over connector
                    elif selected_combinator_index == 1 and self.position_map_cell_customization[target_idx][1] == 0:
                        if self.check_bridge(x, y):
                            if self.combinators_quantity[selected_combinator_index] > 0:
                                self.position_map_cell_customization[target_idx] = (
                                    self.combinators_sprite_map[selected_combinator_index],
                                    selected_combinator_index
                                )
                                self.combinators_quantity[selected_combinator_index] -= 1

        elif button == 3:  # Right mouse button
            if self.position_map_cell_customization[target_idx][0] is not None:
                comb_idx = self.position_map_cell_customization[target_idx][1]
                if self.combinators_quantity[comb_idx] is not None:
                    self.combinators_quantity[comb_idx] += 1
                self.position_map_cell_customization[target_idx] = (None, None)
                self.type_map_texture[target_idx] = 0

        # Update connector textures around the map
        for i, (cx, cy, _, _) in enumerate(self.position_map_cell):
            if self.position_map_cell_customization[i][0] is not None:
                if self.position_map_cell_customization[i][1] == 0:
                    connector_texture = self.update_connector_textures(cx, cy, self.type_map_texture[i])
                    self.position_map_cell_customization[i] = (connector_texture, 0)

        # Recalculate evaluation path
        self.passing_check()

    def get_selected_combinator_index(self):
        for i, (status, pos) in enumerate(self.position_frame):
            if status:
                return i
        return None

    def update_connector_textures(self, x, y, type):
        left_cell = x - 65, y
        right_cell = (x + 65, y)
        up_cell = (x, y - 65)
        down_cell = (x, y + 65)

        left = right = up = down = False

        connector_type = self.combinators_sprite_map[0]

        for i, (customization, _) in enumerate(self.position_map_cell_customization):
            if customization is not None:
                nx, ny = self.position_map_cell[i][:2]
                if (nx, ny) == left_cell:
                    left = True
                elif (nx, ny) == right_cell:
                    right = True
                elif (nx, ny) == up_cell:
                    up = True
                elif (nx, ny) == down_cell:
                    down = True

        match type:
            case 0:
                if right and down:
                    connector_type = self.connector_turn
                elif right and up:
                    connector_type = pygame.transform.rotate(self.connector_turn, 90)
                elif left and up:
                    connector_type = pygame.transform.rotate(self.connector_turn, 180)
                elif left and down:
                    connector_type = pygame.transform.rotate(self.connector_turn, 270)
                elif left or right:
                    connector_type = self.connector
                elif up or down:
                    connector_type = pygame.transform.rotate(self.connector, 90)
            case 1:
                if right and down:
                    connector_type = self.connector_turn_input
                elif right and up:
                    connector_type = pygame.transform.rotate(self.connector_turn_input, 90)
                elif left and up:
                    connector_type = pygame.transform.rotate(self.connector_turn_input, 180)
                elif left and down:
                    connector_type = pygame.transform.rotate(self.connector_turn_input, 270)
                elif left or right:
                    connector_type = self.connector_input
                elif up or down:
                    connector_type = pygame.transform.rotate(self.connector_input, 90)
                else:
                    connector_type = self.connector_inputXY

        return connector_type

    def check_neighbors(self, x, y):
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
        offsets =[(0, -130), (-65, -65), (0, -65), (65, -65), (-130, 0), (-65, 0), (65, 0), (130, 0), (-65, 65), (0, 65), (65, 65), (0, 130)]

        for dx, dy in offsets:
            nx, ny = x + dx, y + dy
            for i, (px, py, _, _) in enumerate(self.position_map_cell):
                if (nx, ny) == (px, py) and self.position_map_cell_customization[i][0] is not None:
                    if (self.position_map_cell_customization[i][0] == self.combinators_sprite_map[1] and ((dx, dy) == (-65, -65) or (dx, dy) == (65, -65) or (dx, dy) == (-65, 65) or (dx, dy) == (65, 65))):
                        return False
                    elif self.position_map_cell_customization[i][1] != 0:
                        return True
                    match (dx, dy):
                        case (0, -130):
                            up_2 = True
                        case (-65, -65):
                            left_up = True
                        case (0, -65):
                            up = True
                        case (65, -65):
                            right_up = True
                        case (-130, 0):
                            left_2 = True
                        case (-65, 0):
                            left = True
                        case (65, 0):
                            right = True
                        case (130, 0):
                            right_2 = True
                        case (-65, 65):
                            down_left = True
                        case (0, 65):
                            down = True
                        case (65, 65):
                            down_right = True
                        case (0, 130):
                            down_2 = True
                    break


        if (left_up and up and up_2) or (left_2 and left and left_up): #левый верхний
            return False
        elif (right_up and up and up_2) or (right_2 and right and right_up): #правый верхный
            return False
        elif ((left_2 and left and down_left) or (down_left and down and down_2)): #нижний левый
            return False
        elif ((down_right and down and down_2) or (down_right and right and right_2)): #нижный правый
            return False
        elif((left_up and left and down_left) or (left_up and up and right_up) or (right_up and right and down_right) or (down_right and down and down_left)): #ровные стороны
            return False
        elif((left and left_up and up) or (right and right_up and up) or (left and down_left and down) or (right and down_right and down)): #внутренние углы
            return False

        return True

    def is_border_cell_at(self, pos):
        for i, (x, y, sprite, value) in enumerate(self.position_map_cell):
            if sprite.get_rect(topleft=(x, y)).collidepoint(pos):
                if sprite == self.void_map_end or sprite == self.left_map_end or sprite == self.up_map_end or sprite == self.right_map_end or sprite == self.down_map_end or value is not None:
                    return True
        return False

    def is_border_cell(self, event):
        return self.is_border_cell_at(event.pos)

    def check_bridge(self, x, y):
        offsets = [(-65, -65), (65, -65), (-65, 65), (65, 65), (0, -65), (-65, 0), (65, 0), (0, 65)]

        for dx, dy in offsets:
            nx, ny = x + dx, y + dy
            for i, (px, py, _, _) in enumerate(self.position_map_cell):
                if (nx, ny) == (px, py) and self.position_map_cell_customization[i][0] is not None:
                    if self.position_map_cell_customization[i][1] == 1:
                        return False
                    match (dx, dy):
                        case (-65, -65):
                            return False
                        case (65, -65):
                            return False
                        case (-65, 65):
                            return False
                        case (65, 65):
                            return False
                    break
        return True

    def passing_check(self):
        self.reset_trace()
        final_res, trace_steps = self.run_evaluation_trace()
        if len(trace_steps) > 1:
            self.trace_active = True
            self.trace_steps = trace_steps
            self.evaluation_result = final_res

            # Pre-populate cell_values with matching values from previous run
            future_values = {}
            for step in trace_steps:
                if step["type"] == "recurse_up":
                    future_values[(step["x"], step["y"])] = step["val"]

            for pos, val in future_values.items():
                if self.previous_cell_values.get(pos) == val:
                    self.cell_values[pos] = val

    def run_evaluation_trace(self):
        start_x, start_y = self.start_x, self.start_y
        cell_width, cell_height = self.cell_width, self.cell_height

        output_data = self.level_data.output
        output_x, output_y = output_data['x'], output_data['y']
        target_value = output_data['target_value']

        real_output_x = start_x + output_x * cell_width
        real_output_y = start_y + output_y * cell_height

        offsets = [(-65, 0), (65, 0), (0, -65), (0, 65)]

        def get_index(x, y):
            for i, (px, py, _, _) in enumerate(self.position_map_cell):
                if px == x and py == y:
                    return i
            return None

        trace = []
        visited = set()

        def trace_path(x, y, visited_set):
            if (x, y) in visited_set:
                return None
            visited_set.add((x, y))

            # Record search going down
            trace.append({"type": "recurse_down", "x": x, "y": y})

            for dx, dy in offsets:
                nx, ny = x + dx, y + dy
                i = get_index(nx, ny)
                if i is not None and self.position_map_cell_customization[i][0] is not None and (nx, ny) not in visited_set:
                    custom_type = self.position_map_cell_customization[i][1]
                    if custom_type is not None:
                        if isinstance(custom_type, int) and custom_type > 1:
                            # Combinator
                            combinator_type = self.level_data.combinators[custom_type - 2]['type']
                            visited_set.add((nx, ny))
                            trace.append({"type": "recurse_down", "x": nx, "y": ny})
                            
                            values = []
                            for j, (ddx, ddy) in enumerate(offsets):
                                nnx, nny = nx + ddx, ny + ddy
                                idx = get_index(nnx, nny)
                                if (nnx, nny) != (x, y) and (nnx, nny) not in visited_set and len(values) < 2 and idx is not None and self.position_map_cell_customization[idx][0] is not None:
                                    val = trace_path(nnx, nny, visited_set.copy())
                                    if val is not None:
                                        values.append((val, self.type_map_texture[idx], nnx, nny))

                            # Evaluate combinator
                            res = None
                            if combinator_type == 'plus' and len(values) == 2:
                                res = values[0][0] + values[1][0]
                            elif combinator_type == 'minus' and len(values) == 2:
                                first = second = None
                                for val, typ, _, _ in values:
                                    if typ == 1: first = val
                                    else: second = val
                                if first is not None and second is not None:
                                    res = first - second
                            elif combinator_type == 'multiply' and len(values) == 2:
                                res = values[0][0] * values[1][0]
                            elif combinator_type == 'divide' and len(values) == 2:
                                first = second = None
                                for val, typ, _, _ in values:
                                    if typ == 1: first = val
                                    else: second = val
                                if first is not None and second is not None and second != 0:
                                    res = first / second
                            elif combinator_type == 'degree' and len(values) == 1:
                                res = values[0][0] ** 2
                            elif combinator_type == 'root' and len(values) == 1:
                                if values[0][0] >= 0:
                                    res = values[0][0] ** 0.5
                            elif combinator_type == 'degree_3' and len(values) == 1:
                                res = values[0][0] ** 3
                            elif combinator_type == 'root_3' and len(values) == 1:
                                res = math.cbrt(values[0][0])

                            if res is not None:
                                if isinstance(res, float) and res.is_integer():
                                    res = int(res)
                                elif isinstance(res, float):
                                    res = round(res, 2)
                                
                                trace.append({"type": "calculate", "x": nx, "y": ny, "op": combinator_type, "res": res})
                                trace.append({"type": "recurse_up", "x": nx, "y": ny, "val": res})
                                return res
                            else:
                                trace.append({"type": "fail", "x": nx, "y": ny})
                                return None

                        elif custom_type == 1:
                            # Bridge
                            bx, by = nx + dx, ny + dy
                            trace.append({"type": "recurse_down", "x": nx, "y": ny})
                            val = trace_path(bx, by, visited_set)
                            if val is not None:
                                trace.append({"type": "recurse_up", "x": nx, "y": ny, "val": val})
                                return val

                        else:
                            # Connection
                            val = trace_path(nx, ny, visited_set)
                            if val is not None:
                                trace.append({"type": "recurse_up", "x": nx, "y": ny, "val": val})
                                return val

            # Check if input cell
            for input_data in self.level_data.inputs:
                ix = input_data['x'] * cell_width + start_x
                iy = input_data['y'] * cell_height + start_y
                if (x, y) == (ix, iy):
                    val = input_data['value']
                    trace.append({"type": "recurse_up", "x": x, "y": y, "val": val})
                    return val

            trace.append({"type": "fail", "x": x, "y": y})
            return None

        final_res = trace_path(real_output_x, real_output_y, visited)
        return final_res, trace

    def reset_trace(self):
        if self.cell_values:
            self.previous_cell_values = self.cell_values.copy()
        self.trace_active = False
        self.trace_steps = []
        self.trace_index = 0
        self.trace_timer = 0
        self.active_search_cells.clear()
        self.cell_values.clear()
        self.fail_cells.clear()
        self.evaluation_result = None
        self.eval_finished = False

    def update_animations(self):
        self.anim_frame_count += 1
        if not self.trace_active:
            return
        self.trace_timer += 1
        if self.trace_timer >= self.trace_step_delay:
            self.trace_timer = 0
            self.advance_trace_step()

    def apply_trace_step(self, step):
        stype = step["type"]
        pos = (step["x"], step["y"])

        if stype == "recurse_down":
            self.active_search_cells.add(pos)
            self.fail_cells.discard(pos)
        elif stype == "recurse_up":
            self.active_search_cells.discard(pos)
            self.cell_values[pos] = step["val"]
        elif stype == "fail":
            self.active_search_cells.discard(pos)
            self.fail_cells.add(pos)

    def advance_trace_step(self):
        if self.trace_index >= len(self.trace_steps):
            self.eval_finished = True
            if self.evaluation_result is not None:
                output_data = self.level_data.output
                if self.evaluation_result == output_data['target_value']:
                    self.level_passed = True
            return

        # Skip matching steps instantly to only animate changes
        while self.trace_index < len(self.trace_steps):
            step = self.trace_steps[self.trace_index]
            pos = (step["x"], step["y"])

            if pos in self.cell_values:
                self.apply_trace_step(step)
                self.trace_index += 1
            else:
                self.apply_trace_step(step)
                self.trace_index += 1
                break

        if self.trace_index >= len(self.trace_steps):
            self.eval_finished = True
            if self.evaluation_result is not None:
                output_data = self.level_data.output
                if self.evaluation_result == output_data['target_value']:
                    self.level_passed = True

    def draw_animations_overlay(self):
        cell_width = self.cell_width
        cell_height = self.cell_height

        # Orbiting electrons around active current-carrying cells
        for (x, y), val in self.cell_values.items():
            target_idx = None
            for idx, (px, py, _, _) in enumerate(self.position_map_cell):
                if px == x and py == y:
                    target_idx = idx
                    break
            
            if target_idx is not None and self.position_map_cell_customization[target_idx][1] == 0:
                t = (self.anim_frame_count * 0.05) % 1.0
                for offset in [0.0, 0.5]:
                    angle = (self.anim_frame_count * 0.08 + offset * math.pi * 2)
                    dot_x = x + cell_width // 2 + int(10 * math.cos(angle))
                    dot_y = y + cell_height // 2 + int(10 * math.sin(angle))
                    pygame.draw.circle(self.screen, (34, 222, 128), (dot_x, dot_y), 3)

        # Draw previous (ghost) values in grey
        for (x, y), val in self.previous_cell_values.items():
            if (x, y) not in self.cell_values:
                surf = pygame.Surface((cell_width, cell_height), pygame.SRCALPHA)
                pygame.draw.rect(surf, (100, 116, 139, 140), (0, 0, cell_width, cell_height), width=2, border_radius=4)
                self.screen.blit(surf, (x, y))

                val_str = str(val)
                text = self.font_value.render(val_str, True, (148, 163, 184))
                text_pos = text.get_rect(center=(x + cell_width // 2, y - 10))
                
                bg_rect = text_pos.inflate(6, 4)
                bg_surf = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
                bg_surf.fill((15, 23, 42, 180))
                self.screen.blit(bg_surf, bg_rect.topleft)
                self.screen.blit(text, text_pos)

        # Draw search glow (recurse_down)
        for (x, y) in self.active_search_cells:
            pulse = int(128 + 127 * math.sin(self.anim_frame_count * 0.15))
            surf = pygame.Surface((cell_width, cell_height), pygame.SRCALPHA)
            pygame.draw.rect(surf, (234, 179, 8, pulse), (0, 0, cell_width, cell_height), width=3, border_radius=4)
            self.screen.blit(surf, (x, y))

        # Draw failure highlight
        pulse = int(140 + 70 * math.sin(self.anim_frame_count * 0.08))
        for (x, y) in self.fail_cells:
            surf = pygame.Surface((cell_width, cell_height), pygame.SRCALPHA)
            pygame.draw.rect(surf, (239, 68, 68, pulse), (0, 0, cell_width, cell_height), width=3, border_radius=4)
            self.screen.blit(surf, (x, y))

        # Draw computed values (recurse_up)
        for (x, y), val in self.cell_values.items():
            surf = pygame.Surface((cell_width, cell_height), pygame.SRCALPHA)
            pygame.draw.rect(surf, (34, 197, 94, 180), (0, 0, cell_width, cell_height), width=2, border_radius=4)
            self.screen.blit(surf, (x, y))

            val_str = str(val)
            text = self.font_value.render(val_str, True, (34, 197, 94))
            text_pos = text.get_rect(center=(x + cell_width // 2, y - 10 + int(2 * math.sin(self.anim_frame_count * 0.1))))
            
            bg_rect = text_pos.inflate(6, 4)
            bg_surf = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
            bg_surf.fill((15, 23, 42, 220))
            self.screen.blit(bg_surf, bg_rect.topleft)
            self.screen.blit(text, text_pos)

        # Status text popup positioned below the left inventory panels
        if self.eval_finished and self.evaluation_result is not None:
            if len(self.position_frame) > 1:
                left_frame_pos = self.position_frame[1][1]
                status_x = left_frame_pos.centerx
                status_y = left_frame_pos.bottom + 45
            else:
                status_x = self.screen_width // 4
                status_y = self.screen_height // 1.25

            output_data = self.level_data.output
            if self.evaluation_result == output_data['target_value']:
                color = (34, 197, 94)  # Green
                line1_str = "SUCCESS!"
                line2_str = f"Calculated: {self.evaluation_result} == Target: {output_data['target_value']}"
            else:
                color = (239, 68, 68)  # Red
                line1_str = "WRONG VALUE!"
                line2_str = f"Calculated: {self.evaluation_result} != Target: {output_data['target_value']}"

            # Render text lines with size-appropriate font
            text1 = self.font_status.render(line1_str, True, color)
            text2 = self.font_status.render(line2_str, True, color)
            
            t1_rect = text1.get_rect()
            t2_rect = text2.get_rect()
            
            w = max(t1_rect.width, t2_rect.width)
            h = t1_rect.height + t2_rect.height + 6
            
            bg_rect = pygame.Rect(0, 0, w + 20, h + 16)
            bg_rect.centerx = status_x
            bg_rect.top = status_y

            # Constrain to left side and screen limits
            if bg_rect.left < 20:
                bg_rect.left = 20
            if bg_rect.right > self.start_x - 15:
                bg_rect.right = self.start_x - 15
                bg_rect.left = bg_rect.right - (w + 20)
                if bg_rect.left < 20:
                    bg_rect.left = 20

            bg_surf = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
            bg_surf.fill((15, 23, 42, 240))
            pygame.draw.rect(bg_surf, color, (0, 0, bg_rect.width, bg_rect.height), width=2, border_radius=6)
            self.screen.blit(bg_surf, bg_rect.topleft)
            
            t1_x = bg_rect.left + (bg_rect.width - t1_rect.width) // 2
            t1_y = bg_rect.top + 8
            t2_x = bg_rect.left + (bg_rect.width - t2_rect.width) // 2
            t2_y = t1_y + t1_rect.height + 6
            
            self.screen.blit(text1, (t1_x, t1_y))
            self.screen.blit(text2, (t2_x, t2_y))