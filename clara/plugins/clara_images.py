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
    clara images create [<image>] [--keep-chroot-dir] [--dist=<name>]
    clara images unpack [<image>] [--dist=<name>]
    clara images repack <directory> [<image>] [--dist=<name>]
    clara images edit [<image>] [--dist=<name>]
    clara images initrd [--dist=<name>] [--output=<dirpath>]
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

import docopt
from clara.utils import clara_exit, run, get_from_config


def run_chroot(cmd):
    logging.debug("images/run_chroot: {0}".format(" ".join(cmd)))

    try:
        retcode = subprocess.call(cmd)
    except OSError, e:
        if (e.errno == errno.ENOENT):
            clara_exit("Binary not found, check your path and/or retry as root. \
                      You were trying to run:\n {0}".format(" ".join(cmd)))

    if retcode != 0:
        umount_chroot()
        if not keep_chroot_dir:
            shutil.rmtree(work_dir)
        clara_exit(' '.join(cmd))


def base_install():
    # Debootstrap
    src_list = work_dir + "/etc/apt/sources.list"
    apt_pref = work_dir + "/etc/apt/preferences.d/00custompreferences"
    apt_conf = work_dir + "/etc/apt/apt.conf.d/99nocheckvalid"
    dpkg_conf = work_dir + "/etc/dpkg/dpkg.cfg.d/excludes"
    etc_host = work_dir + "/etc/hosts"

    run(["debootstrap", get_from_config("images", "debiandist", dist), work_dir,
         get_from_config("images", "debmirror", dist)])

    # Prevent services from starting automatically
    policy_rc = work_dir + "/usr/sbin/policy-rc.d"
    with open(policy_rc, 'w') as p_rcd:
        p_rcd.write("exit 101")
    p_rcd.close()
    os.chmod(work_dir + "/usr/sbin/policy-rc.d", 0o755)

    # Mirror setup
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

    # Misc config
    with open(apt_conf, 'w') as fconf:
        fconf.write('Acquire::Check-Valid-Until "false";\n')

    lists_hosts = get_from_config("images", "etc_hosts", dist).split(",")
    with open(etc_host, 'w') as fhost:
        for elem in lists_hosts:
            if ":" in elem:
                ip, host = elem.split(":")
                fhost.write("{0} {1}\n".format(ip, host))
            else:
                logging.warning("The option etc_hosts is malformed or missing an argument")

    with open(dpkg_conf, 'w') as fdpkg:
        fdpkg.write("""# Drop locales except French
path-exclude=/usr/share/locale/*
path-include=/usr/share/locale/fr/*
path-include=/usr/share/locale/locale.alias

# Drop manual pages
# (We keep manual pages in the image)
## path-exclude=/usr/share/man/*
""")

    # Set root password to 'clara'
    part1 = subprocess.Popen(["echo", "root:clara"], stdout=subprocess.PIPE)
    part2 = subprocess.Popen(["chroot", work_dir, "/usr/sbin/chpasswd"], stdin=part1.stdout)
    part1.stdout.close()  # Allow part1 to receive a SIGPIPE if part2 exits.
    #output = part2.communicate()[0]

def mount_chroot():
    run(["chroot", work_dir, "mount", "-t", "proc", "none", "/proc"])
    run(["chroot", work_dir, "mount", "-t", "sysfs", "none", "/sys"])


def umount_chroot():
    if os.path.ismount(work_dir + "/proc/sys/fs/binfmt_misc"):
        run(["chroot", work_dir, "umount", "/proc/sys/fs/binfmt_misc"])

    if os.path.ismount(work_dir + "/sys"):
        run(["chroot", work_dir, "umount", "/sys"])

    if os.path.ismount(work_dir + "/proc"):
        run(["chroot", work_dir, "umount", "/proc"])
    time.sleep(1)  # Wait one second so the system has time to unmount
    with open("/proc/mounts", "r") as file_to_read:
        for line in file_to_read:
            if work_dir in line:
                clara_exit("Something went wrong when umounting in the chroot")


