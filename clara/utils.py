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

import errno
import subprocess
import ConfigParser
import os
import sys

import ClusterShell.NodeSet
import ClusterShell.Task

class Conf:
    """Class which contains runtime variables"""
    def __init__(self):
        self.debug = False

# global runtime Conf object
conf = Conf()

def clush(hosts, cmds):
    if conf.debug:
        print('D: clush(): ' + cmds)
    task = ClusterShell.Task.task_self()
    task.run(cmds, nodes=hosts)

    for output, nodes in task.iter_buffers():
        print ClusterShell.NodeSet.NodeSet.fromlist(nodes), output


def run(cmd):
    if conf.debug:
        print('D: run(): ' + ' '.join(cmd))
    try:
        retcode = subprocess.call(cmd)
    except OSError, e:
        if (e.errno == errno.ENOENT):
            sys.exit("Binary not found, check your path and/or retry as root. \
                      You were trying to run:\n {0}".format(" ".join(cmd)))

    if retcode != 0:
        sys.exit('E: ' + ' '.join(cmd))

def get_from_config(section, value, dist=''):
    """ Read a value from config.ini and return it"""
    if dist == '':
        return getconfig().get(section, value)

    elif dist in getconfig().get("common", "distributions"):
        or_section = section+"-"+dist
        # Check if override section exist, if not read the value from base section
        if getconfig().has_section(or_section):
            # If the value is not in the override section, return the base value
            if getconfig().has_option(or_section, value):
                return getconfig().get(or_section, value)
            else:
                return getconfig().get(section, value)
        else:
                return getconfig().get(section, value)

    else:
        sys.exit("{0} is not a know distribution".format(dist))

def getconfig():
    if getconfig.config is None:
        getconfig.config = ConfigParser.ConfigParser()
        getconfig.config.read(['/etc/clara/config.ini',
                             os.path.expanduser('~/.config/clara/config.ini')])
    return getconfig.config

getconfig.config = None


def value_from_file(myfile, key):
    """ Read a value from a headless ini file. """
    with open(myfile, 'r') as hand:
        for line in hand:
            if key in line:
                texto = line.rstrip().split("=")
                password = texto[1].strip('"').strip("'")
    return password
