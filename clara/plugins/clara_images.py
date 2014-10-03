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
Creates and updates the images of installation of a cluster.

Usage:
    clara images create [--dist=<name>]
    clara images (unpack|repack <directory>) [--dist=<name>]
    clara images edit [<image>] [--dist=<name>]
    clara images initrd [--dist=<name>]
    clara images -h | --help | help

"""

import errno
import os
import pty
import shutil
import atexit
import subprocess
import sys
import tempfile
import time

import docopt
from clara.utils import clush, run, get_from_config


def clean_and_exit():
    if os.path.exists(work_dir):
        shutil.rmtree(work_dir)

# Not executed in the following cases
# - the program dies because of a signal
# - os._exit() is invoked directly
# - a Python fatal error is detected (in the interpreter)
atexit.register(clean_and_exit)

def run_chroot(cmd):
    try:
        retcode = subprocess.call(cmd)
    except OSError, e:
        if (e.errno == errno.ENOENT):
            sys.exit("Binary not found, check your path and/or retry as root. \
                      You were trying to run:\n {0}".format(" ".join(cmd)))

    if retcode != 0:
        umount_chroot()
        shutil.rmtree(work_dir)
        sys.exit('E: ' + ' '.join(cmd))


def base_install():
    # Step 1 - Debootstrap
    src_list = work_dir + "/etc/apt/sources.list"
    apt_pref = work_dir + "/etc/apt/preferences.d/00custompreferences"
    apt_conf = work_dir + "/etc/apt/apt.conf.d/99nocheckvalid"
    dpkg_conf = work_dir + "/etc/dpkg/dpkg.cfg.d/excludes"
    etc_host = work_dir + "/etc/hosts"

    run(["debootstrap", get_from_config("images", "debiandist", dist), work_dir,
         get_from_config("images", "debmirror", dist) + "/debian"])

    # Step 2 - Mirror setup
    list_repos = get_from_config("images", "list_repos", dist).split(",")
    with open(src_list, 'w') as fsources:
        for line in list_repos:
            fsources.write(line + '\n')

    with open(apt_pref, 'w') as fapt:
        fapt.write("""Package: *
Pin: release o={0}
Pin-Priority: 5000

Package: *
Pin: release o={1}
Pin-Priority: 6000
""".format(dist, get_from_config("common", "origin", dist)))

    with open(apt_conf, 'w') as fconf:
        fconf.write('Acquire::Check-Valid-Until "false";\n')

    lists_hosts = get_from_config("images", "etc_hosts", dist).split(",")
    if (len(lists_hosts) % 2 != 0):
        print "Clara: WARNING: the option etc_hosts is malformed or missing an argument"
    with open(etc_host, 'w') as fhost:
        for elem in range(0, len(lists_hosts), 2):
            fhost.write("{0} {1}\n".format(lists_hosts[elem], lists_hosts[elem + 1]))

    with open(dpkg_conf, 'w') as fdpkg:
        fdpkg.write("""# Drop locales except French
