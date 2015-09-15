#!/usr/bin/env python
# -*- coding: utf-8 -*-
##############################################################################
#  Copyright (C) 2015 EDF SA                                                 #
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
Builds Debian packages

Usage:
    clara build source <dist> <dsc_file>
    clara build repo <dist> <origin_dist> <package_name>
    clara build -h | --help | help
"""

import glob
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile

import docopt

from clara.utils import clara_exit, get_from_config

# this dict both defines the allowed dists in parameter of this script and the
# associated tag appended to the debian version of the rebuilt package
target_dists = {}
for elem in get_from_config("build", "target_dists").split(","):
    key, value = elem.split(":")
    target_dists[key] = value


def copy_files_to_workdir(orig, dest):
    for f in glob.glob(orig):
        logging.debug("Copying {0} to directory {1}".format(f, dest))
        shutil.copy(f, dest)


def print_info(name, full_version, upstream_version, debian_version):
    logging.info("Extracting package source name: {0}".format(name))
    logging.info("Full version: {0}".format(full_version))
    logging.info("Upstream version: {0}".format(upstream_version))
    logging.info("Debian version: {0}".format(debian_version))


def main():
    logging.debug(sys.argv)
    dargs = docopt.docopt(__doc__, options_first=True)

    target_dist = dargs['<dist>']
    if target_dist not in target_dists.keys():
        sys.exit("Unknown target dist {0}".format(target_dist))

    # Create a temp directory
    work_dir = tempfile.mkdtemp(prefix="tmpRebuild")

    if dargs['source']:
        dsc_file = dargs['<dsc_file>']

        # Check dsc file exists
        if not os.path.isfile(dsc_file):
            sys.exit("The file {0} doesn't exist".format(dsc_file))

        # Find out versioning
        name, full_version = os.path.basename(dsc_file)[:-4].split("_")
        if "-" in full_version:
            upstream_version, debian_version = full_version.rsplit("-", 1)
        else:   # Binary package
            upstream_version, debian_version = full_version, ""

        print_info(name, full_version, upstream_version, debian_version)

        dirname = os.path.dirname(dsc_file)
        copy_files_to_workdir(os.path.join(dirname, name + "_" + upstream_version + "*"),
                              work_dir)

    elif dargs['repo']:
        origin_dist = dargs['<origin_dist>']
        package_name = dargs['<package_name>']

        if origin_dist not in target_dists.keys():
            sys.exit("Unknown origin dist {0}".format(origin_dist))

        if not isinstance(package_name, str):
            clara_exit("Package name {0} is not a string".format(package_name))

        # Check if the source package exists in the reprepro of origin_dist
        cmd = ["clara", "repo", "list", origin_dist]
        logging.debug(" ".join(cmd))
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        lines_proc = proc.stdout.readlines()
        found_package = False
        for line in lines_proc:
            if ("|source: {0} ".format(package_name) in line):
                found_package = True
                break

        # If we fail to find the package, we list what's available and exit
        if not found_package:
            logging.info("Package {0} not found. The available packages in {1} are:".format(package_name, origin_dist))
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
            lines_proc = proc.stdout.readlines()
            for l in lines_proc:
                if "|source: " in l:
                    logging.info(l.split(":")[1])

            clara_exit("Select an available package and re-run clara.")

        # Look for the files and copy them to the temp directory
        area = "main"
        if "non-free" in line:
            area = "non-free"

        if package_name.startswith("lib"):
            package_dir = package_name[0:4] + "/" + package_name
        else:
            package_dir = package_name[0] + "/" + package_name

        # Note this is the path from the *origin* dist
        repo_path_pool = get_from_config("build", "repo_path_pool", origin_dist)
        repo_path_pool = repo_path_pool + "{0}/{1}".format(area, package_dir)
        full_version = line.split(" ")[-1].strip()
        upstream_version, debian_version = full_version.split("-")
        name = package_name

        print_info(name, full_version, upstream_version, debian_version)

        copy_files_to_workdir(os.path.join(repo_path_pool, name + "_" + upstream_version + "*"),
                              work_dir)

    # Common code: append the calibre tag and build the package
    os.chdir(work_dir)

    cmd = ["dpkg-source", "-x", "{0}_{1}.dsc".format(name, full_version)]
    logging.debug(" ".join(cmd))
    p = subprocess.call(cmd)

    path = "{0}-{1}".format(name, upstream_version)
    os.chdir(path)

    # Check if the debian version already appends the calibre tag
    tag = target_dists[target_dist]
    debian_version_re = r"(.*)\+{0}([\.\+])(\d)".format(tag)
    debian_version_p = re.compile(debian_version_re)
    debian_version_m = debian_version_p.match(debian_version)
    if debian_version_m:
        calibre_dump_s = debian_version_m.group(3)
        try:
            calibre_dump = int(calibre_dump_s) + 1
        except ValueError:
            # calibre_dump_s was probably not an integer so start with 1
            logging.info("Unable to handle calibre dump '{0}', restarting with 1".format(calibre_dump_s))
            calibre_dump = 1
        debian_version = debian_version_m.group(1)
        sep = debian_version_m.group(2)
        new_full_version = upstream_version + "-" + debian_version + "+" + tag + sep + str(calibre_dump)
    else:
        logging.info("Tag {0} not found in Debian version, appending new one".format(tag))
        new_full_version = full_version + "+" + tag + "+1"

    # Bump the version, adding "+target_dist+1"
    cmd = ["dch", "--force-distribution", "-D", target_dist,
           "-v", new_full_version,
           "Rebuild for " + target_dist + "."]
    logging.debug(" ".join(cmd))
    p = subprocess.call(cmd)

    # Recreate the source package
    os.chdir(work_dir)
    if "-" in new_full_version:
        cmd = ["dpkg-source", "-b", path]
    else:   # Native
        cmd = ["dpkg-source", "-b", "{0}-{1}".format(name, new_full_version)]

    logging.debug(" ".join(cmd))
    p = subprocess.call(cmd)

    # And build with cowbuilder
    cowbuilder_bin = get_from_config("build", "cowbuilder_bin", target_dist)
    if not os.path.isfile(cowbuilder_bin):
        sys.exit("The file {0} doesn't exist".format(cowbuilder_bin))

    cmd = [cowbuilder_bin, "--build", "{0}_{1}.dsc".format(name, new_full_version)]
    logging.debug(" ".join(cmd))
    p = subprocess.call(cmd)

    # Remove work directory
    shutil.rmtree(work_dir)

    repo_bin_dir = get_from_config("build", "repo_bin_dir", target_dist)
    repo_src_dir = get_from_config("build", "repo_src_dir", target_dist)

    dsc_file = "{0}_{1}.dsc".format(name, new_full_version)
    dsc_path = os.path.join(repo_bin_dir, dsc_file)
    changes_file = "{0}_{1}_amd64.changes".format(name, new_full_version)
    changes_path = os.path.join(repo_bin_dir, changes_file)
    orig_file = "{0}_{1}.orig.tar.gz".format(name, upstream_version)
    debian_file = "{0}_{1}.debian.tar.gz".format(name, new_full_version)

    logging.info("""
Commands you are supposed to run then:
-------------8<-----------------------
unset DISPLAY
eval $(gpg-agent --daemon)
clara repo del {0} {1}
clara repo add {0} {2}
clara repo add {0} {3}
cp -v {4}/{{{5},{6},{7}}} {8}/
#-------------8<-----------------------
""".format(target_dist, name, dsc_path, changes_path,
           repo_bin_dir, dsc_file, orig_file, debian_file, repo_src_dir))

if __name__ == '__main__':
    main()
