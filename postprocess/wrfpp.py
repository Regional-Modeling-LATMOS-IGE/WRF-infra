# Copyright (c) 2025 LATMOS (France, UMR 8190) and IGE (France, UMR 5001).
#
# License: BSD 3-clause "new" or "revised" license (BSD-3-Clause).

"""Module wrfpp: an xarray dataset accessor for WRF and WRF-Chem outputs.

References
----------

The WRF model:
    The development of the WRF atmospheric model is chaperoned by UCAR
    (University Corporation for Atmospheric Research). The WRF model code is
    released into the public domain (although the name "WRF" is a registered
    trademark of UCAR).

    It is currently hosted on GitHub:

    https://github.com/wrf-model/WRF

    And mirrored on Software Heritage:

    https://archive.softwareheritage.org/swh:1:dir:6b658fbc98077fe0648cba724921679126464181

"""

# Required imports
from abc import ABC, abstractmethod
import warnings
import numpy as np
import xarray as xr

# Optional imports
try:
    import pyproj
except ImportError:
    pass
try:
    import cartopy
except ImportError:
    pass

# The following constants that are marked with ** use the same values as in
# the WRF model code (WRF/share/module_model_constants.F). We use SI units for
# all constants
constants = dict(
    pot_temp_t0=300,  # Base state potential temperature (K)**
    pot_temp_p0=1e5,  # Base state surface pressure for potential temp. (Pa)**
    r_air=287,  # Specific gas constant of dry air (J kg-1 K-1)**
    cp_air=1004.5,  # Heat cap. of dry air at constant pressure (J kg-1 K-1)**
    mm_dryair=28.966e-3,  # Molar mass of dry air (kg mol-1)**
    mm_water=18.015e-3,  # Molar mass of water (kg mol-1)
)


def _transformer_from_crs(crs, reverse=False):
    """Return the pyproj Transformer corresponding to given CRS.

    Parameters
    ----------
    crs : pyproj.CRS
        The CRS object that represents the projected coordinate system.
    reverse : bool
        The direction of the Transformer:
         - False: from (lon,lat) to (x,y).
         - True: from (x,y) to (lon,lat).

    Returns
    -------
    pyproj.Transformer
        An object that converts (lon,lat) to (x,y), or the other way around if
        reverse is True.

    """
    fr = crs.geodetic_crs
    to = crs
    if reverse:
        fr, to = to, fr
    return pyproj.Transformer.from_crs(fr, to, always_xy=True)


def _units_mpl(units):
    """Return given units, formatted for displaying on Matplotlib plots.

    Parameters:
    -----------
    units : str
        The units to format (eg. "km s-1").

    Returns:
    --------
    str
        The units formatted for Matplotlib (eg. "km s$^{-1}$").

    """
    split = units.split()
    for i, s in enumerate(split):
        n = len(s) - 1
        while n >= 0 and s[n] in "-0123456789":
            n -= 1
        if n < 0:
            raise ValueError("Could not process units.")
        if n != len(s):
            split[i] = "%s$^{%s}$" % (s[: n + 1], s[n + 1 :])
    return " ".join(split)


def _get_nearest_indices(lon, lat, gridlons, gridlats, dx, dy):
    """Return indices (j, i) of gridpoint nearest to (lon, lat).

    Parameters
    ----------
    lat, lon : float or int
        Target coordinate in degrees.
    gridlons, gridlats : np.ndarray
        2D arrays of longitudes and latitudes for the model grid.
    dx, dy : float
        Grid spacing in metres.

    Returns
    -------
    tuple of int
        Indices (j, i) of the nearest grid point.

    Raises
    ------
    ValueError
        If the target point lies outside the model domain.
    """
    geod = pyproj.Geod(ellps="WGS84")
    _, _, dists = geod.inv(
        lon * np.ones(gridlons.shape),
        lat * np.ones(gridlats.shape),
        gridlons,
        gridlats,
    )

    max_dist = np.sqrt(dx**2 + dy**2) / 2
    if np.amin(dists) > max_dist:
        raise ValueError(f"Point ({lat}, {lon}) is outside model domain.")

    j, i = np.unravel_index(np.argmin(dists), gridlons.shape)
    return j, i


