#!/usr/bin/env python

#
# This program is intended to be called by PDL in response to the arrival
# of an origin product. It is used by the Global ShakeMap system at NEIC,
# and therefor has a number NEIC-specific features (like the queries to
# ComCat). If you are adapting this program for your own use, make sure
# to copy it out of the ShakeMap repository so that your changes won't
# be overwritten the next time you update the ShakeMap code.
#

# stdlib imports
import argparse
import os.path
import sys
import time
from datetime import datetime

# third-party imports
from esi_utils_comcat.query import GeoServe
from esi_utils_geo.compass import get_compass_dir_azimuth
from esi_utils_rupture import constants
from shakemap_modules.utils.comcat import get_detail_json
from shakemap_modules.utils.config import get_config_paths
from shakemap_modules.utils.logging import get_generic_logger
from shakemap_modules.utils.utils import get_network_name

# local imports
from shakemap.utils import queue

LOGFILE = "origins.log"


def get_parser():
    """Set up the argparse instance for this script.

    Returns:
        ArgumentParser: argparse instance for this script.
    """
    description = """
    Insert strong motion unassociated peak amplitude files into a database.
    """
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--type", help="Product type")
    parser.add_argument("--status", help="Event status")
    parser.add_argument("--action", help="Event action type")
    parser.add_argument("--source", help='Product source ("us", "nc", etc.)')
    parser.add_argument("--property-title", nargs="*", help="Event location")
    parser.add_argument(
        "--property-event-type",
        nargs="*",
        help="Event type (earthquake, explosion, etc.)",
    )
    parser.add_argument(
        "--property-review-status",
        nargs="*",
        help="Event review status ('automatic', 'reviewed')",
    )
    parser.add_argument(
        "--property-eventsourcecode", help="Event source code (i.e., 2008abcd"
    )
    parser.add_argument(
        "--property-magnitude", type=float, help="Event magnitude"
    )
    parser.add_argument(
        "--property-latitude", type=float, help="Event latitude"
    )
    parser.add_argument(
        "--property-longitude", type=float, help="Event longitude"
    )
    parser.add_argument("--property-depth", type=float, help="Event depth")
    parser.add_argument("--property-eventtime", help="Event time")

    return parser


