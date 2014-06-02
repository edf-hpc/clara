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
"""
Creates, updates and seeds via torrent the images of installation of a cluster.

Usage:
    clara images genimg
    clara images (unpack|repack <directory>)
    clara images apply_config2img
    clara images initrd
    clara images mktorrent
    clara images -h | --help | help

"""

import os
import shutil
import subprocess
import sys
import tempfile
import time

import docopt
from clara.utils import clush, run, getconfig


def base_install():
    # Step 1 - Debootstrap
    src_list = work_dir + "/etc/apt/sources.list"
    apt_pref = work_dir + "/etc/apt/preferences.d/00custompreferences"
    apt_conf = work_dir + "/etc/apt/apt.conf.d/99nocheckvalid"
    dpkg_conf = work_dir + "/etc/dpkg/dpkg.cfg.d/excludes"
    etc_host = work_dir + "/etc/hosts"

    run(["debootstrap", getconfig().get("images", "debiandist"), work_dir,
         getconfig().get("images", "debmirror") + "/debian"])

    # Step 2 - Mirror setup
    list_repos = getconfig().get("images", "list_repos").split(",")
    with open(src_list, 'w') as fsources:
        for line in list_repos:
            fsources.write(line+'\n')

    with open(apt_pref, 'w') as fapt:
        fapt.write("""Package: *
Pin: release o={0}
Pin-Priority: 5000

Package: *
Pin: release o={1}
Pin-Priority: 6000
""".format(getconfig().get("images", "distribution"),
           getconfig().get("images", "origin")))

    with open(apt_conf, 'w') as fconf:
        fconf.write('Acquire::Check-Valid-Until "false";\n')

    with open(etc_host, 'w') as fhost:
        fhost.write("10.89.87.110 atadmnnfs\n")

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
    run(["chroot", work_dir, "umount", "/sys"])
    run(["chroot", work_dir, "umount", "/proc"])
    time.sleep(1)  # Wait one second so the system has time to unmount
    with open("/proc/mounts", "r") as file_to_read:
        for line in file_to_read:
            if work_dir in line:
                sys.exit("Something went wrong when umounting in the chroot")


def system_install():
    package_file = getconfig().get("images", "package_file")
    preseed_file = getconfig().get("images", "preseed_file")
    mount_chroot()
    run(["chroot", work_dir, "apt-get", "update"])
    pkgs = getconfig().get("images", "important_packages").split(',')
    run(["chroot", work_dir, "apt-get", "install", "--yes", "--force-yes"] + pkgs)
    run(["chroot", work_dir, "apt-get", "update"])
    run(["chroot", work_dir, "aptitude", "reinstall", "~i ?not(?priority(required))"])
    shutil.copy(preseed_file, work_dir + "/tmp/preseed.file")
    shutil.copy(package_file, work_dir + "/tmp/packages.file")
    run(["chroot", work_dir, "debconf-set-selections", "/tmp/preseed.file"])
    for i in range(0, 2):
        part1 = subprocess.Popen(["cat", work_dir + "/tmp/packages.file"],
                               stdout=subprocess.PIPE)
        part2 = subprocess.Popen(["chroot", work_dir, "dpkg", "--set-selections"],
                               stdin=part1.stdout, stdout=subprocess.PIPE)
        part1.stdout.close()  # Allow part1 to receive a SIGPIPE if part2 exits.
        output = part2.communicate()[0]
        run(["chroot", work_dir, "apt-get", "dselect-upgrade", "-u", "--yes", "--force-yes"])
    run(["chroot", work_dir, "apt-get", "clean"])
    run(["chroot", work_dir, "/etc/init.d/rsyslog", "stop"])
    umount_chroot()


def install_files():
    list_files_to_install = getconfig().get("images", "list_files_to_install")
    dir_origin = getconfig().get("images", "dir_files_to_install")
    with open(list_files_to_install, "r") as file_to_read:
        for line in file_to_read:
            orig, dest, perm = line.rstrip().split()
            path_orig = dir_origin + "/" + orig
            path_dest = work_dir + "/" + dest
            file_perm = int(perm, 8)  # tell int to use base 8
            final_file = path_dest + orig

            if not os.path.isfile(path_orig):
                sys.exit("Ooops, file {0} doesn't exist!".format(path_orig))

            if not os.path.isdir(path_dest):
                os.makedirs(path_dest)
            shutil.copy(path_orig, path_dest)
            os.chmod(final_file, file_perm)

            if ("etc/init.d" in dest):
                run(["chroot", work_dir, "update-rc.d", orig, "defaults"])

        # Empty hostname
        os.remove(work_dir + "/etc/hostname")
        run(["chroot", work_dir, "touch", "/etc/hostname"])


