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
    clara repo init <dist>
    clara repo sync (all|<dist> [<suites>...])
    clara repo add <dist> <file>... [--reprepro-flags="list of flags"...]
    clara repo del <dist> <name>...
    clara repo list <dist>
    clara repo -h | --help | help

Options:
    <dist> is the target distribution
    <file> can be one or more *.deb binaries, *.changes files or *.dsc files.
    <name> is the package to remove, if the package is a source name, it'll
    remove all the associated binaries
"""

import subprocess
import logging
import os
import sys
import tempfile

import docopt
from clara.utils import clara_exit, run, get_from_config, value_from_file, conf


def do_key():
    key = get_from_config("repo", "gpg_key")
    fnull = open(os.devnull, 'w')
    cmd = ['gpg', '--list-secret-keys', key]
    logging.debug("repo/do_key: {0}".format(" ".join(cmd)))
    retcode = subprocess.call(cmd, stdout=fnull, stderr=fnull)
    fnull.close()

    # We import the key if it hasn't been imported before
    if retcode != 0:
        file_stored_key = get_from_config("repo", "stored_enc_key")
        if os.path.isfile(file_stored_key):
            password = value_from_file(get_from_config("common", "master_passwd_file"), "ASUPASSWD")

            if len(password) > 20:
                fdesc, temp_path = tempfile.mkstemp(prefix="tmpClara")
                cmd = ['openssl', 'aes-256-cbc', '-d', '-in', file_stored_key, '-out', temp_path, '-k', password]
                logging.debug("repo/do_key: {0}".format(" ".join(cmd)))
                retcode = subprocess.call(cmd)

                if retcode != 0:
                    os.close(fdesc)
                    os.remove(temp_path)
                    clara_exit('Command failed {0}'.format(" ".join(cmd)))
                else:
                    logging.info("Trying to import key {0}".format(key))
                    fnull = open(os.devnull, 'w')
                    cmd = ['gpg', '--allow-secret-key-import', '--import', temp_path]
                    logging.debug("repo/do_key: {0}".format(" ".join(cmd)))
                    retcode = subprocess.call(cmd)
                    fnull.close()
                    os.close(fdesc)
                    os.remove(temp_path)
                    if retcode != 0:
                        logging.info("\nThere was a problem with the import, make sure the key you imported "
                              "from {0} is the same you have in your configuration: {1}".format(file_stored_key, key))

            else:
                clara_exit('There was some problem reading the value of ASUPASSWD')
        else:
            clara_exit('Unable to read:  {0}'.format(file_stored_key))
    else:
        logging.info("GPG key was already imported.")


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

        list_flags = ['--ask-passphrase']
        if conf.ddebug:
            list_flags.append("-V")

        run(['reprepro'] + list_flags + \
            ['--basedir', repo_dir,
             '--outdir', get_from_config("repo", "mirror_local", dist),
             'export', dist])


def do_sync(selected_dist, input_suites=[]):
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
    if selected_dist == 'all':  # We sync everything
        suites = all_suites
    elif len(input_suites) == 0:  # We only sync suites related to the default distribution
        suites = info_suites[selected_dist].keys()
    else:  # If we select one or several suites, we check that are valid
        for s in input_suites:
            if s not in all_suites:
                clara_exit("{0} is not a valid suite. Valid suites are: {1}".format(s, " ".join(all_suites)))
            suites = input_suites

    logging.debug("The suites to sync are: {0}.".format(" ".join(suites)))
    for s in suites:
        mirror_root = get_from_config("repo", "mirror_root", suite_dist[s])
        dm_server = get_from_config("repo", "server", suite_dist[s])
        dm_root = info_suites[suite_dist[s]][s]

        suite_name = s
        if s in ["wheezy-security", "jessie-security"]:
            suite_name = s.split("-")[0] + "/updates"

        archs = get_from_config("repo", "archs", suite_dist[s])
        sections = get_from_config("repo", "sections", suite_dist[s])

        extra = []
        if conf.ddebug:  # if extra debug for 3rd party software
            extra = ['--debug']

        run(['debmirror'] + extra + ["--diff=none", "--method=http",
             "--nosource", "--ignore-release-gpg", "--ignore-missing-release",
             "--arch={0}".format(archs),
             "--host={0}".format(dm_server),
             "--root={0}".format(dm_root),
             "--dist={0}".format(suite_name),
             "--section={0}".format(sections),
              mirror_root + "/" + s])


def do_reprepro(action, package=None, flags=None):
    repo_dir = get_from_config("repo", "repo_dir", dist)
    reprepro_config = repo_dir + '/conf/distributions'

    if not os.path.isfile(reprepro_config):
        clara_exit("There is not configuration for the local repository for {0}. Run first 'clara repo init <dist>'".format(dist))

    list_flags = ['--silent', '--ask-passphrase']
    if conf.ddebug:
        list_flags = ['-V', '--ask-passphrase']

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
    logging.debug(sys.argv)
    dargs = docopt.docopt(__doc__)

    global dist
    dist = get_from_config("common", "default_distribution")
    if dargs["<dist>"] is not None:
        dist = dargs["<dist>"]
    if dist not in get_from_config("common", "allowed_distributions"):
        clara_exit("{0} is not a know distribution".format(dist))

    if dargs['key']:
        do_key()
    if dargs['init']:
        do_init()
    elif dargs['sync']:
        if dargs['all']:
            do_sync('all')
        else:
            do_sync(dargs['<dist>'], dargs['<suites>'])
    elif dargs['add']:
        for elem in dargs['<file>']:
            if elem.endswith(".deb"):
                do_reprepro('includedeb', elem, dargs['--reprepro-flags'])
            elif elem.endswith(".changes"):
                do_reprepro('include', elem, dargs['--reprepro-flags'])
            elif elem.endswith(".dsc"):
                do_reprepro('includedsc', elem, dargs['--reprepro-flags'])
            else:
                clara_exit("File is not a *.deb *.dsc or *.changes")
    elif dargs['del']:
        for elem in dargs['<name>']:
            do_reprepro('remove', elem)
            do_reprepro('removesrc', elem)
    elif dargs['list']:
        do_reprepro('list')

if __name__ == '__main__':
    main()
