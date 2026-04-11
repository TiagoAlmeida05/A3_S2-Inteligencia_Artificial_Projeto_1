from dataclasses import dataclass
from typing import List

from models import ProblemInstance, Ride, Vehicle


@dataclass(frozen=True)
class AssignmentEstimate:
    distance_to_start: int
    arrival_time: int
    start_time: int
    waiting_time: int
    finish_time: int
    feasible: bool


def manhattan_distance(r1: int, c1: int, r2: int, c2: int) -> int:
    return abs(r1 - r2) + abs(c1 - c2)


def create_vehicles(problem: ProblemInstance) -> List[Vehicle]:
    vehicles = []
    for vehicle_id in range(problem.vehicle_count):
        # Assignment rule fallback: vehicles start at (0, 0).
        if vehicle_id < len(problem.vehicle_starts):
            start_r, start_c = problem.vehicle_starts[vehicle_id]
        else:
            start_r, start_c = 0, 0
        vehicles.append(Vehicle(vehicle_id=vehicle_id, row=start_r, col=start_c))
    return vehicles


def estimate_assignment(vehicle: Vehicle, ride: Ride, total_time: int) -> AssignmentEstimate:
    distance_to_start = manhattan_distance(vehicle.row, vehicle.col, ride.start[0], ride.start[1])
    arrival_time = vehicle.time_available + distance_to_start
    start_time = max(arrival_time, ride.earliest)
    waiting_time = start_time - arrival_time
    finish_time = start_time + ride.distance
    feasible = finish_time <= ride.latest and finish_time <= total_time

    return AssignmentEstimate(
        distance_to_start=distance_to_start,
        arrival_time=arrival_time,
        start_time=start_time,
        waiting_time=waiting_time,
        finish_time=finish_time,
        feasible=feasible,
    )


def apply_assignment(vehicle: Vehicle, ride: Ride, estimate: AssignmentEstimate) -> None:
    vehicle.row = ride.end[0]
    vehicle.col = ride.end[1]
    vehicle.time_available = estimate.finish_time
    vehicle.assigned_rides.append(ride.ride_id)
