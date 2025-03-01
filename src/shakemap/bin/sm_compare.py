#!/usr/bin/env python
"""
Compare two shakemaps.
"""

import argparse

import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

from mapio.shake import ShakeGrid

SIZE = (8, 4)


def get_parser():
    desc = """Compare two shakemaps.

This program is to quickly make maps comparing two different shakemaps. Since
the main goal is to compare across maps using ShakeMap 3.5 and ShakeMap 4.0
the arguments are paths to grid.xml files.

Note that ratios are grid1/grid2 and differences are grid1 - grid2.
"""
    parser = argparse.ArgumentParser(description=desc, epilog="\n\n")
    parser.add_argument("grid1", type=str, help="Path to a ShakeMap grid.xml file.")
    parser.add_argument("grid2", type=str, help="Path to a ShakeMap grid.xml file.")
    parser.add_argument(
        "-i",
        "--imt",
        type=str,
        default="pga",
        help="Which IMT to use? A String such as pga, pgv, " "psa03, psa10.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default="compare.png",
        help="Output filename. Default: compare.png",
    )
    parser.add_argument(
        "-n",
        "--nocoasts",
        action="store_true",
        help="Suppresses printing of coastlines on the maps.",
    )
    return parser


def main():
    """ """
    parser = get_parser()
    args = parser.parse_args()
    g1 = ShakeGrid.load(args.grid1).getData()[args.imt]
    g2 = ShakeGrid.load(args.grid2).getData()[args.imt]
    g1_geodict = g1.getGeoDict()
    g2_geodict = g2.getGeoDict()
    try:
        cutdict = g1_geodict.getBoundsWithin(g2_geodict)
    except Exception:
        cutdict = g2_geodict.getBoundsWithin(g1_geodict)
    c1 = g1.interpolateToGrid(cutdict)
    c2 = g2.interpolateToGrid(cutdict)

    a1 = c1.getData()
    a2 = c2.getData()
    ratio = a1 / a2
    dif = a1 - a2
    lats = np.linspace(cutdict.ymin, cutdict.ymax, ratio.shape[0])
    lons = np.linspace(cutdict.xmin, cutdict.xmax, ratio.shape[1])

    fig = plt.figure(figsize=SIZE)
    wid = 0.4
    height = 0.8

    # Ratio plot
    levels = list(np.linspace(0.5, 1.5, 11))
    cmap = plt.cm.Spectral
    x1 = 0.05
    y1 = 0.2

    fig = plt.figure(figsize=SIZE)
    ax1 = plt.axes([x1, y1, wid, height], projection=ccrs.PlateCarree())
    fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
    cs1 = ax1.contourf(lons, lats, np.flipud(ratio), levels, cmap=cmap, extend="both")
    if not args.nocoasts:
        ax1.add_feature(cfeature.COASTLINE)

    ax_cbar1 = plt.axes([x1, y1 - 0.1, wid, 0.05])
    cbar1 = fig.colorbar(cs1, cax=ax_cbar1, orientation="horizontal", ticks=levels)
    cbar1.ax.tick_params(labelsize=6)
    cbar1.ax.set_xlabel(f"{args.imt} Ratio")
    cbar1.ax.get_yaxis().labelpad = 15

    # Difference plot
    dif_min = np.min(dif)
    dif_max = np.max(dif)
    if dif_min != dif_max:
        levels = list(np.linspace(dif_min, dif_max, 11))
    else:
        levels = list(np.linspace(-10, 10, 11))
    x1 = 0.55

    ax2 = plt.axes([x1, y1, wid, height], projection=ccrs.PlateCarree())
    fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
    cs2 = ax2.contourf(lons, lats, np.flipud(dif), levels, cmap=cmap, extend="both")
    if not args.nocoasts:
        ax2.add_feature(cfeature.COASTLINE)

    ax_cbar2 = plt.axes([x1, y1 - 0.1, wid, 0.05])
    cbar2 = fig.colorbar(cs2, cax=ax_cbar2, orientation="horizontal", ticks=levels)
    cbar2.ax.tick_params(labelsize=6)
    if args.imt == "pgv":
        cbar2.ax.set_xlabel(f"{args.imt} Difference (cm/s)")
    elif args.imt == "stdpgv":
        cbar2.ax.set_xlabel(f"{args.imt} Difference (ln(cm/s))")
    elif args.imt == "mmi" or args.imt == "stdmmi":
        cbar2.ax.set_xlabel(f"{args.imt} Difference")
    elif "std" in args.imt:
        cbar2.ax.set_xlabel(f"{args.imt} Difference (ln(g))")
    else:
        cbar2.ax.set_xlabel(f"{args.imt} Difference (percent g)")
    cbar2.ax.get_yaxis().labelpad = 15
    plt.savefig(args.output, dpi=300, bbox_inches="tight")


if __name__ == "__main__":
    main()
