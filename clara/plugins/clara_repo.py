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
Creates, updates and synchronizes local Debian repositories.

Usage:
    clara repo key
    clara repo init
    clara repo sync [create]
    clara repo (add|del) <package>
    clara repo -h | --help | help

"""

import subprocess
import os
import sys
import tempfile

import docopt
from clara.utils import run, getconfig, value_from_file


def do_key():
    fnull = open(os.devnull, 'w')
    cmd = ['gpg', '--list-secret-keys', getconfig().get("repo", "gpg_key")]
    retcode = subprocess.call(cmd, stdout=fnull)
    fnull.close()

    # We import the key if it hasn't been imported before
    if retcode != 0:
        file_stored_key = getconfig().get("repo", "stored_enc_key")
        if os.path.isfile(file_stored_key):
            password = value_from_file(getconfig().get("common", "master_passwd_file"), "PASSPHRASE")

            if len(password) > 20:
                fdesc, temp_path = tempfile.mkstemp()
                cmd = ['openssl', 'aes-256-cbc', '-d', '-in', file_stored_key,
                       '-out', temp_path, '-k', password]
                retcode = subprocess.call(cmd)

                if retcode != 0:
                    os.close(fdesc)
                    os.remove(temp_path)
                    sys.exit('Command failed {0}'.format(" ".join(cmd)))
                else:
                    fnull = open(os.devnull, 'w')
                    cmd = ['gpg', '--allow-secret-key-import',
                           '--import', temp_path]
                    retcode = subprocess.call(cmd, stdout=fnull)
                    fnull.close()
                    os.close(fdesc)
                    os.remove(temp_path)
                    if retcode != 0:
                        sys.exit('Command failed {0}'.format(" ".join(cmd)))

            else:
                sys.exit('There was some problem reading the PASSPHRASE')
        else:
            sys.exit('Unable to read:  {0}'.format(file_stored_key))
    else:
        print "GPG key was already imported."


def do_init():
    repo_dir = getconfig().get("repo", "repo_dir")
    reprepro_config = repo_dir + '/conf/distributions'

    if not os.path.isfile(reprepro_config):
        if not os.path.isdir(repo_dir + '/conf'):
            os.makedirs(repo_dir + '/conf')

        freprepro = open(reprepro_config, 'w')
        freprepro.write("""Origin: {0}
Label: {1}
Suite: {1}
Codename: {1}
Version: {2}
Architectures: amd64 source
Components: main contrib non-free
UDebComponents: main
SignWith: {3}
Description: Depot Local {4}
DebIndices: Packages Release . .gz .bz2
DscIndices: Sources Release . .gz .bz2
""".format(getconfig().get("common", "origin"),
            getconfig().get("common", "distribution"),
            getconfig().get("repo", "version"),
            getconfig().get("repo", "gpg_key"),
            getconfig().get("repo", "clustername")))
        freprepro.close()

    os.chdir(repo_dir)
    run(['reprepro', '--ask-passphrase', '--basedir', repo_dir,
         '--outdir', getconfig().get("repo", "mirror_local"),
         'export', getconfig().get("common", "distribution")])


def do_sync(option=''):
    local = getconfig().get("repo", "local_modules").split(',')
    remote = getconfig().get("repo", "remote_modules").split(',')

    for elem in range(0, len(local)):
        if os.path.isdir(getconfig().get("repo", "mirror_root") +
                         "/" + local[elem]) or (option == 'create'):

            run(['rsync',
                 '-az', '--stats', '--force', '--delete', '--ignore-errors',
                 getconfig().get("repo", "server") + '::' + remote[elem],
                 getconfig().get("repo", "mirror_root") + '/' + local[elem]])
        else:
            sys.exit('Local repository not found. '
                     'Please run: \n\tclara repo sync create')


def do_package(action, package):
    run(['reprepro', '--ask-passphrase',
         '--basedir', getconfig().get("repo", "repo_dir"),
         '--outdir', getconfig().get("repo", "mirror_local"),
         action, getconfig().get("repo", "distribution"), package])


def main():
    dargs = docopt.docopt(__doc__)

    if dargs['key']:
        do_key()
    if dargs['init']:
        do_init()
    elif dargs['sync']:
        if dargs['create']:
            do_sync('create')
        else:
            do_sync()
    elif dargs['add']:
        do_package('includedeb', dargs['<package>'])
    elif dargs['del']:
        do_package('remove', dargs['<package>'])


if __name__ == '__main__':
    main()
