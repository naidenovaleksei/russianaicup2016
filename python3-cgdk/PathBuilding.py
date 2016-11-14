from model.Game import Game
from model.World import World
from model.Wizard import Wizard
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

    def initTick(self, me: Wizard, world: World, game: Game):
        self.world = world
        self.game = game
        self.me = me
        np.random.seed(game.random_seed % 0xFFFFFFFF)

    def get_potential(self, point: Point2D, target: Point2D):
        units = self.world.buildings + \
                self.world.wizards + \
                self.world.minions + \
                self.world.bonuses + \
                self.world.projectiles + \
                self.world.trees
        r_to_point = point.get_distance_to_unit(target)
        return 1 / r_to_point if r_to_point > 0 else float("inf")



    def do_move(self, forward, strafe_right, turn, n_ticks_forward):
        my_position = Point2D(self.me.x, self.me.y)
        game = self.game
        max_speed = game.wizard_forward_speed if forward > 0 else game.wizard_backward_speed
        max_strafe_speed = game.wizard_strafe_speed
        hypot = math.hypot(forward / max_speed, strafe_right / max_strafe_speed)
        angle = self.me.angle
        strafe_angle = angle + math.pi * 0.5

        forward = forward / hypot
        strafe_right = strafe_right / hypot

        for _ in range(n_ticks_forward):
            my_position.x += forward * math.cos(angle) + strafe_right * math.cos(strafe_angle)
            my_position.y += forward * math.sin(angle) + strafe_right * math.sin(strafe_angle)
            angle += turn

        return my_position, angle

    def get_optimal_move(self, target: Point2D):
        n_ticks_forward = 3
        n_generations = 2000

        game = self.game
        optimal_forward = 0
        optimal_strafe_right = 0
        optimal_turn = 0
        max_score = 0

        for _ in range(n_generations):
            value_forward = np.random.uniform(low=-game.wizard_backward_speed,
                                              high=game.wizard_forward_speed) #[-wizard_backward_speed; wizard_forward_speed)
            value_strafe_right = np.random.uniform(low=-game.wizard_strafe_speed,
                                              high=game.wizard_strafe_speed) #[-wizard_strafe_speed; wizard_strafe_speed)
            value_turn = np.random.uniform(low=-game.wizard_max_turn_angle,
                                           high=game.wizard_max_turn_angle) #[-wizard_max_turn_angle; wizard_max_turn_angle)

            pos,_ = self.do_move(value_forward, value_strafe_right, value_turn, n_ticks_forward)

            score = self.get_potential(pos, target)
            if score > max_score:
                max_score = score
                optimal_forward, optimal_strafe_right, optimal_turn = value_forward, value_strafe_right, value_turn

        return optimal_forward, optimal_strafe_right, optimal_turn





