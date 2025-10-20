# flake8: noqa: PYI021

from enum import Enum
from typing import Tuple

class PullResult(Enum):
    Standard3Star = ...
    Standard4Star = ...
    Standard5Star = ...
    Featured5Star = ...

class GenshinImpactGachaModel:
    def __init__(self, pt: int, cr: int, guaranteed: bool, seed: int, version: int) -> None: ...
    
    def batch_pull_count(self, pulls: int) -> Tuple[int, int]:
        """
        Perform multiple pulls and count the results.
        
        Args:
            pulls: Number of pulls to perform
            
        Returns:
            A tuple of (featured_5star_count, standard_5star_count)
        """
        ...
