from .bot_base import Bot
from .smart_bot import SmartBot
from .dodging_collect_sphere_bot import DodgingCollectSphereBot
from .state_machine_bot import StateMachineBot
from .collect_sphere_bot import CollectSphereBot
from .wait_cling_bot import WaitClingBot
from .cling_bot import ClingBot
from .do_nothing_bot import DoNothingBot
from .random_bot import RandomBot

bots = [SmartBot, DodgingCollectSphereBot, StateMachineBot, CollectSphereBot, WaitClingBot, ClingBot, DoNothingBot, RandomBot(0.5)]


# bots check
from pygame import Vector2
for bot in bots:
    try:
        # each bot must override the get_action function
        # and have its __init__ method have 4 args: center, velocity, radius, color
        # and have a __name__ attribute to show in the dropdown menu
        b = bot(Vector2(0, 0), Vector2(1, 0), 10, (255, 255, 255))
        bot.__name__
    except AttributeError as e:
        print(f'Bot {bot} has a problem: {e!r}')
        exit()
    except Exception as e:
        print(f'Bot {bot.__name__} has a problem: {e!r}')
        exit()
