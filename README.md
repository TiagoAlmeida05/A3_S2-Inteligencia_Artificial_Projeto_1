## Project Overview
This repository contains a Python implementation of the **Google Hash Code 2018 qualification problem**, commonly known as **Self-Driving Rides**.

The project goal is to assign rides to a fleet of vehicles in a way that maximizes total score under time and feasibility constraints. Instead of relying on a single strategy, the codebase supports **multiple solving approaches** and allows direct comparison between them.

At the current stage, the project includes:
- a **UI simulation mode** (`main.py`) for visual execution and inspection;
- a **CLI optimization mode** (`cli.py`) for running solver experiments;
- three implemented optimization strategies:
  - `greedy`
  - `hill_climbing`
  - `simulated_annealing`
- one placeholder solver module for future extension:
  - `genetic_algorithm`

## Problem Summary
In Self-Driving Rides:
- The city is represented as a **2D grid**.
- A set of **rides** is given, each with:
  - start cell,
  - end cell,
  - earliest start time,
  - latest finish time.
- A fleet of **vehicles** must execute rides sequentially over a fixed simulation horizon.
- The score is based on:
  - total distance of rides completed within constraints;
  - an additional **bonus** when a ride starts exactly at its earliest start.

The optimization challenge is to balance feasibility, travel time to pickup, waiting time, and sequencing quality across all vehicles.

## Project Structure
The repository is organized into modular components for modeling, parsing, scheduling, scoring, solving, simulation, and reporting.

```text
self-driving-cars/
├── main.py
├── cli.py
├── models.py
├── parser.py
├── scheduler.py
├── scoring.py
├── output_writer.py
├── solver_interface.py
├── solvers/
│   ├── greedy_solver.py
│   ├── hill_climbing.py
│   ├── simulated_annealing.py
│   ├── genetic_algorithm.py
│   └── __init__.py
├── simulation/
│   ├── sim.py
│   ├── car.py
│   └── ride.py
├── Policies/
│   ├── greedy_policy.py
│   └── random_policy.py
├── ui/
│   └── pygame_ui.py
├── inputs/
├── outputs/
└── *.in
```

### Core Files and Responsibilities
- `main.py`
  - Entry point for **UI mode**.
  - Loads dataset, runs simulation with policy logic, and opens the Pygame visualizer.

- `cli.py`
  - Entry point for **solver mode**.
  - Parses arguments, runs selected solver, validates assignments, computes score, and writes output/report files.

- `models.py`
  - Defines core data structures: `Ride`, `Vehicle`, `ProblemInstance`, `Solution`.

- `parser.py`
  - Reads Hash Code input files and builds `ProblemInstance`.
  - Uses the assignment rule that vehicles start at `(0, 0)`.

- `scheduler.py`
  - Assignment feasibility and timeline utilities (`estimate_assignment`, `apply_assignment`, vehicle creation).

- `scoring.py`
  - Computes score breakdown for a solution (`total_score`, completed rides, bonus rides, invalid assignments).

- `output_writer.py`
  - Writes Hash Code output format (`.out`) and a human-readable run report (`_report.txt`).

- `solver_interface.py`
  - Abstract base interface for all solvers.

- `solvers/`
  - Contains optimization algorithms and future placeholders.

- `simulation/`
  - UI simulation entities and simulation loop implementation.

- `Policies/`
  - Policies used by the simulation path (e.g., greedy policy for UI simulation flow).

- `ui/`
  - Pygame rendering and interaction logic.

- `inputs/`
  - Dataset files consumed by CLI/UI (or referenced from project root).

- `outputs/`
  - Generated results grouped by solver.

## Implemented Algorithms
This section describes the implemented methods as they are used in this project, not as generic textbook-only descriptions.

### 1) Greedy Solver
**What it is**
- A constructive heuristic that iteratively assigns the best currently feasible ride to each vehicle.

**How it works in this project**
- Implemented in `solvers/greedy_solver.py`.
- For each vehicle, candidate rides are evaluated with a weighted score based on:
  - ride distance,
  - bonus opportunity,
  - distance to pickup,
  - waiting time,
  - slack until latest finish.
