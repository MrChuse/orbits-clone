from back.core import GameState
from . import Bot


# Do not forget to add your bot to __init__ file.
# Import it there and add to the bots list
class DoNothingBot(Bot):
    def get_action(self, state: GameState, time_delta: float) -> bool:
        return super().get_action(state, time_delta)