def main():
    """Main method for script."""
    clean_argv = " ".join(
        [x.replace('"', "").replace("=", " ", 1) for x in sys.argv]
    ).split()
    parser = get_parser()
    args, unknown = parser.parse_known_args(clean_argv)
    install_path, data_path = get_config_paths()
    if not os.path.isdir(data_path):
        logger.info(f"{data_path} is not a valid directory.")
        sys.exit(1)

    config = queue.get_config(install_path)

    # set up a daily rotating file handler logger
    logfile = os.path.join(install_path, "logs", LOGFILE)
    logger = get_generic_logger(logfile=logfile)

    if args.type != "origin" and args.type != "trump-origin":
        logger.info(f"No action on product type {args.type}")
        sys.exit(0)

    if args.status not in ["UPDATE", "DELETE"]:
        logger.info(f"No action on status {args.status}")
        sys.exit(0)

    if args.action not in ["EVENT_ADDED", "EVENT_UPDATED"]:
        logger.info(f"No action on action {args.action}")
        sys.exit(0)

    if not args.property_event_type:
        args.property_event_type = ""
    args.property_event_type = " ".join(args.property_event_type)
    if args.type == "origin" and args.property_event_type != "earthquake":
        logger.info(f"No action on event types of {args.property_event_type}")
        sys.exit(0)

    if not args.property_eventsourcecode:
        logger.info("No event ID, skipping")
        sys.exit(0)

    if args.source != "us":
        logger.info(f"Undesirable product source: {args.source}")
        sys.exit(0)

    eventid = args.source + args.property_eventsourcecode
    if args.status == "DELETE":
        event = {"id": eventid, "netid": args.source, "alt_eventids": eventid}
        queue.send_queue("cancel", event, config["port"])
        logger.info(f"Sending cancel event {eventid} to queue.")
        sys.exit(0)

    if (
        not args.property_eventtime
        or not args.property_latitude
        or not args.property_longitude
        or not args.property_depth
        or not args.property_magnitude
    ):
        logger.info("Missing event parameters for event %s, skipping", eventid)
        sys.exit(0)

    fails = 0
    while fails < 3:
        try:
            _ = get_detail_json(eventid)
        except Exception as e:
            fails += 1
            logger.warn(f"Libcomcat error: {str(e)}")
            logger.warn(
                "Error retrieving event data from comcat for event "
                "%s, will try %d more times" % (eventid, 3 - fails)
            )
            time.sleep(20)
            continue
        else:
            break
    if fails == 3:
        logger.warn(
            f"Unable to retrieve event data from comcat for event {eventid}"
        )
        dt = datetime.strptime(args.property_eventtime, constants.TIMEFMT)
        event_age = (datetime.utcnow() - dt).total_seconds()
        if event_age > 86400:
            # If the event is more than a day old, and -- lacking an
            # authoritative event id -- we just assume that we've run it
            # before (or not) based on better information
            logger.warn(f"Event {eventid} is older than cutoff, skipping")
            sys.exit(0)
        else:
            # Let's run the event
            pass
    else:
        # This used to check if the event was authoritative, but we
        # don't do that anymore.
        pass

    #
    # Only run events that have been reviewed by the network operator
    # (this restriction is subject to change)
    #
    if args.property_review_status[0] != 'reviewed':
        logger.info(
            "Event id %s is not reviewed; (review status=%s)"
            % (eventid, args.property_review_status[0])
        )
        sys.exit(0)
    # We've weeded out the messages we don't want, so construct an event
    # dictionary and send it to the queue
    if not args.property_title:
        fails = 0
        while fails < 3:
            try:
                gs = GeoServe(
                    args.property_latitude,
                    args.property_longitude,
                    maxradius=250,
                    minpop=1000,
                )
            except Exception as e:
                fails += 1
                places = []
                logger.warn(f"Error in GeoServe getPlaces: {str(e)}")
                logger.warn(
                    "Failure communicating with comcat; will try "
                    "%d more times" % (3 - fails)
                )
                time.sleep(20)
            else:
                places = gs.getPlaces()
                break
        if fails < 3:
            if len(places):
                props = places[0]["properties"]
                if props["country_code"] == "US":
                    country = ""
                else:
                    country = props["country_code"]
                azimuth = props["azimuth"] + 180
                if azimuth > 360:
                    azimuth = azimuth - 360
                location = "%d km %s of %s, %s, %s" % (
                    int(props["distance"]),
                    get_compass_dir_azimuth(
                        azimuth, resolution="meteorological"
                    ),
                    props["name"],
                    props["admin1_name"],
                    country,
                )
            else:
                region = gs.getRegions()
                if region is not None:
                    try:
                        location = region["fe"]["features"][0]["properties"][
                            "name"
                        ]
                    except KeyError:
                        location = ""
                    except IndexError:
                        location = ""
                else:
                    location = ""
        else:
            location = ""
    else:
        location = " ".join(args.property_title)

    if not args.source:
        args.source = ""
        network = ""
    else:
        network = get_network_name(args.source)
        if network == "unknown":
            network = ""
    if args.action == "EVENT_ADDED":
        action = "Event added"
    else:
        action = "Origin updated"
    if args.property_review_status == "reviewed":
        reviewed = "true"
    elif args.property_review_status == "automatic":
        reviewed = "false"
    else:
        reviewed = "unknown"
    event = {
        "id": eventid,
        "netid": args.source,
        "network": network,
        "time": args.property_eventtime,
        "lat": args.property_latitude,
        "lon": args.property_longitude,
        "depth": args.property_depth,
        "mag": args.property_magnitude,
        "locstring": location,
        "alt_eventids": eventid,
        "action": action,
        "reviewed": reviewed,
    }
    logger.info(f"Sending event {eventid} to queue.")

    # Poke the queue to run shake on this event.
    queue.send_queue("origin", event, config["port"])


if __name__ == "__main__":
    main()
