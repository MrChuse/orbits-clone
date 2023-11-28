from back.core import GameState
from . import Bot

class DoNothingBot(Bot):
    def get_action(self, state: GameState, time_delta: float) -> bool:
        return super().get_action(state, time_delta)