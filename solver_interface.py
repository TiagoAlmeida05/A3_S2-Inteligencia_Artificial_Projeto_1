from abc import ABC, abstractmethod

from models import ProblemInstance, Solution


class Solver(ABC):
    @abstractmethod
    def solve(self, problem_instance: ProblemInstance) -> Solution:
        raise NotImplementedError