path-exclude=/usr/share/locale/*
path-include=/usr/share/locale/fr/*
path-include=/usr/share/locale/locale.alias

# Drop manual pages
# (We keep manual pages in the image)
## path-exclude=/usr/share/man/*
""")


def mount_chroot():
    run(["chroot", work_dir, "mount", "-t", "proc", "none", "/proc"])
    run(["chroot", work_dir, "mount", "-t", "sysfs", "none", "/sys"])


def umount_chroot():
    if os.path.ismount("/proc/sys/fs/binfmt_misc"):
        run(["chroot", work_dir, "umount", "/proc/sys/fs/binfmt_misc"])

    if os.path.ismount("/sys"):
        run(["chroot", work_dir, "umount", "/sys"])

    if os.path.ismount("/proc"):
        run(["chroot", work_dir, "umount", "/proc"])
    time.sleep(1)  # Wait one second so the system has time to unmount
    with open("/proc/mounts", "r") as file_to_read:
        for line in file_to_read:
            if work_dir in line:
                sys.exit("Something went wrong when umounting in the chroot")


def system_install():
    package_file = get_from_config("images", "package_file", dist)
    if os.path.isfile(package_file):
        shutil.copy(package_file, work_dir + "/tmp/packages.file")
    else:
        print "Clara: WARNING: %s is not a file!" % package_file

    preseed_file = get_from_config("images", "preseed_file", dist)
    if os.path.isfile(preseed_file):
        shutil.copy(preseed_file, work_dir + "/tmp/preseed.file")
    else:
        print "Clara: WARNING: %s is not a file!" % preseed_file

    mount_chroot()
    run_chroot(["chroot", work_dir, "apt-get", "update"])
    pkgs = get_from_config("images", "important_packages", dist).split(',')
    run_chroot(["chroot", work_dir, "apt-get", "install", "--no-install-recommends", "--yes", "--force-yes"] + pkgs)
    run_chroot(["chroot", work_dir, "apt-get", "update"])
    run_chroot(["chroot", work_dir, "aptitude", "reinstall", "--without-recommends", "~i ?not(?priority(required))"])
    run_chroot(["chroot", work_dir, "/usr/lib/dpkg/methods/apt/update", "/var/lib/dpkg/"])
    run_chroot(["chroot", work_dir, "debconf-set-selections", "/tmp/preseed.file"])
    for i in range(0, 2):
        part1 = subprocess.Popen(["cat", work_dir + "/tmp/packages.file"],
                                 stdout=subprocess.PIPE)
        part2 = subprocess.Popen(["chroot", work_dir, "dpkg", "--set-selections"],
                                 stdin=part1.stdout, stdout=subprocess.PIPE)
        part1.stdout.close()  # Allow part1 to receive a SIGPIPE if part2 exits.
        output = part2.communicate()[0]
        run_chroot(["chroot", work_dir, "apt-get", "dselect-upgrade", "-u", "--yes", "--force-yes"])
    run_chroot(["chroot", work_dir, "apt-get", "clean"])
    run_chroot(["chroot", work_dir, "/etc/init.d/rsyslog", "stop"])
    umount_chroot()


def install_files():
    list_files_to_install = get_from_config("images", "list_files_to_install", dist)
    if not os.path.isfile(list_files_to_install):
        print "Clara: WARNING: %s is not a file!" % list_files_to_install

    dir_origin = get_from_config("images", "dir_files_to_install", dist)
    if not os.path.isdir(dir_origin):
        print "Clara: WARNING: %s is not a directory!" % dir_origin

    with open(list_files_to_install, "r") as file_to_read:
        for line in file_to_read:
            orig, dest, perm = line.rstrip().split()
            path_orig = dir_origin + "/" + orig
            path_dest = work_dir + "/" + dest
            file_perm = int(perm, 8)  # tell int to use base 8
            final_file = path_dest + orig

            if not os.path.isfile(path_orig):
                print "Clara: WARNING: %s is not a file!" % path_orig

            if not os.path.isdir(path_dest):
                os.makedirs(path_dest)
            shutil.copy(path_orig, path_dest)
            os.chmod(final_file, file_perm)

            if ("etc/init.d" in dest):
                run_chroot(["chroot", work_dir, "update-rc.d", orig, "defaults"])

        # Empty hostname
        os.remove(work_dir + "/etc/hostname")
        run_chroot(["chroot", work_dir, "touch", "/etc/hostname"])


def remove_files():
    files_to_remove = get_from_config("images", "files_to_remove", dist).split(',')
    for f in files_to_remove:
        if os.path.isfile(work_dir + "/" + f):
            os.remove(work_dir + "/" + f)


def genimg():
    squashfs_file = get_from_config("images", "trg_img", dist)
    if os.path.isfile(squashfs_file):
        os.rename(squashfs_file, squashfs_file + ".old")
        print("Previous image renamed to {0}.".format(squashfs_file + ".old"))

    print "Creating image at {0}".format(squashfs_file)
    run_chroot(["chroot", work_dir, "apt-get", "clean"])
    run(["mksquashfs", work_dir, squashfs_file, "-no-exports", "-noappend"])
    os.chmod(squashfs_file, 0o755)


def extract_image():
    squashfs_file = get_from_config("images", "trg_img", dist)
    if not os.path.isfile(squashfs_file):
        sys.exit("The image {0} does not exist!".format(squashfs_file))

    print "Extracting {0} to {1} ...".format(squashfs_file, work_dir)
    run(["unsquashfs", "-f", "-d", work_dir, squashfs_file])


def geninitrd():
    trg_dir = get_from_config("images", "trg_dir", dist)
    if not os.path.isdir(trg_dir):
        sys.exit("Directory {0} does not exist!".format(trg_dir))

    mkinitrfs = get_from_config("images", "mkinitramfs", dist)
    if not os.path.isfile(mkinitrfs):
        sys.exit("{0} does not exist!".format(mkinitrfs))

    initramfsc = get_from_config("images", "initramfs-config", dist)
    if not os.path.isdir(initramfsc):
        sys.exit("Directory {0} does not exist!".format(initramfsc))

    kver = get_from_config("images", "kver", dist)
    # Generate the initrd
    run([mkinitrfs, "-d", initramfsc, "-o", trg_dir + "/initrd-" + kver, kver])
    os.chmod(trg_dir + "/initrd-" + kver, 0o644)
    print "Initrd generated in " + trg_dir + "/initrd-" + kver

    # Copy kernel into right directory
    shutil.copy("/boot/vmlinuz-" + kver, trg_dir + "/linux-" + kver)
    print "Kernel copied in " + trg_dir + "/linux-" + kver


def edit(image):
    if (image is None):
        squashfs_file = get_from_config("images", "trg_img", dist)
    else:
        squashfs_file = image

    if not os.path.isfile(squashfs_file):
        sys.exit("The image file {0} doesn't exist.".format(squashfs_file))

    # Extract the image.
    print "Extracting {0} to {1} ...".format(squashfs_file, work_dir)
    run(["unsquashfs", "-f", "-d", work_dir, squashfs_file])
    # Work in the image
    os.chdir(work_dir)
    print "Entering into a bash shell to edit the image. ^d when you have finished"
    os.putenv("PROMPT_COMMAND", "echo -ne  '\e[1;31m clara images> \e[0m'")
    pty.spawn(["/bin/bash"])
    # Rename old image and recreate new one
    os.rename(squashfs_file, squashfs_file + ".old")
    print("Previous image renamed to {0}.".format(squashfs_file + ".old"))
    print "Recreating image at {0}".format(squashfs_file)
    run(["mksquashfs", work_dir, squashfs_file, "-no-exports", "-noappend"])
    os.chmod(squashfs_file, 0o755)


def main():
    dargs = docopt.docopt(__doc__)

    global work_dir
    if dargs['repack']:
        work_dir = dargs['<directory>']
    else:
        work_dir = tempfile.mkdtemp()

    global dist
    dist = get_from_config("common", "distribution")
    if dargs["--dist"] is not None:
        dist = dargs["--dist"]
    if dist not in get_from_config("common", "distributions"):
        sys.exit("{0} is not a know distribution".format(dist))

    if dargs['create']:
        base_install()
        system_install()
        install_files()
        remove_files()
        genimg()
    elif dargs['repack']:
        genimg()
    elif dargs['unpack']:
        extract_image()
        print "Modify the image at {0} and then run:\n " \
              "\tclara images repack {0}".format(work_dir)
    elif dargs['initrd']:
        geninitrd()
    elif dargs['edit']:
        edit(dargs['<image>'])

    if not dargs['unpack']:
        shutil.rmtree(work_dir)


if __name__ == '__main__':
    main()