class GenericDatasetAccessor(ABC):
    """Template for xarray dataset accessors.

    Parameters
    ----------
    dataset: xarray dataset
        The xarray dataset instance for which the accessor is defined.

    """

    def __init__(self, dataset):
        self._dataset = dataset

    # Emulate the interface of xarray datasets

    def __getitem__(self, *args, **kwargs):
        return self._dataset.__getitem__(*args, **kwargs)

    @property
    def dims(self):
        return self._dataset.dims

    @property
    def sizes(self):
        return self._dataset.sizes

    @property
    def attrs(self):
        return self._dataset.attrs

    def close(self, *args, **kwargs):
        return self._dataset.close(*args, **kwargs)

    # Facilities for dealing with units

    def units(self, varname):
        """Return units of given variable.

        Parameters
        ----------
        varname : str
            The name of the variable in the NetCDF file.

        Returns
        -------
        str
            The units of this variable as defined in the NetCDF file.

        """
        attrs = self[varname].attrs
        try:
            units = attrs["units"]
        except KeyError:
            units = attrs["unit"]
        return units

    def units_nice(self, varname):
        """Return units of given variable, in a predictible format.

        Predictable format:

         - uses single spaces to separate the dimensions in the units

         - uses negative exponents instead of division symbols

         - always orders dimensions in this order: mass, length, time

         - never uses parentheses

        Parameters
        ----------
        varname : str
            The name of the variable in the NetCDF file.

        Returns
        -------
        str
            The formatted units (or None for dimensionless variables).

        """
        units = self.units(varname)
        replacements = {
            "-": None,
            "1": None,
            "m2/s2": "m2 s-2",
            "kg/m2": "kg m-2",
            "kg/(s*m2)": "kg m-2 s-1",
            "kg/(m2*s)": "kg m-2 s-1",
            "kg/m2/s": "kg m-2 s-1",
            "W m{-2}": "W m-2",
        }
        try:
            units = replacements[units]
        except KeyError:
            pass
        return units

    def check_units(self, varname, expected, nice=True):
        """Make sure that units of given variable are as expected.

        Parameters
        ----------
        varname : str
            The name of the variable to check.
        expected : str
            The expected units.
        nice : bool
            Whether expected units are given as "nice" units
            (cf. method units_nice)

        Raises
        ------
        ValueError
            If the units are not as expected.

        """
        if nice:
            actual = self.units_nice(varname)
        else:
            actual = self[varname].attrs["units"]
        if actual != expected:
            msg = 'Bad units: expected "%s", got "%s"' % (expected, actual)
            raise ValueError(msg)

    def units_mpl(self, varname):
        """Return the units of given variable, formatted for Matplotlib.

        Parameters
        ----------
        varname: str
            The name of the variable.

        Returns
        -------
        str
            The units of given variable, formatted for Matplotlib.

        """
        return _units_mpl(self.units_nice(varname))

    # Facilities for handling geographical projections

    @property
    @abstractmethod
    def crs_pyproj(self):
        """The CRS (pyproj) corresponding to dataset."""
        pass

    @property
    @abstractmethod
    def crs_cartopy(self):
        """The CRS (cartopy) corresponding to dataset."""
        pass

    @property
    def crs(self):
        """The CRS corresponding to the dataset.

        We choose here to return the cartopy CRS rather than the pyproj CRS
        because the cartopy CRS is a subclass of the pyproj CRS, so it
        potentially has additional functionalily.

        """
        return self.crs_cartopy

    def ll2xy(self, lon, lat):
        """Convert from (lon,lat) to (x,y).

        Parameters
        ----------
        lon: numeric (scalar, sequence, or numpy array)
            The longitude value(s).
        lat: numeric (scalar, sequence, or numpy array)
            The latitude value(s). Must have the same shape as "lon".

        Returns
        -------
        [numeric, numeric] (each has the same shape as lon and lat)
            The x and y values, respectively.

        """
        tr = _transformer_from_crs(self.crs)
        return tr.transform(lon, lat)

    def xy2ll(self, x, y):
        """Convert from (x,y) to (lon,lat).

        Parameters
        ----------
        x: numeric (scalar, sequence, or numpy array)
            The x value(s).
        y: numeric (scalar, sequence, or numpy array)
            The y value(s). Must have the same shape as "x".

        Returns
        -------
        [numeric, numeric] (each has the same shape as x and y)
            The longitude and latitude values, respectively.

        """
        tr = _transformer_from_crs(self.crs, reverse=True)
        return tr.transform(x, y)

    def value_around_point(self, lon, lat, method="centre"):
        """Return dataset around given location.

        Find 9 nearest gridpoints to a given coordinate (lon,lat)
        and return either the central gridpoint or a statistic (mean,
        min, max) over the 3×3 grid, depending on the chosen method.

        Parameters
        ----------
        lat : float or int
            The target latitude value
        lon : float or int
            The target longitude value
        method : {"centre", "mean", "min", "max"}, default="centre"
            Determines which value to return:
            - "centre": the gridpoint containing the target coordinate.
            - "mean": mean value over the 3×3 grid.
            - "min": minimum value over the 3×3 grid.
            - "max": maximum value over the 3×3 grid.

        Returns
        -------
        xarray.Dataset
            The data from the extracted gridpoint(s).

        Raises
        ------
        ValueError
            If `method` is not an expected value.

        ValueError
            If (lon,lat) is not within the model domain.

        """
        allowed = {"centre", "mean", "min", "max"}
        if method not in allowed:
            raise ValueError(
                f"Invalid mode: {method!r}. Expected one of {allowed}."
            )

        # Get (i,j) indices of model gridpoint containing (lon,lat)
        wrflons, wrflats = self.lonlat
        j, i = _get_nearest_indices(
            lon,
            lat,
            wrflons,
            wrflats,
            self._dataset.attrs["DX"],
            self._dataset.attrs["DY"],
        )

        # Extract from model output
        if method == "centre":
            extracted = self._dataset.isel(south_north=j, west_east=i)
        else:
            # make index arrays for 9 nearest points, making sure 0 < i < nx
            (ny, nx) = wrflons.shape
            imin, imax = max(0, i - 1), min(nx, i + 2)
            jmin, jmax = max(0, j - 1), min(ny, j + 2)
            islice = range(imin, imax)
            jslice = range(jmin, jmax)
            subset = self._dataset.isel(south_north=jslice, west_east=islice)
            if method == "mean":
                extracted = subset.mean(
                    dim=["south_north", "west_east"], keep_attrs=True
                )
            elif method == "min":
                extracted = subset.min(
                    dim=["south_north", "west_east"], keep_attrs=True
                )
            elif method == "max":
                extracted = subset.max(
                    dim=["south_north", "west_east"], keep_attrs=True
                )
        return extracted