- The best feasible ride is assigned immediately, and the process repeats until no additional assignment is possible.

**Why it was chosen**
- It is fast, deterministic (for fixed input/state), and provides a solid baseline for larger optimization methods.

**What it improves over a naive approach**
- Better than random assignment because it explicitly uses feasibility and score-related features.

**Strengths**
- Very fast execution.
- Produces valid schedules quickly.
- Strong baseline for subsequent local-search methods.

**Limitations**
- Myopic decisions: good local choices can block better global plans.
- Cannot revise earlier assignments once made.

### 2) Hill Climbing
**What it is**
- A local search improvement strategy that starts from a complete solution and repeatedly applies improving neighborhood moves.

**How it works in this project**
- Implemented in `solvers/hill_climbing.py`.
- Starts from the Greedy solution.
- Generates neighborhoods with ride-level moves such as:
  - moving rides between vehicles,
  - swapping rides across routes,
  - reordering rides inside a route.
- Uses problem-aware candidate generation (promising source/target choices and insertion positions).
- Scores each candidate with the same scoring pipeline used globally.
- Accepts best improving candidates and stops on iteration/no-improvement limits.
- Includes diagnostics counters and optional restart behavior.

**Why it was chosen**
- Natural second step after Greedy: preserve speed while enabling iterative improvement.

**What it improves over Greedy**
- Can revisit and improve initial assignments.
- Explores nearby solutions that Greedy cannot reach once decisions are fixed.

**Strengths**
- Usually better solution quality than pure constructive greedy.
- Relatively simple to reason about and debug.
- Benefits from domain-aware neighborhood design.

**Limitations**
- Can stagnate in local optima.
- Quality depends on neighborhood richness and stopping parameters.

### 3) Simulated Annealing
**What it is**
- A probabilistic local search method that allows occasional non-improving moves to escape local optima.

**How it works in this project**
- Implemented in `solvers/simulated_annealing.py`.
- Starts from the Greedy solution.
- Reuses neighborhood-generation utilities from Hill Climbing.
- At each iteration:
  - generates a batch of neighbors,
  - ranks candidates,
  - samples from top candidates,
  - accepts better solutions deterministically,
  - may accept worse solutions according to temperature-based probability.
- Temperature decreases according to configurable cooling parameters.
- Tracks diagnostics (generated/valid neighbors, accepted/improving moves).

**Why it was chosen**
- Added specifically to reduce Hill Climbing stagnation and improve exploration.

**What it improves over Hill Climbing**
- Can cross valleys in the search space by temporarily accepting lower scores.
- Better chance to escape local maxima.

**Strengths**
- More robust exploration than strict improvement-only methods.
- Flexible and tunable for different dataset profiles.

**Limitations**
- Sensitive to parameter tuning (`initial_temperature`, `cooling_rate`, iteration budget).
- Can underperform if temperature schedule is not well calibrated.



### 4) Genetic Algorithm
**What it is**
- A fully implemented population-based metaheuristic inspired by natural selection, evolving a set of candidate solutions (assignments) over generations.

**How it works in this project**
- Implemented in `solvers/genetic_algorithm.py`.
- Each individual (chromosome) represents a complete assignment of rides to vehicles.
- The algorithm maintains a population of solutions, initialized with one Greedy solution and the rest random valid assignments.
- In each generation:
  - Solutions are evaluated using the same scoring pipeline as other solvers, with fitness values cached for efficiency (no redundant evaluations).
  - The best solutions (elitism) are preserved.
  - New solutions are created by selecting parents (tournament selection), performing crossover (combining vehicle routes from both parents), and applying mutation (random moves, swaps, or reorders, reusing Hill Climbing logic).
  - The crossover operator is carefully designed to always assign all rides: after inheriting routes from parents, any missing rides are explicitly assigned to random vehicles, ensuring no ride is ever lost.
  - All solutions are normalized to ensure feasibility (no duplicate or out-of-range rides).
- After a fixed number of generations, the best solution found is returned.

