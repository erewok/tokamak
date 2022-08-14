use std::cmp::min;
use std::iter::zip;

use pyo3::prelude::*;


/// Find the first non-matching index in two strings
#[pyfunction]
fn first_nonequal_idx(left: &str, right: &str) -> usize {
    let mut idx: usize = 0;
    let mut chars_iter = zip(left.chars(), right.chars());

    let max_search_len = min(left.len(), right.len());
    while idx < max_search_len {
        match chars_iter.next() {
            None => break,
            Some((a, b)) => {
                if a == b {
                    idx += 1;
                } else {
                    break;
                }

            }
        }
    }
    idx
}

/// A Python module implemented in Rust.
#[pymodule]
fn tokamak_rs(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(first_nonequal_idx, m)?)?;
    Ok(())
}