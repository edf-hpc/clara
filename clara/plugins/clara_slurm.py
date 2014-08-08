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
Shows information from SLURM

Usage:
    clara slurm health <hotlist>
    clara slurm drain [<hotlist>]
    clara slurm down [<hotlist>]
    clara slurm -h | --help

"""
import subprocess

import docopt
from clara.utils import clush


def show_nodes(option):
    selection = []
    part1 = subprocess.Popen(["sinfo"], stdout=subprocess.PIPE)
    for line in part1.stdout:
        if option in line:
            cols = line.rstrip().split(" ")
            selection.append(cols[-1])

    part2 = subprocess.Popen(["scontrol", "show", "node", ",".join(selection)],
                             stdout=subprocess.PIPE)
    for line in part2.stdout:
        if "NodeName" in line:
            print line.split(" ")[0]
        if "Reason" in line:
            print line


def main():
    dargs = docopt.docopt(__doc__)

    if dargs['drain']:
        if dargs['<hotlist>'] is None:
            show_nodes("drain")
        else:
            print "TODO: drain nodes from the <hotlist>"
    elif dargs['down']:
        if dargs['<hotlist>'] is None:
            show_nodes("down")
        else:
            print "TODO: put down nodes from the <hotlist>"
    elif dargs['health']:
        clush(dargs['<hotlist>'],
              "/usr/lib/slurm/check_node_health.sh --no-slurm")

if __name__ == '__main__':
    main()
