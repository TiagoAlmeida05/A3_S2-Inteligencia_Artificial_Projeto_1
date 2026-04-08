def read_simulation_params(filepath):
    with open(filepath, 'r') as file:
        first_line = file.readline().strip()

    values = list(map(int, first_line.split()))

    return {
        'R': values[0], # rows
        'C': values[1], # columns
        'F': values[2], # vehicles
        'N': values[3], # number of rides
        'B': values[4], # per-ride bonus
        'T': values[5], # steps in the simulation
    }

def read_rides(filepath):
    rides = []
    with open(filepath, 'r') as file:
        next(file)
        for ride_id, line in enumerate(file):
            parts = line.strip().split()

            if not parts:
                continue

            a = int(parts[0]) # start row
            b = int(parts[1]) # start col
            x = int(parts[2]) # end row
            y = int(parts[3]) # end col
            s = int(parts[4]) # earliest start
            f = int(parts[5]) # latest finish

            ride_data = {
                "id": ride_id,
                "start_r": a,
                "start_c": b,
                "end_r": x,
                "end_c": y,
                "earliest": s,
                "latest": f
            }

            rides.append(ride_data)

    return rides