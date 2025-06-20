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
import configparser
import sys
try:
    import distro
except ImportError as e:
    import platform

import ClusterShell.NodeSet
import ClusterShell.Task

import json
import shlex

try:
    from requests.packages.urllib3.exceptions import InsecureRequestWarning
    import requests
except:
    print("[WARN] PLS raise 'pip install requests' or install 'python3-requests' package, need by redfish!")
    pass

import distutils
from distutils import util

class Conf:
    """Class which contains runtime variables"""
    def __init__(self):
        self.debug = False
        self.ddebug = False
        self.config = None

# global runtime Conf object
conf = Conf()

class Colorizer(object):

    BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)

    @staticmethod
    def colorize(string, color, bold=True, background=True):
        s_bold = ''
        if bold:
            s_bold = '1;'
        if background:
            return("\x1b[" + s_bold + "%dm" % (40+color) + string + "\x1b[0m")
        else:
            return("\x1b[" + s_bold + "%dm" % (30+color) + string + "\x1b[0m")

    @staticmethod
    def yellow(string, bold=True, background=True, color=False):
        if color or string == '':
            return Colorizer.colorize(string, Colorizer.YELLOW, bold, background)
        else:
            return string

    @staticmethod
    def green(string, bold=True, background=True, color=False):
        if color or string == '':
            return Colorizer.colorize(string, Colorizer.GREEN, bold, background)
        else:
            return string

    @staticmethod
    def blue(string, bold=True, background=True, color=False):
        if color or string == '':
            return Colorizer.colorize(string, Colorizer.BLUE, bold, background)
        else:
            return string

    @staticmethod
    def red(string, bold=True, background=True, color=False):
        if color or string == '':
            return Colorizer.colorize(string, Colorizer.RED, bold, background)
        else:
            return string

