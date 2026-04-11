from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass(frozen=True)
class Ride:
    ride_id: int
    start: Tuple[int, int]
    end: Tuple[int, int]
    earliest: int
    latest: int

    @property
    def distance(self) -> int:
        return abs(self.start[0] - self.end[0]) + abs(self.start[1] - self.end[1])


@dataclass
class Vehicle:
    vehicle_id: int
    row: int = 0
    col: int = 0
    time_available: int = 0
    assigned_rides: List[int] = field(default_factory=list)


@dataclass(frozen=True)
class ProblemInstance:
    rows: int
    cols: int
    vehicle_count: int
    ride_count: int
    bonus: int
    total_time: int
    rides: List[Ride]
    vehicle_starts: List[Tuple[int, int]]


@dataclass
class Solution:
    assignments: List[List[int]]
