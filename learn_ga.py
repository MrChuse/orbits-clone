from back import BotKeys, Game, PlayerSphere, GameStage
from battle_the_bots import create_colors, play_a_console_game
from bots import SmartBot
from bots import DoNothingBot
from bots.keras_bot import state_to_vector, KerasBot, create_default_keras_model, player_to_vector

import time

import pygad
import pygad.kerasga
from pygad.kerasga import model_weights_as_matrix
import tensorflow.keras
from tqdm import tqdm

import pygame


def create_model_from_solution(model, solution):
    # Fetch the parameters of the best solution.
    solution_weights = model_weights_as_matrix(model=model,
                                               weights_vector=solution)
    _model = tensorflow.keras.models.clone_model(model)
    _model.set_weights(solution_weights)
    return _model

def fitness_func(ga_instance: pygad.GA, solutions, sol_idxs):
    global keras_ga, model

    bots = [KerasBot(create_model_from_solution(model, solution)) for solution in solutions]
    colors = create_colors(bots, BotKeys)
    scores = play_a_console_game(ga_instance.generations_completed, ga_instance.generations_completed, colors, GameStage.SHOWING_RESULTS)
    return scores

# def on_generation(ga_instance: pygad.GA):
    # print(f"Generation = {ga_instance.generations_completed}")
    # print(f"Fitness    = {ga_instance.best_solution()[1]}")

def main():
    global keras_ga, model
    model = create_default_keras_model()
    keras_ga = pygad.kerasga.KerasGA(model, 12)

    num_generations = 250
    ga = pygad.GA(num_generations=num_generations,
                  num_parents_mating=4,
                  fitness_func=fitness_func,
                  fitness_batch_size=12,
                  initial_population=keras_ga.population_weights,
                #   on_generation=on_generation,
                  keep_parents=0,
                  keep_elitism=0,
                  )


    ga.run()
    ga.save(f'genetic_algorithm_results_{num_generations}')



if __name__ == '__main__':
    main()
