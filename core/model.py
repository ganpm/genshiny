from random import Random
from enum import Enum


class PullType(Enum):
    """Enumeration for different types of pulls."""
    Normal = 0
    Standard = 1
    Featured = 2


class GIGachaModel:
    """Simulation model for Genshin Impact's gacha system."""

    def __init__(
            self,
            seed,
            pt,
            cr,
            guaranteed,
            ):

        self.rng = Random(seed)
        self.hard_pt = 90
        self.soft_pt = 73
        self.normal_p = 0.006
        self.p_gain = 0.06
        self.pt = pt
        self.cr = cr
        self.cr_flag = False
        self.guaranteed = guaranteed

    def pull_cr(self):
        self.cr_flag = False

        roll = self.rng.random()
        success = True
        if self.pt <= self.soft_pt:
            success = roll < self.normal_p
        elif self.pt < self.hard_pt:
            success = roll < self.normal_p + self.p_gain * (self.pt - self.soft_pt)
        else:
            success = True

        if success:
            self.pt = 0
            if self.guaranteed:
                self.guaranteed = False
                return PullType.Featured
            else:
                ff_roll = self.rng.random()
                if ff_roll < 0.5:
                    self.guaranteed = False
                    return PullType.Featured
                else:
                    self.guaranteed = True
                    if self.cr == 0:
                        self.cr = 1
                        return PullType.Standard
                    elif self.cr == 1:
                        self.cr = 2
                        return PullType.Standard
                    elif self.cr == 2:
                        cr_roll = self.rng.random()
                        if cr_roll < 0.5:
                            self.cr = 0
                            self.guaranteed = False
                            self.cr_flag = True
                            return PullType.Featured
                        else:
                            self.cr = 3
                            self.guaranteed = True
                            return PullType.Standard
                    else:
                        self.cr = 0
                        self.guaranteed = False
                        self.cr_flag = True
                        return PullType.Featured
        else:
            self.pt += 1
            return PullType.Normal

    def reset(self):
        self.pt = 0

    def batch_pull_count(self, pulls: int):
        featured_rolls = 0
        standard_rolls = 0
        for _ in range(pulls):
            pull = self.pull_cr()
            if pull == PullType.Featured:
                featured_rolls += 1
            elif pull == PullType.Standard:
                standard_rolls += 1

        return featured_rolls, standard_rolls


def simulate(
        pulls: int,
        sim_length: int,
        seed: int,
        guaranteed: bool = False,
        pity: int = 0,
        cr: int = 0,
        ):

    model = GIGachaModel(seed, pity, cr, guaranteed)
    combined_counts = {}

    for _ in range(sim_length):
        featured_rolls = 0
        standard_rolls = 0
        for _ in range(pulls):
            pull = model.pull_cr()
            if pull == PullType.Featured:
                featured_rolls += 1
            elif pull == PullType.Standard:
                standard_rolls += 1

        key = (featured_rolls, standard_rolls)
        if key in combined_counts:
            combined_counts[key] += 1
        else:
            combined_counts[key] = 1

    return combined_counts
