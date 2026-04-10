class Car:
    def __init__(self, car_id, x=0, y=0):
        self.car_id = car_id
        self.x = x
        self.y = y
        self.time_available = 0
        self.assigned_rides = []

        self.history = [{
            "r": x,
            "c": y,
            "target_r": x,
            "target_c": y,
            "state": "idle"
        }]

    def move_to(self, x, y, travel_time):
        self.x = x
        self.y = y
        self.time_available += travel_time

    def dist_to(self, x, y):
        return abs(self.x - x) + abs(self.y - y)
