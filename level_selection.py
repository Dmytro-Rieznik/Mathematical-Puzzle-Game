import pygame

class LevelSelection:
    def __init__(self, screen, screen_width, screen_height):
        self.screen = screen
        self.screen_width = screen_width
        self.screen_height = screen_height

        self.font = pygame.font.Font(None, 46)
        self.font_lvl = pygame.font.Font(None, 100)

        self.back = 'Back'
        self.back_position = ()  # переменная для хранения прямоугольника опции
        self.options_position = []  # Список для хранения прямоугольников опций

        self.background = pygame.image.load('images/background.png')
        self.lvl_frame = pygame.image.load('images/frame.png')


    def draw(self, completed_levels):
        self.screen.blit(self.background, (0, 0))

        self.back_position = (0, 0)   # Очистка переменной прямоугольника перед отрисовкой
        self.options_position = []  # Очистка списка прямоугольников перед отрисовкой

        mouse_pos = pygame.mouse.get_pos()  # Получение позиции курсора мыши

        color = (255, 255, 255)  # Белый цвет по умолчанию
        text = self.font.render(self.back, True, (color))  # Белый цвет по умолчанию
        text_pos = self.screen.blit(text, (self.screen_width // 2 - text.get_width() // 2, (self.screen_height // 1.15 - text.get_height())))

        if text_pos.collidepoint(mouse_pos):
            color = (255, 0, 0)  # Изменение цвета на красный, если курсор наведен

        text = self.font.render(self.back, True, color)
        self.screen.blit(text, text_pos)
        self.back_position = text_pos

        frame_width, frame_height = self.lvl_frame.get_size()
        margin = 20 # отступ
        rows, cols = 5, 10  # Определите количество строк и столбцов
        start_x = (self.screen_width - (cols * frame_width + (cols - 1) * margin)) // 2
        start_y = ((self.screen_height - (rows * frame_height + (rows - 1) * margin)) // 2) - 30

        level = 1
        for row in range(rows):
            for col in range(cols):
                if level > completed_levels:
                    break
                x = start_x + col * (frame_width + margin)
                y = start_y + row * (frame_height + margin)
                frame_pos = self.lvl_frame.get_rect(topleft=(x, y))
                self.screen.blit(self.lvl_frame, frame_pos)
                self.options_position.append(frame_pos)

                # Определение номера уровня
                level_number = row * cols + col + 1

                # Изменение цвета текста при наведении
                color = (255, 255, 255)
                if frame_pos.collidepoint(mouse_pos):
                    color = (255, 0, 0)

                # Отрисовка номера уровня
                level_number = self.font_lvl.render(str(level_number), True, color)
                text_position = level_number.get_rect(center=frame_pos.center)
                self.screen.blit(level_number, text_position)

                level += 1
            if level > completed_levels:
                break

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return 'menu'
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos
            if self.back_position.collidepoint(mouse_pos):
                return 'menu'
            for i, frame_pos in enumerate(self.options_position):
                if frame_pos.collidepoint(mouse_pos):
                    return i
        return 'level_selection'
