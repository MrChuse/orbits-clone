import pygad

import back

def inspect(self):
    from learn_ga import create_model_from_solution
    from bots.keras_bot import create_keras_model, KerasBot
    filename = 'genetic_algorithm_results_250'
    ga_instance: pygad.GA = pygad.load(filename)

    ga_instance.summary()
    ga_instance.plot_fitness()
    solution, fitness, idx = ga_instance.best_solution(ga_instance.last_generation_fitness)
    print(solution, fitness, idx)
    model = create_keras_model()
    model = create_model_from_solution(model, solution)
    model.save_weights('weights')
    bot = KerasBot(model)
    print(bot)

def bots_thing():
    import back
    from battle_the_bots import create_colors, play_a_console_game
    from bots.keras_split_bot import state_to_vector, KerasBot
    from bots import DoNothingBot
    import keras
    import numpy as np

    def create_keras_model():
        inps = [keras.Input(shape=(62,)) for i in range(12)]
        i13 = keras.Input(shape=(47,))
        d = keras.layers.Dense(10, activation='relu')
        inters = [d(i) for i in inps]
        inter13 = keras.layers.Dense(10, activation='relu')(i13)
        x = keras.layers.concatenate(inters + [inter13])
        output = keras.layers.Dense(1, activation='tanh')(x)
        return (keras.Model(inputs=inps+[i13], outputs=output),)

    model, = create_keras_model()

    game = back.Game(create_colors([KerasBot() for i in range(12)], back.BotKeys))
    for _ in range(200):
        game.update(1/60)
    state = game.get_state()
    vector = state_to_vector(state)
    print(vector)
    print(model.predict(vector))
    # play_a_console_game(1, 1, , back.GameStage.SHOWING_RESULTS)


def numpy_model_test():
    from bots.keras_bot_numpy import Model, STATE_VECTOR_SHAPE
    import numpy as np

    m = Model()
    print(m(np.random.random(STATE_VECTOR_SHAPE)))

numpy_model_test()