class Ride:
    def __init__(self, ride_id, start, end, earliest, latest):
        self.ride_id = ride_id
        self.start = start
        self.end = end
        self.earliest = earliest
        self.latest = latest
        self.assigned = False
        self.distance = abs(start[0] - end[0]) + abs(start[1] - end[1])