from .car import Car
from .ride import Ride

class Simulation:
    def __init__(self, rows, cols, bonus, total_time, cars, rides):
        self.rides = rides
        self.rows = rows
        self.cols = cols
        self.bonus = bonus
        self.total_time = total_time
        self.cars = cars    #List of cars
        self.rides = rides  #List of rides

        self.current_score = 0
        self.completed_rides = 0

    def dist (self,x1,y1,x2,y2):
        return abs(x1-x2) + abs(y1-y2)
    
    def get_feasible_rides(self, car):
        feasible = []

        for ride in self.rides:
            if ride.assigned:
                continue

            distance_to_start = self.dist(car.x,car.y,ride.start[0],ride.start[1])

            arrival_time = car.time_available + distance_to_start

            actual_start = max(arrival_time, ride.earliest)

            finish_time = actual_start + ride.distance

            if finish_time <= ride.latest and finish_time <= self.total_time:
                feasible.append(ride)
        
        return feasible

    def apply_ride (self, car, ride):

        distance_to_start = self.dist(car.x,car.y,ride.start[0],ride.start[1])

        arrival_time = car.time_available + distance_to_start

        start_time = max(arrival_time, ride.earliest)

        waiting_time = start_time - arrival_time

        finish_time = start_time + ride.distance

        if finish_time > ride.latest or finish_time > self.total_time:
            raise ValueError(
                f"Ride {ride.ride_id} not feasible for car {car.car_id}: "
                f"finish_time={finish_time}, latest={ride.latest}, T={self.total_time}"
            )
        
        self.current_score += ride.distance

        got_bonus = (start_time == ride.earliest)
        if got_bonus:
            self.current_score += self.bonus

        car.x = ride.end[0]
        car.y = ride.end[1]
        car.time_available = finish_time
        car.assigned_rides.append(ride.ride_id)

        ride.assigned = True
        self.completed_rides += 1

        return {
            "distance_to_start": distance_to_start,
            "arrival_time": arrival_time,
            "waiting_time": waiting_time,
            "start_time": start_time,
            "finish_time": finish_time,
            "got_bonus": got_bonus,
        }

    def step(self, policy):
        any_assigned = False

        for car in self.cars:
            feasible = self.get_feasible_rides(car)
            if not feasible:
                continue

            ride = policy.select_ride(self, car)
            if ride is None:
                continue

            if ride.assigned:
                continue

            self.apply_ride(car, ride)
            any_assigned = True

        return any_assigned
