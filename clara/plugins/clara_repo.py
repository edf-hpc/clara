#!/usr/bin/env python
# -*- coding: utf-8 -*-
##############################################################################
#  Copyright (C) 2014-2017 EDF SA                                            #
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
    clara repo init <dist> [--force]
    clara repo sync (all|<dist> [<suites>...])
    clara repo push [<dist>]
    clara repo add <dist> <file>... [--reprepro-flags="list of flags"...] [--no-push]
    clara repo del <dist> <name>... [--no-push]
    clara repo search <keyword> [rpm|deb]
    clara repo list (all|rpm|deb|<dist>)
    clara repo copy <dist> <package> <from-dist> [--no-push]
    clara repo move <dist> <package> <from-dist> [--no-push]
    clara repo jenkins (list|<dist>) <job> [--source=<arch>] [--reprepro-flags="list of flags"...] [--build=<build>]
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
import configparser
import re
import glob
import shutil

import docopt
from clara.utils import clara_exit, run, get_from_config, get_from_config_or, value_from_file, conf, os_distribution, os_major_version, do_print

try:
    from prettytable import PrettyTable as prettytable
except:
    print("[WARN] PLS raise 'pip install prettytable' or install 'python3-prettytable' package!")
    pass

_opt = {'dist': None}

def do_update(dist, path_repo=None, makecache=True):
    if not path_repo:
        # default to "/srv/repos" distribution base repository
        repo_dir = get_from_config_or("repo", "repo_rpm", dist, "/srv/repos")
        path_repo = os.path.join(repo_dir, dist)

    fnull = open(os.devnull, 'w')
    cmd = ["/usr/bin/createrepo", "--update", path_repo]
    run(cmd, stdout=fnull, stderr=fnull)
    cmd = ["/usr/bin/yum-config-manager", "--enable", dist]
    run(cmd, stdout=fnull, stderr=fnull)
    if makecache:
        cmd = ["/usr/bin/yum", "makecache", "--disablerepo=*", "--enablerepo=%s" % dist]
        run(cmd, stdout=fnull, stderr=fnull)
    fnull.close()

def do_create(dest_dir="Packages", force=False):
    # default to "/srv/repos" distribution base repository
    repo_dir = get_from_config_or("repo", "repo_rpm", _opt['dist'], '/srv/repos')
    path_repo = os.path.join(repo_dir, _opt['dist'])

    if os.path.isdir(path_repo):
        if not force:
            message = "The repository '{}' already exists!\n".format(path_repo)
            message += "              - If need, add switch --force to recreate it!"
            clara_exit(message)
    else:
        logging.info("Creating repository {} in directory {} ...".format(_opt['dist'], repo_dir))
        os.makedirs(os.path.join(path_repo, dest_dir))

    do_update(_opt['dist'], path_repo, makecache=False)

    createrepo_config = os.path.join("/etc/yum/repos.d/", _opt['dist'] + ".repo")
    fcreaterepo = open(createrepo_config, 'w')
    fcreaterepo.write("""[{0}]
name={0}
baseurl={1}
enabled=1
autorefresh=1
gpgcheck=1
""".format(_opt['dist'], "file://" + path_repo))

    fcreaterepo.close()

def do_add(package, dest_dir="Packages"):
    # default to "/srv/repos" distribution base repository
    repo_dir = get_from_config_or("repo", "repo_rpm", _opt['dist'], "/srv/repos")
    path_repo = os.path.join(repo_dir, _opt['dist'])
    if not os.path.isdir(path_repo):
        message = "There is no configuration for repository %s!\n" % _opt['dist']
        message += "PLS, run first 'clara repo init <dist>'"
        clara_exit(message)

    path = os.path.join(path_repo, dest_dir)
    if not os.path.isdir(path):
        os.makedirs(path)

    if os.path.isfile(package):
        logging.info("Adding package %s to repository %s ..." % (package,_opt['dist']))
        shutil.copy(package, path)
    else:
        logging.warn("Path %s to package don't exist!" % package)

