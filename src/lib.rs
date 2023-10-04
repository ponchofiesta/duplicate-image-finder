use image::GenericImage;
use image::ImageBuffer;
use imageproc::stats::histogram;
use pyo3::exceptions::PyException;
use pyo3::prelude::*;

/// Formats the sum of two numbers as string.
#[pyfunction]
fn get_histograms_from_image(path: &str) -> PyResult<Vec<[u32; 256]>> {
    match image::open(path) {
        Ok(img) => {
            let mut buffer = ImageBuffer::new(img.width(), img.height());
            buffer.copy_from(&img, 0, 0).unwrap();
            let histograms = histogram(&buffer);
            Ok(histograms.channels)
        }
        Err(error) => Err(PyException::new_err(error.to_string())),
    }
}

#[pymodule]
fn image_utils(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(get_histograms_from_image, m)?)?;
    Ok(())
}
