# flake8: noqa: PYI021

from enum import Enum
from datetime import timedelta


class PullResult(Enum):
    """
    Enumeration representing the possible result of a gacha pull.
    ### Members:
    - `Standard3Star`
    - `Standard4Star`
    - `Standard5Star`
    - `Featured5Star`
    """

    Standard3Star = ...
    Standard4Star = ...
    Standard5Star = ...
    Featured5Star = ...


class CapturingRadianceModel:
    """
    Simulation model for the Capturing Radiance system.
    ### Versions:
    - `0` - Capturing Radiance is disabled. Always 50/50.
    - `1` - Basic model. 10% chance to trigger CR and win if you lost the 50/50.
    - `2` - Best approximate model
    - `3` - Experimental model
    """

    cr: int
    version: int

    def __init__(
            self,
            cr: int,
            version: int
            ) -> None:
        ...

    def pull(self) -> PullResult:
        ...

    def pull_v0(self) -> PullResult:
        ...

    def pull_v1(self) -> PullResult:
        ...

    def pull_v2(self) -> PullResult:
        ...

    def pull_v3(self) -> PullResult:
        ...


class GenshinImpactGachaModel:
    """
    Simulation model for Genshin Impact gacha system.
    ### Args:
    - `g` - Whether the next 5-star is guaranteed to be featured
    - `cr_model` - Capturing Radiance model to use
    - `rate5` - Base rate for 5-star before the soft pity threshold for 5-stars
    - `rate4` - Base rate for 4-star before the soft pity threshold for 4-stars
    - `rateup5` - Rate increase after the soft pity threshold for 5-stars
    - `rateup4` - Rate increase after the soft pity threshold for 4-stars
    - `softpt5` - Soft pity threshold for 5-stars
    - `softpt4` - Soft pity threshold for 4-stars
    - `counter5` - Current pull count (pity) since last 5-star
    - `counter4` - Current pull count (pity) since last 4-star
    """

    g: bool
    cr_model: CapturingRadianceModel
    rate5: float
    rate4: float
    rateup5: float
    rateup4: float
    softpt5: int
    softpt4: int
    counter5: int
    counter4: int

    def __init__(
            self,
            pt: int,
            g: bool,
            cr_model: CapturingRadianceModel,
            seed: int,
            ) -> None:
        ...

    def pull(self) -> PullResult:
        """
        Perform a single gacha pull.

        ### Returns:
        - A `PullResult` indicating the type of pull obtained.
        """
        ...
    
    def batch_pull_count(
            self,
            pulls: int
            ) -> tuple[int, int]:
        """
        Perform multiple pulls and count the results.
        
        ### Args:
        - `pulls` - Number of pulls to perform

        ### Returns:
        - A tuple of two integers containing the number
        of featured and standard 5-stars obtained, respectively.
        """
        ...


class SimulationResult:

    featured_rolls: dict[int, int]
    standard_rolls: dict[int, int]
    total_rolls: dict[int, int]
    joint_rolls: dict[tuple[int, int], int]
    simulation_count: int
    ftd_range: tuple[int, int]
    std_range: tuple[int, int]
    sim_duration: timedelta

    def __init__(
            self,
            featured_rolls: dict[int, int],
            standard_rolls: dict[int, int],
            total_rolls: dict[int, int],
            joint_rolls: dict[tuple[int, int], int],
            simulation_count: int,
            ftd_range: tuple[int, int],
            std_range: tuple[int, int],
            sim_duration: timedelta,
            ) -> None:
        ...


class SimulationThread:

    def __init__(
            self,
            model: GenshinImpactGachaModel,
            pulls: int,
            sim_length: int,
            ) -> None:
        ...

    def run(self) -> None:
        ...

    def stop(self) -> None:
        ...

    def is_running(self) -> bool:
        ...

    def get_current_results(self) -> SimulationResult:
        ...
