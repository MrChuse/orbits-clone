import random
from typing import Any

from back.core import GameState
from . import Bot


# Do not forget to add your bot to __init__ file.
# Import it there and add to the bots list
class RandomBot():
    def __init__(self, cutoff):
        self.cutoff = cutoff
        self.__name__ = f'RandomBot{cutoff}'

    def __call__(self, center, velocity, radius, color):
        return RandomBotThing(self.cutoff, center, velocity, radius, color)

class RandomBotThing(Bot):
    def __init__(self, cutoff, center, velocity, radius, color):
        super().__init__(center, velocity, radius, color)
        self.cutoff = cutoff
    def get_action(self, state: GameState, time_delta: float) -> bool:
        return random.random() < self.cutoff