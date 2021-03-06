"""Test features of lightkurve that interact with the data archive at MAST.

Note: if you have the `pytest-remotedata` package installed, then tests flagged
with the `@pytest.mark.remote_data` decorator below will only run if the
`--remote-data` argument is passed to py.test.  This allows tests to pass
if no internet connection is available.
"""
from __future__ import division, print_function

import pytest

from ..mast import (search_kepler_products, ArchiveError)
from .. import KeplerTargetPixelFile, KeplerLightCurveFile
from astropy.coordinates import SkyCoord
import astropy.units as u
import numpy as np


@pytest.mark.remote_data
def test_search_kepler_tpf_products():
    """Tests `lightkurve.mast.search_kepler_tpf_products`."""
    # EPIC 210634047 was observed twice in long cadence
    assert(len(search_kepler_products(210634047)) == 2)
    # ...including Campaign 4
    assert(len(search_kepler_products(210634047, campaign=4)) == 1)
    # KIC 11904151 (Kepler-10) was observed in LC in 15 Quarters
    assert(len(search_kepler_products(11904151)) == 15)
    # ...including quarter 11 but not 12:
    assert(len(search_kepler_products(11904151, quarter=11)) == 1)
    assert(len(search_kepler_products(11904151, quarter=12)) == 0)
    # should work for all split campaigns
    campaigns = [[91, 92, 9], [101, 102, 10], [111, 112, 11]]
    ids = [200068780, 200071712, 202975993]
    for c, idx in zip(campaigns, ids):
        ca = search_kepler_products(idx, quarter=c[0])
        cb = search_kepler_products(idx, quarter=c[1])
        assert(len(ca) == 1)
        assert(len(ca) == len(cb))
        assert(~np.any(ca['description'] == cb['description']))
        assert(~np.any(ca['dataURI'] == cb['dataURI']))
        ca = search_kepler_products(idx, quarter=c[0], targetlimit=3, radius=400)
        assert(len(ca) == 3)
        # If you specify the whole campaign, both split parts must be returned.
        cc = search_kepler_products(idx, quarter=c[2], targetlimit=3, radius=400)
        assert(len(cc) == 6)
    # We should also be able to resolve it by its name instead of KIC ID
    assert(len(search_kepler_products('Kepler-10')) == 15)
    # An invalid KIC/EPIC ID should be dealt with gracefully
    with pytest.raises(ArchiveError) as exc:
        search_kepler_products(-999)
    assert('Could not resolve' in str(exc))
    # If we ask for all cadence types, there should be four Kepler files given
    assert(len(search_kepler_products(4914423, quarter=6, cadence='any')) == 4)
    # Should be able to resolve an ra/dec
    assert(len(search_kepler_products('297.5835, 40.98339', quarter=6) == 1))
    # Should be able to resolve a SkyCoord
    c = SkyCoord('297.5835 40.98339', unit=(u.deg, u.deg))
    assert(len(search_kepler_products(c, quarter=6) == 1))


@pytest.mark.remote_data
def test_search_kepler_lightcurve_products():
    """Tests `lightkurve.mast.search_kepler_lightcurve_products`."""
    assert(len(search_kepler_products('Kepler-10', filetype='Lightcurve')) == 15)
    assert(len(search_kepler_products(200071712, quarter=102, filetype='Lightcurve')) == 1)


