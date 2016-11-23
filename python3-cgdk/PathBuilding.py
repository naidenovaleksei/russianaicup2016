import math
import numpy as np
# import interpolator as interp

from Points2D import *

from model.Game import Game
from model.World import World
from model.Wizard import Wizard
from model.CircularUnit import CircularUnit
from model.LivingUnit import LivingUnit
from model.Minion import Minion
from model.MinionType import MinionType
from model.ActionType import ActionType
from model.Building import Building
from model.Faction import Faction
from model.Projectile import Projectile

n_ticks_forward = 1
neutral_coef = 0.05 # - 0.01
enemy_coef = 1
projectile_coef = 10


def get_view_radius(me: Wizard):
    return me.vision_range # 200


class VisibleMap:
    def __init__(self, debug=None, me: Wizard = None, world: World = None, game: Game = None):
        self.world = world
        self.game = game
        self.me = me
        # self.potential_interp = None
        self.note_enemy_angle = True
        self.neutral_coef = 1
        self.neutral_dist_coef = 1
        self.life_coef = 1

    def init_tick(self, me: Wizard, world: World, game: Game):
        self.world = world
        self.game = game
        self.me = me
        np.random.seed(game.random_seed % 0xFFFFFFFF)
        self.note_enemy_angle = True
        self.neutral_coef = neutral_coef * np.random.normal(1, 0.3)
        self.neutral_dist_coef = 1
        # self.life_coef = 1 - 0.5 * me.life / me.max_life

    def get_negative_linear_score(self, dist, max_dist, coef):
        if dist <= 0:
            return float("-inf")
        elif 0 < dist <= max_dist:
            return dist * (coef / max_dist) - coef
        else:
            return 0

    def get_score_to_goal(self, pos: Point2D, goal: Point2D):
        dist = pos.get_distance_to_unit(goal) if goal is not None else 0
        # dist = pos.get_distance_to_unit(goal)
        return 1 / dist if dist > 0 else float("inf")

    # проверить
    def get_score_to_goal_ex(self, pos: Point2D, goal: Point2D, angle: float):
        dist = pos.get_distance_to_unit(goal) if goal is not None else 1
        angle_score = 1 - abs(pos.get_angle_to_point(goal, angle)) / math.pi
        return angle_score / dist if dist > 0 else float("inf")

    def get_score_to_neutral(self, point: Point2D, unit: CircularUnit):
        if unit.id == self.me.id:
            return 0
        dist = point.get_distance_to_unit(unit) - self.me.radius - unit.radius
        raduis = max(unit.radius / 4, self.me.radius / 2)
        # raduis = unit.radius / 4
        raduis *= np.random.normal(self.neutral_dist_coef, 0.1 * self.neutral_dist_coef)
        coef = self.neutral_coef * np.random.normal(1, 0.1)
        return self.get_negative_linear_score(dist, raduis, coef)

    def get_score_to_enemy(self, point: Point2D, unit: LivingUnit):
        coef = enemy_coef
        # danger_radius = 1
        if type(unit) is Wizard:
            # danger_radius = min_atack_distance(self.me) - self.me.radius # (unit).cast_range
            danger_radius = (unit).cast_range
            coef *= self.game.magic_missile_direct_damage
        elif type(unit) is Building:
            # danger_radius = min_atack_distance(self.me) - self.me.radius # (unit).attack_range
            danger_radius = (unit).attack_range
            coef *= self.game.guardian_tower_damage
        elif type(unit) is Minion:
            danger_radius = min_atack_distance(self.me) / 2
            # danger_radius = self.game.orc_woodcutter_attack_range if (unit).type == MinionType.ORC_WOODCUTTER else self.game.fetish_blowdart_attack_range
            coef *= self.game.orc_woodcutter_damage if (unit).type == MinionType.ORC_WOODCUTTER else self.game.dart_direct_damage
        else:
            danger_radius = 1


        # danger_radius = max(min(min_atack_distance(self.me) - self.me.radius, danger_radius), min_atack_distance(self.me) / 2)
        # min_atack_distance(self.me) - self.me.radius

        danger_radius = min(danger_radius, min_atack_distance(self.me) - self.me.radius) * self.life_coef

        if self.me.remaining_cooldown_ticks_by_action[ActionType.MAGIC_MISSILE] > 0:
            coef *= 100

        dist = point.get_distance_to_unit(unit) - self.me.radius
        score = self.get_negative_linear_score(dist, danger_radius, enemy_coef)
        return score if (dist <= danger_radius or danger_radius == 0) else (1 / dist - 1 / danger_radius)

    def get_score_to_nearest_enemy(self, point: Point2D, unit: LivingUnit):
        coef = enemy_coef
        if type(unit) is Wizard:
            danger_radius = (unit).cast_range
            coef *= self.game.magic_missile_direct_damage
        elif type(unit) is Building:
            danger_radius = (unit).attack_range
            coef *= self.game.guardian_tower_damage
        elif type(unit) is Minion:
            danger_radius = self.game.orc_woodcutter_attack_range if (unit).type == MinionType.ORC_WOODCUTTER else self.game.fetish_blowdart_attack_range
            coef *= self.game.orc_woodcutter_damage if (unit).type == MinionType.ORC_WOODCUTTER else self.game.dart_direct_damage
        else:
            danger_radius = 1

        danger_radius += self.me.radius

        # danger_radius *= 1.5
        # danger_radius = max(min(min_atack_distance(self.me) - self.me.radius, danger_radius), min_atack_distance(self.me) / 2)

        # if self.me.remaining_cooldown_ticks_by_action[ActionType.MAGIC_MISSILE] > 0:
        #     coef *= 100

        dist = point.get_distance_to_unit(unit) - self.me.radius - unit.radius
        return self.get_negative_linear_score(dist, danger_radius, enemy_coef)

    def get_score_to_projectile(self, point: Point2D, projectile: Projectile):
        danger_radius = 2 * self.me.radius
        dist = point.get_distance_to_unit(projectile) - self.me.radius - projectile.radius
        return self.get_negative_linear_score(dist, danger_radius, projectile_coef)

    # def is_enemy(self, unit: LivingUnit):
    #     return unit.faction != self.me.faction and unit.faction != Faction.NEUTRAL and (type(unit) is Wizard or type(unit) is Building or type(unit) is Minion)

    # проверить уклонение от снарядов
    def is_dengerous_projectile(self, point: Point2D, projectile: Projectile):
        disp_x = point.x - projectile.x
        disp_y = point.y - projectile.y
        return (projectile is Projectile) and (projectile.speed_x * disp_x > 0) and (projectile.speed_y * disp_y > 0)

    # def calc_potential(self, pos: Point2D, target: Point2D, angle: float):
    #     view_radius = get_view_radius(self.me)
    #     units = self.world.buildings + \
    #             self.world.wizards + \
    #             self.world.minions + \
    #             self.world.bonuses + \
    #             self.world.projectiles + \
    #             self.world.trees
    #     potential = self.get_score_to_goal(pos, target)
    #     for unit_nearby in units:
    #         if self.me.get_distance_to_unit(unit_nearby) < view_radius:
    #             if is_enemy(unit_nearby, self.me):
    #                 potential += self.get_score_to_enemy(pos, unit_nearby)
    #             elif self.is_dengerous_projectile(pos, unit_nearby):
    #                 potential += self.get_score_to_projectile(pos, unit_nearby)
    #             else:
    #                 potential += self.get_score_to_neutral(pos, unit_nearby)
    #     nearest_target = get_nearest_target(self.me, self.world)
    #     if nearest_target:
    #         nearest_target_score = self.get_score_to_enemy(pos, nearest_target)
    #         angle_score = 1 - abs(pos.get_angle_to_point(nearest_target, angle)) / math.pi
    #         potential += nearest_target_score * angle_score  # - nearest_target_score
    #     return potential

    def calc_potential_ex(self, pos: Point2D, target: Point2D, angle: float, note_angle=False):
        view_radius = get_view_radius(self.me)
        units = self.world.buildings + \
                self.world.wizards + \
                self.world.minions + \
                self.world.bonuses + \
                self.world.projectiles + \
                self.world.trees
        potential = self.get_score_to_goal_ex(pos, target, angle) if note_angle else self.get_score_to_goal(pos, target)
        max_score_to_enemy = float("inf")
        for unit_nearby in units:
            if self.me.get_distance_to_unit(unit_nearby) < view_radius:
                if is_enemy(unit_nearby, self.me):
                    # max_score_to_enemy = min(max_score_to_enemy, self.get_score_to_enemy(pos, unit_nearby))
                    max_score_to_enemy = min(max_score_to_enemy, self.get_score_to_enemy(pos, unit_nearby))
                    # potential += self.get_score_to_enemy(pos, unit_nearby)
                elif self.is_dengerous_projectile(pos, unit_nearby):
                    potential += self.get_score_to_projectile(pos, unit_nearby)
                else:
                    potential += self.get_score_to_neutral(pos, unit_nearby)
        assert max_score_to_enemy <= 0 or max_score_to_enemy == float("inf")
        if max_score_to_enemy < float("inf"):
            potential += max_score_to_enemy
        nearest_target = get_nearest_target(self.me, self.world)
        if self.note_enemy_angle and nearest_target and (pos.get_distance_to_unit(nearest_target) < 1.4 * self.me.cast_range):
            # nearest_target_score = self.get_score_to_enemy(pos, nearest_target)
            # nearest_target_score = self.get_score_to_nearest_enemy(pos, nearest_target)
            # # danger_radius = min_atack_distance(self.me) - self.me.radius
            # # dist = pos.get_distance_to_unit(nearest_target) - self.me.radius
            # # nearest_target_score = self.get_negative_linear_score(dist, danger_radius, 10)
            angle_score = 1 - abs(pos.get_angle_to_point(nearest_target, angle)) / math.pi
            # potential -= nearest_target_score * angle_score  # - nearest_target_score
            potential += 0.1 * angle_score
        return potential

    # def create_potential_map(self, target: Point2D):
    #     r = self.game.wizard_forward_speed * 2 * n_ticks_forward
    #     half_n = 3
    #     k = r / half_n
    #     range_x = range(-half_n, half_n + 1)
    #     range_y = range(-half_n + 1, half_n)
    #     self.coords = ([self.me.x + k*x for x in range_x], [self.me.y + k*y for y in range_y])
    #     self.potential_map = np.array([[self.calc_potential_ex(Point2D(self.me.x + k*x, self.me.y + k*y), target) for y in range_y] for x in range_x])
    #
    #     data = (self.potential_map,)
    #     self.potential_interp = interp.multilinear_interpolator(self.coords, data)

    # def get_potential_in_pos(self, pos: Point2D):
    #     (error_flag, output) = self.potential_interp([pos.x, pos.y])
    #     return output[0] if output else 0

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

    def get_optimal_move(self, target: Point2D, angle=None, note_angle=False):
        game = self.game
        optimal_forward = 0
        optimal_strafe_right = 0
        optimal_turn = 0
        max_score = float("-inf")

        # [-wizard_backward_speed; wizard_forward_speed]
        value_forward_list = [-self.game.wizard_backward_speed, 0, self.game.wizard_forward_speed]
        # [-wizard_strafe_speed; wizard_strafe_speed)
        value_strafe_right_list = [-1, 0, 1]
        # [-wizard_max_turn_angle; wizard_max_turn_angle]
        # value_turn_list = [(i - 4) / 4 * game.wizard_max_turn_angle for i in range(10)] if angle is None
        # ввели случайную состовляющую поворота. должна помочь выбираться из тупиковых ситуаций
        value_turn_list = np.random.uniform(-game.wizard_max_turn_angle, game.wizard_max_turn_angle, 10) if angle is None else [angle]
        np.random.shuffle(value_forward_list)
        np.random.shuffle(value_strafe_right_list)

        # if True or note_angle:
        for value_forward in value_forward_list:
            for value_strafe_right in value_strafe_right_list:
                for value_turn in value_turn_list:
                    pos, angle = self.do_move(value_forward, value_strafe_right, value_turn, n_ticks_forward)
                    score = self.calc_potential_ex(pos, target, angle, note_angle)
                    if score > max_score:
                        optimal_forward, optimal_strafe_right, optimal_turn = value_forward, value_strafe_right, value_turn
                        max_score = score
        # else:
        #     self.create_potential_map(target)
        #     for value_forward in value_forward_list:
        #         for value_strafe_right in value_strafe_right_list:
        #             for value_turn in value_turn_list:
        #                 pos, _ = self.do_move(value_forward, value_strafe_right, value_turn, n_ticks_forward)
        #                 score = self.get_potential_in_pos(pos)
        #
        #                 if score > max_score:
        #                     optimal_forward, optimal_strafe_right, optimal_turn = value_forward, value_strafe_right, value_turn
        #                     max_score = score
        game = self.game
        max_speed = game.wizard_forward_speed if optimal_forward > 0 else game.wizard_backward_speed
        max_strafe_speed = game.wizard_strafe_speed
        optimal_strafe_right = optimal_strafe_right * max_strafe_speed * (1 - (optimal_forward/max_speed)**2) ** 0.5
        # запретили поворот на месте, если не движимся
        if optimal_forward == optimal_strafe_right == 0:
            optimal_turn = 0
        return optimal_forward, optimal_strafe_right, optimal_turn





