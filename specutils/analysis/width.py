import numpy as np
from astropy.stats.funcs import gaussian_sigma_to_fwhm
from ..spectra import SpectralRegion
from ..manipulation import extract_region
from . import centroid


__all__ = ['gaussian_sigma_width', 'gaussian_fwhm', 'fwhm']


def _computation_wrapper(func, spectrum, region):

    # No region, therefore whole spectrum.
    if region is None:
        return func(spectrum)

    # Single region
    elif isinstance(region, SpectralRegion):
        return func(spectrum, region=region)

    # List of regions
    elif isinstance(region, list):
        return [func(spectrum, region=reg) for reg in region]


def gaussian_sigma_width(spectrum, region=None):
    """
    Estimate the width of the spectrum using a second-moment analysis.
    
    The value is scaled to match the sigma/standard deviation parameter of a
    standard Gaussian profile. This will be calculated over the regions, if
    they are specified.

    Parameters
    ----------
    spectrum : `~specutils.spectra.spectrum1d.Spectrum1D`
        The spectrum object over which the width will be calculated.

    region: `~specutils.utils.SpectralRegion` or list of `~specutils.utils.SpectralRegion`
        Region within the spectrum to calculate the gaussian sigma width. If
        region is `None`, computation is performed over entire spectrum.

    Returns
    -------
    approx_sigma: `~astropy.units.Quantity` or list (based on region input)
        Approximated sigma value of the spectrum

    Notes
    -----
    The spectrum should be continuum subtracted before being passed to this
    function.
    """
    return _computation_wrapper(_compute_gaussian_sigma_width, spectrum, region)


def gaussian_fwhm(spectrum, region=None):
    """
    Estimate the width of the spectrum using a second-moment analysis.
    
    The value is scaled to match the full width at half max of a standard
    Gaussian profile.  This will be calculated over the regions, if they are
    specified.

    Parameters
    ----------
    spectrum : `~specutils.spectra.spectrum1d.Spectrum1D`
        The spectrum object overwhich the width will be calculated.

    region: `~specutils.utils.SpectralRegion` or list of `~specutils.utils.SpectralRegion`
        Region within the spectrum to calculate the FWHM value. If region is
        `None`, computation is performed over entire spectrum.

    Returns
    -------
    gaussian_fwhm : `~astropy.units.Quantity` or list (based on region input)
        Approximate full width of the signal at half max

    Notes
    -----
    The spectrum should be continuum subtracted before being passed to this
    function.
    """
    return _computation_wrapper(_compute_gaussian_fwhm, spectrum, region)


def fwhm(spectrum, region=None):
    """
    Compute the true full width half max of the spectrum.
    
    This makes no assumptions about the shape of the spectrum (e.g. whether it
    is Gaussian). It finds the maximum of the spectrum, and then locates the
    point closest to half max on either side of the maximum, and
    measures the distance between them. This will be calculated over the
    regions, if they are specified. 

    Parameters
    ----------
    spectrum : `~specutils.spectra.spectrum1d.Spectrum1D`
        The spectrum object over which the width will be calculated.

    region: `~specutils.utils.SpectralRegion` or list of `~specutils.utils.SpectralRegion`
        Region within the spectrum to calculate the FWHM value. If region is
        `None`, computation is performed over entire spectrum.

    Returns
    -------
    whm : `~astropy.units.Quantity` or list (based on region input)
        Full width of the signal at half max

    Notes
    -----
    The spectrum should be continuum subtracted before being passed to this
    function.
    """
    return _computation_wrapper(_compute_fwhm, spectrum, region)


def _compute_gaussian_fwhm(spectrum, region=None):
    """
    This is a helper function for the above `gaussian_fwhm()` method.
    """

    fwhm = _compute_gaussian_sigma_width(spectrum, region) * gaussian_sigma_to_fwhm

    return fwhm


def _compute_gaussian_sigma_width(spectrum, region=None):
    """
    This is a helper function for the above `gaussian_sigma_width()` method.
    """

    if region is not None:
        calc_spectrum = extract_region(spectrum, region)
    else:
        calc_spectrum = spectrum

    flux = calc_spectrum.flux
    spectral_axis = calc_spectrum.spectral_axis

    centroid_result = centroid(spectrum, region)

    if flux.ndim > 1:
        spectral_axis = np.broadcast_to(spectral_axis, flux.shape) * spectral_axis.unit
        centroid_result = centroid_result[:, np.newaxis]

    dx = spectral_axis - centroid_result
    sigma = np.sqrt(np.sum((dx * dx) * flux, axis=-1) / np.sum(flux, axis=-1))

    return sigma


def _compute_single_fwhm(flux, spectral_axis):

    argmax = np.argmax(flux)
    halfval = flux[argmax] / 2

    left = flux[:argmax] <= halfval
    right = flux[argmax+1:] <= halfval

    l_idx = np.where(left == True)[0][-1]
    r_idx = np.where(right == True)[0][0] + argmax

    return spectral_axis[r_idx] - spectral_axis[l_idx]


def _compute_fwhm(spectrum, region=None):
    """
    This is a helper function for the above `fwhm()` method.
    """

    if region is not None:
        calc_spectrum = extract_region(spectrum, region)
    else:
        calc_spectrum = spectrum

    flux = calc_spectrum.flux
    spectral_axis = calc_spectrum.spectral_axis

    if flux.ndim > 1:
        return [_compute_single_fwhm(x, spectral_axis) for x in flux]
    else:
        return _compute_single_fwhm(flux, spectral_axis)