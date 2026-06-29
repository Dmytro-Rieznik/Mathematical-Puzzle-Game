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

    def draw(self):
        self.draw_button_back()
        self.draw_map()
        self.draw_frames()

    def handle_event(self, event):
        if self.level_passed:
            return self.level_data.level_id + 2
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return 'level_selection'
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos
            if self.back_position.collidepoint(mouse_pos):
                return 'level_selection'
            self.handle_frame(mouse_pos)  # Обработка нажатия на рамки
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.handle_map(event)
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

            start_x = (self.screen_width - cols * self.cell_width) // 2
            start_y = (self.screen_height - rows * self.cell_height) // 2.5

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
                self.screen.blit(pygame.transform.scale(self.frame_active, (pos.width, pos.height)), pos.topleft)
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

    def handle_map(self, event):
        if self.is_border_cell(event):
            return
        if event.button == 1:  # Левая кнопка мыши
            selected_combinator_index = self.get_selected_combinator_index()
            if selected_combinator_index is not None:
                for i, (x, y, sprite, _) in enumerate(self.position_map_cell):
                    if sprite.get_rect(topleft=(x, y)).collidepoint(event.pos):
                        if self.position_map_cell_customization[i][0] is None:  # Проверка, свободна ли ячейка
                            if self.combinators_quantity[selected_combinator_index] is None: #Разместить конектор
                                if self.check_neighbors(x, y):
                                    self.position_map_cell_customization[i] = (self.combinators_sprite_map[selected_combinator_index], selected_combinator_index)
                            elif self.combinators_quantity[selected_combinator_index] > 0: #Разместить комбинатор
                                if selected_combinator_index == 1: #если выбран мост
                                    if self.check_bridge(x, y):
                                        self.position_map_cell_customization[i] = (self.combinators_sprite_map[selected_combinator_index],selected_combinator_index)
                                        self.combinators_quantity[selected_combinator_index] -= 1
                                else: #если выбран комбинатор
                                    self.position_map_cell_customization[i] = (self.combinators_sprite_map[selected_combinator_index], selected_combinator_index)
                                    self.combinators_quantity[selected_combinator_index] -= 1
                            break
                        elif selected_combinator_index == 0: #если выбран коннектор
                            if self.position_map_cell_customization[i][1] == 0: #если стоит конектор, меняем
                                match self.type_map_texture[i]:
                                    case 0:
                                        self.type_map_texture[i] = 1
                                    case 1:
                                        self.type_map_texture[i] = 0
                            break
                        elif selected_combinator_index == 1 and self.position_map_cell_customization[i][1] == 0: #если выбран мост и стоит коннектор
                            if self.check_bridge(x, y):
                                if self.combinators_quantity[selected_combinator_index] > 0:
                                    self.position_map_cell_customization[i] = (self.combinators_sprite_map[selected_combinator_index], selected_combinator_index)
                                    self.combinators_quantity[selected_combinator_index] -= 1
                            break

        elif event.button == 3:  # Правая кнопка мыши
            for i, (x, y, sprite, _) in enumerate(self.position_map_cell):
                if sprite.get_rect(topleft=(x, y)).collidepoint(event.pos):
                    if self.position_map_cell_customization[i][0] is not None:  # Проверка, занята ли ячейка
                        if self.combinators_quantity[self.position_map_cell_customization[i][1]] is not None:
                            self.combinators_quantity[self.position_map_cell_customization[i][1]] += 1  # Возврат комбинатора на склад
                        self.position_map_cell_customization[i] = (None, None)  # Освобождение ячейки
                        self.type_map_texture[i] = 0
                    break

        for i, (x, y, sprite, _) in enumerate(self.position_map_cell): #обновление текстур
            if self.position_map_cell_customization[i][0] is not None:
                if self.position_map_cell_customization[i][1] == 0: #если коннектор
                    correct_combinator_index = self.position_map_cell_customization[i][1]
                    connector_texture = self.update_connector_textures(x, y, self.type_map_texture[i])
                    self.position_map_cell_customization[i] = (connector_texture, correct_combinator_index)

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

    def is_border_cell(self, event):
        for i, (x, y, sprite, value) in enumerate(self.position_map_cell):
            if sprite.get_rect(topleft=(x, y)).collidepoint(event.pos):
                if sprite == self.void_map_end or sprite == self.left_map_end or sprite == self.up_map_end or sprite == self.right_map_end or sprite == self.down_map_end or value is not None:
                    return True
        return False

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
        # Получаем начальные координаты карты и размеры ячеек
        start_x, start_y = self.position_map_cell[0][:2]
        cell_width, cell_height = self.cell_width, self.cell_height

        # Получаем координаты выходной точки
        output_data = self.level_data.output
        output_x, output_y = output_data['x'], output_data['y']
        target_value = output_data['target_value']

        # Рассчитываем реальные координаты выходной точки на карте
        real_output_x = start_x + output_x * cell_width
        real_output_y = start_y + output_y * cell_height

        # Проверка соседних ячеек
        offsets = [(-65, 0), (65, 0), (0, -65), (0, 65)]

        # Вспомогательная функция для получения индекса ячейки
        def get_index(x, y):
            for i, (px, py, _, _) in enumerate(self.position_map_cell):
                if px == x and py == y:
                    return i
            return None

        # Рекурсивная функция для поиска соединений
        def find_path(x, y, visited):
            # Проверка на выход за границы и повторное посещение
            if (x, y) in visited:
                return None
            visited.add((x, y))

            for dx, dy in offsets:
                nx, ny = x + dx, y + dy
                for i, (px, py, _, _) in enumerate(self.position_map_cell):
                    if (nx, ny) == (px, py) and self.position_map_cell_customization[i][0] is not None and (nx, ny) not in visited:
                        if self.position_map_cell_customization[i][1] is not None:
                            if isinstance(self.position_map_cell_customization[i][1], int) and self.position_map_cell_customization[i][1] > 1:
                                # Если нашли комбинатор
                                combinator_type = self.level_data.combinators[self.position_map_cell_customization[i][1] - 2]['type']

                                visited.add((nx, ny))
                                values = []

                                for j, (ddx, ddy) in enumerate(offsets):
                                    nnx, nny = nx + ddx, ny + ddy
                                    if (nnx, nny) != (x, y) and (nnx, nny) not in visited and len(values) < 2 and self.position_map_cell_customization[get_index(nnx, nny)][0] is not None:  # Не возвращаться назад и не посещать уже посещенные или пустые
                                        value = find_path(nnx, nny, visited.copy())

                                        if value is not None:
                                            values.append((value[0], self.type_map_texture[get_index(nnx, nny)]))

                                if combinator_type == 'plus' and len(values) == 2: # плюс
                                    result = values[0][0] + values[1][0]
                                    return [result]
                                elif combinator_type == 'minus' and len(values) == 2: # минус
                                    first = second = None
                                    for val, typ in values:
                                        if typ == 1:
                                            first = val
                                        else:
                                            second = val
                                    if first is not None and second is not None:
                                        result = first - second
                                        return [result]
                                elif combinator_type == 'multiply' and len(values) == 2: # умножить
                                    result = values[0][0] * values[1][0]
                                    return [result]
                                elif combinator_type == 'divide' and len(values) == 2: # делить
                                    # Определяем порядок операндов
                                    first = second = None
                                    for val, typ in values:
                                        if typ == 1:
                                            first = val
                                        else:
                                            second = val
                                    if first is not None and second is not None and second != 0:
                                        result = first / second
                                        return [result]
                                    else:
                                        return None
                                elif combinator_type == 'degree' and len(values) == 1: # степень квадрата
                                    # Возведение в квадрат
                                    base_value = values[0][0]
                                    result = base_value ** 2
                                    return [result]
                                elif combinator_type == 'root' and len(values) == 1: # корень квадратный
                                    # Определяем значение для вычисления корня
                                    val = values[0][0]
                                    result = val ** 0.5
                                    return [result]
                                elif combinator_type == 'degree_3' and len(values) == 1: # степень кубическая
                                    # Определяем значение для вычисления куба
                                    val = values[0][0]
                                    result = val ** 3
                                    return [result]
                                elif combinator_type == 'root_3' and len(values) == 1: # корень кубический
                                    # Определяем значение для вычисления кубического корня
                                    val = values[0][0]
                                    result = math.cbrt(val)
                                    return [result]

                            elif self.position_map_cell_customization[i][1] == 1:  # Проверка на наличие моста
                                # Определяем направление моста и перескакиваем через одну клетку
                                if (dx, dy) == (-65, 0) and (nx - 65, ny) not in visited:  # Мост слева
                                    return find_path(nx - 65, ny, visited)
                                elif (dx, dy) == (65, 0) and (nx + 65, ny) not in visited:  # Мост справа
                                    return find_path(nx + 65, ny, visited)
                                elif (dx, dy) == (0, -65) and (nx, ny - 65) not in visited:  # Мост сверху
                                    return find_path(nx, ny - 65, visited)
                                elif (dx, dy) == (0, 65) and (nx, ny + 65) not in visited:  # Мост снизу
                                    return find_path(nx, ny + 65, visited)

                            else:
                                # Если нашли соединение, рекурсивно продолжаем поиск
                                result = find_path(nx, ny, visited)
                                if result is not None:
                                    return result

            # Если достигли входной точки, возвращаем значение
            for input_data in self.level_data.inputs:
                if (x, y) == (input_data['x'] * self.cell_width + start_x, input_data['y'] * self.cell_height + start_y):
                    return [input_data['value']]
            return None

        # Начинаем поиск с выходной точки
        visited = set()
        result = find_path(real_output_x, real_output_y, visited)

        # Проверяем результат
        if result is not None and result[0] == target_value:
            self.level_passed = True