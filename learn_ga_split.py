from back import BotKeys, Game, PlayerSphere, GameStage
from battle_the_bots import create_colors, play_a_console_game
from bots import SmartBot
from bots import DoNothingBot
from bots.keras_split_bot import state_to_vector, KerasBot, create_keras_model, player_to_vector

import time

import pygad
import pygad.kerasga
from pygad.kerasga import model_weights_as_matrix
import tensorflow.keras
import numpy as np
from tqdm import tqdm

import pygame


def create_model_from_solution(models, solution):
    global model_sizes
    _models = []
    size_from = 0
    size_to = model_sizes[0]
    for i, (model, size) in enumerate(zip(models, model_sizes[1:]+[None])):
        solution_weights = model_weights_as_matrix(model=model,
                                                   weights_vector=solution[size_from:size_to])
        size_from = size_to
        if size is not None:
            size_to += size
        else:
            size_to = None
        _model = tensorflow.keras.models.clone_model(model)
        _model.set_weights(solution_weights)
        _models.append(_model)
    return _models

def fitness_func(ga_instance: pygad.GA, solutions, sol_idxs):
    global model_sizes, models

    bots = [KerasBot(*create_model_from_solution(models, solution)) for solution in solutions]
    colors = create_colors(bots, BotKeys)
    scores = play_a_console_game(ga_instance.generations_completed, ga_instance.generations_completed, colors, GameStage.SHOWING_RESULTS)
    return scores

def main():
    global model_sizes, models
    models = create_keras_model()
    keras_gas = [pygad.kerasga.KerasGA(m, 12) for m in models if m is not None]
    model_sizes = [len(kga.population_weights[0]) for kga in keras_gas]
    initial_population = np.hstack([kga.population_weights for kga in keras_gas])

    num_generations = 1
    ga = pygad.GA(num_generations=num_generations,
                  num_parents_mating=4,
                  fitness_func=fitness_func,
                  fitness_batch_size=12,
                  initial_population=initial_population,
                #   on_generation=on_generation,
                  keep_parents=0,
                  keep_elitism=0,
                  )


    ga.run()
    ga.save(f'genetic_algorithm_results_{num_generations}')



if __name__ == '__main__':
    main()
