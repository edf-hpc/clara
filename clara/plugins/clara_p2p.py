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
    clara [options] p2p status
    clara [options] p2p restart
    clara [options] p2p mktorrent [--image=<path>]
    clara p2p -h | --help | help

Options:
    --debug         Enable debug output
    --image=<path>  Path to squashfs image.
"""
import os
import sys
import time

import docopt
import ClusterShell.NodeSet

from clara.utils import clush, run, get_from_config, value_from_file


def mktorrent(image):
    ml_path = "/var/lib/mldonkey"
    trg_dir = get_from_config("images", "trg_dir")
    if (image is None):
        squashfs_file = get_from_config("images", "trg_img")
    else:
        squashfs_file = image
    seeders = get_from_config("p2p", "seeders")
    trackers = get_from_config("p2p", "trackers")
    trackers_port = get_from_config("p2p", "trackers_port")
    trackers_schema = get_from_config("p2p", "trackers_schema")

    if not os.path.isfile(squashfs_file):
        sys.exit("The file {0} doesn't exist".format(squashfs_file))

    if os.path.isfile(trg_dir + "/image.torrent"):
        os.remove(trg_dir + "/image.torrent")

    clush(seeders, "service ctorrent stop")
    clush(trackers, "service mldonkey-server stop")

    for files in ["torrents/old", "torrents/seeded", "torrents/tracked"]:
        clush(trackers, "rm -f {0}/{1}/*".format(ml_path, files))

    clush(trackers, "ln -sf {0} {1}/incoming/files/".format(squashfs_file, ml_path))

    clush(trackers, "awk 'BEGIN{verb=1}; / tracked_files = / {verb=0}; /^$/ {verb=1}; {if (verb==1) print}' /var/lib/mldonkey/bittorrent.ini > /var/lib/mldonkey/bittorrent.ini.new")
    clush(trackers, "mv {0}/bittorrent.ini.new {0}/bittorrent.ini".format(ml_path))

    announce = []
    for t in list(ClusterShell.NodeSet.NodeSet(trackers)):
        announce.append("{0}://{1}:{2}/announce".format(trackers_schema, t, trackers_port))
    run(["/usr/bin/mktorrent", "-a", ",".join(announce), "-o", trg_dir + "/image.torrent", squashfs_file])
    clush(trackers, "ln -sf {0}/image.torrent {1}/torrents/seeded/".format(trg_dir, ml_path))

    clush(trackers, "service mldonkey-server start")
    clush(seeders, "service ctorrent start")


def main():
    dargs = docopt.docopt(__doc__)

    trackers = get_from_config("p2p", "trackers")
    seeders = get_from_config("p2p", "seeders")

    if dargs['status']:
        clush(trackers, "service mldonkey-server status")
        clush(seeders, "service ctorrent status")
    elif dargs['restart']:
        clush(seeders, "service ctorrent stop")
        clush(trackers, "service mldonkey-server stop")
        time.sleep(1)
        clush(trackers, "service mldonkey-server start")
        clush(seeders, "service ctorrent start")
    elif dargs['mktorrent']:
        mktorrent(dargs['--image'])

if __name__ == '__main__':
    main()
