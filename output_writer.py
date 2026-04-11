from pathlib import Path
from typing import Dict

from models import Solution


def write_solution(filepath: str, solution: Solution) -> None:
    with open(filepath, "w", encoding="utf-8") as file:
        for rides in solution.assignments:
            rides_text = " ".join(map(str, rides))
            if rides_text:
                file.write(f"{len(rides)} {rides_text}\n")
            else:
                file.write("0\n")


def write_report(filepath: str, report_data: Dict[str, object]) -> None:
    path = Path(filepath)
    with path.open("w", encoding="utf-8") as file:
        file.write("Hash Code Run Report\n")
        file.write("====================\n\n")
        file.write(f"Input file: {report_data['input_file']}\n")
        file.write(f"Solver: {report_data['solver']}\n")
        file.write(f"Score: {report_data['score']}\n")
        file.write(f"Total completed rides: {report_data['completed_rides']}\n")
        file.write(f"Total bonus rides: {report_data['bonus_rides']}\n")
        file.write(f"Invalid assignments: {report_data['invalid_assignments']}\n")
        file.write(f"Execution time (s): {report_data['execution_time_s']:.6f}\n")
        file.write(f"Output assignment file path: {report_data['assignment_output_path']}\n")
        file.write("\n")

        file.write(f"Number of vehicles used: {report_data['vehicles_used']}\n")
        file.write(f"Number of rides assigned: {report_data['rides_assigned']}\n")
        file.write(f"Average rides per vehicle: {report_data['avg_rides_per_vehicle']:.3f}\n")
        file.write("\n")

        file.write("Parameters used:\n")
        parameters = report_data.get("parameters", {})
        if isinstance(parameters, dict):
            for key, value in parameters.items():
                file.write(f"- {key}: {value}\n")