@xr.register_dataset_accessor("wrf")
class WRFDatasetAccessor(GenericDatasetAccessor):
    """Accessor for WRF and WRF-Chem outputs.

    Parameters
    ----------
    dataset: xarray dataset
        The xarray dataset instance for which the accessor is defined.

    """

    # Facilities for handling geographical projections

    @property
    def crs_pyproj(self):
        """The pyproj CRS corresponding to dataset."""
        if self.attrs["POLE_LON"] != 0:
            raise ValueError("Invalid POLE_LON: %f." % self.attrs["POLE_LON"])
        if self.attrs["POLE_LAT"] not in (90, -90):
            raise ValueError("Invalid value for attribute POLE_LAT.")
        proj = self.attrs["MAP_PROJ"]
        if proj == 1:
            crs = self._crs_pyproj_lcc
        elif proj == 2:
            crs = self._crs_pyproj_polarstereo
        elif proj in (0, 102, 3, 4, 5, 6, 105, 203):
            raise NotImplementedError("Projection code %d." % proj)
        else:
            raise ValueError("Invalid projection code: %d." % proj)
        return crs

    @property
    def _crs_pyproj_lcc(self):
        """The pyproj CRS corresponding to dataset.

        This method handles the specific case of Lambert conformal conic
        projections.

        """
        proj_name = "Lambert Conformal Conic"
        map_proj_char = self.attrs.get("MAP_PROJ_CHAR", proj_name)
        if map_proj_char != proj_name:
            raise ValueError("Invalid value for MAP_PROJ_CHAR.")
        if self.attrs["STAND_LON"] != self.attrs["CEN_LON"]:
            raise ValueError("Inconsistency in central longitude values.")
        if self.attrs["MOAD_CEN_LAT"] != self.attrs["CEN_LAT"]:
            raise ValueError("Inconsistency in central latitude values.")
        proj = dict(
            proj="lcc",
            lat_0=self.attrs["CEN_LAT"],
            lon_0=self.attrs["CEN_LON"],
            lat_1=self.attrs["TRUELAT1"],
            lat_2=self.attrs["TRUELAT2"],
        )
        return pyproj.CRS.from_dict(proj)

    @property
    def _crs_pyproj_polarstereo(self):
        """The pyproj CRS corresponding to dataset.

        This method handles the specific case of polar stereographic
        projections.

        """
        proj_name = "Polar Stereographic"
        map_proj_char = self.attrs.get("MAP_PROJ_CHAR", proj_name)
        if map_proj_char != proj_name:
            raise ValueError("Invalid value for MAP_PROJ_CHAR.")
        if self.attrs["STAND_LON"] != self.attrs["CEN_LON"]:
            raise ValueError("Inconsistency in central longitude values.")
        for which in ("TRUELAT1", "TRUELAT2", "MOAD_CEN_LAT"):
            if round(self.attrs[which], 4) != round(self.attrs["CEN_LAT"], 4):
                raise ValueError("Inconsistency in true latitude values.")
        proj = dict(
            proj="stere",
            lat_0=self.attrs["POLE_LAT"],
            lat_ts=self.attrs["TRUELAT1"],
            lon_0=self.attrs["CEN_LON"],
        )
        return pyproj.CRS.from_dict(proj)

    @property
    def crs_cartopy(self):
        """The cartopy CRS corresponding to dataset."""
        # We let self.crs_pyproj do all the quality checking
        crs_pyproj = self.crs_pyproj
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            proj = crs_pyproj.to_dict()
        if proj["proj"] == "lcc":
            crs = cartopy.crs.LambertConformal(
                central_longitude=proj["lon_0"],
                central_latitude=proj["lat_0"],
                false_easting=proj["x_0"],
                false_northing=proj["y_0"],
                standard_parallels=(proj["lat_1"], proj["lat_2"]),
                globe=cartopy.crs.Globe(datum=proj["datum"]),
            )
        elif proj["proj"] == "stere":
            crs = cartopy.crs.Stereographic(
                central_longitude=proj["lon_0"],
                central_latitude=proj["lat_0"],
                false_easting=proj["x_0"],
                false_northing=proj["y_0"],
                true_scale_latitude=proj["lat_ts"],
                globe=cartopy.crs.Globe(datum=proj["datum"]),
            )
        else:
            raise ValueError("Unsupported projection: %s." % proj["proj"])
        return crs

    @property
    def lonlat(self):
        """Return the longitude and latitude arrays from the WRF grid.

        Returns
        -------
        tuple of np.ndarray
            The (lon, lat) arrays, with time dimension removed if present.
        """
        wrf = self._dataset
        lons, lats = wrf["XLONG"].values, wrf["XLAT"].values
        if "Time" in wrf.dims:
            lons = lons[0]
            lats = lats[0]
        return lons, lats

    # Derived variables

    @property
    def potential_temperature(self):
        """The DerivedVariable object to calculate potential temperature."""
        return WRFPotentialTemperature(self._dataset)

    @property
    def atm_pressure(self):
        """The DerivedVariable object to calculate atmopsheric pressure."""
        return WRFAtmPressure(self._dataset)

    @property
    def air_temperature(self):
        """The DerivedVariable object to calculate air temperature."""
        return WRFAirTemperature(self._dataset)

    @property
    def density_of_dry_air(self):
        """The DerivedVariable object to calculate dry air density."""
        return WRFDensityOfDryAir(self._dataset)

    @property
    def relative_humidity(self):
        """The DerivedVariable object to calculate relative humidity."""
        return WRFRelativeHumidity(self._dataset)

    @property
    def accumulated_precipitation(self):
        """The DerivedVariable object to calculate accumulated total precipitation."""
        return WRFAccumulatedPrecipitation(self._dataset)


