from model.Game import Game
from model.World import World
from model.Wizard import Wizard
from model.CircularUnit import CircularUnit

import math
import numpy as np
import interpolator.interpolator as interp


class Point2D:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def get_distance_to(self, x, y):
        return math.hypot(self.x - x, self.y - y)

    def get_distance_to_unit(self, unit):
        return self.get_distance_to(unit.x, unit.y)


class VisibleMap:
    def __init__(self, debug=None, me: Wizard = None, world: World = None, game: Game = None):
        self.debug = debug
        self.world = world
        self.game = game
        self.me = me
        self.potential_interp = None

        try:
            from debug_client import Color
            self.green = Color(r=0.0, g=1.0, b=0.0)
            self.red = Color(r=1.0, g=0.0, b=0.0)
            self.grey = Color(r=0.7, g=0.7, b=0.7)
            self.black = Color(r=0.0, g=0.0, b=0.0)
        except ImportError:
            pass

    def init_tick(self, me: Wizard, world: World, game: Game):
        self.world = world
        self.game = game
        self.me = me
        np.random.seed(game.random_seed % 0xFFFFFFFF)

    def get_score_to_goal(self, pos: Point2D, goal: Point2D):
        dist = pos.get_distance_to_unit(goal)
        return 1 / dist if dist > 0 else float("inf")

    # TODO: skip potential if an object do not lay on your path
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
                return 0

    def calc_potential(self, pos: Point2D, target: Point2D):
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

    def create_potential_map(self, target: Point2D):
        n_ticks_forward = 2
        r = self.game.wizard_forward_speed * n_ticks_forward
        half_n = 3
        k = r / half_n
        range_x = range(-half_n, half_n + 1)
        range_y = range(-half_n + 1, half_n)
        self.coords = ([self.me.x + k*x for x in range_x], [self.me.y + k*y for y in range_y])
        self.potential_map = np.array([[self.calc_potential(Point2D(self.me.x + k*x, self.me.y + k*y), target) for y in range_y] for x in range_x])

        data = (self.potential_map,)
        self.potential_interp = interp.multilinear_interpolator(self.coords, data)

        if self.debug:
            max_ = np.amax(self.potential_map)
            min_ = np.amin(self.potential_map)
            with self.debug.post() as dbg:
                xs, ys = self.coords
                from debug_client import Color
                for x in xs:
                    for y in ys:
                        score = (self.get_potential_in_pos(Point2D(x, y)) - min_)/ (max_ - min_) if (max_ - min_) > 0 else 0
                        dbg.fill_circle(x, y, 2, Color(r=score, g=1-score, b=0.0))

    def get_potential_in_pos(self, pos: Point2D):
        (error_flag, output) = self.potential_interp([pos.x, pos.y])
        return output[0] if output else 0

    def do_move(self, forward_speed, strafe_right, turn, n_ticks_forward):
        game = self.game
        max_speed = game.wizard_forward_speed if forward_speed > 0 else game.wizard_backward_speed
        max_strafe_speed = game.wizard_strafe_speed
        strafe_speed = strafe_right * max_strafe_speed * (1 - (forward_speed/max_speed)**2) ** 0.5
        angle = self.me.angle

        my_position = Point2D(self.me.x, self.me.y)
        for _ in range(n_ticks_forward):
            angle += turn
            cos_x = math.cos(angle)
            sin_x = math.sin(angle)
            my_position.x += forward_speed * cos_x - strafe_speed * sin_x
            my_position.y += forward_speed * sin_x + strafe_speed * cos_x
        return my_position, angle

    def get_optimal_move(self, target: Point2D):
        n_ticks_forward = 1

        game = self.game
        optimal_forward = 0
        optimal_strafe_right = 0
        optimal_turn = 0
        max_score = 0

        # [-wizard_backward_speed; wizard_forward_speed]
        value_forward_list = [-self.game.wizard_backward_speed, 0, self.game.wizard_forward_speed]
        # [-wizard_strafe_speed; wizard_strafe_speed)
        value_strafe_right_list = [-1, 0, 1]
        # [-wizard_max_turn_angle; wizard_max_turn_angle]
        value_turn_list = np.random.uniform(-game.wizard_max_turn_angle, game.wizard_max_turn_angle, 20)

        self.create_potential_map(target)
        for value_forward in value_forward_list:
            for value_strafe_right in value_strafe_right_list:
                for value_turn in value_turn_list:
                    pos, _ = self.do_move(value_forward, value_strafe_right, value_turn, n_ticks_forward)
                    score = self.get_potential_in_pos(pos)

                    pos_forward, _ = self.do_move(self.game.wizard_forward_speed,
                                                  0, 0, n_ticks_forward)
                    score_forward = self.get_potential_in_pos(pos_forward)

                    if score > max_score:
                        optimal_pos = pos
                        optimal_forward, optimal_strafe_right, optimal_turn = value_forward, value_strafe_right, value_turn
                        max_score = score

        game = self.game
        max_speed = game.wizard_forward_speed if optimal_forward > 0 else game.wizard_backward_speed
        max_strafe_speed = game.wizard_strafe_speed
        optimal_strafe_right = optimal_strafe_right * max_strafe_speed * (1 - (optimal_forward/max_speed)**2) ** 0.5
        return optimal_forward, optimal_strafe_right, optimal_turn