def remove_files():
    files_to_remove = getconfig().get("images", "files_to_remove").split(',')
    for f in files_to_remove:
        if os.path.isfile(work_dir + "/" + f):
            os.remove(work_dir + "/" + f)


def genimg():
    squashfs_file = getconfig().get("images", "trg_img")
    if os.path.isfile(squashfs_file):
        os.rename(squashfs_file, squashfs_file + ".old")
        print("Previous image renamed to {0}.".format(squashfs_file + ".old"))

    print "Creating image at {0}".format(squashfs_file)
    run(["chroot", work_dir, "apt-get", "clean"])
    run(["mksquashfs", work_dir, squashfs_file, "-no-exports", "-noappend"])
    os.chmod(squashfs_file, 0o755)


def mktorrent():
    ml_path = "/var/lib/mldonkey"
    trg_dir = getconfig().get("images", "trg_dir")
    squashfs_file = getconfig().get("images", "trg_img")
    seeders = getconfig().get("images", "seeders")
    mldonkey_servers = getconfig().get("images", "mldonkey_servers")
    trackers = getconfig().get("images", "trackers")

    if not os.path.isfile(squashfs_file):
        sys.exit("The file {0} doesn't exist".format(squashfs_file))

    if os.path.isfile(trg_dir + "/image.torrent"):
        os.remove(trg_dir + "/image.torrent")

    clush(seeders, "service ctorrent stop")
    clush(mldonkey_servers, "service mldonkey-server stop")

    for files in ["torrents/old", "torrents/seeded", "torrents/tracked"]:
        clush(mldonkey_servers, "rm -f {0}/{1}/*".format(ml_path, files))

    clush(mldonkey_servers, "ln -sf {0} {1}/incoming/files/".format(squashfs_file, ml_path))

    clush(mldonkey_servers, "awk 'BEGIN{verb=1}; / tracked_files = / {verb=0}; /^$/ {verb=1}; {if (verb==1) print}' /var/lib/mldonkey/bittorrent.ini > /var/lib/mldonkey/bittorrent.ini.new")
    clush(mldonkey_servers, "mv {0}/bittorrent.ini.new {0}/bittorrent.ini".format(ml_path))

    run(["/usr/bin/mktorrent", "-a", trackers, "-o", trg_dir + "/image.torrent", squashfs_file])
    clush(mldonkey_servers, "ln -sf {0}/image.torrent {1}/torrents/seeded/".format(trg_dir, ml_path))

    clush(mldonkey_servers, "service mldonkey-server start")
    clush(seeders, "service ctorrent start")


def extract_image():
    squashfs_file = getconfig().get("images", "trg_img")
    print "Extracting {0} to {1} ...".format(squashfs_file, work_dir)
    run(["unsquashfs", "-f", "-d", work_dir, squashfs_file])


def geninitrd():
    trg_dir = getconfig().get("images", "trg_dir")
    if not os.path.isdir(trg_dir):
        sys.exit("Directory {0} does not exist!".format(trg_dir))

    mkinitrfs = getconfig().get("images", "mkinitramfs")
    initramfsc = getconfig().get("images", "initramfs-config")
    kver = getconfig().get("images", "kver")
    # Generate the initrd
    run([mkinitrfs, "-d", initramfsc, "-o", trg_dir + "/initrd-" + kver, kver])
    os.chmod(trg_dir + "/initrd-" + kver, 0o644)
    print "Initrd generated in " + trg_dir + "/initrd-" + kver

    # Copy kernel into right directory
    shutil.copy("/boot/vmlinuz-" + kver, trg_dir + "/linux-" + kver)
    print "Kernel copied in " + trg_dir + "/linux-" + kver


def main():
    dargs = docopt.docopt(__doc__)

    global work_dir
    if dargs['repack']:
        work_dir = dargs['<directory>']
    else:
        work_dir = tempfile.mkdtemp()

    if dargs['genimg']:
        base_install()
        system_install()
        install_files()
        remove_files()
        genimg()
        mktorrent()
    elif dargs['repack']:
        genimg()
        mktorrent()
    elif dargs['unpack']:
        extract_image()
        print "Modify the image at {0} and then run:\n "
               "\tclara images repack {0}".format(work_dir)
    elif dargs['apply_config2img']:
        extract_image()
        system_install()
        install_files()
        mktorrent()
    elif dargs['initrd']:
        geninitrd()
    elif dargs['mktorrent']:
        mktorrent()

    if not dargs['unpack']:
        shutil.rmtree(work_dir)


if __name__ == '__main__':
    main()