class DerivedVariable(ABC):
    """Abstract class to define derived variables.

    Parameters
    ----------
    dataset: xarray.Dataset
        The dataset from which to calculate the derived variable.

    """

    def __init__(self, dataset):
        self._dataset = dataset

    @abstractmethod
    def __getitem__(self, *args):
        """The slicing method.

        Parameters
        ----------
        *args: slice
            Slice of interest in the WRF output. For example, if the variable
            of interest is 4-dimensional, use [:10, 0, :, :] to calculate its
            value for the first ten time steps, the first vertical layer, and
            the entire horizontal grid.

        Return
        ------
        xarray.DataArray
            The derived variable for given slice.

        """
        pass

    @property
    def values(self):
        """The values object corresponding to the derived variable.

        Returns
        -------
        np.array
            The values object corresponding to the derived variable.

        """
        return self[:].values

    def __str__(self):
        """String representation of the DataArray of the derived variable.

        Warnings
        --------
        If the dataset has been opened without activating dask, calling this
        method will calculate the entire array of the derived variable. This is
        inefficient for large data sets. This is not a problem if dask is
        activated because lazy loading will be used in this case.

        """
        return self[:].__str__()


class WRFPotentialTemperature(DerivedVariable):
    """Derived variable for potential temperature from WRF outputs."""

    def __getitem__(self, *args):
        """Return the potential temperature.

        Parameters
        ----------
        *args: slice
            Slice of interest in the WRF output.

        Return
        ------
        xarray.DataArray
            The potential temperature for given slice, in K.

        """
        varname, expected_units = "T", "K"
        self._dataset.wrf.check_units(varname, expected_units)
        pot_temp_t0 = constants["pot_temp_t0"]
        return xr.DataArray(
            pot_temp_t0 + self._dataset[varname].__getitem__(*args),
            name="potential temperature",
            attrs=dict(long_name="Potential temperature", units="K"),
        )


