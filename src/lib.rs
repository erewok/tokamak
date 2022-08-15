use pyo3::prelude::*;

pub mod radix_tree;

use radix_tree::parsing;

/// A Python module implemented in Rust.
#[pymodule]
fn tokamak_rs(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(radix_tree::parsing::first_nonequal_idx, m)?)?;
    Ok(())
}
