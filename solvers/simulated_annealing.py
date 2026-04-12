import math
import random
from typing import Callable, Dict, Optional, Tuple

from models import ProblemInstance, Solution
from scoring import score_solution
from solvers.greedy_solver import GreedySolver
from solvers.hill_climbing import HillClimbingSolver
from solver_interface import Solver


class SimulatedAnnealingSolver(Solver):
    def __init__(
        self,
        max_iterations: int = 300,
        initial_temperature: float = 1000.0,
        cooling_rate: float = 0.995,
        min_temperature: float = 0.1,
        neighborhood_size: int = 10,
        random_seed: Optional[int] = None,
        progress_callback: Optional[Callable[[Dict[str, float]], None]] = None,
    ):
        self.max_iterations = max_iterations
        self.initial_temperature = initial_temperature
        self.cooling_rate = cooling_rate
        self.min_temperature = min_temperature
        self.neighborhood_size = neighborhood_size
        self.random_seed = random_seed
        self.progress_callback = progress_callback

        self.last_initial_score = None
        self.last_final_score = None

        # Reuse neighborhood and assignment utility logic from hill climbing.
        self._hc_helper = HillClimbingSolver(neighborhood_size=neighborhood_size)

    def solve(self, problem_instance: ProblemInstance) -> Solution:
        rng = random.Random(self.random_seed)

        initial_solution = GreedySolver().solve(problem_instance)
        current_assignments = self._hc_helper._normalize_assignments(
            initial_solution.assignments,
            vehicle_count=problem_instance.vehicle_count,
            ride_count=problem_instance.ride_count,
        )

        current_score = self._score_tuple(problem_instance, current_assignments)
        best_assignments = self._hc_helper._copy_assignments(current_assignments)
        best_score = current_score
        self.last_initial_score = current_score[0]

        total_neighbors_generated = 0
        total_valid_candidates = 0
        total_accepted_moves = 0
        total_improving_moves = 0

        temperature = max(self.initial_temperature, self.min_temperature)

        self._emit_progress(
            {
                "event": "start",
                "iteration": 0,
                "initial_greedy_score": float(current_score[0]),
                "current_score": float(current_score[0]),
                "best_score": float(best_score[0]),
                "temperature": float(temperature),
                "neighbors_generated": 0.0,
                "valid_candidates": 0.0,
                "accepted_moves": 0.0,
                "improving_moves": 0.0,
            }
        )

        iteration = 0
        while iteration < self.max_iterations and temperature > self.min_temperature:
            iteration += 1

            neighbors, generated_count = self._hc_helper._generate_neighbors(current_assignments, rng)
            total_neighbors_generated += generated_count
            total_valid_candidates += len(neighbors)

            if not neighbors:
                temperature = max(temperature * self.cooling_rate, self.min_temperature)
                self._emit_progress(
                    {
                        "event": "iteration",
                        "iteration": float(iteration),
                        "initial_greedy_score": float(self.last_initial_score),
                        "current_score": float(current_score[0]),
                        "best_score": float(best_score[0]),
                        "temperature": float(temperature),
                        "neighbors_generated": float(generated_count),
                        "valid_candidates": float(len(neighbors)),
                        "accepted_moves": float(total_accepted_moves),
                        "improving_moves": float(total_improving_moves),
                    }
                )
                continue

            scored_neighbors = []
            for candidate_assignments in neighbors:
                candidate_score = self._score_tuple(problem_instance, candidate_assignments)
                scored_neighbors.append((candidate_score, candidate_assignments))
            scored_neighbors.sort(key=lambda item: item[0], reverse=True)

            top_k = min(3, len(scored_neighbors))
            selected_score, selected_assignments = rng.choice(scored_neighbors[:top_k])

            delta = selected_score[0] - current_score[0]
            accept = False
            if delta >= 0:
                accept = True
            else:
                acceptance_probability = math.exp(delta / max(temperature, 1e-12))
                if rng.random() < acceptance_probability:
                    accept = True

            if accept:
                current_assignments = selected_assignments
                current_score = selected_score
                total_accepted_moves += 1

            if current_score > best_score:
                best_score = current_score
                best_assignments = self._hc_helper._copy_assignments(current_assignments)
                total_improving_moves += 1

            temperature = max(temperature * self.cooling_rate, self.min_temperature)

            self._emit_progress(
                {
                    "event": "iteration",
                    "iteration": float(iteration),
                    "initial_greedy_score": float(self.last_initial_score),
                    "current_score": float(current_score[0]),
                    "best_score": float(best_score[0]),
                    "temperature": float(temperature),
                    "neighbors_generated": float(generated_count),
                    "valid_candidates": float(len(neighbors)),
                    "accepted_moves": float(total_accepted_moves),
                    "improving_moves": float(total_improving_moves),
                }
            )

        if self._hc_helper._has_duplicate_rides(best_assignments):
            best_assignments = self._hc_helper._normalize_assignments(
                best_assignments,
                vehicle_count=problem_instance.vehicle_count,
                ride_count=problem_instance.ride_count,
            )

        self.last_final_score = best_score[0]
        self._emit_progress(
            {
                "event": "final",
                "iteration": float(iteration),
                "initial_greedy_score": float(self.last_initial_score),
                "current_score": float(current_score[0]),
                "best_score": float(best_score[0]),
                "temperature": float(temperature),
                "final_score": float(best_score[0]),
                "neighbors_generated": float(total_neighbors_generated),
                "valid_candidates": float(total_valid_candidates),
                "accepted_moves": float(total_accepted_moves),
                "improving_moves": float(total_improving_moves),
            }
        )

        return Solution(assignments=best_assignments)

    def _score_tuple(
        self,
        problem_instance: ProblemInstance,
        assignments,
    ) -> Tuple[int, int, int, int]:
        breakdown = score_solution(problem_instance, Solution(assignments=assignments))
        return (
            breakdown.total_score,
            breakdown.completed_rides,
            breakdown.bonus_count,
            -breakdown.invalid_assignments,
        )

    def _emit_progress(self, payload: Dict[str, float]) -> None:
        if self.progress_callback is not None:
            self.progress_callback(payload)
