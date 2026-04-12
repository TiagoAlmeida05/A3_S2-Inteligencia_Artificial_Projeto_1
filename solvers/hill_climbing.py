import random
from typing import Callable, Dict, List, Optional, Tuple

from models import ProblemInstance, Solution
from scoring import score_solution
from solvers.greedy_solver import GreedySolver
from solver_interface import Solver


class HillClimbingSolver(Solver):
    def __init__(
        self,
        max_iterations: int = 300,
        max_no_improve: int = 60,
        neighborhood_size: int = 10,
        restarts: int = 1,
        random_seed: Optional[int] = None,
        progress_callback: Optional[Callable[[Dict[str, float]], None]] = None,
    ):
        self.max_iterations = max_iterations
        self.max_no_improve = max_no_improve
        self.neighborhood_size = neighborhood_size
        self.restarts = max(1, restarts)
        self.random_seed = random_seed
        self.progress_callback = progress_callback
        self.last_initial_score = None
        self.last_final_score = None

        self._problem: Optional[ProblemInstance] = None
        self._rides_by_id: Dict[int, object] = {}

    def solve(self, problem_instance: ProblemInstance) -> Solution:
        rng = random.Random(self.random_seed)
        self._problem = problem_instance
        self._rides_by_id = {ride.ride_id: ride for ride in problem_instance.rides}

        initial_solution = GreedySolver().solve(problem_instance)
        base_assignments = self._normalize_assignments(
            initial_solution.assignments,
            vehicle_count=problem_instance.vehicle_count,
            ride_count=problem_instance.ride_count,
        )

        base_score = self._score_tuple(problem_instance, base_assignments)
        self.last_initial_score = base_score[0]

        best_assignments = self._copy_assignments(base_assignments)
        best_score = base_score

        total_neighbors_generated = 0
        total_valid_candidates = 0
        total_accepted_moves = 0
        total_improving_moves = 0

        self._emit_progress(
            {
                "event": "start",
                "iteration": 0,
                "initial_greedy_score": base_score[0],
                "current_best_score": best_score[0],
                "no_improve": 0,
                "neighbors_generated": 0,
                "valid_candidates": 0,
                "accepted_moves": 0,
                "improving_moves": 0,
            }
        )

        global_iteration = 0
        for restart in range(self.restarts):
            if restart == 0:
                current_assignments = self._copy_assignments(base_assignments)
            else:
                current_assignments = self._perturb_assignments(best_assignments, rng)

            current_score = self._score_tuple(problem_instance, current_assignments)
            no_improve = 0

            for _ in range(self.max_iterations):
                global_iteration += 1
                candidates, generated_count = self._generate_neighbors(current_assignments, rng)
                total_neighbors_generated += generated_count
                total_valid_candidates += len(candidates)

                iteration_best_assignments = None
                iteration_best_score = current_score
                for candidate in candidates:
                    candidate_score = self._score_tuple(problem_instance, candidate)
                    if candidate_score > iteration_best_score:
                        iteration_best_score = candidate_score
                        iteration_best_assignments = candidate

                if iteration_best_assignments is None:
                    no_improve += 1
                    self._emit_progress(
                        {
                            "event": "iteration",
                            "iteration": global_iteration,
                            "restart": restart,
                            "initial_greedy_score": self.last_initial_score,
                            "current_best_score": best_score[0],
                            "no_improve": no_improve,
                            "neighbors_generated": generated_count,
                            "valid_candidates": len(candidates),
                            "accepted_moves": total_accepted_moves,
                            "improving_moves": total_improving_moves,
                        }
                    )
                    if no_improve >= self.max_no_improve:
                        break
                    continue

                current_assignments = iteration_best_assignments
                current_score = iteration_best_score
                total_accepted_moves += 1

                if current_score > best_score:
                    total_improving_moves += 1
                    best_score = current_score
                    best_assignments = self._copy_assignments(current_assignments)
                    no_improve = 0
                else:
                    no_improve += 1

                self._emit_progress(
                    {
                        "event": "iteration",
                        "iteration": global_iteration,
                        "restart": restart,
                        "initial_greedy_score": self.last_initial_score,
                        "current_best_score": best_score[0],
                        "no_improve": no_improve,
                        "neighbors_generated": generated_count,
                        "valid_candidates": len(candidates),
                        "accepted_moves": total_accepted_moves,
                        "improving_moves": total_improving_moves,
                    }
                )

                if no_improve >= self.max_no_improve:
                    break

        if self._has_duplicate_rides(best_assignments):
            best_assignments = self._normalize_assignments(
                best_assignments,
                vehicle_count=problem_instance.vehicle_count,
                ride_count=problem_instance.ride_count,
            )

        self._emit_progress(
            {
                "event": "final",
                "iteration": global_iteration,
                "initial_greedy_score": self.last_initial_score,
                "current_best_score": best_score[0],
                "no_improve": 0,
                "final_score": best_score[0],
                "neighbors_generated": total_neighbors_generated,
                "valid_candidates": total_valid_candidates,
                "accepted_moves": total_accepted_moves,
                "improving_moves": total_improving_moves,
            }
        )
        self.last_final_score = best_score[0]

        return Solution(assignments=best_assignments)

    def _emit_progress(self, payload: Dict[str, float]) -> None:
        if self.progress_callback is not None:
            self.progress_callback(payload)

    def _score_tuple(
        self,
        problem_instance: ProblemInstance,
        assignments: List[List[int]],
    ) -> Tuple[int, int, int, int]:
        breakdown = score_solution(problem_instance, Solution(assignments=assignments))
        return (
            breakdown.total_score,
            breakdown.completed_rides,
            breakdown.bonus_count,
            -breakdown.invalid_assignments,
        )

    def _generate_neighbors(
        self,
        assignments: List[List[int]],
        rng: random.Random,
    ) -> Tuple[List[List[List[int]]], int]:
        neighbors = []
        attempts = 0
        max_attempts = max(self.neighborhood_size * 6, 20)

        while len(neighbors) < self.neighborhood_size and attempts < max_attempts:
            attempts += 1
            move_type = rng.choices(
                population=("move", "reorder", "swap"),
                weights=(0.5, 0.3, 0.2),
                k=1,
            )[0]

            if move_type == "move":
                candidate = self._neighbor_move(assignments, rng)
            elif move_type == "swap":
                candidate = self._neighbor_swap(assignments, rng)
            else:
                candidate = self._neighbor_reorder(assignments, rng)

            if candidate is not None:
                neighbors.append(candidate)

        return neighbors, attempts

    def _neighbor_move(
        self,
        assignments: List[List[int]],
        rng: random.Random,
    ) -> Optional[List[List[int]]]:
        source_vehicles = [idx for idx, route in enumerate(assignments) if route]
        if not source_vehicles or len(assignments) < 2:
            return None

        source_vehicle = rng.choice(source_vehicles)
        source_route = assignments[source_vehicle]
        source_index = self._select_promising_source_index(source_vehicle, source_route, rng)

        ride_id = source_route[source_index]
        target_candidates = self._select_promising_target_vehicles(assignments, source_vehicle, ride_id, rng)
        if not target_candidates:
            return None

        target_vehicle = rng.choice(target_candidates)

        candidate = self._copy_assignments(assignments)
        ride_id = candidate[source_vehicle].pop(source_index)

        target_pos = self._best_insertion_position(
            route=candidate[target_vehicle],
            ride_id=ride_id,
            vehicle_id=target_vehicle,
        )
        candidate[target_vehicle].insert(target_pos, ride_id)
        return candidate

    def _neighbor_swap(
        self,
        assignments: List[List[int]],
        rng: random.Random,
    ) -> Optional[List[List[int]]]:
        non_empty = [idx for idx, route in enumerate(assignments) if route]
        if len(non_empty) < 2:
            return None

        v1 = rng.choice(non_empty)
        v2_candidates = self._select_promising_swap_vehicles(assignments, v1, rng)
        if not v2_candidates:
            return None
        v2 = rng.choice(v2_candidates)

        i1 = self._select_promising_source_index(v1, assignments[v1], rng)
        i2 = self._select_promising_source_index(v2, assignments[v2], rng)

        candidate = self._copy_assignments(assignments)
        candidate[v1][i1], candidate[v2][i2] = candidate[v2][i2], candidate[v1][i1]
        return candidate

    def _neighbor_reorder(
        self,
        assignments: List[List[int]],
        rng: random.Random,
    ) -> Optional[List[List[int]]]:
        reorderable = [idx for idx, route in enumerate(assignments) if len(route) >= 2]
        if not reorderable:
            return None

        vehicle = rng.choice(reorderable)
        route = assignments[vehicle]

        sample_pairs = []
        route_len = len(route)
        for _ in range(min(8, route_len * 2)):
            i, j = rng.sample(range(route_len), 2)
            if i > j:
                i, j = j, i
            sample_pairs.append((i, j))
        if not sample_pairs:
            return None

        best_pair = sample_pairs[0]
        best_delta = float("inf")
        for i, j in sample_pairs:
            delta = self._swap_reorder_delta(vehicle, route, i, j)
            if delta < best_delta:
                best_delta = delta
                best_pair = (i, j)

        i, j = best_pair

        candidate = self._copy_assignments(assignments)
        candidate[vehicle][i], candidate[vehicle][j] = candidate[vehicle][j], candidate[vehicle][i]
        return candidate

    def _select_promising_source_index(self, vehicle_id: int, route: List[int], rng: random.Random) -> int:
        if len(route) == 1:
            return 0

        scored = []
        for idx in range(len(route)):
            score = self._removal_gain(vehicle_id, route, idx)
            scored.append((score, idx))
        scored.sort(reverse=True)
        top = [idx for _, idx in scored[: min(3, len(scored))]]
        return rng.choice(top)

    def _select_promising_target_vehicles(
        self,
        assignments: List[List[int]],
        source_vehicle: int,
        ride_id: int,
        rng: random.Random,
    ) -> List[int]:
        ride = self._rides_by_id.get(ride_id)
        if ride is None:
            return [idx for idx in range(len(assignments)) if idx != source_vehicle]

        ranked = []
        for vehicle_id, route in enumerate(assignments):
            if vehicle_id == source_vehicle:
                continue
            anchor_r, anchor_c = self._route_anchor(vehicle_id, route)
            distance = abs(anchor_r - ride.start[0]) + abs(anchor_c - ride.start[1])
            ranked.append((distance, vehicle_id))
        ranked.sort()

        top_count = min(3, len(ranked))
        top = [vehicle_id for _, vehicle_id in ranked[:top_count]]
        if not top:
            return top
        if len(top) == 1:
            return top
        return top + [rng.choice(top)]

    def _select_promising_swap_vehicles(
        self,
        assignments: List[List[int]],
        v1: int,
        rng: random.Random,
    ) -> List[int]:
        if not assignments[v1]:
            return []

        v1_anchor = self._route_anchor(v1, assignments[v1])
        ranked = []
        for v2, route in enumerate(assignments):
            if v2 == v1 or not route:
                continue
            v2_anchor = self._route_anchor(v2, route)
            distance = abs(v1_anchor[0] - v2_anchor[0]) + abs(v1_anchor[1] - v2_anchor[1])
            ranked.append((distance, v2))
        ranked.sort()

        top = [v2 for _, v2 in ranked[: min(3, len(ranked))]]
        if not top:
            return []
        if len(top) == 1:
            return top
        return top + [rng.choice(top)]

    def _route_anchor(self, vehicle_id: int, route: List[int]) -> Tuple[int, int]:
        if not route:
            if self._problem is not None and vehicle_id < len(self._problem.vehicle_starts):
                return self._problem.vehicle_starts[vehicle_id]
            return 0, 0

        last_ride = self._rides_by_id.get(route[-1])
        if last_ride is None:
            return 0, 0
        return last_ride.end

    def _best_insertion_position(self, route: List[int], ride_id: int, vehicle_id: int) -> int:
        best_pos = 0
        best_delta = float("inf")
        for pos in range(len(route) + 1):
            delta = self._insertion_delta(route, pos, ride_id, vehicle_id)
            if delta < best_delta:
                best_delta = delta
                best_pos = pos
        return best_pos

    def _insertion_delta(self, route: List[int], pos: int, ride_id: int, vehicle_id: int) -> int:
        ride = self._rides_by_id.get(ride_id)
        if ride is None:
            return 0

        prev_end = self._previous_end(route, pos, vehicle_id)
        next_start = self._next_start(route, pos)

        old_cost = 0 if next_start is None else self._dist(prev_end, next_start)
        new_cost = self._dist(prev_end, ride.start) + ride.distance
        if next_start is not None:
            new_cost += self._dist(ride.end, next_start)

        return new_cost - old_cost

    def _removal_gain(self, vehicle_id: int, route: List[int], idx: int) -> int:
        ride_id = route[idx]
        ride = self._rides_by_id.get(ride_id)
        if ride is None:
            return 0

        prev_end = self._previous_end(route, idx, vehicle_id)
        next_start = self._next_start(route, idx + 1)

        old_cost = self._dist(prev_end, ride.start) + ride.distance
        if next_start is not None:
            old_cost += self._dist(ride.end, next_start)

        new_cost = 0 if next_start is None else self._dist(prev_end, next_start)
        return old_cost - new_cost

    def _swap_reorder_delta(self, vehicle_id: int, route: List[int], i: int, j: int) -> int:
        baseline = self._route_transition_cost(vehicle_id, route)
        trial = route.copy()
        trial[i], trial[j] = trial[j], trial[i]
        return self._route_transition_cost(vehicle_id, trial) - baseline

    def _route_transition_cost(self, vehicle_id: int, route: List[int]) -> int:
        if not route:
            return 0

        if self._problem is not None and vehicle_id < len(self._problem.vehicle_starts):
            prev_end = self._problem.vehicle_starts[vehicle_id]
        else:
            prev_end = (0, 0)

        total = 0
        for ride_id in route:
            ride = self._rides_by_id.get(ride_id)
            if ride is None:
                continue
            total += self._dist(prev_end, ride.start)
            total += ride.distance
            prev_end = ride.end
        return total

    def _previous_end(self, route: List[int], pos: int, vehicle_id: int) -> Tuple[int, int]:
        if pos == 0:
            if self._problem is not None and vehicle_id < len(self._problem.vehicle_starts):
                return self._problem.vehicle_starts[vehicle_id]
            return 0, 0

        prev_ride = self._rides_by_id.get(route[pos - 1])
        if prev_ride is None:
            return 0, 0
        return prev_ride.end

    def _next_start(self, route: List[int], pos: int) -> Optional[Tuple[int, int]]:
        if pos >= len(route):
            return None
        next_ride = self._rides_by_id.get(route[pos])
        if next_ride is None:
            return None
        return next_ride.start

    def _dist(self, a: Tuple[int, int], b: Tuple[int, int]) -> int:
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def _perturb_assignments(self, assignments: List[List[int]], rng: random.Random) -> List[List[int]]:
        candidate = self._copy_assignments(assignments)
        perturb_steps = max(1, min(5, self.neighborhood_size // 10 + 1))
        for _ in range(perturb_steps):
            move_type = rng.choices(
                population=("move", "reorder", "swap"),
                weights=(0.6, 0.25, 0.15),
                k=1,
            )[0]
            if move_type == "move":
                updated = self._neighbor_move(candidate, rng)
            elif move_type == "reorder":
                updated = self._neighbor_reorder(candidate, rng)
            else:
                updated = self._neighbor_swap(candidate, rng)
            if updated is not None:
                candidate = updated
        return candidate

    def _copy_assignments(self, assignments: List[List[int]]) -> List[List[int]]:
        return [route.copy() for route in assignments]

    def _normalize_assignments(
        self,
        assignments: List[List[int]],
        vehicle_count: int,
        ride_count: int,
    ) -> List[List[int]]:
        normalized = [[] for _ in range(vehicle_count)]
        used = set()

        for vehicle_id, route in enumerate(assignments[:vehicle_count]):
            for ride_id in route:
                if ride_id not in used and 0 <= ride_id < ride_count:
                    normalized[vehicle_id].append(ride_id)
                    used.add(ride_id)

        if len(used) < ride_count:
            missing_rides = [r for r in range(ride_count) if r not in used]
            
            for i, ride_id in enumerate(missing_rides):
                normalized[i % vehicle_count].append(ride_id)

        return normalized

    def _has_duplicate_rides(self, assignments: List[List[int]]) -> bool:
        used = set()
        for route in assignments:
            for ride_id in route:
                if ride_id in used:
                    return True
                used.add(ride_id)
        return False