**Why it was chosen**
- Genetic algorithms can explore a broader solution space and sometimes escape local optima that trap local search methods.
- They are useful for large, complex instances where diverse solution strategies may yield better results.

**What it improves over other methods**
- Can combine features of multiple good solutions, not just make local changes.
- May find better solutions on hard instances, given enough time and tuning.

**Strengths**
- Flexible and robust to local optima.
- Leverages and combines existing move logic for effective mutation.
- Can be tuned for solution quality vs. runtime.
- Always produces valid solutions with all rides assigned.
- Efficient: caches fitness values to avoid redundant scoring.

**Limitations**
- Computationally expensive: slower than greedy or local search for large populations/generations.
- Solution quality depends on parameter tuning (population size, mutation/crossover rates, generations).
- No guarantee of outperforming tuned local search on all instances.

## Algorithm Progression and Design Rationale
The algorithmic evolution in this project follows a deliberate progression:

1. **Greedy first (baseline construction)**
   - The project needed a fast and reliable baseline capable of generating valid assignments quickly.
   - This enabled immediate testing of parser, scheduler, scoring, and output pipeline.

2. **Hill Climbing second (local refinement)**
   - Once a baseline existed, local improvements became the next logical step.
   - Hill Climbing was added to improve solution quality without redesigning the whole solver stack.
   - It introduces neighborhood-based refinement while preserving compatibility with the same score/evaluation modules.

3. **Simulated Annealing third (escaping local optima)**
   - Hill Climbing can stagnate when no nearby improving move exists.
   - Simulated Annealing was introduced as a direct improvement to search behavior by allowing controlled non-improving moves.
   - In practical terms, this broadens exploration while keeping the same solution representation and scoring logic.

## Synthetic Datasets With Clear Solver Gaps
To make solver differences easier to observe, this repository now includes three synthetic inputs designed so that metaheuristics typically beat pure greedy:

- `inputs/f_meta_gap_1.in`
- `inputs/f_meta_gap_2.in`
- `inputs/f_meta_gap_3.in`

They are generated deterministically by:

- `scripts/generate_challenging_inputs.py`

### Why These Datasets Behave This Way
These synthetic instances were made to create cases where Greedy picks options that look good right now, but hurt the final result, while hill climbing, simulated annealing, and genetic algorithm can adjust and find better overall schedules.

Main design patterns used in these datasets:

1. **Tight feasibility windows**
  - Many rides have relatively small slack (`latest - earliest - distance`).
  - A small sequencing mistake early can make several later rides infeasible.
  - Greedy commits immediately and cannot revisit those early choices.

2. **Conflicting local vs global choices**
  - Some rides look attractive because they are close or offer immediate bonus potential.
  - Taking them can move vehicles away from better future ride clusters.
  - Greedy's weighted score is local per decision step, so it can miss multi-step value.

3. **Route-order sensitivity**
  - Reordering a few rides within or across vehicles can unlock extra feasible rides or bonuses.
  - Hill Climbing can exploit this with move/swap/reorder neighbors.
  - Simulated Annealing can accept temporary score drops to escape local optima.
  - Genetic Algorithm can recombine useful route segments from multiple individuals.

4. **Mixed short and medium/long rides**
  - Short rides may be attractive for quick bonus capture.
  - Medium/long rides can be strategically better if sequenced well.
  - This creates the trade-off that usually separates Greedy from the metaheuristics.

Why improvements differ across solvers in the same dataset:

- **Hill Climbing** improves when the useful fixes are reachable by local improvements.
- **Simulated Annealing** improves more when escaping a local optimum is necessary.
- **Genetic Algorithm** improves when combining partial structures from different solutions is beneficial.

Because of this, the three `f_meta_gap_*` datasets tend to show a clear separation from Greedy, but they do not force a fixed ranking between Hill Climbing, SA, and GA on every run.

Run the generator at any time to recreate exactly the same files:

```bash
python scripts/generate_challenging_inputs.py
```

Quick benchmark command (all four solvers on all three datasets):