def do_del(packages, dest_dir="Packages"):
    # default to "/srv/repos" distribution base repository
    repo_dir = get_from_config_or("repo", "repo_rpm", _opt['dist'], "/srv/repos")
    path_repo = os.path.join(repo_dir , _opt['dist'])
    path = os.path.join(path_repo, dest_dir)

    # default to "x86_64,src,i686,noarch" archs
    archs = get_from_config_or("repo", "archs_rpm", _opt['dist'], default="x86_64,src,i686,noarch")
    for package in packages:
        elem = package.split(':')
        cmd = "repoquery -a --show-duplicates --search " + elem[0] + " --archlist=" + archs + " -q --qf='%{location}'"
        output, _ = run(cmd, shell=True)
        for line in output.split('\n'):
            filename = line[7:]
            if len(elem) == 2:
                if re.search(elem[1], filename):
                    if os.path.isfile(filename):
                        logging.info("removing path {} to repository {}".format(filename, _opt['dist']))
                        os.remove(filename)
                    else:
                        logging.warn("path {} to package {} don't exist!".format(filename, package))
            else:
                if os.path.isfile(filename):
                    logging.info("removing path {} to package".format(filename, package))
                    os.remove(filename)
                else:
                    logging.warn("path {} to package {} don't exist!".format(filename, package))

    do_update(_opt['dist'], path_repo)

def do_list(dest_dir="Packages", dist=None):
    # default to "x86_64,src,i686,noarch" archs
    archs = get_from_config_or("repo", "archs_rpm", _opt['dist'], default="x86_64,src,i686,noarch")
    if dist:
        cmd = "repoquery --repoid=" + dist + " -a --archlist=" + archs + " --envra --show-duplicates"
        logging.debug("repo/do_list(repo): {}".format(cmd))
        output, error = run(cmd, shell=True)
        if len(error):
            logging.error("repo/do_list(repo): {}".format(error))
        else:
            for line in output.split('\n'):
                if len(line):
                    lst = line.split('.')
                    tab = lst[0].split('-')
                    package = '-'.join(tab[0:-1]) + ' ' + tab[-1] + '.'
                    version = '.'.join(lst[1:-1])
                    arch = lst[-1]
                    print("{}|rpm|{}: {}{}".format(_opt['dist'], arch, package[2:], version ))
                else:
                    message = "repo/do_list: no package yet added to repository {}!\n".format(_opt['dist'])
                    message += "                - you probably need to initilize existing repository manually created!"
                    logging.warn(message)
    else:
        cmd = "repoquery -a --archlist=" + archs + " --show-duplicates -q --qf='%{repoid} %{location}'"
        logging.debug("repo/do_list: {}".format(cmd))
        output, _ = run(cmd, shell=True)
        for line in output.split('\n'):
            if len(line):
                lst = line.split('/')
                repo = lst[0].split(' ')[0]
                idx = lst.index(repo)
                filename = os.path.basename(line)
                rpm_os = filename.split('.')
                fullname = '/'.join(lst[idx + 1:])
                print("{}|{}|{} {}".format(repo, rpm_os[-1], rpm_os[-2], fullname))
            else:
                message = "repo/do_list: no yet known rpm repository!\n"
                message += "                - you probably need to initilize existing repository manually created!"
                logging.warn(message)

def do_search(extra, table):
    # default to "x86_64,src,i686,noarch" archs
    archs = get_from_config_or("repo", "archs_rpm", _opt['dist'], default="x86_64,src,i686,noarch")

    cmd = "repoquery -a --show-duplicates --search " + extra + " --archlist=" + archs + " -q --qf='%{repoid} %{name} %{location}'"
    output, _ = run(cmd, shell=True)
    arch = {}

    for line in output.split('\n'):
        if line == "":
            continue
        filename = os.path.basename(line)
        repoid = line.split(' ')[0]
        package = line.split(' ')[1]
        tab = filename[len(package) + 1:].split('.')
        version = '.'.join(tab[0:-2])
        key = package + ' ' + version + ' ' + repoid
        name = tab[-2]
        if key in arch:
           arch[key] += ',' + name
        else:
           arch[key] = name
    for key in arch:
        do_print(table, key.split(' ') + [arch[key]])

