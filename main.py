import pygame
import sys
from menu import MainMenu
from level_selection import LevelSelection
from game_level import GameLevel
from completed_levels import CompletedLevels
from passed_screen import PassedScreen

def main():
    pygame.init()

    screen_width = 1920
    screen_height = 1080

    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption('GraduateWorkGame')

    main_menu = MainMenu(screen, screen_width, screen_height)
    level_selection = LevelSelection(screen, screen_width, screen_height)
    completed_levels = CompletedLevels()
    passed_screen = PassedScreen(screen, screen_width, screen_height)

    state = 'menu'
    last_level = None

    while True:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # Обработка событий в зависимости от текущего состояния
            match state:
                case 'menu':
                    state = main_menu.handle_event(event)
                case 'level_selection':
                    state = level_selection.handle_event(event)
                    if isinstance(state, int):
                        last_level = state
                        game_level = GameLevel(screen, screen_width, screen_height, state)  # передаём данные в конструктор game_level
                        state = 'game'
                case 'game':
                    state = game_level.handle_event(event)
                    if isinstance(state, int):
                        completed_levels.update_level(state)
                        state = 'passed_screen'
                case 'passed_screen':
                    state = passed_screen.handle_event(event)
                    if state == 'game':
                        last_level = last_level + 1
                        game_level = GameLevel(screen, screen_width, screen_height, last_level)

        # Отрисовка экранов в зависимости от текущего состояния
        match state:
            case 'menu':
                main_menu.draw()
            case 'level_selection':
                level_selection.draw(completed_levels.get_level())
            case 'game':
                game_level.draw()
            case 'passed_screen':
                passed_screen.draw()
            case 'exit':
                pygame.quit()
                sys.exit()

        # Обновление дисплея и ограничение частоты кадров
        pygame.display.flip()
        pygame.time.Clock().tick(60)

if __name__ == "__main__":
    main()