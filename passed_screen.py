import pygame

class PassedScreen:
    def __init__(self, screen, screen_width, screen_height):
        self.screen = screen
        self.screen_width = screen_width
        self.screen_height = screen_height

        self.font = pygame.font.Font(None, 46)
        self.options = ['Next level', 'Back']
        self.option_position = []

        self.congratulations_font = pygame.font.Font(None, 72)
        self.message_font = pygame.font.Font(None, 56)

        self.background = pygame.image.load('images/background.png')

    def draw(self):
        self.screen.blit(self.background, (0, 0))

        # Відтворення тексту привітання
        congrats_text = "Congratulations!"
        congrats_rendered = self.congratulations_font.render(congrats_text, True, (255, 255, 255))
        congrats_rect = congrats_rendered.get_rect(center=(self.screen_width // 2, self.screen_height // 2.5 - 50))
        self.screen.blit(congrats_rendered, congrats_rect)

        message_text = "The level has been completed"
        message_rendered = self.message_font.render(message_text, True, (255, 255, 255))
        message_rect = message_rendered.get_rect(center=(self.screen_width // 2, self.screen_height // 2.5 + 20))
        self.screen.blit(message_rendered, message_rect)

        self.option_position = []  # Очищення списку прямокутників перед відтворенням
        mouse_pos = pygame.mouse.get_pos()  # Отримання позиції курсора миші

        for i, option in enumerate(self.options):
            color = (255, 255, 255)  # Білий колір за замовчуванням
            text = self.font.render(option, True, (color))  # Білий колір за замовчуванням
            text_pos = self.screen.blit(text, (self.screen_width // 2 - text.get_width() // 2, (self.screen_height // 1.7 - text.get_height() * 2 + i * 80)))

            if text_pos.collidepoint(mouse_pos):
                color = (255, 0, 0)  # Зміна кольору на червоний, якщо курсор наведений

            text = self.font.render(option, True, color)
            self.screen.blit(text, text_pos)
            self.option_position.append(text_pos)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos
            for i, rect in enumerate(self.option_position):
                if rect.collidepoint(mouse_pos):
                    if self.options[i] == 'Next level':
                        return 'game'
                    elif self.options[i] == 'Back':
                        return 'level_selection'
        return 'passed_screen'
