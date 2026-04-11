from dataclasses import dataclass

from models import ProblemInstance, Solution
from scheduler import apply_assignment, create_vehicles, estimate_assignment


@dataclass(frozen=True)
class ScoreBreakdown:
    total_score: int
    completed_rides: int
    bonus_count: int
    invalid_assignments: int


def score_solution(problem: ProblemInstance, solution: Solution) -> ScoreBreakdown:
    vehicles = create_vehicles(problem)
    rides_by_id = {ride.ride_id: ride for ride in problem.rides}

    total_score = 0
    completed_rides = 0
    bonus_count = 0
    invalid_assignments = 0
    used_ride_ids = set()

    for vehicle_id, assigned_ride_ids in enumerate(solution.assignments):
        if vehicle_id >= len(vehicles):
            invalid_assignments += len(assigned_ride_ids)
            continue

        vehicle = vehicles[vehicle_id]
        for ride_id in assigned_ride_ids:
            if ride_id in used_ride_ids or ride_id not in rides_by_id:
                invalid_assignments += 1
                continue

            ride = rides_by_id[ride_id]
            estimate = estimate_assignment(vehicle, ride, problem.total_time)

            # Output scoring should always advance vehicle timeline along the submitted route.
            apply_assignment(vehicle, ride, estimate)
            used_ride_ids.add(ride_id)

            if estimate.feasible:
                total_score += ride.distance
                completed_rides += 1
                if estimate.start_time == ride.earliest:
                    total_score += problem.bonus
                    bonus_count += 1

    return ScoreBreakdown(
        total_score=total_score,
        completed_rides=completed_rides,
        bonus_count=bonus_count,
        invalid_assignments=invalid_assignments,
    )
