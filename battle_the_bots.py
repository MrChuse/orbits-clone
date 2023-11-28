from collections import Counter
import time

import pygame
pygame.init()

from back import Game, BotKeys, Team, GameStage
from bots import SmartBot, DoNothingBot

# GAMES = 100 # now using seeds : TODO maybe use seeded seed generation to get same seeds each run instead of having that seed list
PLAYERS = [SmartBot, SmartBot, DoNothingBot, DoNothingBot] # not more than 12


assert len(PLAYERS) <= 12

colors = {
    key: (team, class_.__name__ + f' {counter}', class_) for key, team, (counter, class_) in zip(BotKeys, Team, enumerate(PLAYERS))
}
# print(colors)
def play_a_console_game(number, seed):
    sstart_time = time.time()
    start_time = time.time()
    game = Game(colors, seed)
    while game.stage != GameStage.END_SCREEN:
        t = time.time()
        current_time = t - start_time
        overall_time = t - sstart_time
        time_delta = 1 / 60 # seconds
        game.update(time_delta)
        if current_time > 1:
            # print(' '*50, '\r', end='')
            s = f'Game {number}: seed {game.seed} | {game.stage.name} {game.scores} {overall_time:.1f}'
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
    seeds = [787251266, 968271055, 109343014, 581667902, 854334122, 611688196, 601120768, 484691195, 857432951, 508818228, 202498239, 168362712, 153090000, 891572378, 629210471, 246177171, 442757202, 436592637, 468111692, 302367863, 992324453, 855935731, 984202434, 591644537, 503974825, 785524348, 88878125, 144351835, 599968379, 181569796, 228103852, 791174225, 605257316, 815810279, 721292242, 504329190, 555155765, 558730856, 228398930, 298848590, 237944805, 935390629, 439442625, 908527079, 485428665, 804105406, 700461605, 608538327, 561535972, 733285131, 37539035, 193262144, 94048620, 900415354, 619468819, 60036589, 827460053, 333197116, 452424559, 707985269, 817029849, 729948939, 31495869, 778892060, 728021479, 524084484, 92534795, 21483267, 216996293, 939874795, 169546128, 1236526, 741089702, 92600992, 286051289, 72434738, 57370079, 857079062, 880213289, 958549841, 199465350, 171340932, 351400607, 372941186, 266192059, 764242959, 314184390, 215945602, 556759145, 928468740, 664582682, 759908453, 563974013, 394553980, 542083439, 979431316, 540203510, 438744192, 88979073, 180301569]
    # surface = set_up_gui_games()
    start_time = time.time()
    wins = []
    for game_number, seed in enumerate(seeds):
        # scores = play_a_gui_game(surface)
        scores = play_a_console_game(game_number, seed)
        best = max(enumerate(scores), key=lambda x: x[1])
        best_player = PLAYERS[best[0]].__name__ + f' {best[0]}'
        score = best[1]
        wins.append(best_player)
        print(f'Game {game_number}: winner is {best_player} with score {score}. {time.time() - start_time} seconds from start')
    print(Counter(wins))
    print(time.time() - start_time, 'seconds passed.')

if __name__ == '__main__':
    main()