use pyo3::prelude::*;
use fastrand;
use std::sync::{Arc, Mutex};
use std::thread;
use std::collections::HashMap;


#[pyclass(eq, eq_int)]
#[derive(PartialEq, Eq)]
pub enum PullResult {
    Standard3Star,
    Standard4Star,
    Standard5Star,
    Featured5Star,
}


#[pyclass]
#[derive(Clone)]
pub struct CapturingRadianceModel {
    #[pyo3(get, set)]
    cr: i32,
    #[pyo3(get, set)]
    version: i32,
}

#[pymethods]
impl CapturingRadianceModel {

    #[new]
    #[pyo3(signature = (cr=0, version=2))]
    fn new(
        cr: i32,
        version: i32
    ) -> Self {

        Self {
            cr,
            version
        }

    }

    fn pull(
        &mut self,
    ) -> PullResult {

        match self.version {
            3 => self.pull_v3(),
            2 => self.pull_v2(),
            1 => self.pull_v1(),
            _ => self.pull_v0(),
        }

    }

    /// Always 50/50. This is the system before CR was introduced.
    /// Using this mode effectively disables the CR system.
    fn pull_v0(
        &mut self,
    ) -> PullResult {

        if fastrand::f64() < 0.5 {
            PullResult::Featured5Star
        } else {
            PullResult::Standard5Star
        }

    }

    /// 10% chance to trigger CR and win if you lost the 50/50.
    /// This is what people initially thought the system was.
    fn pull_v1(
        &mut self,
    ) -> PullResult {

        if fastrand::f64() < 0.5 {
            PullResult::Featured5Star
        } else if fastrand::f64() < 0.1 {
            PullResult::Featured5Star
        } else {
            PullResult::Standard5Star
        }

    }

