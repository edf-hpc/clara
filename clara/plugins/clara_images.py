#!/usr/bin/env python
# -*- coding: utf-8 -*-
##############################################################################
#  Copyright (C) 2014-2020 EDF SA                                            #
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
Creates and updates the images of installation of a cluster.

Usage:
    clara images create [--no-sync] <dist> [<image>] [--keep-chroot-dir]
    clara images unpack ( <dist> | --image=<path> )
    clara images repack <directory> ( <dist> | --image=<path> )
    clara images edit <dist> [<image>]
    clara images initrd [--no-sync] <dist> [--output=<dirpath>]
    clara images push <dist> [<image>]
    clara images -h | --help | help
"""

import errno
import logging
import os
import pty
import shutil
import atexit
import subprocess
import sys
import tempfile
import time
import glob
import docopt
import re
import requests

from clara.utils import clara_exit, run, makedirs_mode, get_from_config, get_from_config_or, has_config_value, conf, get_bool_from_config_or
from clara import sftp

_opts = {'keep_chroot_dir': None}


dists = {
    "debian": {
        "pkgManager": "apt-get",
        "src_list": "/etc/apt/sources.list",
        "apt_pref": "/etc/apt/preferences.d/00custompreferences",
        "apt_conf": "/etc/apt/apt.conf.d/99nocheckvalid",
        "dpkg_conf": "/etc/dpkg/dpkg.cfg.d/excludes",
        "bootstrapper": "debootstrap",
        "initrdGen": "mkinitramfs"
    }
}

dists.update({
    distro: {
        "pkgManager": "dnf",
        "src_list": "/etc/yum.repos.d/%s.repo" % distro,
        "rpm_lib": "/var/lib/rpm",
        "bootstrapper": "dnf",
        "initrdGen": "dracut",
        "sources": {
            'baseos': {'subdir': 'BaseOS%s' % ('' if distro == "rhel" else '/x86_64/os') },
            'appstream': {'subdir': 'AppStream%s' % ('' if distro == "rhel" else '/x86_64/os') }
        }
      } for distro in ["rhel", "centos", "rocky", "almalinux"]
})

class osRelease:
    # Common base class for OS release
    def __init__(self, ID, VERSION_ID):
        self.ID = ID
        self.VERSION_ID = VERSION_ID
        self.dist = dists[ID]

    def bootstrapper(self, opts):
        opts.insert(0,self.dist["bootstrapper"])
        run(opts)

    def genInitrd(opts):
        run([self.dist["initrdGen"],opts])

class imageInstant(osRelease):
    # Common base class for
    def __init__(self, workdir, ID, VERSION_ID):
        osRelease.__init__(self, ID, VERSION_ID)
        self.workdir = workdir

def run_chroot(cmd, work_dir):
    logging.debug("images/run_chroot: {0}".format(" ".join(cmd)))

    try:
        retcode = subprocess.call(cmd)
    except OSError as e:
        if (e.errno == errno.ENOENT):
            clara_exit("Binary not found, check your path and/or retry as root. \
                      You were trying to run:\n {0}".format(" ".join(cmd)))

    if retcode != 0:
        umount_chroot(work_dir)
        if not _opts['keep_chroot_dir']:
            shutil.rmtree(work_dir)
        clara_exit(' '.join(cmd))


def get_osRelease(dist):
    pattern = re.compile(r"(?P<distro>[a-z]+)(?P<version>\d+)")
    match = pattern.match(dist)
    if match:
        ID = 'debian' if "scibian" in dist else match.group('distro')
        ID_Version = match.group('version')

        logging.debug("images/get_osRelease: %s => %s/%s", dist, ID, ID_Version)
        return ID, ID_Version
    else:
        clara_exit("images/get_osRelease: can't figured out distro/version for %s" % dist)
    
def list_all_repos(dist):
	list_repos_nonsplitted = get_from_config("images", "list_repos", dist)
	if ';' in list_repos_nonsplitted:
		separator = ';'
	else:
		separator = ','
	list_repos = list_repos_nonsplitted.split(separator)
	return list_repos

def set_yum_src_file(src_list, baseurl, gpgcheck, gpgkey, sources, list_repos = None, proxy = None):
    if not baseurl.endswith('/'):
         baseurl = baseurl + '/'
    dir_path = os.path.dirname(os.path.realpath(src_list))
    files = glob.glob(dir_path+"/*")
    for f in files:
        os.remove(f)
    f = open(src_list, "w")
    for source_name in sources.keys():
        name = "bootstrap_" + source_name
        base_url = baseurl + sources[source_name]['subdir']
        lines = ["["+name+"]",
                 "name="+name,
                 "enabled=1",
                 "gpgcheck="+str(gpgcheck),
                 "gpgkey=file://"+gpgkey,
                 "baseurl="+base_url,
                 "sslverify=0\n",]
        # Add proxy setting if defined
        if proxy is not None:
            lines.insert(6, "proxy="+str(proxy))
        lines = "\n".join(lines)
        logging.debug("Added yum repo in file %s:\n%s", src_list, lines)
        f.writelines(lines)
    indice = 0
    for repo in list_repos:
        repo_gpg_key = None
        priority = None
        if '|' in repo:
            repo_opts = repo.split('|')
            repo = repo_opts[0]
            # GPG key is optional, check it is not empty
            if len(repo_opts[1]):
                repo_gpg_key = repo_opts[1]
            # Priority field is optional, check it is present and not empty.
            if len(repo_opts) > 2 and len(repo_opts[2]):
                try:
                    priority = int(repo_opts[2])
                except ValueError:
                    logging.warning("Ignoring invalid format of repo %s priority '%s'", repo, repo_opts[2])


        name = "bootstrap_repo_" + str(indice)
        lines = ["["+name+"]",
                 "name="+name,
                 "enabled=1",
                 "baseurl="+repo,
                 "sslverify=0\n",]
        # Add priority setting if defined
        if priority is not None:
            lines.insert(4, "priority="+str(priority))
        # Add GPG keyring settings if defined
        if repo_gpg_key is not None:
            lines[3:3] = ["gpgcheck=true", "gpgkey=file://"+repo_gpg_key]
        else:
            lines.insert(3, "gpgcheck=false")
        lines = "\n".join(lines)
        f.writelines(lines)
        logging.debug("Added yum repo in %s:\n%s", src_list, lines)

        indice += 1
    f.close()

def remove_original_repos(src_list, pattern):
    dir_path = os.path.dirname(os.path.realpath(src_list))
    files = glob.glob(dir_path+"/?%s-*.repo" % pattern)
    for f in files:
        logging.debug("removing repo file %s" % f)
        os.remove(f)

def base_install(work_dir, dist):
    ID, VERSION_ID = get_osRelease(dist)
    image = imageInstant(work_dir, ID, VERSION_ID)
    distrib = image.dist
    opts = []

    # bootstrap
    src_list = work_dir + distrib["src_list"]
    etc_host = work_dir + "/etc/hosts"
    if dists[ID]['bootstrapper'] == "debootstrap":
        logging.debug("images/base_install: Using debootstrap for %s (%s/%s)", dist, ID, VERSION_ID)
        apt_pref = work_dir + distrib["apt_pref"]
        apt_conf = work_dir + distrib["apt_conf"]
        dpkg_conf = work_dir + distrib["dpkg_conf"]

        debiandist = get_from_config("images", "debiandist", dist)
        debmirror = get_from_config("images", "debmirror", dist)

        opts = [debiandist , work_dir, debmirror]

    if dists[ID]['bootstrapper'] == "dnf":
        logging.debug("images/base_install: Using RPM for %s (%s/%s)", dist, ID, VERSION_ID)
        minimal_packages_list = [ 'yum', 'util-linux', 'shadow-utils', 'glibc-minimal-langpack' ]
        rpm_lib = work_dir + distrib["rpm_lib"]
        baseurl = get_from_config("images", "baseurl", dist)

        # Temporarily change umask to create directories of dnf/yum repos and initialize RPM db
        repos_dir = os.path.join(work_dir,'etc','yum.repos.d')
        makedirs_mode(repos_dir, 0o0755)
        makedirs_mode(rpm_lib, 0o0755)
        umask = os.umask(0o022)
        run(["rpm", "--root", work_dir ,"-initdb"])
        os.umask(umask)  # Restore umask

        opts = ["install", "-y", "--nobest", "--installroot=" + work_dir, "--setopt=reposdir="+repos_dir] + minimal_packages_list

    if conf.ddebug:
        opts = ["--verbose"] + opts

    # Get GPG options
    gpg_check = get_bool_from_config_or("images", "gpg_check", dist, True)
    gpg_keyring = get_from_config_or("images", "gpg_keyring", dist, None)
    proxy = get_from_config_or("images", "proxy", dist, None)

    if gpg_keyring is None:
        gpg_keyring = 'XXXXXXXXXXXXXX'
    elif not os.path.exists(gpg_keyring):
        dir_path = os.path.dirname(os.path.realpath(gpg_keyring))
        # Removing a trailing slash from url, if need
        # Then, retrieve latest url path
        url_path = baseurl.rstrip('/').split('/')[-1]
        # form url without latest url path + gpg keying basename
        url = baseurl.replace(url_path,'') + os.path.basename(os.path.realpath(gpg_keyring))
        msg = """
