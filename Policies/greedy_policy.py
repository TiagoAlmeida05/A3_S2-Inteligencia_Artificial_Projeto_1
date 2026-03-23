from simulation.car import Car
from simulation.sim import Simulation

class GreedyPolicy:
    def __init__(self, weights=None):
        if weights is None:
            weights = {
                "ride_distance": 2.0,
                "bonus": 5.0,
                "distance_to_start": 1.5,
                "waiting_time": 1.0,
                "slack": 0.1,
            }

        self.weights = weights

    def select_ride(self, sim, car):
        feasible = sim.get_feasible_rides(car)

        if not feasible:
            return None

        best_ride = None
        best_score = float("-inf")

        for ride in feasible:
            distance_to_start = sim.dist(car.x, car.y, ride.start[0], ride.start[1])
            arrival_time = car.time_available + distance_to_start
            start_time = max(arrival_time, ride.earliest)
            waiting_time = start_time - arrival_time
            finish_time = start_time + ride.distance
            slack = ride.latest - finish_time

            bonus = 1 if start_time == ride.earliest else 0

            score = (
                self.weights["ride_distance"] * ride.distance
                + self.weights["bonus"] * bonus
                - self.weights["distance_to_start"] * distance_to_start
                - self.weights["waiting_time"] * waiting_time
                - self.weights["slack"] * slack
            )

            if score > best_score:
                best_score = score
                best_ride = ride

        return best_ride