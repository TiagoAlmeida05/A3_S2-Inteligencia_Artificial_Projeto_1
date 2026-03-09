from simulation.car import Car
from simulation.sim import Simulation
import random

class RandomPolicy:
    def select_ride(self,sim,car):
        feasible = sim.get_feasible_rides(car)
        if not feasible:
            return None
        return random.choice(feasible)