#!/usr/bin/env python

# stdlib imports
import json
import subprocess
import tempfile
from pathlib import Path

# third party imports
import numpy as np
from shakemap.bin.sm_rupture import read_fsp_file, read_neic
from esi_shakelib.rupture.factory import get_rupture, rupture_from_dict
from esi_shakelib.rupture.origin import Origin
from esi_shakelib.rupture.quad_rupture import QuadRupture

homedir = Path(__file__).parent
shakedir = (homedir / ".." / ".." / "..").resolve()
datadir = shakedir / "tests" / "data" / "ruptures"

# Dummy origin
dummy = {
    "mag": np.nan,
    "id": "dummy",
    "locstring": "dummy",
    "mech": "ALL",
    "lon": np.nan,
    "lat": np.nan,
    "depth": np.nan,
    "netid": "",
    "network": "",
    "time": "",
}
origin = Origin(dummy)

program = shakedir / "src" / "shakemap" / "bin" / "sm_rupture.py"


def test_read_json():
    with open(datadir / "tohoku_rupture.json") as f:
        rup = rupture_from_dict(json.load(f))
    assert len(rup.getQuadrilaterals()) == 1


def test_read_fsp():
    rup = read_fsp_file(datadir / "s2003TOKACHkoke.fsp", origin)
    assert isinstance(rup, QuadRupture)
    strike_diff = (rup.getStrike() - 230) % 360
    assert min(strike_diff, 360 - strike_diff) < 1.0
    assert abs(rup.getDip() - 20) < 1.0
    assert abs(rup.getLength() - 120) < 1.0
    assert abs(rup.getWidth() - 100) < 1.0


def test_read_neic():
    rup = read_neic(datadir / "neic_fault.txt", origin)
    assert isinstance(rup, QuadRupture)
    assert len(rup.getQuadrilaterals()) == 1


def test_rupture():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Read in a fault file
        rup1_file = (
            shakedir
            / "tests"
            / "data"
            / "eventdata"
            / "northridge"
            / "current"
            / "northridge_fault.txt"
        )
        rup1 = get_rupture(origin, str(rup1_file))

        # Known point is p0
        dx = 0
        dy = 0
        p0 = rup1.getQuadrilaterals()[0][0]
        px = p0.x
        py = p0.y
        pz = p0.z
        length = rup1.getLength()
        width = rup1.getWidth()
        strike = rup1.getStrike()
        dip = rup1.getDip()

        outfile = Path(tmpdir) / "test.json"

        op = subprocess.Popen(
            [program, outfile, "--no-plot"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
        )
        responses = (
            "test\n"
            + "1\n"
            + "1\n"
            + str(px)
            + "\n"
            + str(py)
            + "\n"
            + str(pz)
            + "\n"
            + str(dx)
            + "\n"
            + str(dy)
            + "\n"
            + str(length)
            + "\n"
            + str(width)
            + "\n"
            + str(strike)
            + "\n"
            + str(dip)
            + "\n"
        )
        op.communicate(responses.encode("ascii"))
        rup2 = get_rupture(origin, str(outfile))

        # testing, note that some difference will occur since the original
        # points are not necessarily coplanar or even rectangular, which
        # are conditions enfored on the derived rupture and so this cannot
        # be a very precise comparison.
        rtol = 1e-4
        np.testing.assert_allclose(rup2.lats, rup1.lats, rtol=rtol)
        np.testing.assert_allclose(rup2.lons, rup1.lons, rtol=rtol)
        rtol = 2e-3
        np.testing.assert_allclose(rup2.depths, rup1.depths, rtol=rtol)


if __name__ == "__main__":
    test_rupture()
