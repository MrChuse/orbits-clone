from back.core import BotKeys, GameState, GameState, Sphere, PlayerSphere#,  save_state
from back.game import Game
from bots.do_nothing_bot import DoNothingBot
from . import Bot
from battle_the_bots import create_colors

from typing import Optional
import dataclasses

import numpy as np
import keras

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
        # print('player is dead, shape is', player_to_vector.player_vector_shape)
        return np.zeros(player_to_vector.player_vector_shape) # calculated by a function below

def calc_player_vector_shape():
    sh = player_to_vector(PlayerSphere(
        pygame.Vector2(0, 0),
        pygame.Vector2(1, 0),
        10,
        (255, 255, 255)
    )).shape
    print(f'player shape is {sh}')
    return sh
player_to_vector.player_vector_shape = calc_player_vector_shape()


def state_to_vector(state: GameState, bot=None, verbose=False):
    vector = [
        *map(lambda x: player_to_vector(x, bot, verbose), state.player_spheres),
        np.zeros((player_to_vector.player_vector_shape[0] * (12 - len(state.player_spheres)),)),
        from_sphere_list_to_vector(state.active_spheres, 10),
        from_sphere_list_to_vector(state.inactive_spheres, 10),
        from_sphere_list_to_vector(state.bursts, 3),
        [state.timer]
    ]
    if verbose:
        print('state lengths:')
        for i in vector:
            print(len(i))
    a = np.hstack(vector).reshape((1, -1))
    return a

def calc_state_vector_shape():
    shapes_per_bot_amount = []
    for bots_amount in  range(1, 13):
        bots = [DoNothingBot] * bots_amount
        g = Game(create_colors([DoNothingBot, DoNothingBot], BotKeys))
        for i in range(190):
            g.update(1/60)
        verbose = False # bots_amount==12
        sh = state_to_vector(g.get_state(), verbose=verbose).shape
        shapes_per_bot_amount.append(sh)
    for sh in shapes_per_bot_amount:
        assert sh == shapes_per_bot_amount[0]
    state_shape = (sh[1],)
    print(f'state shape is {state_shape}')
    return state_shape
state_to_vector.state_vector_shape = calc_state_vector_shape()

def create_default_keras_model():
    model = keras.Sequential([
        keras.Input(state_to_vector.state_vector_shape),
        keras.layers.Dense(50, activation='relu'),
        keras.layers.Dense(1, activation='tanh')
    ])
    print(f'Default model has {model.count_params()} params')
    return model

class KerasBot:
    def __init__(self, model: Optional[keras.Model]=None):
        if model is None:
            model = create_default_keras_model()
        self.model = model
        self.__name__ = f'KerasBot'

    def __call__(self, center, velocity, radius, color):
        return KerasBotThing(self.model, center, velocity, radius, color)

class KerasBotThing(Bot):
    def __init__(self, model: keras.Model, center, velocity, radius, color):
        super().__init__(center, velocity, radius, color)
        self.model = model

    def get_action(self, state: GameState, time_delta: float) -> bool:
        vector = state_to_vector(state, self)
        if vector.shape[1] != state_to_vector.state_vector_shape[0]:
            print(f'vector shape doesnt match: {vector.shape} != {state_to_vector.state_vector_shape}')
            state_to_vector(state, verbose=True)
            state.save(f'faulty_state.pickle')

        return self.model(vector) > 0 # call directly for faster execution of small inputs
