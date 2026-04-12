import argparse
from time import perf_counter
from pathlib import Path

from output_writer import write_report, write_solution
from parser import read_problem_instance
from scoring import score_solution
from solvers.genetic_algorithm import GeneticAlgorithmSolver
from solvers.greedy_solver import GreedySolver
from solvers.hill_climbing import HillClimbingSolver
from solvers.simulated_annealing import SimulatedAnnealingSolver


INPUTS_DIR = Path("inputs")
OUTPUTS_DIR = Path("outputs")
OUTPUT_SUBFOLDERS = {
    "greedy": "greedy",
    "hill_climbing": "hill_climbing",
    "simulated_annealing": "simulated_annealing",
    "genetic_algorithm": "genetic_algorithm",
}


def _validate_solution(problem, solution):
    seen = set()
    duplicates = 0
    out_of_range = 0

    for route in solution.assignments:
        for ride_id in route:
            if not (0 <= ride_id < problem.ride_count):
                out_of_range += 1
                continue
            if ride_id in seen:
                duplicates += 1
                continue
            seen.add(ride_id)

    return duplicates, out_of_range


def _build_solver(args, progress_callback=None):
    name = args.solver
    if name == "greedy":
        return GreedySolver()
    if name == "hill_climbing":
        return HillClimbingSolver(
            max_iterations=args.max_iterations,
            max_no_improve=args.max_no_improve,
            random_seed=args.random_seed,
            progress_callback=progress_callback,
        )
    if name == "simulated_annealing":
        return SimulatedAnnealingSolver(
            max_iterations=args.max_iterations,
            initial_temperature=args.initial_temperature,
            cooling_rate=args.cooling_rate,
            min_temperature=args.min_temperature,
            random_seed=args.random_seed,
            progress_callback=progress_callback,
        )
    if name == "genetic_algorithm":
        return GeneticAlgorithmSolver(random_seed=args.random_seed)
    raise ValueError(f"Unknown solver: {name}")


def _ensure_output_structure() -> None:
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    for folder_name in OUTPUT_SUBFOLDERS.values():
        (OUTPUTS_DIR / folder_name).mkdir(parents=True, exist_ok=True)


def _resolve_input_path(input_arg: str) -> Path:
    candidate = Path(input_arg)
    if candidate.is_absolute() or candidate.parent != Path("."):
        return candidate
    return INPUTS_DIR / input_arg


def _build_output_paths(input_path: Path, solver_name: str, output_arg: str | None) -> tuple[Path, Path]:
    solver_folder = OUTPUTS_DIR / OUTPUT_SUBFOLDERS[solver_name]
    solver_folder.mkdir(parents=True, exist_ok=True)

    if output_arg:
        output_candidate = Path(output_arg)
        if output_candidate.is_absolute() or output_candidate.parent != Path("."):
            assignment_path = output_candidate
        else:
            assignment_path = solver_folder / output_candidate.name
    else:
        assignment_path = solver_folder / f"{input_path.stem}.out"

    report_path = assignment_path.with_name(f"{assignment_path.stem}_report.txt")
    assignment_path.parent.mkdir(parents=True, exist_ok=True)
    return assignment_path, report_path


def _build_progress_callback(verbose: bool, solver_name: str):
    if not verbose:
        return None

    def _progress(data):
        event = data.get("event")
        if solver_name == "hill_climbing":
            if event == "start":
                print(f"[HC] initial greedy score: {data['initial_greedy_score']}")
                return
            if event == "iteration":
                print(
                    f"[HC] iter={data['iteration']} best={data['current_best_score']} "
                    f"no_improve={data['no_improve']} "
                    f"gen={int(data.get('neighbors_generated', 0))} "
                    f"valid={int(data.get('valid_candidates', 0))} "
                    f"accepted={int(data.get('accepted_moves', 0))} "
                    f"improving={int(data.get('improving_moves', 0))}"
                )
                return
            if event == "final":
                print(
                    f"[HC] final score: {data['final_score']} "
                    f"gen_total={int(data.get('neighbors_generated', 0))} "
                    f"valid_total={int(data.get('valid_candidates', 0))} "
                    f"accepted_total={int(data.get('accepted_moves', 0))} "
                    f"improving_total={int(data.get('improving_moves', 0))}"
                )
                return

        if solver_name == "simulated_annealing":
            if event == "start":
                print(f"[SA] initial greedy score: {int(data['initial_greedy_score'])}")
                return
            if event == "iteration":
                print(
                    f"[SA] iter={int(data['iteration'])} temp={data['temperature']:.4f} "
                    f"current={int(data['current_score'])} best={int(data['best_score'])} "
                    f"gen={int(data.get('neighbors_generated', 0))} "
                    f"valid={int(data.get('valid_candidates', 0))} "
                    f"accepted={int(data.get('accepted_moves', 0))} "
                    f"improving={int(data.get('improving_moves', 0))}"
                )
                return
            if event == "final":
                print(
                    f"[SA] final score: {int(data['final_score'])} "
                    f"gen_total={int(data.get('neighbors_generated', 0))} "
                    f"valid_total={int(data.get('valid_candidates', 0))} "
                    f"accepted_total={int(data.get('accepted_moves', 0))} "
                    f"improving_total={int(data.get('improving_moves', 0))}"
                )

    return _progress


