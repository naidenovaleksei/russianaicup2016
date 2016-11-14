from model.Game import Game
from model.World import World
from model.Wizard import Wizard
from model.CircularUnit import CircularUnit

import math
import numpy as np


class Point2D:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def get_distance_to(self, x, y):
        return math.hypot(self.x - x, self.y - y)

    def get_distance_to_unit(self, unit):
        return self.get_distance_to(unit.x, unit.y)


class VisibleMap:
    def __init__(self, me: Wizard = None, world: World = None, game: Game = None):
        self.world = world
        self.game = game
        self.me = me

    def init_tick(self, me: Wizard, world: World, game: Game):
        self.world = world
        self.game = game
        self.me = me
        np.random.seed(game.random_seed % 0xFFFFFFFF)

    def get_score_to_goal(self, pos: Point2D, goal: Point2D):
        dist = pos.get_distance_to_unit(goal)
        return 1 / dist if dist > 0 else float("inf")

    def get_score_to_neutral(self, point: Point2D, unit: CircularUnit):
        neutral_coef = - 0.01

        if unit.id == self.me.id:
            return 0
        else:
            dist = point.get_distance_to_unit(unit) - self.me.radius - unit.radius
            if dist <= 0:
                return float("-inf")
            elif 0 < dist:
                return neutral_coef / dist**2 if dist > 0 else float("inf")
            else:
                #NOPE
                return 0

    def get_potential(self, pos: Point2D, target: Point2D):
        view_radius = 200
        units = self.world.buildings + \
                self.world.wizards + \
                self.world.minions + \
                self.world.bonuses + \
                self.world.projectiles + \
                self.world.trees
        potential = self.get_score_to_goal(pos, target)
        for unit_nearby in units:
            if self.me.get_distance_to_unit(unit_nearby) < view_radius:
                potential += self.get_score_to_neutral(pos, unit_nearby)
        return potential

    def do_move(self, forward_speed, strafe_right, turn, n_ticks_forward):
        my_position = Point2D(self.me.x, self.me.y)
        game = self.game
        max_speed = game.wizard_forward_speed if forward_speed > 0 else game.wizard_backward_speed
        max_strafe_speed = game.wizard_strafe_speed
        strafe_speed = strafe_right * max_strafe_speed * (1 - (forward_speed/max_speed)**2) ** 0.5
        angle = self.me.angle
        strafe_angle = angle + math.pi * 0.5

        for _ in range(n_ticks_forward):
            my_position.x += forward_speed * math.cos(angle) + strafe_speed * math.cos(strafe_angle)
            my_position.y += forward_speed * math.sin(angle) + strafe_speed * math.sin(strafe_angle)
            angle += turn

        return my_position, angle

    def get_optimal_move(self, target: Point2D):
        n_ticks_forward = 2

        game = self.game
        optimal_forward = 0
        optimal_strafe_right = 0
        optimal_turn = 0
        max_score = 0

        # [-wizard_backward_speed; wizard_forward_speed]
        # value_forward_list = np.arange(-game.wizard_backward_speed, game.wizard_forward_speed + 0.1, 0.5)
        value_forward_list = np.random.uniform(-game.wizard_backward_speed, game.wizard_forward_speed, 10)
        # [-wizard_strafe_speed; wizard_strafe_speed)
        value_strafe_right_list = [-1, 1]
        # [-wizard_max_turn_angle; wizard_max_turn_angle]
        # value_turn_list = np.arange(-game.wizard_max_turn_angle, game.wizard_max_turn_angle + 0.1, 0.1)
        value_turn_list = np.random.uniform(-game.wizard_max_turn_angle, game.wizard_max_turn_angle, 10)

        for value_forward in value_forward_list:
            for value_strafe_right in value_strafe_right_list:
                for value_turn in value_turn_list:
                    pos, _ = self.do_move(value_forward, value_strafe_right, value_turn, n_ticks_forward)

                    score = self.get_potential(pos, target)
                    if score > max_score:
                        max_score = score
                        optimal_forward, optimal_strafe_right, optimal_turn = value_forward, value_strafe_right, value_turn
        return optimal_forward, optimal_strafe_right, optimal_turn





