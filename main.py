from simulation.parser import read_simulation_params, read_rides
from ui.pygame_ui import Visualizer

def main():
    while True:
        filename = input("Name of the dataset file: ")
        try:
            params = read_simulation_params(filename)
            rides = read_rides(filename)
            print("Data loaded successfully!")
            break
        except FileNotFoundError:
            print(f"Error: Could not find '{filename}'. Try again.\n")

    fleet = []
    for f in range(params['F']):
        color = ((f*60) % 255, (f*100) % 255, (f * 140 + 100) % 255)
        fleet.append({
            "id": f,
            "r": 0,
            "c": 0,
            "color": color
        })
    
    initial_state = {
        "rows": params['R'],
        "cols": params['C'],
        "current_step": 0,
        "score": 0,
        "vehicles": fleet,
        "unassigned_rides": rides
    }

    print("Starting visualizer...")
    ui = Visualizer(width = 800, height = 800)

    while True:
        ui.render(initial_state)

if __name__ == "__main__":
    main()