def do_copy(from_dist, package, move=False):
    # default to "x86_64,src,i686,noarch" archs
    archs = get_from_config_or("repo", "archs_rpm", _opt['dist'], default="x86_64,src,i686,noarch")

    version = None
    if ':' in package:
        package, version = package.split(':')
    cmd = "repoquery -a --show-duplicates --search " + package + " --archlist=" + archs + " -q --qf='%{repoid} %{name} %{location}'"
    output, _ = run(cmd, shell=True)
    packages = {}
    done = {}

    for line in output.split('\n'):
        if line == "":
            continue
        repoid, name, filename = line.replace('file://','').split(' ')
        basename = os.path.basename(filename)
        if (version == None and name == package) or (version and basename.startswith(package + '-' + version)):
            if not os.path.isfile(filename):
                logging.debug("repo/do_copy: file %s don't exist!" % filename)
                continue
            if repoid == _opt['dist']:
                # package already exist in destination dist!
                done[basename] = ''
                continue
            elif repoid == from_dist:
                # consider only package from needfull dist!
                packages[filename] = ''

    count = 0
    if len(packages):
        for elem in packages:
            if os.path.basename(elem) in done:
                continue
            count += 1
            if elem.endswith(".rpm"):
                do_add(elem)
            elif elem.endswith(".src.rpm"):
                do_add(elem, dest_dir="SPackages")
            if move:
                logging.debug("repo/do_copy: removing package %s from dist %s!" % (package, from_dist))
                os.remove(elem)

        if count:
            do_update(_opt['dist'])
            if move:
                do_update(from_dist)
        else:
            logging.info("repo/do_copy: package %s already exist in dist %s!" % (package, _opt['dist']))
    else:
        message = " (version: %s)" % version if version else ""
        logging.info("repo/do_copy: no package %s%s exist in dist %s!" % (package, message, from_dist))

# Returns a boolean to tell if password derivation can be used with OpenSSL.
# It is disabled on Debian < 10 (eg. in stretch) because it is not supported by
# openssl provided in these old distributions.
#
# This code can be safely removed when Debian 9 stretch support is dropped.
def enable_password_derivation():

    return os_distribution() != 'debian' or os_major_version() > 9

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

            digest = get_from_config_or("common", "digest_type", default="sha256")
            if digest not in ['md2', 'md5', 'mdc2', 'rmd160', 'sha', 'sha1', 'sha224', 'sha256', 'sha384', 'sha512']:
                logging.warning("Invalid digest type : {0}, using default digest type: sha256".format(digest))
                digest = "sha256"

            if len(password) > 20:
                fdesc, temp_path = tempfile.mkstemp(prefix="tmpClara")
                cmd = ['openssl', 'enc', '-aes-256-cbc', '-md', digest, '-d', '-in', file_stored_key, '-out', temp_path, '-k', password]

                # Return the openssl command to proceed with operation op, with or without key
                # derivation.
                if enable_password_derivation():
                    # The number of iterations is hard-coded as it must be changed
                    # synchronously on both clara and puppet-hpc for seamless handling of
                    # encrypted files. It is set explicitely to avoid relying on openssl
                    # default value and being messed by sudden change of this default
                    # value.
                    cmd[3:3] = ['-iter', '+100000', '-pbkdf2' ]

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
                clara_exit("There was some problem while reading ASUPASSWD's value")
        else:
            clara_exit('Unable to read:  {0}'.format(file_stored_key))
    else:
        logging.info("GPG key was already imported.")


