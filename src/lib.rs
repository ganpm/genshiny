use pyo3::prelude::*;
use fastrand::Rng as Rng;

#[pyclass(eq, eq_int)]
#[derive(PartialEq, Eq)]
pub enum PullResult {
    Standard3Star,
    Standard4Star,
    Standard5Star,
    Featured5Star,
}

#[pyclass]
struct GenshinImpactGachaModel {
    rng: Rng,
    cr_model: CapturingRadianceModel,
    g: bool,
    rate5: f64,
    rate4: f64,
    rateup5: f64,
    rateup4: f64,
    softpt5: i32,
    softpt4: i32,
    counter5: i32,
    counter4: i32,
}

impl GenshinImpactGachaModel {

    pub fn pull(
        &mut self
    ) -> PullResult {

        let x: f64 = self.rng.f64();

        let prob5 = if self.counter5 <= self.softpt5 {
            self.rate5
        } else {
            self.rateup5 * (self.counter5 - self.softpt5) as f64 + self.rate5
        };

        let prob4 = if self.counter4 <= self.softpt4 {
            self.rate4
        } else {
            self.rateup4 * (self.counter4 - self.softpt4) as f64 + self.rate4
        };

        if x < prob5 {
            self.counter5 = 1;
            self.counter4 += 1;
            if self.g {
                self.g = false;
                PullResult::Featured5Star
            } else {
                let pull = self.cr_model.cr_pull(&mut self.rng);
                self.g = pull == PullResult::Standard5Star;
                pull
            }
        } else if x < prob5 + prob4 {
            self.counter5 += 1;
            self.counter4 = 1;
            PullResult::Standard4Star
        } else {
            self.counter5 += 1;
            self.counter4 += 1;
            PullResult::Standard3Star
        }

    }

}


#[pymethods]
impl GenshinImpactGachaModel {

    #[new]
    #[pyo3(signature = (pt, cr, guaranteed, seed, version=2))]
    pub fn new(
        pt: i32,
        cr: i32,
        guaranteed: bool,
        seed: u64,
        version: i32,
    ) -> Self {

        let rng = Rng::with_seed(seed);
        let cr_model = CapturingRadianceModel::new(cr, version);

        let rate5 = 0.006;
        let rate4 = 0.051;

        Self {
            rng,
            cr_model,
            g: guaranteed,
            rate5,
            rate4,
            rateup5: 10.0 * rate5,
            rateup4: 10.0 * rate4,
            softpt5: 73,
            softpt4: 8,
            counter5: pt,
            counter4: 0,
        }

    }

    pub fn batch_pull_count(
        &mut self,
        pulls: i32
    ) -> PyResult<(i32, i32)> {

        let mut featured_rolls = 0;
        let mut standard_rolls = 0;

        for _ in 0..pulls {
            match self.pull() {
                PullResult::Featured5Star => featured_rolls += 1,
                PullResult::Standard5Star => standard_rolls += 1,
                _ => continue,
            }
        }

        Ok((featured_rolls, standard_rolls))

    }

}

pub struct CapturingRadianceModel {
    cr: i32,
    version: i32,
}

impl CapturingRadianceModel {

    pub fn new(
        cr: i32,
        version: i32
    ) -> Self {

        println!("Using CR model version {}", version);
        Self { cr, version }

    }

    pub fn cr_pull(
        &mut self,
        rng: &mut Rng
    ) -> PullResult {

        match self.version {
            3 => self.cr_pull_v3(rng),
            2 => self.cr_pull_v2(rng),
            1 => self.cr_pull_v1(rng),
            _ => self.cr_pull_v0(rng),
        }

    }

    /// Always 50/50. This is the system before CR was introduced.
    /// Using this mode effectively disables the CR system.
    fn cr_pull_v0(
        &mut self,
        rng: &mut Rng
    ) -> PullResult {

        if rng.f64() < 0.5 {
            PullResult::Featured5Star
        } else {
            PullResult::Standard5Star
        }

    }

    /// 10% chance to trigger CR and win if you lost the 50/50.
    /// This is what people initially thought the system was.
    fn cr_pull_v1(
        &mut self,
        rng: &mut Rng
    ) -> PullResult {

        if rng.f64() < 0.5 {
            PullResult::Featured5Star
        } else if rng.f64() < 0.1 {
            PullResult::Featured5Star
        } else {
            PullResult::Standard5Star
        }

    }

    /// The current best representation of the in-game system. See README.
    fn cr_pull_v2(
        &mut self,
        rng: &mut Rng
    ) -> PullResult {

        // 4 states total.
        // cr = 0:
        //     50% Featured, cr = 0
        //     50% Standard, cr = 1
        // cr = 1:
        //     50% Featured, cr = 0
        //     50% Standard, cr = 2
        // cr = 2:
        //     p Featured, cr = 1
        //     1-p Standard, cr = 3
        // cr = 3:
        //     100% Featured, cr = 1
        //
        // The value of p here is the combined probability of triggering
        // CR and winning 50/50, since this model currently does not
        // distinguish between the two. According to analysis online,
        // this value is said to be between 52% and 60%.
        // Empirical analysis suggests this value to be 6/11 or ~54.55%.

        let p = 0.5454545454545454;
        match self.cr {
            0 => {
                if rng.f64() < 0.5 {
                    self.cr = 0;
                    PullResult::Featured5Star
                } else {
                    self.cr = 1;
                    PullResult::Standard5Star
                }
            }
            1 => {
                if rng.f64() < 0.5 {
                    self.cr = 0;
                    PullResult::Featured5Star
                } else {
                    self.cr = 2;
                    PullResult::Standard5Star
                }
            }
            2 => {
                if rng.f64() < p {
                    self.cr = 1;
                    PullResult::Featured5Star
                } else {
                    self.cr = 3;
                    PullResult::Standard5Star
                }
            }
            _ => {
                self.cr = 1;
                PullResult::Featured5Star
            }
        }

    }

    /// 4 states total. 25/75, then 50/50, then 75/25, then 100/0.
    /// Moves up a state on losing, down a state on winning.
    fn cr_pull_v3(
        &mut self,
        rng: &mut Rng
    ) -> PullResult {

        match self.cr {
            0 => {
                if rng.f64() < 0.25 {
                    self.cr = 0;
                    PullResult::Featured5Star
                } else {
                    self.cr = 1;
                    PullResult::Standard5Star
                }
            }
            1 => {
                if rng.f64() < 0.50 {
                    self.cr = 0;
                    PullResult::Featured5Star
                } else {
                    self.cr = 2;
                    PullResult::Standard5Star
                }
            }
            2 => {
                if rng.f64() < 0.75 {
                    self.cr = 1;
                    PullResult::Featured5Star
                } else {
                    self.cr = 3;
                    PullResult::Standard5Star
                }
            }
            _ => {
                self.cr = 2;
                PullResult::Featured5Star
            }
        }

    }

}

/// A Python module implemented in Rust.
#[pymodule]
fn gachamodel(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<GenshinImpactGachaModel>()?;
    m.add_class::<PullResult>()?;
    Ok(())
}
