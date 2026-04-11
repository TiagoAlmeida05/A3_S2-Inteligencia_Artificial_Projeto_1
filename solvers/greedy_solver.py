from models import ProblemInstance, Solution
from scheduler import apply_assignment, create_vehicles, estimate_assignment
from solver_interface import Solver


class GreedySolver(Solver):
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

    def solve(self, problem_instance: ProblemInstance) -> Solution:
        vehicles = create_vehicles(problem_instance)
        rides_by_id = {ride.ride_id: ride for ride in problem_instance.rides}
        unassigned = set(rides_by_id.keys())

        assignments = [[] for _ in range(problem_instance.vehicle_count)]

        any_assigned = True
        while any_assigned:
            any_assigned = False

            for vehicle in vehicles:
                best_ride_id = None
                best_score = float("-inf")
                best_estimate = None

                for ride_id in unassigned:
                    ride = rides_by_id[ride_id]
                    estimate = estimate_assignment(vehicle, ride, problem_instance.total_time)
                    if not estimate.feasible:
                        continue

                    slack = ride.latest - estimate.finish_time
                    bonus = 1 if estimate.start_time == ride.earliest else 0

                    score = (
                        self.weights["ride_distance"] * ride.distance
                        + self.weights["bonus"] * bonus
                        - self.weights["distance_to_start"] * estimate.distance_to_start
                        - self.weights["waiting_time"] * estimate.waiting_time
                        - self.weights["slack"] * slack
                    )

                    if score > best_score:
                        best_score = score
                        best_ride_id = ride_id
                        best_estimate = estimate

                if best_ride_id is None:
                    continue

                best_ride = rides_by_id[best_ride_id]
                apply_assignment(vehicle, best_ride, best_estimate)
                assignments[vehicle.vehicle_id].append(best_ride_id)
                unassigned.remove(best_ride_id)
                any_assigned = True

        return Solution(assignments=assignments)
