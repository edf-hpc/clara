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
Show the set of configuration used in config.ini

Usage:
    clara show <section> [<dist>]

"""

import logging
import os
import shutil
import subprocess
import sys
import tempfile

import docopt

from clara.utils import clara_exit, conf, initialize_logger, getconfig


def print_section(list_items):
    for key, value in list_items:
        print("{}:{}".format(key, value))
    print('\n')


def show(section='all',dist=None):
    if section == 'all':
        for sec in getconfig().sections():
            print_section(getconfig().items(sec))

    elif section in getconfig().sections():
        if dist is None:
            print_section(getconfig().items(section))
        elif dist in getconfig().get("common", "allowed_distributions"):
            s_section = "{}-{}".format(section, dist)
            print("Section - {}".format(section))
            print_section(getconfig().items(section))
            print("Section - {}".format(s_section))
            if s_section in getconfig().sections():
                print_section(getconfig().items(section))
            else:
                clara_exit("'{0}' is not section in config.ini".format(s_section))
    else:
        clara_exit("'{0}' is not a section in config.ini".format(section))


def main():
    logging.debug(sys.argv)
    dargs = docopt.docopt(__doc__)

    if dargs['<section>']:
        section = dargs['<section>']
        dist = dargs['<dist>']
        show(section,dist)

if __name__ == '__main__':
    main()
