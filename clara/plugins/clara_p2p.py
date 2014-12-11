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
    torrent_file = squashfs_file + ".torrent"
    seeders = get_from_config("p2p", "seeders", dist)
    trackers = get_from_config("p2p", "trackers", dist)
    trackers_port = get_from_config("p2p", "trackers_port", dist)
    trackers_schema = get_from_config("p2p", "trackers_schema", dist)

    if not os.path.isfile(squashfs_file):
        clara_exit("The file {0} doesn't exist".format(squashfs_file))

    if os.path.isfile(torrent_file):
        os.remove(torrent_file)

    clush(seeders, "service ctorrent stop")

    announce = []
    for t in list(ClusterShell.NodeSet.NodeSet(trackers)):
        announce.append("{0}://{1}:{2}/announce".format(trackers_schema, t, trackers_port))
    run(["/usr/bin/mktorrent", "-a", ",".join(announce), "-o", torrent_file, squashfs_file])

    clush(seeders, "service ctorrent start")


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

    if dargs['status']:
        clush(trackers, "service opentracker status")
        clush(seeders, "service ctorrent status")
    elif dargs['restart']:
        clush(seeders, "service ctorrent stop")
        clush(trackers, "service opentracker stop")
        time.sleep(1)
        clush(trackers, "service opentracker start")
        clush(seeders, "service ctorrent start")
    elif dargs['mktorrent']:
        mktorrent(dargs['--image'])

if __name__ == '__main__':
    main()