class WRFAtmPressure(DerivedVariable):
    """Derived variable for atmospheric pressure from WRF outputs."""

    def __getitem__(self, *args):
        """Return the atmospheric pressure.

        Parameters
        ----------
        *args: slice
            Slice of interest in the WRF output.

        Return
        ------
        xarray.DataArray
            The atmospheric pressure for given slice, in Pa.

        """
        varname_p, varname_pb, expected_units = "P", "PB", "Pa"
        self._dataset.wrf.check_units(varname_p, expected_units)
        self._dataset.wrf.check_units(varname_pb, expected_units)
        return xr.DataArray(
            self._dataset[varname_p].__getitem__(*args)
            + self._dataset[varname_pb].__getitem__(*args),
            name="atmospheric pressure",
            attrs=dict(long_name="Atmospheric pressure", units="Pa"),
        )


class WRFAirTemperature(DerivedVariable):
    """Derived variable for air temperature from WRF outputs."""

    def __getitem__(self, *args):
        """Return the air temperature.

        Parameters
        ----------
        *args: slice
            Slice of interest in the WRF output.

        Return
        ------
        xarray.DataArray
            The air temperature for given slice, in K.

        """
        wrf = self._dataset.wrf
        pot_temp = wrf.potential_temperature.__getitem__(*args)
        pressure = wrf.atm_pressure.__getitem__(*args)
        exponent = constants["r_air"] / constants["cp_air"]
        return xr.DataArray(
            pot_temp * (pressure / constants["pot_temp_p0"]) ** exponent,
            name="air temperature",
            attrs=dict(long_name="Air temperature", units="K"),
        )