PLS be a that unexistent gpg_keyring for distribution {}{} will be downloaded
from url
Don't usoduced image if you don't trusted this link and associated key !
Notice a that, if need, directory {} will be created to receive gpg keys.
"""
        logging.warning(msg.format(ID, VERSION_ID, url, dir_path))
        if not os.path.exists(dir_path):
            logging.info("creating directoring %s" % dir_path)
            makedirs_mode(dir_path, 0o0755)

        response = requests.get(url)
        if response.status_code == 200:
            logging.info("Dowloading gpg key from url %s to %s" % (url, dir_path))
            with open(gpg_keyring, 'wb') as f:
                f.write(response.content)
            os.chmod(gpg_keyring, 0o644)
        else:
            clara_exit("Failed to download gpg key from url %s" % url)

    if dists[ID]['pkgManager'] == "apt-get":
        if gpg_check:
            if gpg_keyring is not None:
                opts.insert(0, "--keyring=%s" % gpg_keyring)
        else:
            opts.insert(1, "--no-check-gpg")

    if conf.ddebug:
        opts.insert(1, "--verbose")

    if dists[ID]['pkgManager'] == "dnf":
        # generate dnf/yum repos files in work_dir
        set_yum_src_file(src_list, baseurl, gpg_check, gpg_keyring, dists[ID]['sources'], list_all_repos(dist), proxy)

    # run the bootstrap
    image.bootstrapper(opts)

    # Remove original repo as we are in air-gapped environment and so haven't outside internet access!
    if dists[ID]['pkgManager'] == "dnf":
        remove_original_repos(src_list, ID[1:])

    if dists[ID]['pkgManager'] == "apt-get":
        # Prevent services from starting automatically
        policy_rc = work_dir + "/usr/sbin/policy-rc.d"
        with open(policy_rc, 'w') as p_rcd:
            p_rcd.write("exit 101")
        p_rcd.close()
    
        os.chmod(policy_rc, 0o755)
        # Mirror setup
        list_repos = list_all_repos(dist)
    
        with open(src_list, 'w') as fsources:
            for line in list_repos:
                fsources.write(line + '\n')
        os.chmod(src_list, 0o644)
    
        with open(apt_pref, 'w') as fapt:
            fapt.write("""Package: *
    Pin: release o={0}
    Pin-Priority: 5000
    
    Package: *
    Pin: release o={1}
    Pin-Priority: 6000
    """.format(dist, get_from_config("common", "origin", dist)))
        os.chmod(apt_pref, 0o644)
    
        # Misc config
        with open(apt_conf, 'w') as fconf:
            fconf.write('Acquire::Check-Valid-Until "false";\n')
        os.chmod(apt_conf, 0o644)
    
    
        with open(dpkg_conf, 'w') as fdpkg:
            fdpkg.write("""# Drop locales except French
