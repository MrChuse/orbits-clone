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
    d = [np.array(p).reshape(1, -1) for p in players]
    d.append(rest.reshape(1, -1))
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

def create_keras_model():
    dense_output_size = 10
    model1 = keras.Sequential([
        keras.Input(shape=PLAYER_VECTOR_SHAPE),
        keras.layers.Dense(dense_output_size, activation='relu')
    ])

    model2 = keras.Sequential([
        keras.Input(shape=STATE_VECTOR_SHAPE),
        keras.layers.Dense(dense_output_size, activation='relu')
    ])

    model3 = keras.Sequential([
        keras.Input(shape=(dense_output_size*13,)),
        keras.layers.Dense(1, activation='tanh')
    ])

    w1 = model1.count_params()
    w2 = model2.count_params()
    w3 = model3.count_params()
    print(f'Split model has {w1}+{w2}+{w3}={w1+w2+w3} params')
    # model = keras.Sequential([
    #     keras.Input((STATE_VECTOR_SHAPE[0]+12*PLAYER_VECTOR_SHAPE[0],)),
    #     keras.layers.Dense(50, activation='relu'),
    #     keras.layers.Dense(1, activation='tanh')
    # ])
    # w = model.count_params()
    # print(f'Split model has {w} params')
    return model1, model2, model3

class KerasBot:
    def __init__(self, model1: Optional[keras.Model]=None, model2=None, model3=None):
        if model1 is None or model2 is None or model3 is None:
            model1, model2, model3 = create_keras_model()
        self.model1 = model1
        self.model2 = model2
        self.model3 = model3
        self.__name__ = f'KerasBot'

    def __call__(self, center, velocity, radius, color):
        return KerasBotThing(self.model1, self.model2, self.model3, center, velocity, radius, color)

class KerasBotThing(Bot):
    def __init__(self, model1: keras.Model, model2, model3, center, velocity, radius, color):
        super().__init__(center, velocity, radius, color)
        self.model1 = model1
        self.model2 = model2
        self.model3 = model3

    def get_action(self, state: GameState, time_delta: float) -> bool:
        vector = state_to_vector(state, self)
        assert len(vector) == 13
        players_things = [self.model1(i) for i in vector[:12]]
        rest = self.model2(vector[-1])
        players_things.append(rest)
        new_inp = np.hstack(players_things)
        res = self.model3(new_inp)
        # vector = np.hstack(vector)
        # res = self.model1(vector)
        return res > 0

        # if vector[-1].shape[-1] != STATE_VECTOR_SHAPE[0]:
        #     print(f'vector shape doesnt match: {vector[-1].shape} != {STATE_VECTOR_SHAPE}')
        #     state_to_vector(state, verbose=True)
        #     state.save(f'faulty_state.pickle')

        # vector = [np.hstack(vector[:6]), np.hstack(vector[6:-1]), vector[-1]]

# def create_split_keras_model():
#     dense_output_size = 12

#     inputs_submodel = keras.Input(shape=PLAYER_VECTOR_SHAPE)
#     outputs_submodel = keras.layers.Dense(dense_output_size, activation='relu')(inputs_submodel)
#     submodel = keras.Model(inputs=inputs_submodel, outputs=outputs_submodel, name='player_submodel')

#     inputs = keras.Input(shape=STATE_VECTOR_SHAPE)
#     intermediates = []
#     def split(first_index, last_index):
#         def f(x):
#             return x[:, first_index:last_index]
#         print('split', first_index, last_index)
#         return keras.layers.Lambda(f)
#     dense = keras.layers.Dense(dense_output_size, activation='relu')
#     for i in range(12):
#         first_index = i * PLAYER_VECTOR_SHAPE[0]
#         last_index = first_index + PLAYER_VECTOR_SHAPE[0]
#         out = split(first_index, last_index)(inputs)
#         out = dense(out)
#         intermediates.append(out)
#     rest_of_inputs = split(last_index, None)(inputs)
#     rest_of_inputs_densed = keras.layers.Dense(dense_output_size, activation='relu')(rest_of_inputs)
#     intermediates.append(rest_of_inputs_densed)
#     intermediates_concatenated = keras.layers.concatenate(intermediates)

#     output = keras.layers.Dense(1, activation='tanh')(intermediates_concatenated)
#     model = keras.Model(inputs=inputs, outputs=output)
#     print(f'Split model has {model.count_params()} params')
#     return model
