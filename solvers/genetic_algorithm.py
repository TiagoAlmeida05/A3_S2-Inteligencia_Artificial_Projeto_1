import random
from typing import List, Tuple, Optional

from models import ProblemInstance, Solution
from solver_interface import Solver
from scoring import score_solution
from solvers.greedy_solver import GreedySolver
from solvers.hill_climbing import HillClimbingSolver


class GeneticAlgorithmSolver(Solver):
    def __init__(
        self,
        population_size: int = 30,
        generations: int = 80,
        crossover_rate: float = 0.7,
        mutation_rate: float = 0.3,
        elite_count: int = 2,
        random_seed: Optional[int] = None,
    ):
        self.population_size = population_size
        self.generations = generations
        self.crossover_rate = crossover_rate
        self.mutation_rate = mutation_rate
        self.elite_count = elite_count
        self.random_seed = random_seed
        self._hc_helper = HillClimbingSolver(neighborhood_size=10)


    def solve(self, problem_instance: ProblemInstance) -> Solution:
        rng = random.Random(self.random_seed)
        vehicle_count = problem_instance.vehicle_count
        ride_count = problem_instance.ride_count

        population = []
        greedy_assignments = GreedySolver().solve(problem_instance).assignments
        population.append(self._normalize(greedy_assignments, vehicle_count, ride_count))
        
        for _ in range(self.population_size - 1):
            assignments = self._random_solution(vehicle_count, ride_count, rng)
            population.append(self._normalize(assignments, vehicle_count, ride_count))

        pop_with_fitness = [(ind, self._fitness(problem_instance, ind)) for ind in population]

        for gen in range(self.generations):
            pop_with_fitness.sort(key=lambda x: x[1], reverse=True)
            new_pop_with_fitness = pop_with_fitness[:self.elite_count]

            adaptive_mutation_rate = self.mutation_rate * (1 - gen / self.generations)

            while len(new_pop_with_fitness) < self.population_size:
                parent1 = self._tournament_selection(pop_with_fitness, rng)
                parent2 = self._tournament_selection(pop_with_fitness, rng)
                if rng.random() < self.crossover_rate:
                    child = self._crossover(parent1, parent2, rng, ride_count, vehicle_count)
                else:
                    child = [route.copy() for route in parent1]
                if rng.random() < adaptive_mutation_rate:
                    child = self._mutate(child, rng)
                child = self._normalize(child, vehicle_count, ride_count)
                child_fitness = self._fitness(problem_instance, child)
                new_pop_with_fitness.append((child, child_fitness))
            pop_with_fitness = new_pop_with_fitness

        best_ind, best_fitness = max(pop_with_fitness, key=lambda x: x[1])
        return Solution(assignments=best_ind)

    def _fitness(self, problem_instance: ProblemInstance, assignments: List[List[int]]) -> int:
        return score_solution(problem_instance, Solution(assignments=assignments)).total_score

    def _random_solution(self, vehicle_count: int, ride_count: int, rng: random.Random) -> List[List[int]]:
        rides = list(range(ride_count))
        rng.shuffle(rides)
        assignments = [[] for _ in range(vehicle_count)]
        for idx, ride_id in enumerate(rides):
            assignments[idx % vehicle_count].append(ride_id)
        return assignments

    def _tournament_selection(self, pop_with_fitness, rng: random.Random, k: int = 3) -> List[List[int]]:
        selected = rng.sample(pop_with_fitness, k)
        selected.sort(key=lambda x: x[1], reverse=True)
        return [route.copy() for route in selected[0][0]]

    def _crossover(self, parent1: List[List[int]], parent2: List[List[int]], rng: random.Random, ride_count: int, vehicle_count: int) -> List[List[int]]:
        child = []
        assigned = set()
        for v in range(vehicle_count):
            if rng.random() < 0.5:
                route = [r for r in parent1[v] if r not in assigned]
            else:
                route = [r for r in parent2[v] if r not in assigned]
            assigned.update(route)
            child.append(route)
            
        return child

    def _mutate(self, assignments: List[List[int]], rng: random.Random) -> List[List[int]]:
        move_type = rng.choices(["move", "swap", "reorder"], weights=[0.5, 0.3, 0.2])[0]
        if move_type == "move":
            updated = self._hc_helper._neighbor_move(assignments, rng)
        elif move_type == "swap":
            updated = self._hc_helper._neighbor_swap(assignments, rng)
        else:
            updated = self._hc_helper._neighbor_reorder(assignments, rng)
        return updated if updated is not None else assignments

    def _normalize(self, assignments: List[List[int]], vehicle_count: int, ride_count: int) -> List[List[int]]:
        return self._hc_helper._normalize_assignments(assignments, vehicle_count, ride_count)
