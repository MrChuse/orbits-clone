from collections import Counter
import time
from copy import deepcopy

import pygame
pygame.init()

from back import Game, BotKeys, Team, GameStage
from front import draw_game
from screens import GameScreen
from bots import SmartBot, DoNothingBot

GAMES = 100
PLAYERS = [SmartBot, SmartBot, DoNothingBot, DoNothingBot] # not more than 12


assert len(PLAYERS) <= 12

colors = {
    key: (team, class_.__name__ + f' {counter}', class_) for key, team, (counter, class_) in zip(BotKeys, Team, enumerate(PLAYERS))
}
# print(colors)
def play_a_console_game(number):
    sstart_time = time.time()
    start_time = time.time()
    game = Game(colors)
    print(f'Game {number}: seed {game.seed}')
    while game.stage != GameStage.END_SCREEN:
        t = time.time()
        current_time = t - start_time
        overall_time = t - sstart_time
        time_delta = 1 / 60 # seconds
        game.update(time_delta)
        if current_time > 1:
        #     # print(' '*50, '\r', end='')
            s = f'{game.stage.name} {game.scores} {overall_time:.1f}'
            print(f'{s:<50}\r', end='')
            start_time = time.time()
    return game.scores

def set_up_gui_games():
    surface = pygame.display.set_mode((600, 300))
    return surface
# def play_a_gui_game(surface):
#     gs = GameScreen(surface, colors)
#     gs.main()

def main():
    # surface = set_up_gui_games()
    wins = []
    for game_number in range(GAMES):
        # scores = play_a_gui_game(surface)
        res = play_a_console_game(game_number)
        if res[0]:
            scores = res[1]
            best = max(enumerate(scores), key=lambda x: x[1])
            best_player = PLAYERS[best[0]].__name__ + f' {best[0]}'
            score = best[1]
            wins.append(best_player)
            print(f'Game {game_number}: winner is {best_player} with score {score}')
        else:
            break
    print(Counter(wins))

if __name__ == '__main__':
    main()