def system_install():
    mount_chroot()
    run_chroot(["chroot", work_dir, "apt-get", "update"])

    # Set presseding if the file has been set in config.ini
    preseed_file = get_from_config("images", "preseed_file", dist)
    if not os.path.isfile(preseed_file):
        logging.warning("preseed_file contains '{0}' and it is not a file!".format(preseed_file))
    else:
        shutil.copy(preseed_file, work_dir + "/tmp/preseed.file")
        # we need to install debconf-utils
        run_chroot(["chroot", work_dir, "apt-get", "install", "--no-install-recommends", "--yes", "--force-yes", "debconf-utils"])
        run_chroot(["chroot", work_dir, "apt-get", "update"])
        run_chroot(["chroot", work_dir, "/usr/lib/dpkg/methods/apt/update", "/var/lib/dpkg/"])
        run_chroot(["chroot", work_dir, "debconf-set-selections", "/tmp/preseed.file"])

    # Install packages from package_file if this file has been set in config.ini
    package_file = get_from_config("images", "package_file", dist)
    if not os.path.isfile(package_file):
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
            run_chroot(["chroot", work_dir, "apt-get", "dselect-upgrade", "-u", "--yes", "--force-yes"])

    # Install extra packages if extra_packages_image has been set in config.ini
    extra_packages_image = get_from_config("images", "extra_packages_image", dist)
    if len(extra_packages_image) == 0:
        logging.warning("extra_packages_image hasn't be set in the config.ini")
    else:
        pkgs = extra_packages_image.split(",")
        run_chroot(["chroot", work_dir, "apt-get", "install", "--no-install-recommends", "--yes", "--force-yes"] + pkgs)

    run_chroot(["chroot", work_dir, "apt-get", "clean"])
    umount_chroot()


def install_files():
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
    os.remove(work_dir + "/usr/sbin/policy-rc.d")


def run_script_post_creation():
    script = get_from_config("images", "script_post_image_creation", dist)
    if len(script) == 0:
        logging.warning("script_post_image_creation hasn't be set in the config.ini")
    elif not os.path.isfile(script):
        logging.warning("File {0} not found!".format(script))
    else:
        # Copy the script into the chroot and make sure it's executable
        shutil.copy(script, work_dir + "/tmp/script")
        os.chmod(work_dir + "/tmp/script", 0o755)
        run_chroot(["chroot", work_dir, "bash", "/tmp/script"])


def genimg(image):
    if (image is None):
        squashfs_file = get_from_config("images", "trg_img", dist)
    else:
        path_to_image = os.path.dirname(image)
        if not os.path.isdir(path_to_image):
            os.makedirs(path_to_image)
        squashfs_file = image

    if os.path.isfile(squashfs_file):
        os.rename(squashfs_file, squashfs_file + ".old")
        logging.info("Previous image renamed to {0}.".format(squashfs_file + ".old"))

    logging.info("Creating image at {0}".format(squashfs_file))
    run_chroot(["chroot", work_dir, "apt-get", "clean"])
    run(["mksquashfs", work_dir, squashfs_file, "-no-exports", "-noappend"])
    os.chmod(squashfs_file, 0o755)


def extract_image(image):
    if (image is None):
        squashfs_file = get_from_config("images", "trg_img", dist)
    else:
        squashfs_file = image

    if not os.path.isfile(squashfs_file):
        clara_exit("The image {0} does not exist!".format(squashfs_file))

    extract_dir = tempfile.mkdtemp(prefix="tmpClara")
    logging.info("Extracting {0} to {1} ...".format(squashfs_file, extract_dir))
    run(["unsquashfs", "-f", "-d", extract_dir, squashfs_file])
    logging.info("Modify the image at {0} and then run:\n"
          "\tclara images repack {0}".format(extract_dir))