def yes_or_no(question, default="no"):
    """ Ask a yes/no question via input() and return their answer.
    """

    valid = {"yes": True, "y": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("Invalid default answer: '{0}'".format(default))

    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' (or 'y' or 'n').\n")


def do_print(table, data, legacy=None):
    if not len(data): return
    if legacy:
        print(table.format(*data))
    else:
        try:
            # try to use prettytable
            table.add_row(data)
        except:
            # drop down prettytable if any issue, falling back to default print
            print(table.format(*data))


def get_response(url, endpoint, headers, data=None, method=None, verify=False):
    try:
        if data == None and method == None:
            method = 'GET'
        elif method == None:
            method = 'POST'
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
        response = requests.request(url=url + endpoint, auth=headers, json=data, method=method, timeout=5, verify=verify)
        response.raise_for_status()
        try:
            return response.json()
        except ValueError as e:
            return response
    except requests.exceptions.HTTPError as errh:
        print(errh)
        sys.exit(1)
    except requests.exceptions.ConnectionError as errc:
        print(errc)
        sys.exit(1)
    except requests.exceptions.Timeout as errt:
        print(errt)
        sys.exit(1)
    except requests.exceptions.RequestException as err:
        print(err)
        sys.exit(1)

def clush(hosts, cmds):
    logging.debug("utils/clush: {0} {1}".format(cmds, hosts))

    task = ClusterShell.Task.task_self()
    task.run(cmds, nodes=hosts)

    for output, nodes in task.iter_buffers():
        logging.info("{0} {1}".format(ClusterShell.NodeSet.NodeSet.fromlist(nodes),
                                      output.message().decode('utf8')))


def run(cmd, exit_on_error=True, stdin=None, input=None, stdout=None, stderr=None, shell=False, debug=True):
    """Run a command and check its return code.

       Arguments:
       * cmd: list of command arguments
       * exit_on_error: boolean to control behaviour on command error (ie.
           return code != 0). If true (default) clara exits, otherwise the
           function raises an RuntimeError exception.
     """

    if debug:
        logging.debug("utils/run: %s" % cmd if shell else " ".join(cmd))

    try:
        if shell:
            popen = subprocess.Popen(cmd, shell=True, stdin=stdin,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output, error = popen.communicate()
            retcode = popen.returncode

        else:
            retcode = subprocess.call(cmd, stdin=stdin, stdout=stdout, stderr=stderr)
    except OSError as e:
        if (e.errno == errno.ENOENT):
            clara_exit("Binary not found, check your path and/or retry as root. \
                      You were trying to run:\n {0}".format(" ".join(cmd)))

    if retcode != 0:
        if exit_on_error:
            clara_exit(' '.join(cmd))
        elif shell:
            return error.decode(), retcode
        else:
            raise RuntimeError("Error {0} while running cmd: {1}" \
                               .format(retcode, ' '.join(cmd)))
    elif shell:
        return output.rstrip().decode(), error.rstrip().decode()


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
            if getconfig().has_option(section, value):
                return getconfig().get(section, value).strip()
            else:
                # we specify a certain values that can accept a None as a value
                if (value=="trg_dir" or value=="trg_img" or value=="mirror_local"):
                    return None
                else:
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

def get_bool_from_config_or(section, value, dist='', default=False):
    """ Read a boolean value from config.ini and return it"""
    string_value = get_from_config_or(section, value, dist, None)
    if string_value is None:
        return default
    return distutils.util.strtobool(string_value) == 1

def has_config_value(section, value, dist=''):
    """Return True if value is found in config.ini"""
    return (get_from_config_or(section, value, dist, None) is not None)


def getconfig():
    # Set a default configuration file in /usr as a backup conf file where it loads ONLY
    # the configuration params that are missing in the provided conf file /etc/clara/config.ini

    files = ['/usr/share/clara/config.ini','/etc/clara/config.ini']
    if conf.config:
        files.append(conf.config)

    if getconfig.config is None:
        getconfig.config = configparser.ConfigParser()
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
    if os.geteuid() == 0:
        output_dir = "/var/log/clara"
    else:
        output_dir = "%s/log/clara" % os.environ["HOME"]
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


def os_distribution():
    if 'platform' in sys.modules:
        return platform.dist()[0]
    else:
        return distro.distro_release_info()['id']


def os_major_version():
    if 'platform' in sys.modules:
        return int(platform.dist()[1].split('.')[0])
    else:
        return int(distro.major_version())

def makedirs_mode(path, mode):
    """Create directory recursively and set specific mode, no matter the
       current umask. The path can end with a slash ('/'), in which case it is
       stripped to avoid double creation of the same path with the ending slash
       and its dirname without the slash."""
    # Remove possible trailing '/' to avoid double processing with dirname(path)
    path = path.rstrip('/')
    if os.path.exists(path):
        return
    else:
        # create parent directory first
        makedirs_mode(os.path.dirname(path), mode)
        logging.info("Creating local directory path %s with mode %o", path, mode)
        os.mkdir(path)
        os.chmod(path, mode)


def clara_exit(msg):
    logging.error(msg)
    sys.exit(1)

def module(command, *arguments, **kwargs):
    """
    Execute a regular Lmod command and apply environment changes to
    the current Python environment (i.e. os.environ).

    In case len(arguments) == 1 the string will be split on whitespace into
    separate arguments. Pass a list of strings to avoid this.

    Raises an exception in case Lmod execution returned a non-zero
    exit code.

    Use with keyword argument show_environ_updates=True to show the actual
    changes made to os.environ (mostly for debugging).

    Examples:
    module('list')
    module('load', 'gcc')
    module('load', 'gcc cmake')
    module('load', 'gcc cmake', show_environ_updates=True)
    """
    numArgs = len(arguments)

    A = [
        "%s/lmod/lmod/libexec/lmod" % os.environ.get('EBROOTLMOD','/usr/share'),
        'python',
        command
    ]
    if (numArgs == 1):
        A += arguments[0].split()
    else:
        A += list(arguments)

    try:
        stdout, stderr = run(shlex.join(A), shell=True, exit_on_error=False)
    except:
        stdout, stderr = run(" ".join(A), shell=True, exit_on_error=False)
    if (os.environ.get('LMOD_REDIRECT','no') != 'no'):
        stdout = stderr

    return stdout, stderr
