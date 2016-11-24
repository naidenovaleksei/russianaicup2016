import math

class Point2D:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def get_distance_to(self, x, y):
        return math.hypot(self.x - x, self.y - y)

    def get_distance_to_point(self, point):
        return self.get_distance_to(point.x, point.y)

    def get_distance_to_unit(self, unit):
        return self.get_distance_to(unit.x, unit.y)

    def get_angle_to(self, x, y, angle):
        absolute_angle_to = math.atan2(y - self.y, x - self.x)
        relative_angle_to = absolute_angle_to - angle

        while relative_angle_to > math.pi:
            relative_angle_to -= 2.0 * math.pi

        while relative_angle_to < -math.pi:
            relative_angle_to += 2.0 * math.pi

        return relative_angle_to

    def get_angle_to_point(self, point, angle):
        return self.get_angle_to(point.x, point.y, angle)

    def get_angle_to_unit(self, unit, angle):
        return self.get_angle_to(unit.x, unit.y, angle)
