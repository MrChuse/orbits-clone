from dataclasses import dataclass
from typing import Optional, Callable
import random
import heapq

import pygame
import pygame.freetype
from pygame import Vector2

from .core import (
    SPHERE_SIZE,
    PLAYER_SIZE,
    ROTATOR_SIZE,
    DEFAULT_SPEED,

    Team,
    GameStage,
    PlayerScore,
    GameState,
    Map,
    BotKeys,

    VerticalLine,
    HorizontalLine,
    Sphere,
    PlayerSphere,
    RotatorSphere,
)
from bots import Bot

map1 = Map([
    (0.1, 0.2, ROTATOR_SIZE),
    (0.3666, 0.2, ROTATOR_SIZE),
    (0.6333, 0.2, ROTATOR_SIZE),
    (0.9, 0.2, ROTATOR_SIZE),
    (0.2333, 0.5, ROTATOR_SIZE),
    (0.5, 0.5, ROTATOR_SIZE),
    (0.7666, 0.5, ROTATOR_SIZE),
    (0.1, 0.8, ROTATOR_SIZE),
    (0.3666, 0.8, ROTATOR_SIZE),
    (0.6333, 0.8, ROTATOR_SIZE),
    (0.9, 0.8, ROTATOR_SIZE),
])

class Game:
    def __init__(self, colors: dict[int, tuple[Team, str, Callable[[], PlayerSphere]]], seed=None) -> None:
        size = (2, 1)
        self.size = size
        self.leftwall = None
        self.rightwall = None
        self.topwall = None
        self.bottomwall = None
        self.debug_surface = None
        self.set_dimensions(size) # set these things

        self.colors = colors
        self.num_players = 0
        self.keys_list = []
        self.actions_in_last_frame: list[int] = []
        self.register_players_and_keys(list(self.colors.keys())) # set things above
        self.old_scores = []
        self.scores = [0] * self.num_players

        self.rotators = []
        self.load_map(map1)

        self.seed = seed
        # print(self.seed)
        self.random = None
        self.total_uniforms = 0

        self.player_spheres: list[PlayerSphere] = []
        self.bot_player_spheres: list[Bot] = []
        self.active_spheres: list[Sphere] = []
        self.inactive_spheres: list[Sphere] = []
        self.attacking_spheres: list[list[Sphere]] = None
        self.someone_won = False

        self.stage = GameStage.ROTATING_AROUND_CENTER
        # ROTATING_AROUND_CENTER
        self.timer = 0
        self.starting_angle = 0

        # GAMING
        self.death_order: list[int] = []

        # SHOWING_RESULTS
        self.score1 = 0
        self.score2 = 0
        self.how_to_win_text = ''
        self.player_scores = None

        self.restart_game(seed)

    def load_map(self, map_: Map):
        for i in map_.rotators_coords:
            self.rotators.append(RotatorSphere(Vector2(i[0]*self.size[0], i[1]*self.size[1]), i[2]))

    def random_uniform(self, a, b, from_where='unknown'):
        self.total_uniforms += 1
        # print('uniform', self.total_uniforms, from_where)
        return self.random.uniform(a, b)

    def random_randint(self, a, b):
        # print('randint')
        return self.random.randint(a, b)

    def restart_round(self):
        self.starting_angle = self.random_uniform(0, 360, 'starting angle')

        self.bot_player_spheres = []
        self.player_spheres = []
        for key, (team, name, PlayerClass) in self.colors.items():
            pos = Vector2(0, 0)
            vel = Vector2(0, 0)
            ps = PlayerClass(pos, vel, PLAYER_SIZE, team.value)
            if isinstance(ps, Bot):
                self.bot_player_spheres.append(ps)
            self.player_spheres.append(ps)
        self.attacking_spheres = [[] for _ in range(self.num_players)]

        self.inactive_spheres = []
        self.active_spheres = []
        for i in range(10):
            self.add_random_sphere()

        self.someone_won = False

        self.stage = GameStage.ROTATING_AROUND_CENTER
        self.timer = 0
        self.death_order: list[int] = []

    def restart_game(self, seed=None):
        self.seed = seed
        if self.seed is None:
            self.seed = random.randint(0, 1000000000)
        self.random = random.Random(self.seed)
        self.total_uniforms = 0
        # print('reset seed to', seed, 'and uniforms to 0')

        self.scores = [0] * self.num_players
        self.restart_round()

    def set_dimensions(self, size):
        self.size = size
        self.leftwall = VerticalLine(0)
        self.rightwall = VerticalLine(size[0])
        self.topwall = HorizontalLine(0)
        self.bottomwall = HorizontalLine(size[1])

        self.debug_surface = pygame.Surface(self.size)
        # self.debug_surface.fill(pygame.Color('#00000000'))

    def register_players_and_keys(self, keys_list: list):
        self.num_players = len(keys_list)
        self.keys_list = keys_list
        self.actions_in_last_frame = []

    def get_random_spawn_position(self, radius):
        return (self.random_uniform(radius, self.size[0]-radius, 'random pos x'),
                self.random_uniform(radius, self.size[1]-radius, 'random pos y'))

    def add_random_sphere(self):
        self.active_spheres.append(Sphere(Vector2(self.get_random_spawn_position(SPHERE_SIZE)),
                                   Vector2(0, 0),
                                   SPHERE_SIZE,
                                   (255,255,255)))

    def check_wall_collision(self, sphere: Sphere):
        if sphere.intersects(self.topwall):
            sphere.velocity.y *= -1
            sphere.center.y = sphere.radius
            return True
        if sphere.intersects(self.bottomwall):
            sphere.velocity.y *= -1
            sphere.center.y = self.bottomwall.y - sphere.radius
            return True
        if sphere.intersects(self.leftwall):
            sphere.velocity.x *= -1
            sphere.center.x = sphere.radius
            return True
        if sphere.intersects(self.rightwall):
            sphere.velocity.x *= -1
            sphere.center.x = self.rightwall.x - sphere.radius
            return True

    def process_actions(self, actions):
        # self.actions_in_last_frame: list[int] = []
        for action in actions:
            if action in self.keys_list:
                self.actions_in_last_frame.append(self.keys_list.index(action))
        # if len(actions) > 0:
        #     print(actions, self.actions_in_last_frame)

    def perform_actions(self):
        if self.actions_in_last_frame is not None:
            for player in self.actions_in_last_frame:
                player_sphere = self.player_spheres[player]
                for rotator in self.rotators:
                    if player_sphere.check_center_inside(rotator) and not player_sphere.is_dodging():
                        if player_sphere.rotating_around is None:
                            player_sphere.rotating_around = rotator
                        else:
                            player_sphere.rotating_around = None
                        break
                else:
                    # not in a rotator
                    if player_sphere.can_dodge():
                        player_sphere.dodge_initiated = True
                        if len(player_sphere.trail) > 0:
                            attacking_sphere = player_sphere.remove_sphere()
                            attacking_sphere.velocity = player_sphere.velocity * 2
                            attacking_sphere.damping_factor = 1
                            self.attacking_spheres[player].append(attacking_sphere)
                if self.stage == GameStage.END_SCREEN:
                    self.timer += 2
        self.actions_in_last_frame = []

    def update_positions_and_wall_collisions(self):
        for i in self.player_spheres:
            if not i.alive: continue
            if self.check_wall_collision(i):
                i.rotating_around = None
            i.update()
        for player, attacking_spheres in zip(self.player_spheres, self.attacking_spheres):
            for i in attacking_spheres:
                if self.check_wall_collision(i) and not player.is_dodging():
                    i.color = (255, 255, 255)
                    self.inactive_spheres.append(i)
                    attacking_spheres.remove(i)
                    i.damping_factor = 0.98
                i.update()
        for i in self.active_spheres:
            self.check_wall_collision(i)
            i.update()
        for i in self.inactive_spheres:
            self.check_wall_collision(i)
            i.update()

    def update_positions_to_rotate_around_center(self):
        ROTATION_SPEED = 500
        FINAL_SIZE = 0.15
        t = self.timer / 3
        center = Vector2(self.size) / 2
        right = Vector2(FINAL_SIZE, 0)
        for index, sphere in enumerate(self.player_spheres):
            angle = index / self.num_players * 360 + t * ROTATION_SPEED + self.starting_angle
            direction = right.rotate(angle)
            position = center.lerp(center+direction, t)
            sphere.center = position
            if t > 0.5:
                velocity = (center - position).rotate(-90)
                velocity.scale_to_length(DEFAULT_SPEED)
                sphere.velocity = velocity

    def process_collisions(self):
        for index, sphere in enumerate(self.player_spheres):
            if not sphere.alive: continue
            # other players
            for sphere_to_check in self.player_spheres[index+1:]:
                if not sphere_to_check.alive: continue
                if sphere.intersects(sphere_to_check):
                    sphere.rotating_around = None
                    sphere_to_check.rotating_around = None
                    if not sphere.is_dodging() and not sphere_to_check.is_dodging():
                        sphere.collide_with(sphere_to_check)

            # other players' trails
            for other_player in self.player_spheres:
                if sphere == other_player:
                    continue
                for sphere_to_check in other_player.trail:
                    if sphere.intersects(sphere_to_check) and not sphere.is_dodging():
                        self.process_player_death(index, sphere, killer_sphere=other_player)

            # attacking spheres
            for index2, players_spheres in enumerate(self.attacking_spheres):
                if index == index2: continue # this players' spheres
                for sphere_to_check in players_spheres:
                    if sphere.intersects(sphere_to_check) and not sphere.is_dodging():
                        self.process_player_death(index, sphere, killer_index=index2)

            # white spheres
            for sphere_to_check in self.active_spheres:
                if sphere.intersects(sphere_to_check):
                    if not sphere.is_dodging():
                        sphere.add_sphere_to_queue(sphere_to_check)
                        self.active_spheres.remove(sphere_to_check)
                        self.add_random_sphere()
            for sphere_to_check in self.inactive_spheres:
                if sphere.intersects(sphere_to_check):
                    if not sphere.is_dodging():
                        sphere.add_sphere_to_queue(sphere_to_check)
                        self.inactive_spheres.remove(sphere_to_check)

    def process_player_death(self, killed_index: int, killed_sphere: PlayerSphere, *, killer_index: Optional[int] = None, killer_sphere: Optional[PlayerSphere] = None):
        if killer_index is None and killer_sphere is None:
            raise ValueError('provide at least one')
        if killer_sphere is None:
            killer_sphere = self.player_spheres[killer_index]
        if not killed_sphere.alive: return
        self.death_order.append(killed_index)
        for sphere_to_pop in killed_sphere.trail:
            killer_sphere.add_sphere_to_queue(sphere_to_pop)
        killed_sphere.trail = []
        killed_sphere.alive = False

    def process_results(self, winner_index):
        assert len(self.death_order) == self.num_players-1, len(self.death_order)
        assert winner_index not in self.death_order
        self.death_order.append(winner_index)

        self.old_scores = self.scores.copy()
        for score, player in enumerate(self.death_order):
            self.scores[player] += score
        self.score1, self.score2 = heapq.nlargest(2, self.scores)
        self.death_order = []

        player_scores = [PlayerScore(color=player.color) for player in self.player_spheres]

        sorted_old_scores = sorted(enumerate(self.old_scores), key=lambda x:x[1], reverse=True)
        for i, (player_index, old_score) in enumerate(sorted_old_scores):
            player_scores[player_index].old_position = i
            player_scores[player_index].old_score = old_score

        sorted_scores = sorted(enumerate(self.scores), key=lambda x:x[1], reverse=True)
        for i, (player_index, score) in enumerate(sorted_scores):
            player_scores[player_index].new_position = i
            player_scores[player_index].new_score = score
        self.player_scores = player_scores


    def update(self, time_delta: float):
        # get bots actions
        state = self.get_state()
        bots_actions = []
        for bot, key in zip(self.bot_player_spheres, BotKeys):
            action = bot.get_action(state, time_delta)
            if action:
                # print(f'{Team(bot.color).name} action at {self.timer:.1f}')
                # print(f'{self.bot_player_spheres}')
                bots_actions.append(key)
        self.process_actions(bots_actions)

        # perform actions. actions were commited in process actions function
        if self.stage == GameStage.ROTATING_AROUND_CENTER:
            if self.timer < 3:
                self.update_positions_to_rotate_around_center()
                self.timer += time_delta
            else:
                self.stage = GameStage.GAMING
                self.timer = 0
        elif self.stage == GameStage.GAMING:
            self.perform_actions()

            self.update_positions_and_wall_collisions()

            # other collisions
            self.process_collisions()

            for i in self.player_spheres:
                i.velocity.scale_to_length(DEFAULT_SPEED)

            self.timer += time_delta

            winner = [(index, p.color) for index, p in enumerate(self.player_spheres) if p.alive]
            if len(winner) < 2 and self.num_players > 1:
                self.stage = GameStage.SHOWING_RESULTS
                self.timer = 0
                self.process_results(winner[0][0])

                if self.score1 < 5 * (self.num_players-1):
                    self.how_to_win_text = f'Reach {5 * (self.num_players-1)} points'
                    self.next_stage = GameStage.RESTART_ROUND
                elif self.score1 >= 5 * (self.num_players-1) and self.score1 - self.score2 < 2:
                    self.how_to_win_text = 'Get a 2-point lead'
                    self.next_stage = GameStage.RESTART_ROUND
                else:
                    self.someone_won = winner[0][1]
                    self.next_stage = GameStage.END_SCREEN
        elif self.stage == GameStage.SHOWING_RESULTS:
            self.perform_actions()

            self.update_positions_and_wall_collisions()

            # other collisions
            self.process_collisions()

            for i in self.player_spheres:
                i.velocity.scale_to_length(DEFAULT_SPEED)

            if self.timer > 5:
                self.stage = self.next_stage
                self.timer = 0
            self.timer += time_delta
        elif self.stage == GameStage.RESTART_ROUND:
            self.restart_round()
        elif self.stage == GameStage.END_SCREEN:
            self.perform_actions()

            self.update_positions_and_wall_collisions()

            # other collisions
            self.process_collisions()

            for i in self.player_spheres:
                i.velocity.scale_to_length(DEFAULT_SPEED)
            if self.timer > 30:
                self.restart_game()
            self.timer += time_delta


    def get_state(self):
        return GameState(self.player_spheres,
                         self.active_spheres,
                         self.inactive_spheres,
                         self.attacking_spheres,
                         self.rotators,
                         self.timer,
                         self.death_order,)
                        #  self.random)

    def get_front_state(self):
        return self.get_state().update_to_front(self.player_scores, self.how_to_win_text, self.stage, self.someone_won)


    def set_state(self, state: GameState):
        self.rotators = state.rotators
        self.player_spheres = state.player_spheres
        self.active_spheres = state.active_spheres
        self.inactive_spheres = state.inactive_spheres
        self.attacking_spheres = state.attacking_spheres
        self.timer = state.timer
        self.death_order = state.death_order
        # self.random = state.random_
        # self.stage = state.stage

    def draw_debug(self, debug_surface: pygame.Surface):
        for i in self.player_spheres:
            i.draw_debug(debug_surface)
