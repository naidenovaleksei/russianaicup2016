
from Behaviour import *
from Points2D import Point2D

from model.ActionType import ActionType
from model.Game import Game
from model.Move import Move
from model.Wizard import Wizard
from model.World import World



class MyStrategy:
    def init_tick(self, me: Wizard, world: World, game: Game, move: Move):
        self.me = me
        self.world = world

    def log(self, message=""):
        print(self.world.tick_index, message, sep='\t')

    def distance_to_me(self, unit: LivingUnit):
        return self.me.get_distance_to(unit)


    ### MOVE ###

    def move(self, me: Wizard, world: World, game: Game, move: Move):
        # init
        self.init_tick(me, world, game, move)

        # nothing to learn

        # shoot/staff action
        target_enemy = self.can_shoot(me, world, game, move)
        if target_enemy:
            self.do_shoot(target_enemy, me, world, game, move)

        # move/turn action
        nearest_bonus = self.see_bonus(me, world, game, move)
        if nearest_bonus:
            self.go_to_bonus(nearest_bonus)
        elif self.forced_to_retreat(me, world, game, move):
            self.retreat(me, world, game, move)
        elif self.can_turn_to_bonus(me, world, game, move):
            self.turn_to_bonus(me, world, game, move)
        elif can_go_to_enemy:
            go_to_enemy
        elif self.can_go_forward(me, world, game, move):
            self.go_forward(me, world, game, move)
        else:
            self.log("nothing_to_do")


    ### SHOOT ###

    def can_shoot(self, me: Wizard, world: World, game: Game, move: Move):
        target_enemy = None
        units = []
        units.extend(world.buildings)
        units.extend(world.minions)
        units.extend(world.wizards)

        enemies = get_target_enemies(units, me, game)
        if len(enemies) > 0:
            target_enemy = sorted(enemies, key=self.distance_to_me)[0]
        return target_enemy

    def do_shoot(self, target_enemy: LivingUnit, me: Wizard, world: World, game: Game, move: Move):
        if target_enemy:
            enemy_distance = me.get_distance_to(target_enemy)
            enemy_angle = me.get_angle_to(target_enemy)
            staff_distance = game.staff_range + target_enemy.radius
            magic_missile_distance = me.cast_range

            if ~me.remaining_cooldown_ticks_by_action[ActionType.STAFF] and enemy_distance <= staff_distance:
                assert abs(enemy_angle) <= game.staff_sector / 2.0
                move.action = ActionType.STAFF
                self.log("staff")
            elif me.remaining_cooldown_ticks_by_action[ActionType.MAGIC_MISSILE] == 0:
                assert enemy_distance <= magic_missile_distance
                move.cast_angle = enemy_angle
                move.action = ActionType.MAGIC_MISSILE
                self.log("magic missile")
            else:
                self.log("recharge")


    ### BONUS ###

    def see_bonus(self, me: Wizard, world: World, game: Game, move: Move):
        target_bonus = None
        units = []
        units.extend(world.bonuses)

        bonuses = get_nearby_bonuses(units, me)
        if len(bonuses) > 0:
            target_bonus = sorted(bonuses, key=self.distance_to_me)[0]

        return target_bonus

    def go_to_bonus(self, bonus: Bonus, me: Wizard, world: World, game: Game, move: Move):
        assert isinstance(bonus, Bonus)
        self.go_to(bonus, me, world, game, move, check_angle=False)


    ### RETREAT ###

    def forced_to_retreat(self, bonus: Bonus, me: Wizard, world: World, game: Game, move: Move):
        life_score = me.life / me.max_life
        return life_score < 0.5

    def retreat(self, me: Wizard, world: World, game: Game, move: Move):
        previous_point = Point2D(0,0)
        self.go_to(previous_point, me, world, game, move, check_angle=False)


    ### FORWARD ###

    def can_go_forward(self, bonus: Bonus, me: Wizard, world: World, game: Game, move: Move):
        return True

    def go_forward(self, me: Wizard, world: World, game: Game, move: Move):
        next_point = Point2D(0, 0)
        self.go_to(next_point, me, world, game, move, check_angle=True)


    ### GO_TO ###

    def go_to_unit(self, unit: LivingUnit, me: Wizard, world: World, game: Game, move: Move, check_angle: bool):
        self.log("go_to_unit")

    def go_to_point(self, point: Point2D, me: Wizard, world: World, game: Game, move: Move, check_angle: bool):
        self.log("go_to_point")
