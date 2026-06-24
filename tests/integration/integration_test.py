#!/usr/bin/env python
import argparse
import json
import math
import pathlib
import subprocess
import configobj

CREATE_CMD = "sm_create -f {EVENT}"
SHAKE_CMD = "shake {EVENT} select assemble -c'test' model info"
CMP_FILE = pathlib.Path(__file__).parent / "integration_tests.json"
PROFILES = pathlib.Path.home() / ".shakemap" / "profiles.conf"
FLOAT_TOLERANCE = 1e-4


def get_command_output(cmd):
    """
    Method for calling external system command.
    Args:
        cmd (str):
            Command to run (e.g., 'ls -l', etc.).
    Returns:
        tuple: Three-element tuple containing a boolean indicating success or
        failure, the stdout from running the command, and stderr.
    """
    proc = subprocess.Popen(
        cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    stdout, stderr = proc.communicate()
    return (proc.returncode == 0, stdout, stderr)


def get_shake_folder():
    """Get the data folder for the installed ShakeMap."""
    config = configobj.ConfigObj(str(PROFILES))
    profile = config["profile"]
    return pathlib.Path(config["profiles"][profile]["data_path"])


def compare_dicts(info_dict, cmp_dict):
    """Compare two event dictionaries with float tolerance."""
    if set(info_dict.keys()) != set(cmp_dict.keys()):
        raise AssertionError(
            f"Event ID mismatch.\n"
            f"Got: {set(info_dict.keys())}\n"
            f"Expected: {set(cmp_dict.keys())}"
        )
    for eventid in info_dict:
        if eventid not in cmp_dict:
            raise AssertionError(f"Event {eventid} not in comparison data")
        for key, val in info_dict[eventid].items():
            if key not in cmp_dict[eventid]:
                raise AssertionError(
                    f"Event {eventid}: key '{key}' not in comparison data"
                )
            cmp_val = cmp_dict[eventid][key]
            if isinstance(val, float):
                if not math.isclose(val, cmp_val, rel_tol=FLOAT_TOLERANCE):
                    raise AssertionError(
                        f"Event {eventid}, key '{key}': "
                        f"got {val}, expected {cmp_val}"
                    )
            else:
                if val != cmp_val:
                    raise AssertionError(
                        f"Event {eventid}, key '{key}': "
                        f"got {val}, expected {cmp_val}"
                    )


def main():
    helpstr = """Test ShakeMap runs against a previous saved run.
    Use the -r argument to create the result against which subsequent runs
    will be compared. This will save a JSON file alongside the script as
    integration_tests.json.
    """
    parser = argparse.ArgumentParser(description=helpstr)
    parser.add_argument(
        "events",
        nargs="+",
        help=(
            "Supply a list of ComCat IDs that should be "
            "run through complete ShakeMap"
        ),
    )
    parser.add_argument(
        "-r",
        "--regenerate",
        action="store_true",
        default=False,
        help="Regenerate output comparison JSON file",
    )
    args = parser.parse_args()
    data_path = get_shake_folder()
    make_json = not CMP_FILE.exists() or args.regenerate

    info_dict = {}
    for event in args.events:
        create_cmd = CREATE_CMD.format(EVENT=event)
        res, stdout, stderr = get_command_output(create_cmd)
        if not res:
            raise Exception(
                f"Failed to run {create_cmd}\nstderr: {stderr.decode()}"
            )

        shake_cmd = SHAKE_CMD.format(EVENT=event)
        res, stdout, stderr = get_command_output(shake_cmd)
        if not res:
            raise Exception(
                f"Failed to run {shake_cmd}\nstderr: {stderr.decode()}"
            )

        info_file = data_path / event / "current" / "products" / "info.json"
        if not info_file.exists():
            raise FileNotFoundError(
                f"info.json not found for event {event} at {info_file}"
            )

        with open(info_file, "rt") as fobj:
            jdict = json.load(fobj)

        eventid = jdict["input"]["event_information"]["event_id"]
        event_dict = {
            "tectonic_region": jdict["strec"]["TectonicRegion"],
        }
        for gm, gmdict in jdict["output"]["ground_motions"].items():
            event_dict[gm] = float(gmdict["max"])
        event_dict["nx"] = float(
            jdict["output"]["map_information"]["grid_points"]["longitude"]
        )
        event_dict["ny"] = float(
            jdict["output"]["map_information"]["grid_points"]["latitude"]
        )
        event_dict["xmin"] = float(
            jdict["output"]["map_information"]["min"]["longitude"]
        )
        event_dict["ymin"] = float(
            jdict["output"]["map_information"]["min"]["latitude"]
        )
        event_dict["xmax"] = float(
            jdict["output"]["map_information"]["max"]["longitude"]
        )
        event_dict["ymax"] = float(
            jdict["output"]["map_information"]["max"]["latitude"]
        )
        info_dict[eventid] = event_dict

    if make_json:
        with open(CMP_FILE, "wt") as fobj:
            json.dump(info_dict, fobj, indent=2)
        print(f"Wrote comparison data for events to {CMP_FILE}")
    else:
        with open(CMP_FILE, "rt") as fobj:
            cmp_dict = json.load(fobj)
        compare_dicts(info_dict, cmp_dict)
        print("All events passed integration tests.")


if __name__ == "__main__":
    main()

