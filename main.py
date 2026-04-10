from simulation.parser import read_simulation_params, read_rides
from ui.pygame_ui import Visualizer
import math

from simulation.sim import Simulation
from Policies.greedy_policy import GreedyPolicy
from simulation.car import Car 
from simulation.ride import Ride

def main():
    while True:
        filename = input("Name of the dataset file: ")
        try:
            params = read_simulation_params(filename)
            raw_rides = read_rides(filename)
            print("Data loaded successfully!")
            break
        except FileNotFoundError:
            print(f"Error: Could not find '{filename}'. Try again.\n")


    rides = []
    for r in raw_rides:
        ride = Ride(r['id'], (r['start_r'], r['start_c']), (r['end_r'], r['end_c']), r['earliest'], r['latest'])
        rides.append(ride)
    fleet = []

    zone_cols = math.ceil(math.sqrt(params['F']))
    zone_rows = math.ceil(params['F'] / zone_cols)

    zone_w = params['C'] / zone_cols
    zone_h = params['R'] / zone_rows
    for f in range(params['F']):
        z_c = f % zone_cols
        z_r = f // zone_cols

        start_c = int((z_c + 0.5) * zone_w)
        start_r = int((z_r +0.5) * zone_h)

        car = Car(f, start_r, start_c)
        car.color = ((f * 60) % 255, (f * 100) % 255, (f * 140 + 100) % 255)
        fleet.append(car)
    
    sim = Simulation(
        rows = params['R'],
        cols = params['C'],
        bonus = params['B'],
        total_time = params['T'],
        cars = fleet,
        rides = rides
    )
    policy = GreedyPolicy()
    print("Running AI Logic...")
    while sim.step(policy):
        pass
    print(f"Simulation Finished! Final Score: {sim.current_score}")

    print("Starting visualizer...")
    ui = Visualizer(width = 800, height = 800)
    simulation_time = 0

    while True:
        running_score = 0
        messages = []

        for ride in sim.rides:
            if hasattr(ride, 'finish_time'):
                if simulation_time >= ride.finish_time:
                    running_score += ride.distance

                if simulation_time >= ride.pickup_time:
                    if ride.pickup_time == ride.earliest:
                        running_score += params["B"]

                if simulation_time == ride.finish_time:
                    messages.append({
                        "r": ride.end[0],
                        "c": ride.end[1],
                        "text": f"+{ride.distance}", "color": (100, 255, 100)
                    })

                if simulation_time == ride.pickup_time and ride.pickup_time == ride.earliest:
                    messages.append({
                        "r": ride.start[0],
                        "c": ride.start[1],
                        "text": f"BONUS +{params['B']}!", "color": (100, 255, 100)
                    })

        frame_state = {
            "rows": params['R'],
            "cols": params['C'],
            "current_step": simulation_time,
            "score": running_score,
            "vehicles": [],
            "unassigned_rides": [],
            "active_rides": [],
            "messages": messages
        }

        for car in sim.cars:
            if simulation_time < len(car.history):
                h_state = car.history[simulation_time]
            else:
                h_state = car.history[-1].copy()
                h_state["state"] = "idle"

            frame_state['vehicles'].append({
                "id": car.car_id, 
                "r": h_state["r"], 
                "c": h_state["c"], 
                "target_r": h_state.get("target_r", h_state["r"]),
                "target_c": h_state.get("target_c", h_state["c"]),
                "dest_r": h_state.get("dest_r"),
                "dest_c": h_state.get("dest_c"),
                "state": h_state["state"],
                "color": car.color
            })

        for ride in sim.rides:
            if not hasattr(ride, 'pickup_time') or simulation_time < ride.pickup_time:
                frame_state["unassigned_rides"].append({
                    "id": ride.ride_id,
                    "start_r": ride.start[0], 
                    "start_c": ride.start[1],
                    "end_r": ride.end[0],
                    "end_c": ride.end[1]
                })
            elif simulation_time < getattr(ride, 'finish_time', 0):
                frame_state["active_rides"].append({
                    "end_r": ride.end[0],
                    "end_c": ride.end[1]
                })

        action = ui.render(frame_state)

        if action == "FORWARD":
            if simulation_time < params['T']:
                simulation_time += 1
        elif action == "BACKWARD":
            if simulation_time > 0:
                simulation_time -= 1

if __name__ == "__main__":
    main()