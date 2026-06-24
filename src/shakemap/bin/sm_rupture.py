#!/usr/bin/env python
"""
This is a utility program for creating ShakeMap 4 rupture.json files, either
from a ShakeMap 3 style *_fault.txt file (and optionally an event.xml file),
or the program will prompt you to manually input rupture data (strike, dip,
length, ...).
"""

import argparse
import copy
import sys
import json
import numpy as np
import matplotlib.pyplot as plt
from esi_shakelib.rupture.factory import get_rupture, rupture_from_dict
from esi_shakelib.rupture.origin import Origin
from esi_shakelib.rupture.quad_rupture import QuadRupture
from esi_shakelib.plotting.plotrupture import map_rupture


# Lame method to detect integer using try block because
# python doesn't have this basic function.
def is_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


def is_float(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


def prompt_user(args, origin):
    ref = input("  - Rupture reference? ")
    origin.reference = ref

    n_quad = input("  - How many quadrilaterals are in this rupture? ")
    if is_int(n_quad):
        n_quad = int(n_quad)
    else:
        raise ValueError("Number of quadrilaterals must be an integer.")

    px = []
    py = []
    pz = []
    dx = []
    dy = []
    length = []
    width = []
    strike = []
    dip = []

    use_vertices = None
    xp0, yp0, zp0 = [], [], []
    xp1, yp1, zp1 = [], [], []
    xp2, yp2, zp2 = [], [], []
    xp3, yp3, zp3 = [], [], []

    for i in range(n_quad):
        print(f"  Quad {i + 1} of {n_quad}...")

        if use_vertices is None:
            method = input(
                "  - Input method:\n"
                "    (1) Orientation parameters (strike/dip/length/width)\n"
                "    (2) Four vertices (lon/lat/depth)\n"
                "  Choice: "
            )
            if method == "1":
                use_vertices = False
            elif method == "2":
                use_vertices = True
            else:
                raise ValueError("Input method must be 1 or 2.")

        if use_vertices:
            print(
                "    Enter 4 vertices in order: top-left, top-right, bottom-right, bottom-left"
            )
            verts = []
            for j in range(4):
                out = input(f"    Vertex {j+1} - Longitude: ")
                if not is_float(out):
                    raise ValueError("Longitude must be a float.")
                vlon = float(out)
                out = input(f"    Vertex {j+1} - Latitude: ")
                if not is_float(out):
                    raise ValueError("Latitude must be a float.")
                vlat = float(out)
                out = input(f"    Vertex {j+1} - Depth (km): ")
                if not is_float(out):
                    raise ValueError("Depth must be a float.")
                vdep = float(out)
                verts.append((vlon, vlat, vdep))
            xp0.append(verts[0][0])
            yp0.append(verts[0][1])
            zp0.append(verts[0][2])
            xp1.append(verts[1][0])
            yp1.append(verts[1][1])
            zp1.append(verts[1][2])
            xp2.append(verts[2][0])
            yp2.append(verts[2][1])
            zp2.append(verts[2][2])
            xp3.append(verts[3][0])
            yp3.append(verts[3][1])
            zp3.append(verts[3][2])
        else:
            out = input("    Longitude of known point: ")
            if is_float(out):
                px.append(float(out))
            else:
                raise ValueError("Longitude of known point must be a float.")

            out = input("    Latitude of known point: ")
            if is_float(out):
                py.append(float(out))
            else:
                raise ValueError("Latitude of known point must be a float.")

            out = input("    Depth (km) of known point: ")
            if is_float(out):
                pz.append(float(out))
            else:
                raise ValueError("Depth of known point must be a float.")

            out = input("    Along-strike distance (km) of known point: ")
            if is_float(out):
                dx.append(float(out))
            else:
                raise ValueError("Distance must be a float.")

            out = input("    Along-dip distance (km) of known point: ")
            if is_float(out):
                dy.append(float(out))
            else:
                raise ValueError("Distance must be a float.")

            out = input("    Length (km) of quadrilateral: ")
            if is_float(out):
                length.append(float(out))
            else:
                raise ValueError("Length must be a float.")

            out = input("    Width (km) of quadrilateral: ")
            if is_float(out):
                width.append(float(out))
            else:
                raise ValueError("Width must be a float.")

            out = input("    Strike (deg) of quadrilateral: ")
            if is_float(out):
                strike.append(float(out))
            else:
                raise ValueError("Strike must be a float.")

            out = input("    Dip (deg) of quadrilateral: ")
            if is_float(out):
                dip.append(float(out))
            else:
                raise ValueError("Dip must be a float.")

    if use_vertices:
        # fmt: off
        return QuadRupture.fromVertices(
            xp0, yp0, zp0, xp1, yp1, zp1,
            xp2, yp2, zp2, xp3, yp3, zp3,
            origin,
            reference=origin.reference,
        )
        # fmt: on
    else:
        return QuadRupture.fromOrientation(
            px, py, pz, dx, dy, length, width, strike, dip, origin
        )


def read_neic(filename, origin):
    segments = []
    current = []

    with open(filename) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("%"):
                continue
            if line == ">":
                if current:
                    segments.append(current)
                    current = []
            else:
                parts = line.split()
                lon, lat, depth = (
                    float(parts[0]),
                    float(parts[1]),
                    float(parts[2]),
                )
                current.append((lon, lat, depth))
    if current:  # last segment with no trailing >
        segments.append(current)

    xp0, yp0, zp0 = [], [], []
    xp1, yp1, zp1 = [], [], []
    xp2, yp2, zp2 = [], [], []
    xp3, yp3, zp3 = [], [], []

    for seg in segments:
        # Remove repeated closing point
        if seg[0] == seg[-1]:
            seg = seg[:-1]

        # Sort by depth to get top (shallow) and bottom (deep) pairs
        seg_sorted = sorted(seg, key=lambda x: x[2])
        top = seg_sorted[:2]  # two shallowest
        bottom = seg_sorted[2:]  # two deepest

        # Order top edge left to right by longitude
        top = sorted(top, key=lambda x: x[0])
        # Order bottom edge left to right by longitude
        bottom = sorted(bottom, key=lambda x: x[0])

        # p0=top-left, p1=top-right, p2=bottom-right, p3=bottom-left
        xp0.append(top[0][0])
        yp0.append(top[0][1])
        zp0.append(top[0][2])
        xp1.append(top[1][0])
        yp1.append(top[1][1])
        zp1.append(top[1][2])
        xp2.append(bottom[1][0])
        yp2.append(bottom[1][1])
        zp2.append(bottom[1][2])
        xp3.append(bottom[0][0])
        yp3.append(bottom[0][1])
        zp3.append(bottom[0][2])

    # fmt: off
    return QuadRupture.fromVertices(
        xp0, yp0, zp0,
        xp1, yp1, zp1,
        xp2, yp2, zp2,
        xp3, yp3, zp3,
        origin,
        reference="USGS NEIC Rapid Finite Fault",
    )
    # fmt: on


def read_fsp_file(filename, origin):
    """Parse an FSP file and return a QuadRupture.
    Code adapted from FaultModel.py (from NEIC's FFM product)"""
    import re

    metadata = {}
    with open(filename) as f:
        for line in f:
            if "Loc" in line:
                metadata["lat"] = float(
                    re.split(r"LAT\s*=", line)[-1].split("LON")[0].strip()
                )
                metadata["lon"] = float(
                    re.split(r"LON\s*=", line)[-1].split("DEP")[0].strip()
                )
                metadata["depth"] = float(
                    re.split(r"DEP\s*=", line)[-1].strip()
                )
            elif "Size" in line:
                metadata["length"] = float(
                    re.split(r"LEN\s*=", line)[-1].split("km")[0].strip()
                )
                metadata["width"] = float(
                    re.split(r"WID\s*=", line)[-1].split("km")[0].strip()
                )
            elif "Mech" in line:
                metadata["strike"] = float(
                    re.split(r"STRK\s*=", line)[-1].split("DIP")[0].strip()
                )
                metadata["dip"] = float(
                    re.split(r"DIP\s*=", line)[-1].split("RAKE")[0].strip()
                )
                metadata["rake"] = float(
                    re.split(r"RAKE\s*=", line)[-1].split("Htop")[0].strip()
                )
                metadata["ztor"] = float(
                    re.split(r"Htop\s*=", line)[-1].split("km")[0].strip()
                )
            elif "Rupt" in line:
                metadata["hypx"] = float(
                    re.split(r"HypX\s*=", line)[-1].split("km")[0].strip()
                )
                metadata["hypz"] = float(
                    re.split(r"HypZ\s*=", line)[-1].split("km")[0].strip()
                )
                break

    # fmt: off
    required = ["lon", "lat", "depth", "length", "width", "strike", "dip", "ztor", "hypx", "hypz"]
    # fmt: on
    missing = [k for k in required if k not in metadata]
    if missing:
        raise ValueError(f"FSP file missing required fields: {missing}")

    # dx = along-strike distance from P1 to hypocenter
    # dy = along-dip distance from top edge to hypocenter
    dx = metadata["hypx"]
    dy = metadata["hypz"]
    origin.reference = f"FSP file: {filename}"

    return QuadRupture.fromOrientation(
        [metadata["lon"]],
        [metadata["lat"]],
        [metadata["depth"]],
        [dx],
        [dy],
        [metadata["length"]],
        [metadata["width"]],
        [metadata["strike"]],
        [metadata["dip"]],
        origin,
    )


def read_fsp_file(filename, origin):
    """Parse an FSP file and return a QuadRupture.
    Code adapted from FaultModel.py (from NEIC's FFM product)"""
    import re

    metadata = {}
    with open(filename) as f:
        for line in f:
            if "Loc" in line:
                metadata["lat"] = float(
                    re.split(r"LAT\s*=", line)[-1].split("LON")[0].strip()
                )
                metadata["lon"] = float(
                    re.split(r"LON\s*=", line)[-1].split("DEP")[0].strip()
                )
                metadata["depth"] = float(
                    re.split(r"DEP\s*=", line)[-1].strip()
                )
            elif "Size" in line:
                metadata["length"] = float(
                    re.split(r"LEN\s*=", line)[-1].split("km")[0].strip()
                )
                metadata["width"] = float(
                    re.split(r"WID\s*=", line)[-1].split("km")[0].strip()
                )
            elif "Mech" in line:
                metadata["strike"] = float(
                    re.split(r"STRK\s*=", line)[-1].split("DIP")[0].strip()
                )
                metadata["dip"] = float(
                    re.split(r"DIP\s*=", line)[-1].split("RAKE")[0].strip()
                )
                metadata["rake"] = float(
                    re.split(r"RAKE\s*=", line)[-1].split("Htop")[0].strip()
                )
                metadata["ztor"] = float(
                    re.split(r"Htop\s*=", line)[-1].split("km")[0].strip()
                )
            elif "Rupt" in line:
                metadata["hypx"] = float(
                    re.split(r"HypX\s*=", line)[-1].split("km")[0].strip()
                )
                metadata["hypz"] = float(
                    re.split(r"HypZ\s*=", line)[-1].split("km")[0].strip()
                )
                break

    required = [
        "lon",
        "lat",
        "depth",
        "length",
        "width",
        "strike",
        "dip",
        "ztor",
        "hypx",
        "hypz",
    ]
    missing = [k for k in required if k not in metadata]
    if missing:
        raise ValueError(f"FSP file missing required fields: {missing}")

    # dx = along-strike distance from P1 to hypocenter
    # dy = along-dip distance from top edge to hypocenter
    dx = metadata["hypx"]
    dy = metadata["hypz"]
    origin.reference = f"FSP file: {filename}"

    return QuadRupture.fromOrientation(
        [metadata["lon"]],
        [metadata["lat"]],
        [metadata["depth"]],
        [dx],
        [dy],
        [metadata["length"]],
        [metadata["width"]],
        [metadata["strike"]],
        [metadata["dip"]],
        origin,
    )


def main():
    """ """
    parser = get_parser()
    args = parser.parse_args()

    if args.file and args.format == "json":
        with open(args.file) as f:
            rup = rupture_from_dict(json.load(f))
    else:
        # First deal with origin
        if args.eventfile:
            origin = Origin.fromFile(args.eventfile)
        else:
            print("* No event.xml file specified, using dummy origin...")
            dummy = {
                "mag": "",
                "id": "",
                "mech": "",
                "lon": np.nan,
                "lat": np.nan,
                "depth": "",
                "locstring": "",
                "netid": "",
                "network": "",
                "time": "",
            }
            origin = Origin(dummy)

        if args.file and args.format == "neic":
            rup = read_neic(args.file, origin)
        elif args.file and args.format == "fsp":
            rup = read_fsp_file(args.file, origin)
        elif args.file:
            rup = get_rupture(origin, file=args.file, new_format=not args.old)
        else:
            explain_text = """
* No fault file specified. You will be prompted to manually enter rupture
information.

You will need to specify the number of quadrilaterals in the rupture. Each
quadrilateral will be defined with the following geometry:

                            strike direction
                        p1*------------------->>p2
                        *        | dy           |
                 dip    |--------o              |
              direction |   dx    known point   | Width
                        V                       |
                        V                       |
                        p4----------------------p3
                                Length
"""
            print(explain_text)
            rup = prompt_user(args, origin)

    if not args.no_plot:
        print("Plotting rupture geometry for verification...")
        map_rupture(rup)
        plt.show(block=False)
        plt.pause(0.1)
        confirm = input("Does the rupture look correct? (y/n): ")
        plt.close()
        if confirm.lower() != "y":
            print("Exiting without writing file.")
            sys.exit(0)

    # Remove any blank or nan origin info
    odict = copy.copy(rup._origin.__dict__)
    for k, v in odict.items():
        if isinstance(v, str):
            if not v:
                rup._geojson["metadata"].pop(k, None)
        if isinstance(v, float):
            if np.isnan(v):
                rup._geojson["metadata"].pop(k, None)

    # Write output
    rup.writeGeoJson(args.outfile)


def get_parser():
    desc = """Create a ShakeMap 4 Rupture File.

This program creates a ShakeMap 4 rupture file. If a ShakeMap 3 *_fault.txt
file is provided, it will try to convert it to a rupture.json file. Otherwise,
the user will be prompted to manually input rupture data (strike, dip, ...).

Note that the rupture.json requires some origin information that is not in
the fault.txt file and so these values are filled in with empty values unless
an event.xml file is also provided.
"""
    parser = argparse.ArgumentParser(description=desc, epilog="\n\n")
    parser.add_argument("outfile", help="Path for output rupture file.")
    parser.add_argument(
        "-f", "--file", type=str, help="Path to ShakeMap 3 fault file."
    )
    parser.add_argument(
        "-e", "--eventfile", type=str, help="Path to an event.xml file."
    )
    parser.add_argument(
        "-o",
        "--old",
        action="store_true",
        help="Indicates that the ShakeMap 3 fault file"
        "uses the old format (ordering lon before "
        "lat).",
    )
    parser.add_argument(
        "--format",
        type=str,
        choices=["shakemap3", "fsp", "neic", "json"],
        default="shakemap3",
        help="Format of input file. Default is shakemap3",
    )
    parser.add_argument(
        "--no-plot",
        action="store_true",
        default=False,
        help="Skip the rupture plot.",
    )
    return parser


if __name__ == "__main__":
    main()
