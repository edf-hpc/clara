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
    clara slurm <cmd> <subject> [<op>] [<spec>...]
    clara slurm -h | --help

Options:
    <cmd> is one of the following ones: job jobs node nodes steps frontend
    partition partitions reservation reservations
"""
import subprocess
import sys

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
    else:
        print dargs, "\n"
        cmd = dargs['<cmd>']
        subject = dargs['<subject>']
        op = dargs['<op>']
        spec = dargs['<spec>']
 
        cmd_list = ['job', 'jobs', 'node', 'nodes', 'steps', 'frontend',
                    'partition', 'partitions', 'reservation', 'reservations']
        op_list = ['show', 'create', 'update', 'delete', None]

        if cmd not in cmd_list:
            sys.exit("The valid commands are: {0}".format(" ".join(cmd_list)))
        # OP=create|delete is valid only for frontend, partition{,s} and reservation{,s}
        if (cmd in ['frontend', 'partition', 'partitions',
                   'reservation', 'reservations']
            and op not in ['create', 'delete']):
                sys.exit("You can't use cmd = {0} with op = {1}".format(cmd, op))

        if (op not in op_list):
            sys.exit("The valid operations: {0}".format(" ".join(op_list)))

         #  If OP and SPEC are not specified, then the default is "OP=show"
         if (op is None and spec is None):
             op = 'show'

        print "VALID. cmd = {0}, subject = {1}, op = {2}, spec = {3}".format(cmd, subject, op, spec)

if __name__ == '__main__':
    main()
