from back import Team, Game, GameStage
import time

def create_colors(players, keys):
    colors = {
        key: (team, class_.__name__ + f' {counter}', class_) for key, team, (counter, class_) in zip(keys, Team, enumerate(players))
    }
    return colors

def play_a_console_game(number, seed, colors, stopping_stage=GameStage.END_SCREEN):
    sstart_time = time.time()
    start_time = time.time()
    game = Game(colors, seed)
    while game.stage != stopping_stage:
        t = time.time()
        current_time = t - start_time
        overall_time = t - sstart_time
        time_delta = 1 / 60 # seconds
        game.update(time_delta)
        if current_time > 1:
            # logging.info(' '*50, '\r', end='')
            s = f'Game {number}: seed {game.seed} | {game.stage.name} {game.scores} {overall_time:.1f} {game.timer:.1f}'
            print(f'{s:<108}\r', end='')
            start_time = time.time()
        if game.stage == GameStage.GAMING and game.timer > 180:
            for index, player in enumerate(game.player_spheres):
                game.process_player_death(index, player, killer_index=0)
    return game.scores