path-exclude=/usr/share/locale/*
path-include=/usr/share/locale/fr/*
path-include=/usr/share/locale/locale.alias
# Drop manual pages
# (We keep manual pages in the image)
## path-exclude=/usr/share/man/*
""")
        os.chmod(dpkg_conf, 0o644)

    # Setup initial /etc/hosts
    lists_hosts = get_from_config("images", "etc_hosts", dist).split(",")
    with open(etc_host, 'w') as fhost:
        for elem in lists_hosts:
            if ":" in elem:
                ip, host = elem.split(":")
                fhost.write("{0} {1}\n".format(ip, host))
            else:
                logging.warning("The option etc_hosts is malformed or missing an argument")
    os.chmod(etc_host, 0o644)

    # Set root password to 'clara'
    part1 = subprocess.Popen(["echo", "root:clara"],
                             stdout=subprocess.PIPE,
                             universal_newlines=True)
    part2 = subprocess.Popen(["chroot", work_dir, "/usr/sbin/chpasswd"],
                             stdin=part1.stdout,
                             universal_newlines=True)
    part1.stdout.close()  # Allow part1 to receive a SIGPIPE if part2 exits.
    #output = part2.communicate()[0]


def mount_chroot(work_dir):
    run(["chroot", work_dir, "mount", "-t", "proc", "none", "/proc"])
    run(["chroot", work_dir, "mount", "-t", "sysfs", "none", "/sys"])
    if not os.path.exists(work_dir+"/etc/resolv.conf"):
        run(["touch", os.path.join(work_dir, "etc/resolv.conf")])
        run(["mount", "-o", "bind", "/etc/resolv.conf", os.path.join(work_dir, "etc/resolv.conf")])
    if os.path.ismount("/run"):
        run(["mount", "-o", "bind", "/run", os.path.join(work_dir, "run")])
    if not os.path.exists(work_dir+"/dev/random"):
        run(["mknod", "-m", "444", work_dir + "/dev/random", "c", "1", "8"])
    if not os.path.exists(work_dir+"/dev/urandom"):
        run(["mknod", "-m", "444", work_dir + "/dev/urandom", "c", "1", "9"])


def umount_chroot(work_dir):
    if os.path.ismount(work_dir + "/proc/sys/fs/binfmt_misc"):
        run(["chroot", work_dir, "umount", "/proc/sys/fs/binfmt_misc"])

    if os.path.ismount(work_dir + "/sys"):
        run(["chroot", work_dir, "umount", "/sys"])

    if os.path.ismount(work_dir + "/proc"):
        run(["chroot", work_dir, "umount","-lf", "/proc"])

    if os.path.ismount(work_dir + "/run"):
        run(["umount","-lf", os.path.join(work_dir, "run")])

    if os.path.ismount(work_dir + "/etc/resolv.conf"):
        run(["umount","-lf", os.path.join(work_dir, "etc/resolv.conf")])
        run(["rm", os.path.join(work_dir, "etc/resolv.conf")])

    time.sleep(1)  # Wait one second so the system has time to unmount
    with open("/proc/mounts", "r") as file_to_read:
        for line in file_to_read:
            if work_dir in line:
                # second change to unmount bind mounting!
                # due to bug https://bugs.python.org/issue29707 (up to 3.6),
                # ismount don't unmount bind mount :-( !
                if "/etc/resolv.conf" in line:
                    run(["umount","-lf", os.path.join(work_dir, "etc/resolv.conf")])
                    run(["rm", os.path.join(work_dir, "etc/resolv.conf")])
                    time.sleep(1)  # Wait one second so the system has time to unmount
                else:
                    clara_exit("Something went wrong when umounting in the chroot for %s" % line)


def system_install(work_dir, dist):
    mount_chroot(work_dir)
    ID, VERSION_ID = get_osRelease(dist)
    image = imageInstant(work_dir, ID, VERSION_ID)
    distrib = image.dist
    src_list = work_dir + distrib["src_list"]
    proxy = get_from_config_or("images", "proxy", dist, None)

# Configure foreign architecture if this has been set in config.ini
    try:
        foreign_archs = get_from_config("images", "foreign_archs", dist).split(",")
    except:
        foreign_archs = None

    if not foreign_archs:
        logging.warning("foreign_archs is not specified in config.ini".format(foreign_archs))
    else:
        if ID == "debian":
            for arch in foreign_archs:
                logging.warning("Configure foreign_arch {0}".format(arch))
                run_chroot(["chroot", work_dir, "dpkg", "--add-architecture", arch], work_dir)
            run_chroot(["chroot", work_dir, distrib["pkgManager"], "update"],work_dir)
        if dists[ID]['pkgManager'] == "dnf":
                run_chroot(["chroot", work_dir, "echo","'multilib_policy=all'", ">>" , work_dir+"/etc/yum.conf"],work_dir)
                run_chroot(["chroot", work_dir, distrib["pkgManager"], "makecache"],work_dir)


    if ID == "debian":
        # Set presseding if the file has been set in config.ini
        preseed_file = get_from_config("images", "preseed_file", dist)
        if not os.path.isfile(preseed_file):
            logging.warning("preseed_file contains '{0}' and it is not a file!".format(preseed_file))
        else:
            shutil.copy(preseed_file, work_dir + "/tmp/preseed.file")
            # we need to install debconf-utils
            run_chroot(["chroot", work_dir, "apt-get", "install",
                        "--no-install-recommends", "--yes", "--force-yes", "debconf-utils"], work_dir)
            run_chroot(["chroot", work_dir, "apt-get", "update"], work_dir)
            run_chroot(["chroot", work_dir, "/usr/lib/dpkg/methods/apt/update", "/var/lib/dpkg/"], work_dir)
            run_chroot(["chroot", work_dir, "debconf-set-selections", "/tmp/preseed.file"], work_dir)
    
        # Install packages from package_file if this file has been set in config.ini
        try:
            package_file = get_from_config("images", "package_file", dist)
        except:
            package_file = None
    
        if not package_file:
            logging.warning("package_file is not specified in config.ini".format(package_file))
        elif not os.path.isfile(package_file):
            logging.warning("package_file contains '{0}' and it is not a file.".format(package_file))
        else:
            shutil.copy(package_file, work_dir + "/tmp/packages.file")
            for i in range(0, 2):
                part1 = subprocess.Popen(["cat", work_dir + "/tmp/packages.file"],
                                         stdout=subprocess.PIPE)
                part2 = subprocess.Popen(["chroot", work_dir, "dpkg", "--set-selections"],
                                         stdin=part1.stdout, stdout=subprocess.PIPE)
                part1.stdout.close()  # Allow part1 to receive a SIGPIPE if part2 exits.
                output = part2.communicate()[0]
                run_chroot(["chroot", work_dir, "apt-get", "dselect-upgrade", "-u", "--yes", "--force-yes"],
                           work_dir)

    # Manage groupinstall for centos
    if dists[ID]['pkgManager'] == "dnf":
        group_pkgs = get_from_config("images", "group_pkgs", dist)
        if len(group_pkgs) == 0:
            logging.warning("group_pkgs hasn't be set in the config.ini")
        else:
            group_pkgs = group_pkgs.split(",")
            if VERSION_ID == "9":
               run_chroot(["chroot", work_dir, "restorecon", "-Rv", distrib["rpm_lib"]], work_dir)
               run_chroot(["chroot", work_dir, "rpmdb", "--rebuilddb"], work_dir)

            run_chroot(["chroot", work_dir, distrib["pkgManager"], "groupinstall", "-y", "--nobest"] + group_pkgs, work_dir)
            # Remove original repo as we are in air-gapped environment and so haven't outside internet access!
            remove_original_repos(src_list, ID[1:])

    # Install extra packages if extra_packages_image has been set in config.ini
    extra_packages_image = get_from_config("images", "extra_packages_image", dist)
    if len(extra_packages_image) == 0:
        logging.warning("extra_packages_image hasn't be set in the config.ini")
    else:
        pkgs = extra_packages_image.split(",")
        if ID == "debian":
            opts = ["--no-install-recommends", "--yes", "--force-yes"]
        if dists[ID]['pkgManager'] == "dnf":
            opts = ["-y", "--nobest"]

        opts = ["chroot", work_dir, distrib["pkgManager"], "install"] + opts + pkgs 	        
        run_chroot(opts,
                   work_dir)

    # Finally, make sure the base image is updated with all the new versions
    if ID == "debian":
        run_chroot(["chroot", work_dir, distrib["pkgManager"], "update"], work_dir)
        run_chroot(["chroot", work_dir, "apt-get", "dist-upgrade", "--yes", "--force-yes"], work_dir)
        run_chroot(["chroot", work_dir, "apt-get", "clean"], work_dir)
    if dists[ID]['pkgManager'] == "dnf":
        # If run from older yum version (like on Debian), this is necessary to do manually
        if not os.path.islink(work_dir + '/var/run'):
            shutil.rmtree(work_dir + "/var/run")
            run_chroot(["chroot", work_dir, "ln", "-s", "../run", "/var/run"], work_dir)
        run_chroot(["chroot", work_dir, distrib["pkgManager"], "upgrade", "-y", "--nobest"], work_dir)
        run_chroot(["chroot", work_dir, distrib["pkgManager"], "clean","all"], work_dir)
        if proxy:
            # we need to remove temporary add proxy entry!
            # using bellow tricks.
            # open the file in r/w mode ("r+") and make use of seek to reset the
            # f-pointer then truncate to remove everything after the last write.
            with open(src_list, "r+") as f:
                lines = f.readlines()
                f.seek(0)
                for line in lines:
                    if not line.strip("\n").startswith("proxy="):
                        f.write(line)
                f.truncate()
    umount_chroot(work_dir)


def install_files(work_dir, dist):
    list_files_to_install = get_from_config("images", "list_files_to_install", dist)
    if not os.path.isfile(list_files_to_install):
        logging.warning("{0} is not a file!".format(list_files_to_install))

    else:
        dir_origin = get_from_config("images", "dir_files_to_install", dist)
        if not os.path.isdir(dir_origin):
            logging.warning("{0} is not a directory!".format(dir_origin))

        with open(list_files_to_install, "r") as file_to_read:
            for line in file_to_read:
                orig, dest, perm = line.rstrip().split()
                path_orig = dir_origin + "/" + orig
                path_dest = work_dir + "/" + dest
                file_perm = int(perm, 8)  # tell int to use base 8
                final_file = path_dest + orig

                if not os.path.isfile(path_orig):
                    logging.warning("{0} is not a file!".format(path_orig))

                makedirs_mode(path_dest, 0o0755)
                shutil.copy(path_orig, path_dest)
                os.chmod(final_file, file_perm)

                if ("etc/init.d" in dest):
                    run_chroot(["chroot", work_dir, "update-rc.d", orig, "defaults"], work_dir)

    # Empty hostname
    hostnamefile = work_dir + "/etc/hostname"
    if os.path.exists(hostnamefile):
        os.remove(hostnamefile)
    run_chroot(["chroot", work_dir, "touch", "/etc/hostname"], work_dir)


def remove_files(work_dir, dist):
    files_to_remove = get_from_config("images", "files_to_remove", dist).split(',')
    for f in files_to_remove:
        if os.path.isfile(work_dir + "/" + f):
            if os.path.exists(work_dir + "/" + f):
                os.remove(work_dir + "/" + f)
    if os.path.exists(work_dir + "/usr/sbin/policy-rc.d"):
        os.remove(work_dir + "/usr/sbin/policy-rc.d")


def run_script_post_creation(work_dir, dist):
    script = get_from_config("images", "script_post_image_creation", dist)
    if len(script) == 0:
        logging.warning("script_post_image_creation hasn't be set in the config.ini")
    elif not os.path.isfile(script):
        logging.warning("File {0} not found!".format(script))
    else:
        # Copy the script into the chroot and make sure it's executable
        shutil.copy(script, work_dir + "/tmp/script")
        os.chmod(work_dir + "/tmp/script", 0o755)
        run_chroot(["chroot", work_dir, "bash", "/tmp/script"], work_dir)


def genimg(image, work_dir, dist):
    if (image is None):
        squashfs_file = get_from_config("images", "trg_img", dist)
        if (squashfs_file=="" or squashfs_file==None):
            image_name=dist+"_image.squashfs"
            squashfs_file = "/var/lib/clara/images/"+image_name
            if os.path.isfile(squashfs_file):
                os.rename(squashfs_file, squashfs_file + ".old")
                logging.info("Previous image renamed to {0}.".format(squashfs_file + ".old"))

    else:
        path_to_image = os.path.dirname(image)
        if len(path_to_image):
            makedirs_mode(path_to_image, 0o0755)
        squashfs_file = image

    if os.path.isfile(squashfs_file):
        os.rename(squashfs_file, squashfs_file + ".old")
        logging.info("Previous image renamed to {0}.".format(squashfs_file + ".old"))

    logging.info("Creating image at {0}".format(squashfs_file))

    makedirs_mode(os.path.dirname(squashfs_file), 0o0755)
 
    if conf.ddebug:
        run(["mksquashfs", work_dir, squashfs_file, "-no-exports", "-noappend", "-info"])
    else:
        run(["mksquashfs", work_dir, squashfs_file, "-no-exports", "-noappend"])

    os.chmod(squashfs_file, 0o755)

    sftp_mode = has_config_value("images", "hosts", dist)
    dargs = docopt.docopt(__doc__)
    if sftp_mode and not dargs['--no-sync']:
        sftp_user = get_from_config("images", "sftp_user", dist)
        sftp_private_key = get_from_config("images", "sftp_private_key", dist)
        sftp_passphrase = get_from_config_or("images", "sftp_passphrase", dist, None)
        sftp_hosts = get_from_config("images", "hosts", dist).split(',')
        sftp_client = sftp.Sftp(sftp_hosts, sftp_user, sftp_private_key, sftp_passphrase)
        sftp_client.upload([squashfs_file], os.path.dirname(squashfs_file), 0o755)


def extract_image(image, dist):
    if (image is None):
        squashfs_file = get_from_config("images", "trg_img", dist)
        if (squashfs_file=="" or squashfs_file==None):
            image_name=dist+"_image.squashfs"
            squashfs_file = "/var/lib/clara/images/"+image_name
    else:
        squashfs_file = image

    if not os.path.isfile(squashfs_file):
        clara_exit("{0} does not exist!".format(squashfs_file))

    extract_dir = tempfile.mkdtemp(prefix="tmpClara")
    logging.info("Extracting {0} to {1} ...".format(squashfs_file, extract_dir))
    if conf.ddebug:
        run(["unsquashfs", "-li", "-f", "-d", extract_dir, squashfs_file])
    else:
        run(["unsquashfs", "-f", "-d", extract_dir, squashfs_file])

    logging.info("Modify the image at {0} and then run:\n"
          "\tclara images repack {0} ( <dist> | --image=<path> )".format(extract_dir))


def geninitrd(path, work_dir, dist):
    ID, VERSION_ID = get_osRelease(dist)
    image = imageInstant(work_dir, ID, VERSION_ID)
    distrib = image.dist

    if (path is None):
        trg_dir = get_from_config("images", "trg_dir", dist)

        if (trg_dir=="" or trg_dir==None):
            trg_dir = "/var/lib/clara/images/"
    else:
        trg_dir = path


    makedirs_mode(trg_dir, 0o0755)
    squashfs_file = get_from_config("images", "trg_img", dist)
    if (squashfs_file=="" or squashfs_file==None):
        image_name=dist+"_image.squashfs"
        squashfs_file = "/var/lib/clara/images/"+image_name
    if not os.path.isfile(squashfs_file):
        clara_exit("{0} does not exist!".format(squashfs_file))

    if conf.ddebug:
        run(["unsquashfs", "-li", "-f", "-d", work_dir, squashfs_file])
    else:
        run(["unsquashfs", "-f", "-d", work_dir, squashfs_file])

    mount_chroot(work_dir)

    # Install the kernel in the image
    kver = get_from_config("images", "kver", dist)
    if len(kver) == 0:
        clara_exit("kver hasn't be set in config.ini")
    else:
        if ID == "debian":
            run_chroot(["chroot", work_dir, distrib["pkgManager"], "update"], work_dir)
            run_chroot(["chroot", work_dir, distrib["pkgManager"], "install",
                    "--no-install-recommends", "--yes", "--force-yes", "linux-image-" + kver], work_dir)
        if dists[ID]['bootstrapper'] == "dnf":
            run_chroot(["chroot", work_dir, distrib["pkgManager"], "makecache"], work_dir)
            run_chroot(["chroot", work_dir, distrib["pkgManager"], "install",
                    "-y", "--nobest", "kernel-"+ kver], work_dir)
    # Install packages from 'packages_initrd'
    packages_initrd = get_from_config("images", "packages_initrd", dist)
    if len(packages_initrd) == 0:
        logging.warning("packages_initrd hasn't be set in config.ini")
    else:
        pkgs = packages_initrd.split(',')
        if ID == "debian":
            opts = ["--no-install-recommends", "--yes", "--force-yes"]
            intitrd_opts = ["-o", "/tmp/initrd-" + kver, kver]
        if dists[ID]['bootstrapper'] == "dnf":
            opts = ["-y", "--nobest"]
            intitrd_opts = ["--force", "--add", "livenet", "-v", "/tmp/initrd-"+ kver, "--kver", kver,
                            "--no-early-microcode"]
        opts = ["chroot", work_dir, distrib["pkgManager"], "install"] + opts + pkgs
        run_chroot(opts, work_dir)

    # Generate the initrd in the image
    intitrd_opts = ["chroot", work_dir, distrib["initrdGen"]] + intitrd_opts
    run_chroot(intitrd_opts, work_dir)

    umount_chroot(work_dir)

    # Copy the initrd out of the chroot
    initrd_file = trg_dir + "/initrd-" + kver
    shutil.copy(work_dir + "/tmp/initrd-" + kver, initrd_file)
    os.chmod(initrd_file, 0o644)
    logging.info("Initrd available at " + initrd_file)

    # Copy vmlinuz out of the chroot
    vmlinuz_file = trg_dir + "/vmlinuz-" + kver
    shutil.copy(work_dir + "/boot/vmlinuz-" + kver, vmlinuz_file)
    os.chmod(vmlinuz_file, 0o644)
    logging.info("vmlinuz available at " + vmlinuz_file)

    # Send files where they will be used
    sftp_mode = has_config_value("images", "hosts", dist)
    dargs = docopt.docopt(__doc__)
    if sftp_mode and not dargs['--no-sync']:
        sftp_user = get_from_config("images", "sftp_user", dist)
        sftp_private_key = get_from_config("images", "sftp_private_key", dist)
        sftp_passphrase = get_from_config_or("images", "sftp_passphrase", dist, None)
        sftp_hosts = get_from_config("images", "hosts", dist).split(',')
        sftp_client = sftp.Sftp(sftp_hosts, sftp_user, sftp_private_key, sftp_passphrase)
        sftp_client.upload([initrd_file, vmlinuz_file], trg_dir, 0o644)

def push(image, dist):
    if (image is None):
        squashfs_file = get_from_config("images", "trg_img", dist)
        if (squashfs_file=="" or squashfs_file==None):
            image_name=dist+"_image.squashfs"
            squashfs_file = "/var/lib/clara/images/"+image_name
    else:
        squashfs_file = image

    if not os.path.isfile(squashfs_file):
        clara_exit("{0} doesn't exist.".format(squashfs_file))

    # Send files where they will be used
    sftp_mode = has_config_value("images", "hosts", dist)
    dargs = docopt.docopt(__doc__)
    if sftp_mode:
        sftp_user = get_from_config("images", "sftp_user", dist)
        sftp_private_key = get_from_config("images", "sftp_private_key", dist)
        sftp_passphrase = get_from_config_or("images", "sftp_passphrase", dist, None)
        sftp_hosts = get_from_config("images", "hosts", dist).split(',')
        sftp_client = sftp.Sftp(sftp_hosts, sftp_user, sftp_private_key, sftp_passphrase)
        sftp_client.upload([squashfs_file], os.path.dirname(squashfs_file), 0o755)
    else:
        clara_exit("Hosts not found for the image {0}".format(squashfs_file))


def edit(image, work_dir, dist):
    if (image is None):
        squashfs_file = get_from_config("images", "trg_img", dist)
        if (squashfs_file=="" or squashfs_file==None):
            image_name=dist+"_image.squashfs"
            squashfs_file = "/var/lib/clara/images/"+image_name
    else:
        squashfs_file = image

    if not os.path.isfile(squashfs_file):
        clara_exit("{0} doesn't exist.".format(squashfs_file))

    # Extract the image.
    logging.info("Extracting {0} to {1} ...".format(squashfs_file, work_dir))
    if conf.ddebug:
        run(["unsquashfs", "-li", "-f", "-d", work_dir, squashfs_file])
    else:
        run(["unsquashfs", "-f", "-d", work_dir, squashfs_file])

    # Work in the image
    os.chdir(work_dir)
    logging.info("Entering into a bash shell to edit the image. ^d when you have finished.")
    os.putenv("PROMPT_COMMAND", "echo -ne  '\e[1;31m({0}) clara images> \e[0m'".format(dist))
    pty.spawn(["/bin/bash"])

    save = input('Save changes made in the image? (N/y)')
    logging.debug("Input from the user: '{0}'".format(save))
    if save not in ('Y', 'y'):
        clara_exit("Changes ignored. The image {0} hasn't been modified.".format(squashfs_file))

    # Rename old image and recreate new one
    os.rename(squashfs_file, squashfs_file + ".old")
    if conf.ddebug:
        run(["mksquashfs", work_dir, squashfs_file, "-no-exports", "-noappend", "-info"])
    else:
        run(["mksquashfs", work_dir, squashfs_file, "-no-exports", "-noappend"])

    os.chmod(squashfs_file, 0o755)
    logging.info("\nPrevious image renamed to {0}."
          "\nThe image has been repacked at {1}".format(squashfs_file + ".old", squashfs_file))


def clean_and_exit(work_dir):
    if os.path.exists(work_dir):
        umount_chroot(work_dir)
        if not _opts['keep_chroot_dir']:
            shutil.rmtree(work_dir)


def main():
    logging.debug(sys.argv)
    dargs = docopt.docopt(__doc__)

    _opts['keep_chroot_dir'] = False

    dist = get_from_config("common", "default_distribution")
    if dargs['<dist>'] is not None:
        dist = dargs["<dist>"]
    if dist not in get_from_config("common", "allowed_distributions"):
        clara_exit("{0} is not a know distribution".format(dist))

    work_dir = ""
    if dargs['repack']:
        work_dir = dargs['<directory>']
    else:
        tmpdir = get_from_config_or("images", "tmp_dir", dist, "/tmp")
        work_dir = tempfile.mkdtemp(prefix="tmpClara", dir=tmpdir)

    # Not executed in the following cases
    # - the program dies because of a signal
    # - os._exit() is invoked directly
    # - a Python fatal error is detected (in the interpreter)
    atexit.register(clean_and_exit, work_dir)

    if dargs['create']:
        if dargs["--keep-chroot-dir"]:
            _opts['keep_chroot_dir'] = True
        base_install(work_dir, dist)
        install_files(work_dir, dist)
        system_install(work_dir, dist)
        remove_files(work_dir, dist)
        run_script_post_creation(work_dir, dist)
        genimg(dargs['<image>'], work_dir, dist)
    elif dargs['repack']:
        genimg(dargs['--image'], work_dir, dist)
    elif dargs['unpack']:
        extract_image(dargs['--image'], dist)
    elif dargs['initrd']:
        geninitrd(dargs['--output'], work_dir, dist)
    elif dargs['edit']:
        edit(dargs['<image>'], work_dir, dist)
    elif dargs['push']:
        push(dargs['<image>'], dist)

if __name__ == '__main__':
    main()
