from models import ProblemInstance, Ride


def _build_vehicle_starts(rows: int, cols: int, vehicle_count: int):
    # Hash Code 2018 rule: all vehicles start at (0, 0).
    return [(0, 0) for _ in range(vehicle_count)]


def read_problem_instance(filepath: str) -> ProblemInstance:
    with open(filepath, "r", encoding="utf-8") as file:
        first_line = file.readline().strip()
        values = list(map(int, first_line.split()))

        rows, cols, vehicle_count, ride_count, bonus, total_time = values

        rides = []
        for line in file:
            parts = line.strip().split()
            if not parts:
                continue

            a, b, x, y, s, f = map(int, parts)
            rides.append(
                Ride(
                    ride_id=len(rides),
                    start=(a, b),
                    end=(x, y),
                    earliest=s,
                    latest=f,
                )
            )

    return ProblemInstance(
        rows=rows,
        cols=cols,
        vehicle_count=vehicle_count,
        ride_count=ride_count,
        bonus=bonus,
        total_time=total_time,
        rides=rides,
        vehicle_starts=_build_vehicle_starts(rows, cols, vehicle_count),
    )
