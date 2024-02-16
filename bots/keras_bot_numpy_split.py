from back.core import BotKeys, GameState, GameState, Sphere, PlayerSphere
from back.game import Game
from bots.do_nothing_bot import DoNothingBot
from . import Bot
from bots_helpers import create_colors

from typing import Optional
import dataclasses

import numpy as np
import pygad

import pygame

def from_sphere_list_to_vector(sphere_list: list[Sphere], amount_needed=None):
    if len(sphere_list) > 0:
        sphere_list = sphere_list[:amount_needed]
        spheres_unpacked = [[s.center.x, s.center.y] for s in sphere_list]
        a = np.hstack(spheres_unpacked)
    else:
        a = np.array([])
    if amount_needed is None:
        return a
    need_to_fill = amount_needed - len(sphere_list)
    a = np.hstack((a, np.zeros(2*need_to_fill)))
    return a

def player_to_vector(player: PlayerSphere, bot=None, verbose=False):
    if player.alive:
        values = [[ player is bot,
                    player.alive,
                    player.center.x,
                    player.center.y,
                    player.velocity.x,
                    player.velocity.y,
                    player.is_dodging(),
                    player.is_dodge_cooldown(),
                    player.can_dodge(),
                    player.rotating_around is not None],
                    [player.rotating_around.center.x,
                    player.rotating_around.center.y]
                    if player.rotating_around is not None
                    else [0, 0],
                    from_sphere_list_to_vector(player.trail, 20),
                    from_sphere_list_to_vector(player.attacking_spheres, 5),
                    ]
        if verbose:
            print('player lengths:')
            for i in values:
                print(len(i))
        return np.hstack(values)
    else:
        # print('player is dead, shape is', PLAYER_VECTOR_SHAPE)
        return np.zeros(PLAYER_VECTOR_SHAPE) # calculated by a function below

def calc_player_vector_shape():
    sh = player_to_vector(PlayerSphere(
        pygame.Vector2(0, 0),
        pygame.Vector2(1, 0),
        10,
        (255, 255, 255)
    )).shape
    print(f'player shape is {sh}')
    return sh
PLAYER_VECTOR_SHAPE = calc_player_vector_shape()

def state_to_vector(state: GameState, bot=None, verbose=False):
    players = [
        *map(lambda x: player_to_vector(x, bot, verbose), state.player_spheres),
    ]
    for _ in range(12 - len(state.player_spheres)):
        players.append(np.zeros(PLAYER_VECTOR_SHAPE))
    rest = [
        from_sphere_list_to_vector(state.active_spheres, 10),
        from_sphere_list_to_vector(state.inactive_spheres, 10),
        from_sphere_list_to_vector(state.bursts, 3),
        [state.timer],
    ]
    if verbose:
        print('state lengths:')
        for i in players+rest:
            print(len(i))
    rest = np.hstack(rest)
    # print(*(player.shape for player in players))
    d = [np.array(p) for p in players]
    d.append(rest)
    return d

def calc_state_vector_shape():
    shapes_per_bot_amount = []
    for bots_amount in  range(1, 13):
        bots = [DoNothingBot] * bots_amount
        g = Game(create_colors([DoNothingBot, DoNothingBot], BotKeys))
        for i in range(190):
            g.update(1/60)
        verbose = False # bots_amount==12
        sh = state_to_vector(g.get_state(), verbose=verbose)[-1].shape
        shapes_per_bot_amount.append(sh)
    for sh in shapes_per_bot_amount:
        assert sh == shapes_per_bot_amount[0]
    state_shape = (sh[-1],)
    print(f'state shape is {state_shape}')
    return state_shape
STATE_VECTOR_SHAPE = calc_state_vector_shape()

class Model:
    def __init__(self, weights: Optional[np.ndarray] = None):
        self.d_out = 10
        if weights is None:
            self.dense1 = np.random.random((PLAYER_VECTOR_SHAPE[0]+1, self.d_out)) * 2 - 1
            self.dense2 = np.random.random((STATE_VECTOR_SHAPE[0]+1, self.d_out)) * 2 - 1
            self.dense3 = np.random.random((self.d_out*13+1, 1)) * 2 - 1
        else:
            part1 = (PLAYER_VECTOR_SHAPE[0]+1)*self.d_out
            part2 = (PLAYER_VECTOR_SHAPE[0]+1)*self.d_out + (STATE_VECTOR_SHAPE[0]+1) * self.d_out
            self.dense1 = weights[:part1].reshape(-1, self.d_out)
            self.dense2 = weights[part1:part2].reshape(-1, self.d_out)
            self.dense3 = weights[part2:].reshape(-1, 1)

    def get_weights(self):
        return np.hstack([self.dense1.reshape(-1),
                          self.dense2.reshape(-1),
                          self.dense3.reshape(-1)])

    def __call__(self, x):
        inter = []
        for i in x[:-1]:
            i = np.hstack((i, [1]))
            i = i @ self.dense1
            i = i * (i > 0) # ReLU
            inter.append(i)
        x13 = np.hstack((x[-1], [1]))
        x13 = x13 @ self.dense2
        x13 = x13 * (x13 > 0) # ReLU
        inter.append(x13)
        inter.append([1])
        x = np.hstack(inter)
        x = x @ self.dense3
        x = np.tanh(x)
        return x

class KerasBot:
    def __init__(self, model: Optional[Model]=None):
        if model is None:
            model = Model()
        self.model = model
        self.__name__ = f'NumpyBotSplit'

    def __call__(self, center, velocity, radius, color):
        return KerasBotThing(self.model, center, velocity, radius, color)

    @staticmethod
    def from_ga_file(filename):
        generations = 1000
        filename = f'genetic_algorithm_results_{generations}'
        ga_instance: pygad.GA = pygad.load(filename)
        solution, fitness, idx = ga_instance.best_solution(ga_instance.last_generation_fitness)
        model = Model(solution)
        bot = KerasBot(model)
        KerasBot.__name__ += str(generations)
        return bot


class KerasBotThing(Bot):
    def __init__(self, model, center, velocity, radius, color):
        super().__init__(center, velocity, radius, color)
        self.model = model

    def get_action(self, state: GameState, time_delta: float) -> bool:
        if not self.alive: return False
        vector = state_to_vector(state, self)
        return self.model(vector) > 0.7