    /// The current best representation of the in-game system. See README.
    fn pull_v2(
        &mut self,
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
                if fastrand::f64() < 0.5 {
                    self.cr = 0;
                    PullResult::Featured5Star
                } else {
                    self.cr = 1;
                    PullResult::Standard5Star
                }
            }
            1 => {
                if fastrand::f64() < 0.5 {
                    self.cr = 0;
                    PullResult::Featured5Star
                } else {
                    self.cr = 2;
                    PullResult::Standard5Star
                }
            }
            2 => {
                if fastrand::f64() < p {
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
    fn pull_v3(
        &mut self,
    ) -> PullResult {

        match self.cr {
            0 => {
                if fastrand::f64() < 0.25 {
                    self.cr = 0;
                    PullResult::Featured5Star
                } else {
                    self.cr = 1;
                    PullResult::Standard5Star
                }
            }
            1 => {
                if fastrand::f64() < 0.50 {
                    self.cr = 0;
                    PullResult::Featured5Star
                } else {
                    self.cr = 2;
                    PullResult::Standard5Star
                }
            }
            2 => {
                if fastrand::f64() < 0.75 {
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


#[pyclass]
#[derive(Clone)]
struct GenshinImpactGachaModel {
    #[pyo3(get, set)]
    g: bool,
    #[pyo3(get, set)]
    cr_model: CapturingRadianceModel,
    #[pyo3(get)]
    rate5: f64,
    #[pyo3(get)]
    rate4: f64,
    #[pyo3(get)]
    rateup5: f64,
    #[pyo3(get)]
    rateup4: f64,
    #[pyo3(get)]
    softpt5: i32,
    #[pyo3(get)]
    softpt4: i32,
    #[pyo3(get, set)]
    counter5: i32,
    #[pyo3(get, set)]
    counter4: i32,
}


#[pymethods]
impl GenshinImpactGachaModel {

    #[new]
    #[pyo3(signature = (pt, g, cr_model, seed))]
    fn new(
        pt: i32,
        g: bool,
        cr_model: CapturingRadianceModel,
        seed: u64
    ) -> Self {

        fastrand::seed(seed);

        let rate5 = 0.006;
        let rate4 = 0.051;

        Self {
            g,
            cr_model,
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

    fn pull(
        &mut self
    ) -> PullResult {

        let x = fastrand::f64();

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
                let pull = self.cr_model.pull();
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

    #[pyo3(signature = (pulls))]
    fn batch_pull_count(
        &mut self,
        pulls: i32
    ) -> (i32, i32) {

        let mut featured_rolls = 0;
        let mut standard_rolls = 0;

        for _ in 0..pulls {
            match self.pull() {
                PullResult::Featured5Star => featured_rolls += 1,
                PullResult::Standard5Star => standard_rolls += 1,
                _ => continue,
            }
        }

        (featured_rolls, standard_rolls)

    }

}


#[pyclass]
#[derive(Clone)]
struct SimulationResult {
    #[pyo3(get)]
    featured_rolls: HashMap<i32, i32>,
    #[pyo3(get)]
    standard_rolls: HashMap<i32, i32>,
    #[pyo3(get)]
    total_rolls: HashMap<i32, i32>,
    #[pyo3(get)]
    joint_rolls: HashMap<(i32, i32), i32>,
    #[pyo3(get)]
    simulation_count: i32,
}

#[pymethods]
impl SimulationResult {

    #[new]
    fn new() -> Self {

        Self {
            featured_rolls: HashMap::new(),
            standard_rolls: HashMap::new(),
            total_rolls: HashMap::new(),
            joint_rolls: HashMap::new(),
            simulation_count: 0,
        }

    }

}


#[pyclass]
#[derive(Clone)]
struct SimulationThread {
    model: Arc<Mutex<GenshinImpactGachaModel>>,
    pulls: i32,
    running: Arc<Mutex<bool>>,
    simulation_result: Arc<Mutex<SimulationResult>>,
}


#[pymethods]
impl SimulationThread {

    #[new]
    #[pyo3(signature = (model, pulls))]
    fn new(
        model: GenshinImpactGachaModel,
        pulls: i32,
    ) -> Self {
        
        Self {
            model: Arc::new(Mutex::new(model)),
            pulls,
            running: Arc::new(Mutex::new(false)),
            simulation_result: Arc::new(Mutex::new(SimulationResult::new())),
        }

    }

    fn run(
        &mut self
    ) {

        thread::spawn({
            let running = Arc::clone(&self.running);
            let simulation_result = Arc::clone(&self.simulation_result);
            let model = Arc::clone(&self.model);
            let pulls = self.pulls;

            move || {
                *running.lock().unwrap() = true;

                while *running.lock().unwrap() {
                    let mut ml_lock = model.lock().unwrap();
                    let (featured, standard) = ml_lock.batch_pull_count(pulls);

                    let mut sr_lock = simulation_result.lock().unwrap();
                    sr_lock.simulation_count += 1;
                    *sr_lock.featured_rolls.entry(featured).or_insert(0) += 1;
                    *sr_lock.standard_rolls.entry(standard).or_insert(0) += 1;
                    *sr_lock.total_rolls.entry(featured + standard).or_insert(0) += 1;
                    *sr_lock.joint_rolls.entry((featured, standard)).or_insert(0) += 1;
                }

                *running.lock().unwrap() = false;
            }
        });

    }

    fn stop(
        &mut self
    ) {

        *self.running.lock().unwrap() = false;

    }

    fn is_running(
        &self
    ) -> bool {

        *self.running.lock().unwrap()

    }

    fn get_current_results(
        &self
    ) -> SimulationResult {

        self.simulation_result.lock().unwrap().clone()

    }

}


/// A Python module implemented in Rust.
#[pymodule]
fn gachamodel(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PullResult>()?;
    m.add_class::<GenshinImpactGachaModel>()?;
    m.add_class::<CapturingRadianceModel>()?;
    m.add_class::<SimulationThread>()?;
    m.add_class::<SimulationResult>()?;
    Ok(())
}