class WRFDensityOfDryAir(DerivedVariable):
    """Derived variable for dry air density from WRF outputs."""

    def __getitem__(self, *args):
        """Return the density of dry air.

        Parameters
        ----------
        *args: slice
            Slice of interest in the WRF output.

        Return
        ------
        xarray.DataArray
            The dry air density for given slice, in kg m-3.

        """
        wrf = self._dataset.wrf
        pressure = wrf.atm_pressure.__getitem__(*args)
        air_temp = wrf.air_temperature.__getitem__(*args)
        return xr.DataArray(
            pressure / (constants["r_air"] * air_temp),
            name="dry air density",
            attrs=dict(long_name="Dry air density", units="kg m-3"),
        )


class WRFRelativeHumidity(DerivedVariable):
    """WRF derived variable for relative humidity."""

    def __getitem__(self, *args):
        """Return the relative humidity.

        Parameters
        ----------
        *args: slice
            Slice of interest in the WRF output.

        Return
        ------
        xarray.DataArray
            The relative humidity for given slice, in %.

        Notes
        -----
        We use the same equation to calculate the saturation vapor pressure as
        in the WRF model (eg. WRF/main/tc_em.F, subroutine qvtorh).

        """
        # Get the water vapor mixing ratio
        wrf = self._dataset.wrf
        varname, expected_units = "QVAPOR", "kg kg-1"
        wrf.check_units(varname, expected_units)
        q = wrf[varname].__getitem__(*args)

        # Calculate the saturation water vapor pressure (in Pa)
        temperature = wrf.air_temperature.__getitem__(*args) - 273.15
        psat = 611.2 * np.exp(17.67 * temperature / (temperature + 243.5))

        # Calculate the saturation water vapor mixing ratio
        pressure = wrf.atm_pressure.__getitem__(*args)
        r = constants["mm_water"] / constants["mm_dryair"]
        qsat = r * psat / (pressure - psat)

        # Calculate and return the relative humidity
        return xr.DataArray(
            100 * q / qsat,
            name="relative humidity",
            attrs=dict(long_name="Relative humidity", units="%"),
        )


class WRFAccumulatedPrecipitation(DerivedVariable):
    """Derived variable for accumulated total precipitation from WRF outputs."""

    def __getitem__(self, *args):
        """Return the accumulated total precipitation.

        Parameters
        ----------
        *args: slice
            Slice of interest in the WRF output.

        Return
        ------
        xarray.DataArray
            The accumulated total precipitation for given slice, in mm.

        """
        wrf = self._dataset.wrf
        wrf.check_units("RAINNC", "mm")
        wrf.check_units("RAINC", "mm")
        rainnc = wrf["RAINNC"].__getitem__(*args)
        rainc = wrf["RAINC"].__getitem__(*args)
        precip = rainnc + rainc
        return xr.DataArray(
            precip,
            name="accumulated total precipitation",
            attrs=dict(
                long_name="Accumulated total precipitation", units="mm"
            ),
        )