def do_init():
    repo_dir = get_from_config("repo", "repo_dir", _opt['dist'])
    reprepro_config = repo_dir + '/conf/distributions'
    mirror_local = get_from_config("repo", "mirror_local", _opt['dist'])
    if (mirror_local=="" or mirror_local==None):
        mirror_local = repo_dir +'/mirror'

    if os.path.isdir(repo_dir):
        clara_exit("The repository '{0}' already exists !".format(repo_dir))
    else :
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
""".format(get_from_config("common", "origin", _opt['dist']),
                    _opt['dist'],
                    get_from_config("repo", "version", _opt['dist']),
                    get_from_config("repo", "gpg_key", _opt['dist']),
                    get_from_config("repo", "clustername", _opt['dist'])))
            freprepro.close()

            os.chdir(repo_dir)

            list_flags = ['--ask-passphrase']
            if conf.ddebug:
                list_flags.append("-V")
            try:

                run(['reprepro'] + list_flags +
                    ['--basedir', repo_dir,
                    '--outdir', mirror_local,
                    'export', _opt['dist']])
            except:
                shutil.rmtree(repo_dir)
                clara_exit("The repository '{0}' has not been initialized properly, it will be deleted  !".format(repo_dir))


def get(config, section, value):

    # If the value is not in the override section, look in "repos" from the config.ini
    if config.has_option(section, value):
        return config.get(section, value).strip()
    else:
        try:
            return get_from_config("repo", value)
        except:
            clara_exit("Value '{0}' not found in section '{1}'".format(value, section))


def do_sync(selected_dist, input_suites=[]):

    suites = []
    # Sync everything
    if selected_dist == 'all':
        for d in get_from_config("common", "allowed_distributions").split(","):
            suites = suites + get_from_config("repo", "suites", d).split(",")
    else:
        # Only sync suites related to the selected distribution
        if len(input_suites) == 0:
            suites = get_from_config("repo", "suites", selected_dist).split(",")
        # User selected one or several suites, check that they are valid
        else:
            for s in input_suites:
                if s not in get_from_config("repo", "suites", selected_dist).split(","):
                    clara_exit("{0} is not a valid suite from distribution {1}.\n"
                        "Valid suites are: {2}".format(
                         s, selected_dist, get_from_config("repo", "suites", selected_dist)))
            suites = input_suites
    suites = [suite for suite in suites if suite]
    logging.debug("The suites to sync are: {0}.".format(" ".join(suites)))

    # Read /etc/clara/repos.ini
    if not os.path.isfile('/etc/clara/repos.ini'):
        clara_exit("File /etc/clara/repos.ini not found.")
    repos = configparser.ConfigParser()
    repos.read("/etc/clara/repos.ini")

    for s in suites:

        extra = []
        if conf.ddebug:  # if extra debug for 3rd party software
            extra = ['--debug']

        final_dir = get(repos, s, "mirror_root") + "/" + s
        run(['debmirror'] + extra + ["--diff=none",
            "--nosource", "--ignore-release-gpg", "--ignore-missing-release",
            "--method={0}".format(get(repos, s, "method")),
            "--arch={0}".format(get(repos, s, "archs")),
            "--host={0}".format(get(repos, s, "server")),
            "--root={0}".format(get(repos, s, "mirror_dir")),
            "--dist={0}".format(get(repos, s, "suite_name")),
            "--section={0}".format(get(repos, s, "sections")),
            final_dir])


def do_push(dist=''):
    push_cmd = get_from_config_or("repo", "push", dist, None)
    if push_cmd:
        push_hosts = get_from_config_or("repo", "hosts", dist, '').split(',')
        if push_hosts and push_hosts[0] is not '':
            for host in push_hosts:
                run(push_cmd.format(host).split(' '))
        else:
            run(push_cmd.split(' '))


def do_reprepro(action, package=None, flags=None, extra=None, table=None):
    repo_dir = get_from_config("repo", "repo_dir", _opt['dist'])
    reprepro_config = repo_dir + '/conf/distributions'
    mirror_local = get_from_config("repo", "mirror_local", _opt['dist'])
    if (mirror_local=="" or mirror_local==None):
        mirror_local = repo_dir +'/mirror'
    oldMask = os.umask(0o022)
    if not os.path.isfile(reprepro_config):
        clara_exit("There is not configuration for the local repository for {0}. Run first 'clara repo init <dist>'".format(_opt['dist']))

    list_flags = ['--silent', '--ask-passphrase']
    if conf.ddebug:
        list_flags = ['-V', '--ask-passphrase']

    if flags is not None:
        list_flags.append(flags)

    cmd = ['reprepro'] + list_flags + \
         ['--basedir', get_from_config("repo", "repo_dir", _opt['dist']),
         '--outdir', mirror_local,
         action]

    if extra is not None:
        for e in extra:
            cmd.append(e)
    else:
        if action in ['includedeb', 'include', 'includedsc', 'remove', 'removesrc', 'list']:
            cmd.append(_opt['dist'])

        if package is not None:
            cmd.append(package)

    if action == 'ls' and table:
        output, _ = run(' '.join(cmd), shell=True)

        for line in output.split('\n'):
            if line == "":
                continue
            do_print(table, [i.strip() for i in line.split('|')])
    else:
        run(cmd)

    os.umask(oldMask)


def copy_jenkins(job, arch, flags=None, build="lastSuccessfulBuild", distro=None, dry_run=False):

    if re.search(r"bin-|-binaries", job):
        jobs = [job]
    elif dry_run:
        jobs = ["*%s*" % job]
    else:
        jobs  = [job + "-binaries", "bin-" + job]
        jobs += [job + "-binariesrpm", job + "-binariesrpm2"]

    jenkins_dir = get_from_config("repo", "jenkins_dir")
    isok = False

    if dry_run:
        try:
            table = prettytable()
            table.field_names = ['Job', 'Path', 'Build', 'Package']
        except:
            table = "{:30}|{:60}|{:15}|{}"

    for job in jobs:
        archive_path = "builds/%s/archive/" % build
        conf = "configurations/"
        axis_arch = conf + "axis-architecture/%s/" % arch
        paths = [ os.path.join(jenkins_dir, job, archive_path),
                  os.path.join(jenkins_dir, job, conf + archive_path),
                  os.path.join(jenkins_dir, job, axis_arch + archive_path)]

        for path in paths:

            if not os.path.isdir(path) and not dry_run:
                continue

            if dry_run:
                for _file in glob.glob(path + "/*"):
                    _file = _file.replace(jenkins_dir, '').split('/')
                    _job = _file[0]
                    _dirname = '/'.join(_file[1:-3])
                    _build = _file[-3]
                    _name = _file[-1]
                    do_print(table, [_job, _dirname, _build, _name])
            else:

                if not distro or distro == "debian":
                    for changesfile in glob.glob(path + "/*_%s.changes" % arch):
                        message = "Found job named {} under path:\n{} ..!\n".format(job, path)
                        logging.info(message)
                        do_reprepro('include', package=changesfile, flags=flags)
                        isok = True
                        break

                # if any, continue breaking, are we are in nested break!
                if isok:
                    break

                # rpm specific treatment
                if not distro or distro == "rhel":
                    for f in os.listdir(path):
                        elem = os.path.join(path+f)
                        if f.endswith(".src.rpm"):
                            do_add(elem, dest_dir="SPackages")
                            isok = True
                        elif f.endswith(".rpm"):
                            do_add(elem)
                            isok = True
                    if isok:
                        do_update(_opt['dist'])

                if isok:
                    break

        # if any, continue breaking, are we are in nested break!
        if isok:
            break

        if not dry_run:
            message  = "No job {} named {} found! ".format(distro, job)
            message += "Either is doesn't exist or needs to be built..!"
            logging.debug(message)

    if dry_run:
        try:
            # instead of printing raw table, work a little around it to have
            # something more intuitive, suppressing redundant information!
            done = {}
            if table._get_rows({'oldsortslice': False,'start': 0, 'end': 1, 'sortby': False}):
                table.align["Path"] = "l"
                table.align["Job"] = "l"
                table.align["Package"] = "l"
                table.sortby = "Job"

                table_txt = ''
                match_line = 0
                empty_cell = False
                # simulate here some tricks not yet supported by prettytable used version!
                # add supplementary horizontal line
                for number, line in enumerate(table.get_string().split('\n')):
                    job = None
                    if number == 0:
                        horizontal = line
                    elif number > 1:
                        if '|' in line:
                            job = line.split('|')[1].strip()
                    if job:
                        if job not in done:
                            done[job] = ''
                            if number > 3:
                                line = '%s\n%s' % (horizontal, line)
                            table_txt = '%s%s\n' % (table_txt, line)
                        else:
                            # for line of witch three first columns have been printed, we no more
                            # print again same information! So table if more readable!
                            # we replace all colum cell data with space
                            cell1 = re.sub(r'.*', lambda x: ' ' * len(x.group()), line.split('|')[1])
                            cell2 = re.sub(r'.*', lambda x: ' ' * len(x.group()), line.split('|')[2])
                            cell3 = re.sub(r'.*', lambda x: ' ' * len(x.group()), line.split('|')[3])
                            line = "|{}|{}|{}|{}".format(cell1, cell2, cell3, '|'.join(line.split('|')[4:]))
                            table_txt = '%s%s\n' % (table_txt, line)
                    else:
                        table_txt = '%s%s\n' % (table_txt, line)

                # we finally print result more funny table!
                print(table_txt)
        except:
            pass



def main():
    logging.debug(sys.argv)
    dargs = docopt.docopt(__doc__)


    if not (dargs['jenkins'] and dargs['list']):
        _opt['dist'] = get_from_config("common", "default_distribution")

        if dargs["<dist>"] is not None:
            _opt['dist'] = dargs["<dist>"]

        if _opt['dist'] not in get_from_config("common", "allowed_distributions"):
            clara_exit("{0} is not a known distribution".format(_opt['dist']))

        if re.match(r"scibian|calibre", _opt['dist']):
            distro = 'debian'
        elif "rpm-hpc" in _opt['dist']:
            distro = 'rhel'
        else:
            pattern = re.compile(r"(?P<distro>[a-z]+)(?P<version>\d+)")
            match = pattern.match(_opt['dist'])
            if match:
                distro = match.group('distro')
                if distro in ['rhel', 'centos', 'almalinux', 'rocky']:
                    distro = 'rhel'
            else:
                # default to "rhel" distribution
                distro = get_from_config_or("repo", "distro", _opt['dist'], "rhel")
                if distro not in ['debian', 'rhel']:
                    clara_exit("provided distribution %s not yet supported!" % distro)
    else:
        distro = None

    if dargs['key']:
        do_key()
    if dargs['init']:
        if distro == "debian":
            do_init()
        elif distro == "rhel":
            do_create(force=dargs['--force'])
    elif dargs['sync']:
        if dargs['all']:
            do_sync('all')
        else:
            do_sync(dargs['<dist>'], dargs['<suites>'])
    elif dargs['push']:
        get_from_config("repo", "push", _opt['dist'])
        if dargs['<dist>']:
            do_push(_opt['dist'])
        else:
            do_push()
    elif dargs['add']:
        if distro == "debian":
            for elem in dargs['<file>']:
                if elem.endswith(".deb"):
                    do_reprepro('includedeb', elem, dargs['--reprepro-flags'])
                elif elem.endswith(".changes"):
                    do_reprepro('include', elem, dargs['--reprepro-flags'])
                elif elem.endswith(".dsc"):
                    do_reprepro('includedsc', elem, dargs['--reprepro-flags'])
                else:
                    clara_exit("File is not a *.deb *.dsc or *.changes")
        elif distro == "rhel":
            for elem in dargs['<file>']:
                if elem.endswith(".rpm"):
                    do_add(elem)
                elif elem.endswith(".src.rpm"):
                    do_add(elem, dest_dir="SPackages")
            do_update(_opt['dist'])
        if dargs['<file>'] and not dargs['--no-push']:
            do_push(_opt['dist'])
    elif dargs['del']:
        if distro == "debian":
            for elem in dargs['<name>']:
                do_reprepro('remove', elem)
                do_reprepro('removesrc', elem)
            if dargs['<name>'] and not dargs['--no-push']:
                do_push(_opt['dist'])
        elif distro == "rhel":
            do_del(dargs['<name>'])
    elif dargs['list'] and not dargs['jenkins']:
        if dargs['all']:
            do_reprepro('dumpreferences')
            do_list()
        elif dargs['rpm']:
            do_list()
        elif dargs['deb']:
            do_reprepro('dumpreferences')
        else:
            if distro == "debian":
                do_reprepro('list')
            elif distro == "rhel":
                do_list(dist=_opt['dist'])
    elif dargs['search']:
        try:
            table = prettytable()
            table.field_names = ['Packages', 'Version', 'Repository', 'Archs']
        except:
            table = "{:20} | {:40} | {:30} | {}"

        if dargs['deb']:
            do_reprepro('ls', extra=[dargs['<keyword>']], table=table)
        elif dargs['rpm']:
            do_search(dargs['<keyword>'], table)
        else:
            do_reprepro('ls', extra=[dargs['<keyword>']], table=table)
            do_search(dargs['<keyword>'], table)

        try:
            # instead of printing raw table, work a little around it to have
            # something more intuitive, suppressing redundant information!
            if table._get_rows({'oldsortslice': False,'start': 0, 'end': 1, 'sortby': False}):
                table.align["Packages"] = "l"
                table.align["Version"] = "r"
                table.align["Repository"] = "r"
                table.align["Archs"] = "l"
                table.sortby = "Repository"

                print(table)
        except:
            pass

    elif dargs['copy']:
        if dargs['<from-dist>'] not in get_from_config("common", "allowed_distributions"):
            clara_exit("{0} is not a known distribution".format(dargs['<from-dist>']))
        if distro == "debian":
            do_reprepro('copy', extra=[_opt['dist'], dargs['<from-dist>'], dargs['<package>']])
        elif distro == "rhel":
            do_copy(dargs['<from-dist>'], dargs['<package>'])
        if not dargs['--no-push']:
            do_push(_opt['dist'])
    elif dargs['move']:
        if dargs['<from-dist>'] not in get_from_config("common", "allowed_distributions"):
            clara_exit("{0} is not a known distribution".format(dargs['<from-dist>']))
        if distro == "debian":
            do_reprepro('copy', extra=[_opt['dist'], dargs['<from-dist>'], dargs['<package>']])
            do_reprepro('remove', extra=[dargs['<from-dist>'], dargs['<package>']])
            do_reprepro('removesrc', extra=[dargs['<from-dist>'], dargs['<package>']])
        elif distro == "rhel":
            do_copy(dargs['<from-dist>'], dargs['<package>'], move=True)
        if not dargs['--no-push']:
            do_push(dargs['<from-dist>'])
            do_push(_opt['dist'])
    elif dargs['jenkins']:
        build = dargs['--build'] if dargs['--build'] else "lastSuccessfulBuild"
        arch = dargs['--source']
        if arch is None:
            arch = "amd64"
        copy_jenkins(dargs['<job>'], arch, flags=dargs['--reprepro-flags'], build=build, distro=distro, dry_run=dargs['list'])


if __name__ == '__main__':
    main()