def geninitrd(path):
    if (path is None):
        trg_dir = get_from_config("images", "trg_dir", dist)
    else:
        trg_dir = path

    if not os.path.isdir(trg_dir):
        os.makedirs(trg_dir)

    squashfs_file = get_from_config("images", "trg_img", dist)
    run(["unsquashfs", "-f", "-d", work_dir, squashfs_file])
    mount_chroot()

    mkinitrfs = get_from_config("images", "mkinitramfs", dist)
    if not os.path.isfile(mkinitrfs):
        clara_exit("{0} does not exist!".format(mkinitrfs))
    else:
        shutil.copy(mkinitrfs, work_dir + "/tmp/mkinitrfs")

    initramfsc = get_from_config("images", "initramfs-config", dist)
    if not os.path.isdir(initramfsc):
        clara_exit("Directory {0} does not exist!".format(initramfsc))
    else:
        shutil.copytree(initramfsc, work_dir + "/tmp/initramfsc")

    # Install the kernel in the image
    kver = get_from_config("images", "kver", dist)
    if len(kver) == 0:
        clara_exit("kver hasn't be set in config.ini")
    else:
        run_chroot(["chroot", work_dir, "apt-get", "update"])
        run_chroot(["chroot", work_dir, "apt-get", "install", "--no-install-recommends", "--yes", "--force-yes", "linux-image-" + kver])

    # Install packages from 'packages_initrd'
    packages_initrd = get_from_config("images", "packages_initrd", dist)
    if len(packages_initrd) == 0:
        logging.warning("packages_initrd hasn't be set in config.ini")
    else:
        pkgs = packages_initrd.split(',')
        run_chroot(["chroot", work_dir, "apt-get", "install", "--no-install-recommends", "--yes", "--force-yes"] + pkgs)

    # Generate the initrd in the image
    run_chroot(["chroot", work_dir, "/tmp/mkinitrfs", "-d", "/tmp/initramfsc", "-o", "/tmp/initrd-" + kver, kver])
    umount_chroot()

    # Copy the initrd out of the chroot
    shutil.copy(work_dir + "/tmp/initrd-" + kver, trg_dir + "/initrd-" + kver)
    os.chmod(trg_dir + "/initrd-" + kver, 0o644)
    logging.info("Initrd available at " + trg_dir + "/initrd-" + kver)

    # Copy vmlinuz out of the chroot
    shutil.copy(work_dir + "/boot/vmlinuz-" + kver, trg_dir + "/vmlinuz-" + kver)
    logging.info("vmlinuz available at " + trg_dir + "/vmlinuz-" + kver)


def edit(image):
    if (image is None):
        squashfs_file = get_from_config("images", "trg_img", dist)
    else:
        squashfs_file = image

    if not os.path.isfile(squashfs_file):
        clara_exit("The image file {0} doesn't exist.".format(squashfs_file))

    # Extract the image.
    logging.info("Extracting {0} to {1} ...".format(squashfs_file, work_dir))
    run(["unsquashfs", "-f", "-d", work_dir, squashfs_file])
    # Work in the image
    os.chdir(work_dir)
    logging.info("Entering into a bash shell to edit the image. ^d when you have finished."
                 "If you don't want to renerate the image just place an empty file named IGNORE in the root directory.")
    os.putenv("PROMPT_COMMAND", "echo -ne  '\e[1;31m({0}) clara images> \e[0m'".format(dist))
    pty.spawn(["/bin/bash"])

    if os.path.isfile(work_dir + "/IGNORE"):
        clara_exit("Changes ignored. The image {0} hasn't been modified.".format(squashfs_file))

    # Rename old image and recreate new one
    os.rename(squashfs_file, squashfs_file + ".old")
    run(["mksquashfs", work_dir, squashfs_file, "-no-exports", "-noappend"])
    os.chmod(squashfs_file, 0o755)
    logging.info("\nPrevious image renamed to {0}."
          "\nThe image has been repacked at {1}".format(squashfs_file + ".old", squashfs_file))


def clean_and_exit():
    if os.path.exists(work_dir):
        umount_chroot()
        if not keep_chroot_dir:
            shutil.rmtree(work_dir)


def main():
    logging.debug(sys.argv)
    dargs = docopt.docopt(__doc__)

    global work_dir, keep_chroot_dir
    if dargs['repack']:
        work_dir = dargs['<directory>']
    else:
        work_dir = tempfile.mkdtemp(prefix="tmpClara")

    keep_chroot_dir = False
    # Not executed in the following cases
    # - the program dies because of a signal
    # - os._exit() is invoked directly
    # - a Python fatal error is detected (in the interpreter)
    atexit.register(clean_and_exit)

    global dist
    dist = get_from_config("common", "default_distribution")
    if dargs["--dist"] is not None:
        dist = dargs["--dist"]
    if dist not in get_from_config("common", "allowed_distributions"):
        clara_exit("{0} is not a know distribution".format(dist))

    if dargs['create']:
        if dargs["--keep-chroot-dir"]:
            keep_chroot_dir = True
        base_install()
        system_install()
        install_files()
        remove_files()
        run_script_post_creation()
        genimg(dargs['<image>'])
    elif dargs['repack']:
        genimg(dargs['<image>'])
    elif dargs['unpack']:
        extract_image(dargs['<image>'])
    elif dargs['initrd']:
        geninitrd(dargs['--output'])
    elif dargs['edit']:
        edit(dargs['<image>'])


if __name__ == '__main__':
    main()
