use indexmap::IndexMap;
use pyo3::prelude::*;
use fastrand;
use std::sync::{Arc, Mutex};
use std::thread;
use std::time::{Instant, Duration};


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
    #[pyo3(get, set)]
    seed: u64,
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

        let rate5 = 0.006;
        let rate4 = 0.051;

        Self {
            g,
            cr_model,
            seed,
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
    featured_rolls: IndexMap<i32, i32>,
    #[pyo3(get)]
    standard_rolls: IndexMap<i32, i32>,
    #[pyo3(get)]
    total_rolls: IndexMap<i32, i32>,
    #[pyo3(get)]
    joint_rolls: IndexMap<(i32, i32), i32>,
    #[pyo3(get)]
    simulation_count: i32,
    #[pyo3(get)]
    ftd_range: (i32, i32),
    #[pyo3(get)]
    std_range: (i32, i32),
    #[pyo3(get)]
    sim_duration: Duration,

}

#[pymethods]
impl SimulationResult {

    #[new]
    fn new() -> Self {

        Self {
            featured_rolls: IndexMap::new(),
            standard_rolls: IndexMap::new(),
            total_rolls: IndexMap::new(),
            joint_rolls: IndexMap::new(),
            simulation_count: 0,
            ftd_range: (0, 0),
            std_range: (0, 0),
            sim_duration: Duration::new(0, 0),
        }

    }

}


impl SimulationResult {

    fn update(
        &mut self,
        featured: i32,
        standard: i32,
    ) {

        self.simulation_count += 1;
        *self.featured_rolls.entry(featured).or_insert(0) += 1;
        *self.standard_rolls.entry(standard).or_insert(0) += 1;
        *self.total_rolls.entry(featured + standard).or_insert(0) += 1;
        *self.joint_rolls.entry((featured, standard)).or_insert(0) += 1;

    }

    fn fill_range(
        &self,
    ) -> SimulationResult {

        let ftd_min = *self.featured_rolls.keys().min().unwrap_or(&0);
        let ftd_max = *self.featured_rolls.keys().max().unwrap_or(&0);
        let std_min = *self.standard_rolls.keys().min().unwrap_or(&0);
        let std_max = *self.standard_rolls.keys().max().unwrap_or(&0);
        let tot_min = *self.total_rolls.keys().min().unwrap_or(&0);
        let tot_max = *self.total_rolls.keys().max().unwrap_or(&0);

        let featured_rolls: IndexMap<i32, i32> = (ftd_min..=ftd_max)
            .map(|ftd| {
                let count = *self.featured_rolls.get(&ftd).unwrap_or(&0);
                (ftd, count)
            })
            .collect();

        let standard_rolls: IndexMap<i32, i32> = (std_min..=std_max)
            .map(|std| {
                let count = *self.standard_rolls.get(&std).unwrap_or(&0);
                (std, count)
            })
            .collect();

        let total_rolls: IndexMap<i32, i32> = (tot_min..=tot_max)
            .map(|total| {
                let count = *self.total_rolls.get(&total).unwrap_or(&0);
                (total, count)
            })
            .collect();

        let joint_rolls = self.joint_rolls.clone();

        SimulationResult {
            featured_rolls,
            standard_rolls,
            total_rolls,
            joint_rolls,
            simulation_count: self.simulation_count,
            ftd_range: (ftd_min, ftd_max),
            std_range: (std_min, std_max),
            sim_duration: self.sim_duration,
        }
    }

}


#[pyclass]
#[derive(Clone)]
struct SimulationThread {
    model: GenshinImpactGachaModel,
    pulls: i32,
    sim_length: i32,
    running: Arc<Mutex<bool>>,
    simulation_result: Arc<Mutex<SimulationResult>>,
}


#[pymethods]
impl SimulationThread {

    #[new]
    #[pyo3(signature = (model, pulls, sim_length))]
    fn new(
        model: GenshinImpactGachaModel,
        pulls: i32,
        sim_length: i32,
    ) -> Self {
        
        Self {
            model,
            pulls,
            sim_length,
            running: Arc::new(Mutex::new(false)),
            simulation_result: Arc::new(Mutex::new(SimulationResult::new())),
        }

    }

    fn run(
        &mut self
    ) {

        // Simulation thread
        thread::spawn({
            let running = Arc::clone(&self.running);
            let sim_result = Arc::clone(&self.simulation_result);
            let mut model = self.model.clone();
            let seed = self.model.seed;
            let pulls = self.pulls;
            let sim_length = self.sim_length;

            move || {
                *running.lock().unwrap() = true;
                let mut sim_count = 0;

                let start_time = Instant::now();
                fastrand::seed(seed);

                while *running.lock().unwrap() && sim_count < sim_length {

                    let (featured, standard) = model.batch_pull_count(pulls);
                    sim_result.lock().unwrap().update(featured, standard);

                    sim_count += 1;
                }

                let elapsed = start_time.elapsed();
                sim_result.lock().unwrap().sim_duration = elapsed;

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

        let sr_lock = self.simulation_result.lock().unwrap();
        let data = sr_lock.clone();
        drop(sr_lock);
        data.fill_range()

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
