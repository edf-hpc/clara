#!/usr/bin/env python
#-*- coding: utf-8 -*-
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

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

# Get version automatically from debian/changelog
VERSION = ''
with open("debian/changelog", 'r') as fcl:
    fl = fcl.readline()
VERSION = fl[fl.find("(")+1:fl.find(")")]

with open("clara/version.py", 'w') as fwv:
    fwv.write("__version__ = '{0}'".format(VERSION))

setup(name='Clara',
      version=VERSION,
      scripts=['bin/clara'],
      packages=['clara',
                'clara.plugins'],
      install_requires=['docopt>=0.6.1',
                        'importlib>=1.0.1',
                        'clustershell>=1.6'],
      package_data={'': ['README.md']},

      author='EDF CCN HPC',
      author_email='dsp-cspit-ccn-hpc@edf.fr',
      license='CeCILL-C (French equivalent to LGPLv2+)',
      url='https://github.com/edf-hpc/clara',
      platforms=['GNU/Linux', 'BSD'],
      keywords='cluster administration',
      description='Cluster Administration Tools',
      classifiers=[
          'Development Status :: 4 - Beta',
          'Environment :: Console',
          'Intended Audience :: System Administrators',
          'License :: OSI Approved',
          'Operating System :: MacOS :: MacOS X',
          'Operating System :: POSIX :: BSD',
          'Operating System :: POSIX :: Linux',
          'Programming Language :: Python',
          'Programming Language :: Python :: 2.6',
          'Programming Language :: Python :: 2.7',
          'Topic :: System :: Clustering',
          'Topic :: System :: Systems Administration']
    )
