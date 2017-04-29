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

import errno
import logging
import os
import subprocess
import ConfigParser
import sys

import ClusterShell.NodeSet
import ClusterShell.Task


class Conf:
    """Class which contains runtime variables"""
    def __init__(self):
        self.debug = False
        self.ddebug = False
        self.config = None

# global runtime Conf object
conf = Conf()


def clush(hosts, cmds):
    logging.debug("utils/clush: {0} {1}".format(cmds, hosts))

    task = ClusterShell.Task.task_self()
    task.run(cmds, nodes=hosts)

    for output, nodes in task.iter_buffers():
        logging.info("{0} {1}".format(ClusterShell.NodeSet.NodeSet.fromlist(nodes), output))


def run(cmd):
    logging.debug("utils/run: {0}".format(" ".join(cmd)))

    try:
        retcode = subprocess.call(cmd)
    except OSError, e:
        if (e.errno == errno.ENOENT):
            clara_exit("Binary not found, check your path and/or retry as root. \
                      You were trying to run:\n {0}".format(" ".join(cmd)))

    if retcode != 0:
        clara_exit(' '.join(cmd))


def get_from_config(section, value, dist=''):
    """ Read a value from config.ini and return it"""
    if dist == '':
        try:
            return getconfig().get(section, value).strip()
        except:
            clara_exit("Value '{0}' not found in the section '{1}'".format(value, section))

    elif dist in getconfig().get("common", "allowed_distributions"):
        or_section = section + "-" + dist

        # If the value is not in the override section, return the base value
        if getconfig().has_option(or_section, value):
            try:
                return getconfig().get(or_section, value).strip()
            except:
                clara_exit("Value '{0}' not found in section '{1}'".format(value, section))
        else:
            try:
                return getconfig().get(section, value).strip()
            except:
                clara_exit("Value '{0}' not found in section '{1}'".format(value, section))
    else:
        clara_exit("{0} is not a known distribution".format(dist))

def get_from_config_or(section, value, dist='', default=''):
    """ Read a value from config.ini and return it"""
    try:
        if dist == '':
            return getconfig().get(section, value).strip()

        elif dist in getconfig().get("common", "allowed_distributions"):
            or_section = section + "-" + dist

            # If the value is not in the override section, return the base value
            if getconfig().has_option(or_section, value):
                return getconfig().get(or_section, value).strip()
            else:
                return getconfig().get(section, value).strip()
    except:
        return default


def has_config_value(section, value, dist=''):
    """Return True if value is found in config.ini"""
    return (get_from_config_or(section, value, dist, None) is not None)


def getconfig():
    files = ['/etc/clara/config.ini']
    if conf.config:
        files.append(conf.config)

    if getconfig.config is None:
        getconfig.config = ConfigParser.ConfigParser()
        getconfig.config.read(files)
    return getconfig.config

getconfig.config = None


def value_from_file(myfile, key):
    """ Read a value from a headless ini file. """
    password = ""
    with open(myfile, 'r') as hand:
        for line in hand:
            if key in line:
                texto = line.rstrip().split("=")
                password = '='.join(texto[1:]).strip('"').strip("'")
    if password == "":
        clara_exit("{0} not found in the file {1}".format(key, myfile))
    return password


def initialize_logger(debug):
    output_dir = "/var/log/clara"
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # Create logs directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Create console handler and set level to info or debug, when it's enabled
    handler = logging.StreamHandler()
    if debug:
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter("clara - %(levelname)s - %(message)s")
    else:
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter("clara - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Create a log file, with everything, handler and set level to debug
    handler = logging.FileHandler(os.path.join(output_dir, "all.log"), "a")
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # create error file, with the most important messages, handler and set level to warning
    handler = logging.FileHandler(os.path.join(output_dir, "important.log"), "a")
    handler.setLevel(logging.WARNING)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def clara_exit(msg):
    logging.error(msg)
    sys.exit(1)