@pytest.mark.remote_data
@pytest.mark.filterwarnings('ignore:Query returned no results')
def test_kepler_tpf_from_archive():
    # Request an object name that does not exist
    with pytest.raises(ArchiveError) as exc:
        KeplerTargetPixelFile.from_archive("LightKurve_Unit_Test_Invalid_Target")
    assert('not resolve' in str(exc))
    # Request an EPIC ID that was not observed
    with pytest.raises(ArchiveError) as exc:
        KeplerTargetPixelFile.from_archive(246000000)
    assert('No Target Pixel File found' in str(exc))
    # Request a valid target that has multiple TPFs
    with pytest.raises(ArchiveError) as exc:
        KeplerTargetPixelFile.from_archive('Kepler-10')
    assert('Please specify quarter' in str(exc))
    # But, if we specify the quarter for Kepler-10 it should work:
    KeplerTargetPixelFile.from_archive('Kepler-10', quarter=11)
    # However, for short cadence there is one file per month in Kepler
    with pytest.raises(ArchiveError) as exc:
        KeplerTargetPixelFile.from_archive('Kepler-10', quarter=11, cadence='short')
    assert('month' in str(exc))
    # In short cadence, if we specify both quarter and month it should work:
    KeplerTargetPixelFile.from_archive('Kepler-10', quarter=11, month=1, cadence='short')
    # If we request 2 quarters it should give a list of two TPFs, ordered by quarter
    tpfs = KeplerTargetPixelFile.from_archive(5728079, cadence='long', quarter=[1, 2])
    assert(isinstance(tpfs, list))
    assert(isinstance(tpfs[0], KeplerTargetPixelFile))
    assert(tpfs[0].quarter == 1)
    # If we ask for a nearby target, it should only give back one extra with the same quarter.
    tpfs = KeplerTargetPixelFile.from_archive(
        5728079, cadence='long', radius=60, quarter=1, targetlimit=2)
    assert(isinstance(tpfs, list))
    assert(isinstance(tpfs[0], KeplerTargetPixelFile))
    assert(tpfs[0].quarter == tpfs[1].quarter)
    assert(tpfs[0].keplerid != tpfs[1].keplerid)


@pytest.mark.remote_data
@pytest.mark.filterwarnings('ignore:Query returned no results')
def test_kepler_lightcurve_from_archive():
    # Request an object name that does not exist
    with pytest.raises(ArchiveError) as exc:
        KeplerLightCurveFile.from_archive("LightKurve_Unit_Test_Invalid_Target")
    assert('not resolve' in str(exc))
    # Request an EPIC ID that was not observed
    with pytest.raises(ArchiveError) as exc:
        KeplerLightCurveFile.from_archive(246000000)
    assert('No Lightcurve File found' in str(exc))
    # Request a valid target that has multiple TPFs
    with pytest.raises(ArchiveError) as exc:
        KeplerLightCurveFile.from_archive('Kepler-10')
    assert('Please specify quarter' in str(exc))
    # But, if we specify the quarter for Kepler-10 it should work:
    KeplerLightCurveFile.from_archive('Kepler-10', quarter=11)
    # However, for short cadence there is one file per month in Kepler
    with pytest.raises(ArchiveError) as exc:
        KeplerLightCurveFile.from_archive('Kepler-10', quarter=11, cadence='short')
    assert('month' in str(exc))
    # In short cadence, if we specify both quarter and month it should work:
    KeplerLightCurveFile.from_archive('Kepler-10', quarter=11, month=1, cadence='short')
    # If we request 2 quarters it should give a list of two TPFs, ordered by quarter
    lcfs = KeplerLightCurveFile.from_archive(5728079, cadence='long', quarter=[1, 2])
    assert(isinstance(lcfs, list))
    assert(isinstance(lcfs[0], KeplerLightCurveFile))
    assert(lcfs[0].quarter == 1)
    # If we ask for a nearby target, it should only give back one extra with the same quarter.
    lcfs = KeplerLightCurveFile.from_archive(
        5728079, cadence='long', radius=60, quarter=1, targetlimit=2)
    assert(isinstance(lcfs, list))
    assert(isinstance(lcfs[0], KeplerLightCurveFile))
    assert(lcfs[0].quarter == lcfs[1].quarter)
    assert(lcfs[0].keplerid != lcfs[1].keplerid)


def test_verbosity(capfd):
    tpf = KeplerTargetPixelFile.from_archive(5728079, quarter=1, verbose=False)
    out, err = capfd.readouterr()
    assert len(out) == 0
