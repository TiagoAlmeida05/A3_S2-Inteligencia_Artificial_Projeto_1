from models import ProblemInstance, Solution
from solver_interface import Solver


class GeneticAlgorithmSolver(Solver):
    def solve(self, problem_instance: ProblemInstance) -> Solution:
        # Placeholder for future implementation.
        return Solution(assignments=[[] for _ in range(problem_instance.vehicle_count)])
