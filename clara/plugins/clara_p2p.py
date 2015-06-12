#!/usr/bin/env python
# -*- coding: utf-8 -*-
##############################################################################
#  Copyright (C) 2014 EDF SA                                                 #
#                                                                            #
#  This file is part of Clara                                                #
#                                                                            #
#  This software is governed by the CeCILL-C license under French law and    #
#  abiding by the rules of distribution of free software. You can use,       #
#  modify and/ or redistribute the software under the terms of the CeCILL-C  #
#  license as circulated by CEA, CNRS and INRIA at the following URL         #
#  "http://www.cecill.info".                                                 #
#                                                                            #
#  As a counterpart to the access to the source code and rights to copy,     #
#  modify and redistribute granted by the license, users are provided only   #
#  with a limited warranty and the software's author, the holder of the      #
#  economic rights, and the successive licensors have only limited           #
#  liability.                                                                #
#                                                                            #
#  In this respect, the user's attention is drawn to the risks associated    #
#  with loading, using, modifying and/or developing or reproducing the       #
#  software by the user in light of its specific status of free software,    #
#  that may mean that it is complicated to manipulate, and that also         #
#  therefore means that it is reserved for developers and experienced        #
#  professionals having in-depth computer knowledge. Users are therefore     #
#  encouraged to load and test the software's suitability as regards their   #
#  requirements in conditions enabling the security of their systems and/or  #
#  data to be ensured and, more generally, to use and operate it in the      #
#  same conditions as regards security.                                      #
#                                                                            #
#  The fact that you are presently reading this means that you have had      #
#  knowledge of the CeCILL-C license and that you accept its terms.          #
#                                                                            #
##############################################################################
"""
Makes torrent images and seeds them via BitTorrent

Usage:
    clara p2p status
    clara p2p restart
    clara p2p mktorrent <dist> [--image=<path>]
    clara p2p -h | --help | help

Options:
    <dist> is the target distribution
    --image=<path>  Path to squashfs image.
"""

import logging
import os
import sys
import time

import docopt
import ClusterShell.NodeSet

from clara.utils import clara_exit, clush, run, get_from_config


def mktorrent(image):
    if (image is None):
        squashfs_file = get_from_config("images", "trg_img", dist)
    else:
        squashfs_file = image
    seeders = get_from_config("p2p", "seeders", dist)
    trackers_port = get_from_config("p2p", "trackers_port", dist)
    trackers_schema = get_from_config("p2p", "trackers_schema", dist)
    seeding_service = get_from_config("p2p", "seeding_service", dist)
    init_stop = get_from_config("p2p", "init_stop", dist)
    init_start = get_from_config("p2p", "init_start", dist)

    # trackers is a dictionary with pairs nodeset and torrent file
    trackers = {}
    for e in get_from_config("p2p", "trackers", dist).split(";"):
        k, v = e.split(":")
        trackers[k] = v

    if not os.path.isfile(squashfs_file):
        clara_exit("The file {0} doesn't exist".format(squashfs_file))

    # Remove old torrent files
    for f in trackers.values():
        if os.path.isfile(f):
            os.remove(f)

    clush(seeders, init_stop.format(seeding_service))

    for e in trackers.keys():
        announce = []
        for t in list(ClusterShell.NodeSet.NodeSet(e)):
            announce.append("{0}://{1}:{2}/announce".format(trackers_schema, t, trackers_port))
        run(["/usr/bin/mktorrent", "-a", ",".join(announce), "-o", trackers[e], squashfs_file])

    clush(seeders, init_start.format(seeding_service))

def main():
    logging.debug(sys.argv)
    dargs = docopt.docopt(__doc__)

    global dist
    dist = get_from_config("common", "default_distribution")
    if dargs["<dist>"] is not None:
        dist = dargs["<dist>"]
    if dist not in get_from_config("common", "allowed_distributions"):
        clara_exit("{0} is not a know distribution".format(dist))

    trackers = get_from_config("p2p", "trackers", dist)
    seeders = get_from_config("p2p", "seeders", dist)

    tracking_service = get_from_config("p2p", "tracking_service", dist)
    seeding_service = get_from_config("p2p", "seeding_service", dist)

    if dargs['status']:
        init_status = get_from_config("p2p", "init_status")
        clush(trackers, init_status.format(tracking_service))
        clush(seeders, init_status.format(seeding_service))
    elif dargs['restart']:
        init_stop = get_from_config("p2p", "init_stop")
        clush(seeders, init_stop.format(seeding_service))
        clush(trackers, init_stop.format(tracking_service))
        time.sleep(1)
        init_start = get_from_config("p2p", "init_start")
        clush(trackers, init_start.format(tracking_service))
        clush(seeders, init_start.format(seeding_service))
    elif dargs['mktorrent']:
        mktorrent(dargs['--image'])

if __name__ == '__main__':
    main()
