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
    clara repo init [--dist=<name>]
    clara repo sync (all|<suite>...|--dist=<name>)
    clara repo add <file>... [--dist=<name>] [--reprepro-flags="list of flags"...]
    clara repo del <name>...[--dist=<name>]
    clara repo list [--dist=<name>]
    clara repo -h | --help | help

Options:
    --dist=<name>  Distribution target [default is set on distribution field
                   at the file config.ini].
    <file> can be one or more *.deb binaries, *.changes files or *.dsc files.
    <name> is the package to remove, if the package is a source name, it'll
    remove all the associated binaries
"""

import subprocess
import os
import sys
import tempfile

import docopt
from clara.utils import conf, run, get_from_config, value_from_file


def do_key():
    key = get_from_config("repo", "gpg_key")
    fnull = open(os.devnull, 'w')
    cmd = ['gpg', '--list-secret-keys', key]
    if conf.debug:
        print "CLARA Debug - repo/do_key: {0}".format(" ".join(cmd))
    retcode = subprocess.call(cmd, stdout=fnull, stderr=fnull)
    fnull.close()

    # We import the key if it hasn't been imported before
    if retcode != 0:
        file_stored_key = get_from_config("repo", "stored_enc_key")
        if os.path.isfile(file_stored_key):
            password = value_from_file(get_from_config("common", "master_passwd_file"), "ASUPASSWD")

            if len(password) > 20:
                fdesc, temp_path = tempfile.mkstemp()
                cmd = ['openssl', 'aes-256-cbc', '-d', '-in', file_stored_key, '-out', temp_path, '-k', password]
                if conf.debug:
                    print "CLARA Debug - repo/do_key: {0}".format(" ".join(cmd))
                retcode = subprocess.call(cmd)

                if retcode != 0:
                    os.close(fdesc)
                    os.remove(temp_path)
                    sys.exit('Command failed {0}'.format(" ".join(cmd)))
                else:
                    print "Trying to import key {0}".format(key)
                    fnull = open(os.devnull, 'w')
                    cmd = ['gpg', '--allow-secret-key-import', '--import', temp_path]
                    if conf.debug:
                        print "CLARA Debug - repo/do_key: {0}".format(" ".join(cmd))
                    retcode = subprocess.call(cmd)
                    fnull.close()
                    os.close(fdesc)
                    os.remove(temp_path)
                    if retcode != 0:
                        print "\nThere was a problem with the import, make sure the key you imported " \
                              "from {0} is the same you have in your configuration: {1}".format(file_stored_key, key)

            else:
                sys.exit('There was some problem reading the value of ASUPASSWD')
        else:
            sys.exit('Unable to read:  {0}'.format(file_stored_key))
    else:
        print "GPG key was already imported."


def do_init():
    repo_dir = get_from_config("repo", "repo_dir", dist)
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
""".format(get_from_config("common", "origin", dist),
            dist,
            get_from_config("repo", "version", dist),
            get_from_config("repo", "gpg_key", dist),
            get_from_config("repo", "clustername", dist)))
        freprepro.close()

    os.chdir(repo_dir)
    run(['reprepro', '--ask-passphrase', '--basedir', repo_dir,
         '--outdir', get_from_config("repo", "mirror_local", dist),
         'export', dist])


def do_sync(input_suites):
    info_suites = {}  # Contains all the information
    suite_dist = {}  # Contains the pairs suite - webdir
    all_suites = []  # Contains a list with all the suites names

    for distribution in get_from_config("common", "allowed_distributions").split(","):
        elements = get_from_config("repo", "info_suites", distribution).split(",")
        tmp_info_suites = {}

        for e in elements:
            k, v = e.split(":")
            all_suites.append(k)
            suite_dist[k] = distribution
            tmp_info_suites[k] = v

        info_suites[distribution] = tmp_info_suites

    suites = []
    if input_suites == 'all':
        suites = all_suites
    elif len(input_suites) == 0:  # We only sync suites related to the default distribution
        suites = info_suites[dist].keys()
    else:  # If we select one or several suites, we check that are valid
        for s in input_suites:
            if s not in all_suites:
                sys.exit("{0} is not a valid suite. Valid suites are: {1}".format(s, " ".join(all_suites)))
            suites = input_suites

    for s in suites:
        mirror_root = get_from_config("repo", "mirror_root", suite_dist[s])
        dm_server = get_from_config("repo", "server", suite_dist[s])
        dm_root = info_suites[suite_dist[s]][s]

        suite_name = s
        if s in ["wheezy-security", "jessie-security"]:
            suite_name = s.split("-")[0] + "/updates"

        run(['debmirror',
             # '--dry-run', '--debug', '--progress', '--verbose',
             "--diff=none", "--method=http", "--arch=i386,amd64",
             "--nosource", "--ignore-release-gpg", "--ignore-missing-release",
             "--host={0}".format(dm_server),
             "--root={0}".format(dm_root),
             "--dist={0}".format(suite_name),
             "--section=main,contrib,non-free",
              mirror_root + "/" + s])


def do_reprepro(action, package, flags):
    list_flags = ['--silent', '--ask-passphrase']

    if flags is not None:
        list_flags.append(flags)

    cmd = ['reprepro'] + list_flags + \
         ['--basedir', get_from_config("repo", "repo_dir", dist),
         '--outdir', get_from_config("repo", "mirror_local", dist),
         action, dist]

    if package is not None:
        cmd.append(package)

    run(cmd)


def main():
    dargs = docopt.docopt(__doc__)

    global dist
    dist = get_from_config("common", "default_distribution")
    if dargs["--dist"] is not None:
        dist = dargs["--dist"]
    if dist not in get_from_config("common", "allowed_distributions"):
        sys.exit("{0} is not a know distribution".format(dist))

    if dargs['key']:
        do_key()
    if dargs['init']:
        do_init()
    elif dargs['sync']:
        if dargs['all']:
            do_sync('all')
        else:
            do_sync(dargs['<suite>'])
    elif dargs['add']:
        for elem in dargs['<file>']:
            if elem.endswith(".deb"):
                do_reprepro('includedeb', elem, dargs['--reprepro-flags'])
            elif elem.endswith(".changes"):
                do_reprepro('include', elem, dargs['--reprepro-flags'])
            elif elem.endswith(".dsc"):
                do_reprepro('includedsc', elem, dargs['--reprepro-flags'])
            else:
                sys.exit("File is not a *.deb *.dsc or *.changes")
    elif dargs['del']:
        for elem in dargs['<name>']:
            do_reprepro('remove', elem)
            do_reprepro('removesrc', elem)
    elif dargs['list']:
        do_reprepro('list', None)

if __name__ == '__main__':
    main()