```bash
for ds in f_meta_gap_1.in f_meta_gap_2.in f_meta_gap_3.in; do
  python cli.py "$ds" --solver greedy
  python cli.py "$ds" --solver hill_climbing --random-seed 42
  python cli.py "$ds" --solver simulated_annealing --random-seed 42
  python cli.py "$ds" --solver genetic_algorithm --random-seed 42
done
```

4. **Genetic Algorithm fourth (global exploration)**
  - While Simulated Annealing helps escape local optima, it remains a single-solution trajectory; a population-based approach was the next logical step to explore multiple search regions simultaneously.
  - A full Genetic Algorithm was implemented, overcoming high complexity through careful chromosome encoding, feasibility-preserving crossover, and fitness caching for efficiency.
  - It acts as a "memetic" algorithm by reusing the existing Hill Climbing operators for its mutation step, seamlessly combining global exploration with local refinement.

Overall, each step increases search sophistication:
- Greedy: constructive feasibility and speed;
- Hill Climbing: targeted local improvement;
- Simulated Annealing: improved exploration beyond strict local ascent.

## Input and Output Organization
### Inputs
- Datasets are expected in `inputs/` (or passed with explicit paths).
- Example datasets include files such as `a_example.in`, `b_should_be_easy.in`, etc.

### Outputs
Solver outputs are grouped by solver name:
- `outputs/greedy/`
- `outputs/hill_climbing/`
- `outputs/simulated_annealing/`
- `outputs/genetic_algorithm/` (placeholder workflow)

For each run, the CLI generates:
1. **Raw assignment file** (`.out`) in Hash Code submission format.
2. **Human-readable report** (`*_report.txt`) with score breakdown, timing, and run parameters.

## How to Run the Program
## 1) Requirements
- Python 3.10+ recommended.
- `pygame` required for UI mode.

## 2) (Optional but recommended) Create a virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 3) Install dependencies
If you only need CLI mode, the standard library is sufficient for the current solver pipeline.

For UI mode, install Pygame:
```bash
pip install pygame
```

## 4) Run UI mode
```bash
python3 main.py
```
The UI flow asks for a dataset filename interactively, runs simulation logic, and opens the visualizer.

## 5) Run CLI mode with specific solvers
### Greedy
```bash
python3 cli.py a_example.in --solver greedy
```

### Hill Climbing
```bash
python3 cli.py a_example.in --solver hill_climbing
```

### Simulated Annealing
```bash
python3 cli.py a_example.in --solver simulated_annealing
```

You can also pass tuning parameters, for example:
```bash
python3 cli.py a_example.in --solver simulated_annealing \
  --max-iterations 500 \
  --initial-temperature 1200 \
  --cooling-rate 0.995 \
  --min-temperature 0.1 \
  --random-seed 42
```

### Verbose progress (local-search solvers)
```bash
python3 cli.py a_example.in --solver hill_climbing --verbose
python3 cli.py a_example.in --solver simulated_annealing --verbose
```

## 6) Generated files
After each CLI run, expect:
- one `.out` assignment file inside the selected solver folder in `outputs/`;
- one `*_report.txt` report file in the same folder.

## Current Limitations
- `genetic_algorithm` is not implemented yet (placeholder only).
- Search quality for Hill Climbing and Simulated Annealing can depend strongly on parameter settings.
- UI simulation path (`main.py`, `simulation/`, `Policies/`) and CLI optimization path (`cli.py`, `solvers/`) are partially separate workflows.
- Large instances may require richer neighborhood operators and additional optimization to consistently improve over baseline heuristics.

## Future Improvements
- Design stronger neighborhood operators (especially for large datasets).
- Perform systematic parameter tuning experiments for Hill Climbing and Simulated Annealing.
- Add experiment automation scripts to run and compare solver configurations across datasets.
- Implement a full Genetic Algorithm with feasibility-aware crossover and mutation.
- Improve performance (profiling, caching, and incremental scoring ideas).
- Extend reporting with benchmark tables/plots and reproducibility metadata.

## Credits and Context
This project is based on the **Google Hash Code 2018 Qualification Round** problem: **Self-Driving Rides**.

It was developed as a university project focused on heuristic optimization, search strategy progression, and practical solver comparison in Python.
