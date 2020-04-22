#!/usr/bin/env python
# -*- coding: utf-8 -*-
##############################################################################
#  Copyright (C) 2014-2016 EDF SA                                            #
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
Performs tasks using SLURM's controller

Usage:
    clara slurm health <nodeset>
    clara slurm resume <nodeset>
    clara slurm drain [<nodeset>] [<reason>...]
    clara slurm undrain <nodeset>
    clara slurm fail [<nodeset>] [<reason>...]
    clara slurm down [<nodeset>]
    clara slurm power <state> <nodeset>
    clara slurm <cmd> <subject> [<op>] [<spec>...]
    clara slurm -h | --help

Options:
    <state> must be either 'up' or 'down'
    <op> is one of the following ones: show, create, update and delete.
    <cmd> is one of the following ones: job, node, steps, frontend,
    partition, reservation, block and submp.
"""

import logging
import subprocess
import sys

import docopt
from clara.utils import clara_exit, clush, run, get_from_config, conf


def show_nodes(option):
    selection = []
    part1 = subprocess.Popen(["sinfo"],
                             stdout=subprocess.PIPE,
                             universal_newlines=True)
    for line in part1.stdout:
        if option in line:
            cols = line.rstrip().split(" ")
            selection.append(cols[-1])

    cmd = ["scontrol", "show", "node", ",".join(selection)]
    logging.debug("slurm/show_nodes: {0}".format(" ".join(cmd)))

    part2 = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                             universal_newlines=True)
    for line in part2.stdout:
        if "NodeName" in line:
            logging.info(line.split(" ")[0])
        if "Reason" in line:
            logging.info(line)


def main():
    logging.debug(sys.argv)
    dargs = docopt.docopt(__doc__)

    debug = []
    if conf.ddebug:
        debug = ["--verbose", "--details"]

    if dargs['resume']:
        run(["scontrol"] + debug + ["update", "NodeName=" + dargs['<nodeset>'],
             "State=RESUME"])
    elif dargs['drain']:
        if dargs['<nodeset>'] is None:
            show_nodes("drain")
        else:
            if len(dargs['<reason>']) == 0:
                clara_exit("You must specify a reason when DRAINING a node")
            else:
                run(["scontrol"] + debug + ["update", "NodeName=" + dargs['<nodeset>'],
                     "State=DRAIN", 'Reason="' + " ".join(dargs['<reason>']) + '"'])
    elif dargs['undrain']:
        run(["scontrol"] + debug + ["update", "NodeName=" + dargs['<nodeset>'],
             "State=UNDRAIN"])
    elif dargs['fail']:
        if dargs['<nodeset>'] is None:
            show_nodes("fail")
        else:
            if len(dargs['<reason>']) == 0:
                clara_exit("You must specify a reason when FAILING a node")
            else:
                run(["scontrol"] + debug + ["update", "NodeName=" + dargs['<nodeset>'],
                     "State=FAIL", 'Reason="' + " ".join(dargs['<reason>']) + '"'])
    elif dargs['down']:
        if dargs['<nodeset>'] is None:
            show_nodes("down")
        else:
            run(["scontrol"] + debug + ["update", "NodeName=" + dargs['<nodeset>'],
                 "State=DOWN"])
    elif dargs['power']:
        if dargs['<state>'] == 'up':
            run(["scontrol"] + debug + ["update", "NodeName=" + dargs['<nodeset>'],
                 "State=POWER_UP"])
        elif dargs['<state>'] == 'down':
            run(["scontrol"] + debug + ["update", "NodeName=" + dargs['<nodeset>'],
                 "State=POWER_DOWN"])
        else:
            clara_exit("Only 'up' and 'down' are valid states")
    elif dargs['health']:
        script_slurm_health = get_from_config("slurm", "script_slurm_health")
        if (len(script_slurm_health) > 0):
            clush(dargs['<nodeset>'], script_slurm_health)
        else:
            clara_exit("You must set a health check program in the configuration file.")
    else:
        cmd_list = ['job', 'node', 'steps', 'frontend', 'partition', 'reservation',
                    'block', 'submp']

        # /!\ ∀ x, ∀ y, op_list[x][y] ⇒ op_list[x][y] ∈ cmd_list
        op_list = {
            'show': ['job', 'node', 'partition', 'reservation', 'steps',
                     'frontend', 'block', 'submp'],
            'update': ['job', 'node', 'partition', 'reservation', 'steps',
                       'frontend', 'block', 'submp'],
            'create': ['partition', 'reservation'],
            'delete': ['partition', 'reservation']
        }

        # /!\ ∀ x ∈ cmd_list ⇒ x ∈ keys_list.keys()
        key_list = {
            'job': 'JobId',
            'steps': 'StepId',
            'node': 'NodeName',
            'frontend': 'FrontendName',
            'partition': 'PartitionName',
            'reservation': 'Reservation',
            'block': 'BlockName',
            'submp': 'SubMPName'
            }

        cmd = dargs['<cmd>']
        subject = dargs['<subject>']
        op = dargs['<op>']
        spec = dargs['<spec>']

        if cmd not in cmd_list:
            clara_exit("Known commands are: {0}".format(" ".join(cmd_list)))

        if spec is None:
            if op is not None and "=" in op:
                spec = [op]
            op = 'show'

        if "=" in op:
            spec = [op] + spec
            op = 'show'

        if op not in op_list:
            clara_exit("Known operations are: {0}".format(" ".join(op_list)))

        if cmd not in op_list[op]:
            clara_exit("You can't use {0} with {1}".format(cmd, op))

        if op == 'show':
            # spec should be empty
            run(["scontrol"] + debug + [op, cmd, subject])
        else:
            run(["scontrol"] + debug + \
                [op,
                 "{0}={1}".format(key_list[cmd], subject),
                 " ".join(spec)])

if __name__ == '__main__':
    main()
