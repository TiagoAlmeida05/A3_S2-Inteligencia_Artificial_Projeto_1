from parser import read_problem_instance
from simulation.car import Car
from simulation.ride import Ride
from simulation.sim import Simulation
from Policies.greedy_policy import GreedyPolicy
from ui.pygame_ui import Visualizer


def classify_ride(ride, simulation_time, total_time):
    if hasattr(ride, "finish_time") and simulation_time >= ride.finish_time:
        return "completed"
    if hasattr(ride, "pickup_time") and simulation_time >= ride.pickup_time:
        return "active"
    if hasattr(ride, "pickup_time") and simulation_time < ride.pickup_time:
        return "assigned"

    latest_possible_finish = min(ride.latest, total_time)
    if simulation_time + ride.distance > latest_possible_finish:
        return "expired"

    return "waiting"


def build_frame_state(sim, problem, simulation_time):
    running_score = 0
    running_bonus_count = 0
    messages = []
    rides_by_state = {
        "waiting": [],
        "assigned": [],
        "active": [],
        "completed": [],
        "expired": [],
    }

    for ride in sim.rides:
        if hasattr(ride, "finish_time"):
            if simulation_time >= ride.finish_time:
                running_score += ride.distance

            if simulation_time >= ride.pickup_time and ride.pickup_time == ride.earliest:
                running_score += problem.bonus
                running_bonus_count += 1

            if simulation_time == ride.finish_time:
                messages.append(
                    {
                        "r": ride.end[0],
                        "c": ride.end[1],
                        "text": f"+{ride.distance}",
                        "color": (100, 255, 100),
                    }
                )

            if simulation_time == ride.pickup_time and ride.pickup_time == ride.earliest:
                messages.append(
                    {
                        "r": ride.start[0],
                        "c": ride.start[1],
                        "text": f"BONUS +{problem.bonus}!",
                        "color": (100, 255, 100),
                    }
                )

        ride_status = classify_ride(ride, simulation_time, problem.total_time)
        rides_by_state[ride_status].append(
            {
                "id": ride.ride_id,
                "start_r": ride.start[0],
                "start_c": ride.start[1],
                "end_r": ride.end[0],
                "end_c": ride.end[1],
                "earliest": ride.earliest,
                "latest": ride.latest,
                "distance": ride.distance,
                "assigned": bool(getattr(ride, "assigned", False)),
                "pickup_time": getattr(ride, "pickup_time", None),
                "finish_time": getattr(ride, "finish_time", None),
                "status": ride_status,
            }
        )

    frame_state = {
        "rows": problem.rows,
        "cols": problem.cols,
        "current_step": simulation_time,
        "total_time": problem.total_time,
        "score": running_score,
        "bonus_count": running_bonus_count,
        "vehicles": [],
        "rides": rides_by_state,
        "messages": messages,
        "stats": {
            "vehicles_total": len(sim.cars),
            "rides_total": len(sim.rides),
            "rides_waiting": len(rides_by_state["waiting"]),
            "rides_assigned": len(rides_by_state["assigned"]),
            "rides_active": len(rides_by_state["active"]),
            "rides_completed": len(rides_by_state["completed"]),
            "rides_expired": len(rides_by_state["expired"]),
            "current_score": running_score,
            "bonus_count": running_bonus_count,
        },
    }

    for car in sim.cars:
        if simulation_time < len(car.history):
            h_state = car.history[simulation_time]
        else:
            h_state = car.history[-1].copy()
            h_state["state"] = "idle"

        frame_state["vehicles"].append(
            {
                "id": car.car_id,
                "r": h_state["r"],
                "c": h_state["c"],
                "target_r": h_state.get("target_r", h_state["r"]),
                "target_c": h_state.get("target_c", h_state["c"]),
                "dest_r": h_state.get("dest_r"),
                "dest_c": h_state.get("dest_c"),
                "state": h_state["state"],
                "assigned_count": len(car.assigned_rides),
                "time_available": car.time_available,
                "color": car.color,
            }
        )

    return frame_state


def build_simulation(problem):
    rides = [
        Ride(
            ride.ride_id,
            ride.start,
            ride.end,
            ride.earliest,
            ride.latest,
        )
        for ride in problem.rides
    ]

    fleet = []
    for vehicle_id, (start_r, start_c) in enumerate(problem.vehicle_starts):
        car = Car(vehicle_id, start_r, start_c)
        car.color = ((vehicle_id * 60) % 255, (vehicle_id * 100) % 255, (vehicle_id * 140 + 100) % 255)
        fleet.append(car)

    return Simulation(
        rows=problem.rows,
        cols=problem.cols,
        bonus=problem.bonus,
        total_time=problem.total_time,
        cars=fleet,
        rides=rides,
    )


def main():
    while True:
        filename = input("Name of the dataset file: ").strip()
        try:
            problem = read_problem_instance(filename)
            print("Data loaded successfully!")
            break
        except FileNotFoundError:
            print(f"Error: Could not find '{filename}'. Try again.\n")

    sim = build_simulation(problem)

    policy = GreedyPolicy()
    print("Running AI Logic...")
    while sim.step(policy):
        pass
    print(f"Simulation Finished! Final Score: {sim.current_score}")

    print("Starting visualizer...")
    ui = Visualizer(width=1200, height=820)
    simulation_time = 0

    while True:
        frame_state = build_frame_state(sim, problem, simulation_time)
        action = ui.render(frame_state)

        if action == "FORWARD":
            if simulation_time < problem.total_time:
                simulation_time += 1
        elif action == "BACKWARD":
            if simulation_time > 0:
                simulation_time -= 1
        elif action == "RESET":
            simulation_time = 0

if __name__ == "__main__":
    main()