def main():
    parser = argparse.ArgumentParser(description="Hash Code 2018 solver CLI")
    parser.add_argument("input", help="Input dataset filename (expected inside inputs/)")
    parser.add_argument("output", nargs="?", help="Optional output filename/path")
    parser.add_argument(
        "--solver",
        default="greedy",
        choices=["greedy", "hill_climbing", "simulated_annealing", "genetic_algorithm"],
        help="Solver to run",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print verbose progress (mainly for hill climbing)",
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=300,
        help="Maximum hill-climbing iterations",
    )
    parser.add_argument(
        "--max-no-improve",
        type=int,
        default=60,
        help="Stop hill-climbing after this many non-improving iterations",
    )
    parser.add_argument(
        "--random-seed",
        type=int,
        default=None,
        help="Optional random seed for deterministic hill-climbing",
    )
    parser.add_argument(
        "--initial-temperature",
        type=float,
        default=1000.0,
        help="Initial temperature for simulated annealing",
    )
    parser.add_argument(
        "--cooling-rate",
        type=float,
        default=0.995,
        help="Cooling rate for simulated annealing",
    )
    parser.add_argument(
        "--min-temperature",
        type=float,
        default=0.1,
        help="Minimum temperature for simulated annealing",
    )

    args = parser.parse_args()

    _ensure_output_structure()
    input_path = _resolve_input_path(args.input)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    assignment_output_path, report_output_path = _build_output_paths(input_path, args.solver, args.output)

    problem = read_problem_instance(str(input_path))
    progress_callback = _build_progress_callback(args.verbose, args.solver)
    solver = _build_solver(args, progress_callback=progress_callback)

    greedy_baseline_breakdown = None
    if args.solver in ("hill_climbing", "simulated_annealing"):
        greedy_baseline_solution = GreedySolver().solve(problem)
        greedy_baseline_breakdown = score_solution(problem, greedy_baseline_solution)

    start_time = perf_counter()
    solution = solver.solve(problem)
    execution_time_s = perf_counter() - start_time

    duplicates, out_of_range = _validate_solution(problem, solution)
    if duplicates or out_of_range:
        raise ValueError(
            f"Invalid solution generated (duplicates={duplicates}, out_of_range={out_of_range})"
        )

    breakdown = score_solution(problem, solution)

    write_solution(str(assignment_output_path), solution)

    rides_assigned = sum(len(route) for route in solution.assignments)
    vehicles_used = sum(1 for route in solution.assignments if route)
    avg_rides_per_vehicle = rides_assigned / len(solution.assignments) if solution.assignments else 0.0

    report_data = {
        "input_file": str(input_path),
        "solver": args.solver,
        "score": breakdown.total_score,
        "completed_rides": breakdown.completed_rides,
        "bonus_rides": breakdown.bonus_count,
        "invalid_assignments": breakdown.invalid_assignments,
        "execution_time_s": execution_time_s,
        "assignment_output_path": str(assignment_output_path),
        "vehicles_used": vehicles_used,
        "rides_assigned": rides_assigned,
        "avg_rides_per_vehicle": avg_rides_per_vehicle,
        "parameters": {
            "max_iterations": args.max_iterations,
            "max_no_improve": args.max_no_improve,
            "random_seed": args.random_seed,
            "verbose": args.verbose,
            "initial_temperature": args.initial_temperature,
            "cooling_rate": args.cooling_rate,
            "min_temperature": args.min_temperature,
        },
    }
    write_report(str(report_output_path), report_data)

    print(f"Solver: {args.solver}")
    print(f"Input read from: {input_path}")
    print(f"Output written to: {assignment_output_path}")
    print(f"Report written to: {report_output_path}")
    print(f"Score: {breakdown.total_score}")
    print(f"Completed rides: {breakdown.completed_rides}")
    print(f"Bonus rides: {breakdown.bonus_count}")
    if args.solver in ("hill_climbing", "simulated_annealing") and greedy_baseline_breakdown is not None:
        if isinstance(solver, HillClimbingSolver) and solver.last_initial_score is not None:
            if solver.last_initial_score != greedy_baseline_breakdown.total_score:
                print(
                    "Warning: hill-climbing initial score differs from external greedy baseline "
                    f"({solver.last_initial_score} vs {greedy_baseline_breakdown.total_score})"
                )
        if isinstance(solver, SimulatedAnnealingSolver) and solver.last_initial_score is not None:
            if solver.last_initial_score != greedy_baseline_breakdown.total_score:
                print(
                    "Warning: simulated annealing initial score differs from external greedy baseline "
                    f"({solver.last_initial_score} vs {greedy_baseline_breakdown.total_score})"
                )
        improvement = breakdown.total_score - greedy_baseline_breakdown.total_score
        print(f"Greedy baseline score: {greedy_baseline_breakdown.total_score}")
        print(f"Final {args.solver} score: {breakdown.total_score}")
        print(f"Score improvement: {improvement}")
    if breakdown.invalid_assignments:
        print(f"Invalid assignments ignored: {breakdown.invalid_assignments}")


if __name__ == "__main__":
    main()
