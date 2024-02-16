from back import BotKeys, GameStage # , Game, PlayerSphere
from bots_helpers import create_colors, play_a_console_game
# from bots import SmartBot
# from bots import DoNothingBot
# from bots.keras_bot_numpy import Model, KerasBot
from bots.keras_bot_numpy_split import Model, KerasBot

import time

import pygad
from tqdm import tqdm

import pygame

def fitness_func(ga_instance: pygad.GA, solutions, sol_idxs):
    bots = [KerasBot(Model(solution)) for solution in solutions]
    colors = create_colors(bots, BotKeys)
    scores = play_a_console_game(ga_instance.generations_completed, ga_instance.generations_completed, colors, GameStage.SHOWING_RESULTS)
    return scores

# def on_generation(ga_instance: pygad.GA):
    # print(f"Generation = {ga_instance.generations_completed}")
    # print(f"Fitness    = {ga_instance.best_solution()[1]}")

def main():
    initial_weights = [Model().get_weights() for i in range(12)]
    print('initial weights:', len(initial_weights[0]))
    # ga = pygad.load('genetic_algorithm_results_1000')
    # initial_weights = ga.population

    num_generations = 1000
    ga = pygad.GA(num_generations=num_generations,
                  num_parents_mating=4,
                  fitness_func=fitness_func,
                  fitness_batch_size=12,
                  initial_population=initial_weights,
                #   on_generation=on_generation,
                  parent_selection_type='rank',
                  keep_parents=0,
                  keep_elitism=0,
                  )


    ga.run()
    ga.save(f'genetic_algorithm_results_{num_generations}')



if __name__ == '__main__':
    main()
