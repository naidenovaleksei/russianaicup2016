import numpy as np

from Points2D import Point2D

from model.Game import Game
from model.Wizard import Wizard
from model.LaneType import LaneType as LineType

WAYPOINT_RADIUS = 100.00

def create_front_paths(map_size):
    return {
        LineType.TOP: [
            Point2D(100.0, map_size - 100.0),
            Point2D(100.0, map_size - 400.0),
            Point2D(200.0, map_size * 0.8),
            Point2D(200.0, map_size * 0.6),
            Point2D(200.0, map_size * 0.4),
            Point2D(200.0, map_size * 0.2),
            Point2D(400.0, 400.0),
            Point2D(map_size * 0.2, 200.0),
            Point2D(map_size * 0.4, 200.0),
            Point2D(map_size * 0.6, 200.0),
            Point2D(map_size * 0.8, 200.0),
            Point2D(map_size - 200.0, 200.0)
        ],
        LineType.MIDDLE: [
            Point2D(100.0, map_size - 100.0),
            np.random.choice([Point2D(600.0, map_size - 200.0), Point2D(200.0, map_size - 600.0)]),
            Point2D(800.0, map_size - 800.0),
            Point2D(1600.0, map_size - 1600.0),
            Point2D(2000.0, map_size - 2000.0),
            Point2D(2400.0, map_size - 2400.0),
            Point2D(map_size - 600.0, 600.0)
        ],
        LineType.BOTTOM: [
            Point2D(100.0, map_size - 100.0),
            Point2D(400.0, map_size - 100.0),
            Point2D(map_size * 0.2, map_size - 200.0),
            Point2D(map_size * 0.4, map_size - 200.0),
            Point2D(map_size * 0.6, map_size - 200.0),
            Point2D(map_size * 0.8, map_size - 200.0),
            Point2D(map_size - 400.0, map_size - 400.0),
            Point2D(map_size - 200.0, map_size * 0.8),
            Point2D(map_size - 200.0, map_size * 0.6),
            Point2D(map_size - 200.0, map_size * 0.4),
            Point2D(map_size - 200.0, map_size * 0.2),
            Point2D(map_size - 200.0, 200.0)
        ]
    }

def create_bonus_path(map_size):
    return {
        0: [
            Point2D(200.0, 200.0),
            Point2D(600.0, 600.0),
            Point2D(800.0, 800.0),
            Point2D(1200.0, 1200.0)
        ],
        1: [
            Point2D(2000.0, 2000.0),
            Point2D(1800.0, 1800.0),
            Point2D(1600.0, 1600.0),
            Point2D(1200.0, 1200.0)
        ],
        2:[
            Point2D(2000.0, 2000.0),
            Point2D(map_size - 1800.0, map_size - 1800.0),
            Point2D(map_size - 1600.0, map_size - 1600.0),
            Point2D(map_size - 1200.0, map_size - 1200.0)
        ],
        3: [
            Point2D(map_size - 200.0, map_size - 200.0),
            Point2D(map_size - 600.0, map_size - 600.0),
            Point2D(map_size - 800.0, map_size - 800.0),
            Point2D(map_size - 1200.0, map_size - 1200.0)
        ]
    }

def get_linetype_to_id(id):
    if 0 < id <= 10:
        return {
            1: LineType.TOP,
            2: LineType.TOP,
            3: LineType.MIDDLE,
            4: LineType.BOTTOM,
            5: LineType.BOTTOM,
            6: LineType.TOP,
            7: LineType.TOP,
            8: LineType.MIDDLE,
            9: LineType.BOTTOM,
            10: LineType.BOTTOM
        }[id]
    else:
        return LineType.MIDDLE


class TilesMap:
    def __init__(self, game: Game):
        self.create_map(game)

    def _create_map(self, game: Game):
        map_size = self.map_size = game.map_size
        assert map_size == 4000
        self.front_paths = create_front_paths(map_size)
        self.bonus_path = create_bonus_path(map_size)

    def _get_waypoints_by_id(self, id):
        return self._get_waypoints_by_linetype(get_linetype_to_id(id))

    def _get_waypoints_by_linetype(self, line_type: LineType):
        return self.front_paths[line_type]

    def get_next_waypoint(self, me: Wizard):
        waypoints = self._get_waypoints_by_id(me.id)
        return self._get_next_of_waypoints(waypoints, me)

    def get_prev_waypoint(self, me: Wizard):
        waypoints = self._get_waypoints_by_id(me.id)
        return self._get_next_of_waypoints(waypoints[::-1], me)

    # kost'il
    def _get_next_of_waypoints(self, waypoints, me: Wizard):
        last_waypoint = waypoints[-1]
        for i, waypoint in enumerate(waypoints[:-1]):
            if waypoint.get_distance_to_unit(me) <= WAYPOINT_RADIUS:
                return waypoints[i + 1]
            if last_waypoint.get_distance_to_point(waypoint) < last_waypoint.get_distance_to_unit(me):
                return waypoint
        return last_waypoint

    def get_next_waypoint_to_bonus(self, me: Wizard):
        sum_pos = me.x + me.y
        if sum_pos <= 1200.0:
            waypoints = self.bonus_path[0]
        elif sum_pos <= 2000.0:
            waypoints = self.bonus_path[1]
        elif sum_pos <= 2800.0:
            waypoints = self.bonus_path[2]
        else:
            waypoints = self.bonus_path[3]
        return self._get_next_of_waypoints(waypoints, me)


