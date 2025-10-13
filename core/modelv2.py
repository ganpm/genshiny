from random import Random
from enum import Enum


class PullResult(Enum):

    Standard_3_Star = "Standard 3-Star"
    Standard_4_Star = "Standard 4-Star"
    Standard_5_Star = "Standard 5-Star"
    Featured_5_Star = "Featured 5-Star"


class GenshinImpactGachaModel:

    def __init__(
            self,
            pt: int = 0,
            cr: int = 0,
            guaranteed: bool = False,
            seed: int = 42,
            ) -> None:

        self.rng = Random(seed)
        self.cr = cr
        self.cr_model = CapturingRadianceModel(self.rng, cr)
        self.g = guaranteed

        self._rate5 = 0.006
        self._rate4 = 0.051

        self._rateup5 = 10 * self._rate5
        self._rateup4 = 10 * self._rate4

        self._softpt5 = 73
        self._softpt4 = 8

        self.counter5 = pt
        self.counter4 = 0

    def pull(self, cr=True) -> PullResult:
        """Gacha pull without Capturing Radiance."""

        x = self.rng.random()

        prob5 = self._rate5 if self.counter5 <= self._softpt5 else self._rateup5 * (self.counter5 - self._softpt5) + self._rate5
        prob4 = self._rate4 if self.counter4 <= self._softpt4 else self._rateup4 * (self.counter4 - self._softpt4) + self._rate4

        if x < prob5:
            self.counter5 = 1
            self.counter4 += 1
            if self.g or self.rng.random() < 0.5:
                self.g = False
                return PullResult.Featured_5_Star
            else:
                if cr:
                    pull = self.cr_model.cr_pull()
                    self.g = pull == PullResult.Standard_5_Star
                    return pull
                else:
                    self.g = True
                    return PullResult.Standard_5_Star
        elif x < prob5 + prob4:
            self.counter5 += 1
            self.counter4 = 1
            return PullResult.Standard_4_Star
        else:
            self.counter5 += 1
            self.counter4 += 1
            return PullResult.Standard_3_Star

    def batch_pull_count(self, pulls: int):

        featured_rolls = 0
        standard_rolls = 0
        for _ in range(pulls):
            match self.pull():
                case PullResult.Featured_5_Star:
                    featured_rolls += 1
                case PullResult.Standard_5_Star:
                    standard_rolls += 1
                case _:
                    continue

        return featured_rolls, standard_rolls


class CapturingRadianceModel:

    def __init__(
            self,
            rng: Random,
            cr: int = 0,
            version: int = 1,
            ) -> None:

        self.cr = cr
        self.rng = rng
        self.version = version

    def cr_pull(self):

        match self.version:
            case 4:
                return self.cr_pull_v4()
            case 3:
                return self.cr_pull_v3()
            case 2:
                return self.cr_pull_v2()
            case 1:
                return self.cr_pull_v1()
            case _:
                return self.cr_pull_v0()

    def cr_pull_v0(self):
        """
        Always standard. Effectively disables the CR system.
        """

        return PullResult.Standard_5_Star

    def cr_pull_v1(self):
        """
        2 standard states followed by a 50/50 on the 3rd state.
        and a guarantee on the 4th state. (4 states total, currently
        the best representation of the in-game system)
        """

        if self.cr == 0:
            self.cr = 1
            return PullResult.Standard_5_Star
        elif self.cr == 1:
            self.cr = 2
            return PullResult.Standard_5_Star
        elif self.cr == 2:
            if self.rng.random() < 0.5:
                self.cr = 0
                return PullResult.Featured_5_Star
            else:
                self.cr = 3
                return PullResult.Standard_5_Star
        else:
            self.cr = 0
            return PullResult.Featured_5_Star

    def cr_pull_v2(self):
        """
        1 standard state followed by a 50/50 on the 2nd state.
        and a guarantee on the 3rd state. (3 states total)
        """

        if self.cr == 0:
            self.cr = 1
            return PullResult.Standard_5_Star
        elif self.cr == 1:
            if self.rng.random() < 0.5:
                self.cr = 0
                return PullResult.Featured_5_Star
            else:
                self.cr = 2
                return PullResult.Standard_5_Star
        else:
            self.cr = 0
            return PullResult.Featured_5_Star

    def cr_pull_v3(self):
        """
        4 states total. First one is standard, then 25/75, then 50/50, then guaranteed.
        """

        if self.cr == 0:
            self.cr = 1
            return PullResult.Standard_5_Star
        elif self.cr == 1:
            if self.rng.random() < 0.25:
                self.cr = 0
                return PullResult.Featured_5_Star
            else:
                self.cr = 2
                return PullResult.Standard_5_Star
        elif self.cr == 2:
            if self.rng.random() < 0.50:
                self.cr = 0
                return PullResult.Featured_5_Star
            else:
                self.cr = 3
                return PullResult.Standard_5_Star
        else:
            self.cr = 0
            return PullResult.Featured_5_Star

    def cr_pull_v4(self):
        """
        4 states total. 25/75, then 50/50, then 75/25, then guaranteed.
        """

        if self.cr == 0:
            if self.rng.random() < 0.25:
                self.cr = 0
                return PullResult.Featured_5_Star
            else:
                self.cr = 1
                return PullResult.Standard_5_Star
        elif self.cr == 1:
            if self.rng.random() < 0.50:
                self.cr = 0
                return PullResult.Featured_5_Star
            else:
                self.cr = 2
                return PullResult.Standard_5_Star
        elif self.cr == 2:
            if self.rng.random() < 0.75:
                self.cr = 0
                return PullResult.Featured_5_Star
            else:
                self.cr = 3
                return PullResult.Standard_5_Star
        else:
            self.cr = 0
            return PullResult.Featured_5_Star
