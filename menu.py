import pygame

class MainMenu:
    def __init__(self, screen, screen_width, screen_height):
        self.screen = screen
        self.screen_width = screen_width
        self.screen_height = screen_height

        self.font = pygame.font.Font(None, 46)

        self.options = ['Start', 'Exit']
        self.option_position = [] # Список для хранения прямоугольников опций

        self.background = pygame.image.load('images/background.png')

    def draw(self):
        self.screen.blit(self.background,(0, 0))

        self.option_position = [] # Очистка списка прямоугольников перед отрисовкой
        mouse_pos = pygame.mouse.get_pos() # Получение позиции курсора мыши

        for i, option in enumerate(self.options):
            color = (255, 255, 255)  # Белый цвет по умолчанию
            text = self.font.render(option, True, (color)) # Белый цвет по умолчанию
            text_pos = self.screen.blit(text, (self.screen_width // 2 - text.get_width() // 2, (self.screen_height // 2 - text.get_height() * 2 + i * 80)))

            if text_pos.collidepoint(mouse_pos):
                color = (255, 0, 0)  # Изменение цвета на красный, если курсор наведен

            text = self.font.render(option, True, color)
            self.screen.blit(text, text_pos)
            self.option_position.append(text_pos)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return 'exit'
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos
            for i, rect in enumerate(self.option_position):
                if rect.collidepoint(mouse_pos):
                    if self.options[i] == 'Start':
                        return 'level_selection'
                    elif self.options[i] == 'Exit':
                        return 'exit'
        return 'menu'