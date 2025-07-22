#!/usr/bin/env python
# -*- coding: utf-8 -*-
#################################################################################
#  Copyright (C) 2024 EDF SA                                                    #
#                                                                               #
#  This file is part of Clara                                                   #
#                                                                               #
#  This software is governed by the CeCILL-C license under French law and       #
#  abiding by the rules of distribution of free software. You can use,          #
#  modify and/ or redistribute the software under the terms of the CeCILL-C     #
#  license as circulated by CEA, CNRS and INRIA at the following URL            #
#  "http://www.cecill.info".                                                    #
#                                                                               #
#  As a counterpart to the access to the source code and rights to copy,        #
#  modify and redistribute granted by the license, users are provided only      #
#  with a limited warranty and the software's author, the holder of the         #
#  economic rights, and the successive licensors have only limited              #
#  liability.                                                                   #
#                                                                               #
#  In this respect, the user's attention is drawn to the risks associated       #
#  with loading, using, modifying and/or developing or reproducing the          #
#  software by the user in light of its specific status of free software,       #
#  that may mean that it is complicated to manipulate, and that also            #
#  therefore means that it is reserved for developers and experienced           #
#  professionals having in-depth computer knowledge. Users are therefore        #
#  encouraged to load and test the software's suitability as regards their      #
#  requirements in conditions enabling the security of their systems and/or     #
#  data to be ensured and, more generally, to use and operate it in the         #
#  same conditions as regards security.                                         #
#                                                                               #
#  The fact that you are presently reading this means that you have had         #
#  knowledge of the CeCILL-C license and that you accept its terms.             #
#                                                                               #
#################################################################################
"""
Manage software installation via easybuild

Usage:
    clara easybuild install <software> [--force] [--container=<container>] [--skip] [--inject-checksums] [--url=<url>] [-e <name>=<value>]... [options]
    clara easybuild backup  <software> [--force] [--backupdir=<backupdir>] [--yes-i-really-really-mean-it] [--elapse <elapse>] [options]
    clara easybuild restore <software> [--force] [--backupdir=<backupdir>] [--source=<source>] [--yes-i-really-really-mean-it] [--devel] [options]
    clara easybuild delete  <software> [--force] [options]
    clara easybuild search  <software> [--force] [--width=<width>] [options]
    clara easybuild show    <software> [options]
    clara easybuild hide    <software> [--clean] [options]
    clara easybuild fetch   <software> [--inject-checksums] [options]
    clara easybuild default <software> [options]
    clara easybuild copy    <software> [<target>] [options]
    clara easybuild -h | --help | help

Options:
    <software>                       software name, either like <name>-<version> or <name>/<version>
    --eb=<ebpath>                    easybuild binary path
    --basedir=<basedir>              easybuild custom repository directory
    --prefix=<prefix>                easybuild installation prefix directory [default: /software/shared/easybuild]
    --buildpath=<buildpath>          easybuild build path [default: <prefix>/build]
    --extension=<extension>          tar backup extension, like bz2, gz or xz [default: gz]
    --compresslevel=<compresslevel>  tar compression gz level, with max 9 [default: 6]
    --dereference                    add symbolic and hard links to the tar archive. Default: False
    --force                          Force (non recursive) backup/restore of existing software/archive
    --only-dependencies              Only retrieve software dependencies
    --quiet                          Proceed silencely. Don't ask any question!
    --dry-run                        Just simulate migrate action! Don't really do anything
    --width=<width>                  Found easyconfigs files max characters per line [default: 100]
    --url=<url>                      easybuild hook url to locally fetch source files
    --yes-i-really-really-mean-it    Force recursive restore. Use only if you known what you are doing!
    --suffix=<suffix>                Add suffix word in tarball name
    --no-suffix                      No suffix in tarball name
    --inject-checksums               Let EasyBuild add or update checksums in one or more easyconfig files
    --skip                           Installing additional extensions when combined with --force
    --elapse <elapse>                Elapse time en seconds after which backup file can be regenerated [default: 300]
    --no-container                   Don't use container image. Only singularity is supported
"""

import logging
import os
import shutil
import sys
import tempfile
import glob
import re
import tarfile
import itertools
import tempfile

try:
    import docopt
except ModuleNotFoundError:
    module = docopt
    logging.error("PLS raise 'pip install %s' or install 'python3-%s' software!" % (module,module))

from clara.utils import clara_exit, run, get_from_config_or, conf, module, yes_or_no, do_print

from pprint import pprint, pformat
from textwrap import fill
from datetime import datetime

try:
    from prettytable import PrettyTable as prettytable
except:
    print("[WARN] PLS raise 'pip install prettytable' or install 'python3-prettytable' software!")
    pass

def copy(software, basedir, target):
    software = re.sub(r'/(\.)?', '-', software)
    if not software.endswith(".eb"):
        software = f"{software}.eb"

    path_dir = "{}/{}/{}".format(basedir, software[0].lower(),
            re.split(r'[/-]', software)[0])
    if not dry_run:
        os.makedirs(path_dir, exist_ok=True)
    path = f"{path_dir}/{target}"

    _dry_run = '--dry-run' if dry_run else ''
    cmd = [eb ,'--robot', basedir, _dry_run, '--hook',
           f'{basedir}/pre_fetch_hook.py', '--copy-ec', software, path]

    output, retcode = run(' '.join(cmd), shell=True, exit_on_error=False)
    if isinstance(retcode, int) and not retcode == 0:
        logging.debug(output)
        clara_exit(f"fail to copy software {software} spec to {path} :-( !")
    else:
        logging.info(f"successfully copy software {software} spec to {path}")
        logging.debug(f"output:\n{output}")
        return output

def module_path(prefix):
    if isinstance(prefix, str):
        if not os.path.isdir(f"{prefix}/modules"):
            clara_exit(f"no directory modules found under {prefix}!")

        modulepath = ":".join([ f"{prefix}/modules/{f.name}"
                     for f in os.scandir(f"{prefix}/modules") if f.is_dir() and not f.name=="all"
                     and os.path.isdir(f"{prefix}/modules")])
    elif isinstance(prefix, list):
        modulepath = ":".join([f"{x}/modules/{f.name}" for x in prefix if os.path.isdir(f"{x}/modules")
                     for f in os.scandir(f"{x}/modules") if f.is_dir() and not f.name=="all"])
    else:
        clara_exit("prefix must be either string, or list!")

    # add back all modules in path
    if isinstance(prefix, str):
        modulepath = f"{modulepath}:{prefix}/modules/all"
    else:
        modulepath = modulepath + ":" + ":".join([f"{x}/modules/all" for x in prefix])
    os.environ["MODULEPATH"] = modulepath
    logging.debug(f"MODULEPATH:\n{modulepath}")

def module_avail(name, prefix, rebuild=False):

    # set MODULEPATH environment variable
    module_path(prefix)

    if not re.match(r"[^-]+-[^\/]+\/", name):
        name = re.sub(r"([^-\/]+)[-\/](\.)?(.*)(\.eb)?", r"\1/\2\3", name)

    if rebuild:
        return name, None, 0

    output, error = module('--show_hidden', 'avail', name)

    if isinstance(error, int) and not error == 0:
        logging.warn(f"fail to get avail modules of software {name} :-( !")
        return name, None, error

    _name = name
    if not re.search(name, error) and not re.search(r"\/\.", name):
    # support also hidden module!
        _name = "/".join([re.sub(r"^(\d+\.)", r".\1", x) for x in name.split("/")])
        logging.debug(f"search hidden module {_name}")
        output, error = module('--show_hidden', 'avail', _name)

    match = re.search(rf"{_name}[^\n ]*", error)
    name = match.group() if match else name

    return name, match, error

def default(software, prefix):

    name, match, output = module_avail(software, prefix)
    if match:
        output, error = module('show', name)
        if error == 1:
            clara_exit(f"Either software {name} is not installed nor is hide! PLS, install or unhide it first!")
        pattern = re.compile(r' [/fs]?[\w]*(/.*\.lua):', re.DOTALL)
        match = pattern.findall(error)

        if len(match) == 1:
            modulelua = "".join(match)
            path = os.path.dirname(modulelua)
            defaultlua = f"{path}/default"
            if os.path.islink(defaultlua):
                logging.debug(f"suppressing existent link default {defaultlua} ...")
                os.unlink(defaultlua)
            elif os.path.isfile(defaultlua):
                logging.debug(f"suppressing existent file default {defaultlua} ...")
                os.remove(defaultlua)

            try:
                os.symlink(modulelua, defaultlua)
            except:
                clara_exit(f"fail to set software {name} as default under {prefix}!")
            else:
                logging.info(f"successfully set software {name} as default under {prefix}!")
                show(name.split("/")[0], prefix)

    else:
        logging.info(f"No software {name} installed under prefix\n{', '.join(prefix)}!")

def hide(software, prefix, clean):
    output, error = module("--version")
    match = re.search(r': Version ([\.\w]+)', error)
    if not match:
        clara_exit("can't figure out current module version :-( !")

    try:
        from packaging.version import Version
    except ModuleNotFoundError:
        _module = "packaging"
        logging.error("PLS raise 'pip install %s' or install 'python3-%s' software!" % (_module, _module))

        clara_exit("PLS, install package python3-packaging")
    if Version(match.group(1)) < Version("8.7.53"):
        clara_exit("Advanced module hidden need Lmod version greater than 8.7.53. Try \"module load Lmod\"!")

    name, match, output = module_avail(software, prefix)
    if match:
        output, error = module('show', name)
        if error == 1:
            clara_exit(f"Either software {name} is not installed nor is hide! PLS, install or unhide it first!")
        pattern = re.compile(r' [/fs]?[\w]*(/.*\.lua):', re.DOTALL)
        match = pattern.findall(error)

        if len(match) == 1:
            path = os.path.dirname("".join(match))
            defaultlua = f"{path}/default"
            if os.path.exists(defaultlua):
                message = f"default file {defaultlua} exist and it's can work this way to hide module!"
                message += "\nDo you want it to be deleted ?"
                if not force:
                    if not yes_or_no(message):
                        clara_exit(f"hidden to software {name} under {prefix} have been aborted!")
            if os.path.islink(defaultlua):
                logging.debug(f"suppressing existent link default {defaultlua} ...")
                os.unlink(defaultlua)
            elif os.path.isfile(defaultlua):
                logging.debug(f"suppressing existent file default {defaultlua} ...")
                os.remove(defaultlua)

            modulerc = f"{path}/.modulerc.lua"
            if clean and os.path.isfile(modulerc):
                os.remove(modulerc)
                clara_exit(f"module hidden file {modulerc} have been deleted!")

            module_name = software.split('/')[0]
            _name = module_name if software==module_name else name
            try:
                # open file in read/write to be able to update it, if need!
                with open(modulerc, "a+") as f:
                    f.seek(0)
                    data = f.read()
                    if 'name=' in data:
                        match = re.search(r"name=[\{]?([^\}]+)[\}]?", data, re.DOTALL)
                        # Do anything if module have been already hidden!
                        if module_name == match.group(1) or name in match.group(1):
                            logging.debug(f"module {_name} already hidden!")
                        else:
                            logging.info(f"hidding software {_name} using file {modulerc}!")
                            f.seek(0)
                            f.truncate()
                            f.write("hide{name={%s,'%s'}}" % (match.group(1),_name))
                    else:
                        # if it's first time
                        # when module name (without version) have been provided, use it instead of
                        # automatically retrieving from module_avail function
                        logging.info(f"[DEBUG] hidding software {_name} using file {modulerc}!")
                        f.write("hide{name='%s'}" % _name)
            except:
                clara_exit(f"fail to hide software {name} under {prefix}!")
            else:
                show(module_name, prefix)

    else:
        logging.info(f"No software {name} installed under prefix\n{', '.join(prefix)}!")

def show(software, prefix):
    name, match, output = module_avail(software, prefix)
    if match:
        print(output)
    else:
        logging.info(f"No software {name} installed under prefix {' or '.join(prefix)}!")

def search(software, basedir, width, force):
    if re.search(r"/", software):
        message = "searching easybuild software including '/' won't work!"
        message += "\nAre you sure you want to proceed any way?"
        if not force:
            if not yes_or_no(message):
                return
    match = re.search(r"(\w+[-\.\d]*)[\.eb]*", software.split("/")[-1])
    if match:
        _software = match.group()
        cmd = [eb, '--hook', f'{basedir}/pre_fetch_hook.py',
                '--robot', basedir, '--search', _software,
                '--detect-loaded-modules=ignore', '--check-ebroot-env-vars=ignore']
        output, _ = run(' '.join(cmd), shell=True)
        pattern = re.compile(r' \* ([^ ]*\.eb)', re.DOTALL)
        match = pattern.findall(output)
        easyconfig = {}
        if match:
            for x in match:
                CFGS, path = os.path.dirname(x), os.path.basename(x)
                if CFGS in easyconfig:
                    easyconfig[CFGS].append(path)
                else:
                    easyconfig[CFGS] = [path]

            try:
                table = prettytable()
                table.field_names = ["easyconfig files"]
            except:
                table = f":{width}"

            for CFGS, paths in easyconfig.items():
                do_print(table, [CFGS])
                do_print(table, [fill(" ".join(paths), width=width)])

            try:
                if table._get_rows({'oldsortslice': False,'start': 0, 'end': 1, 'sortby': False}):
                    table.align["easyconfig files"] = "l"
                    count = 0
                    table_txt = ''
                    # simulate here some tricks not yet supported by prettytable used version!
                    for number, line in enumerate(table.get_string().split('\n')):
                        if number == 0:
                            horizontal = line
                        if re.search(r'\/', line):
                            if count:
                                table_txt = '%s%s\n%s\n%s\n' % (table_txt, horizontal, line, horizontal)
                            else:
                                count += 1
                                table_txt = '%s%s\n%s\n' % (table_txt, line, horizontal)
                        else:
                            table_txt = '%s%s\n' % (table_txt, line)
                # print transformed table!
                print(table_txt)
            except:
                print(table)
        else:
            logging.warn(f"no easyconfig file for software {software}!")
    else:
        logging.warn(f"no easyconfig file for software {software}!")

def get_dependencies(software, prefix, basedir, rebuild):
    cmd = [eb ,'--robot', basedir, '--dry-run', '--hook',
            f'{basedir}/pre_fetch_hook.py', software]

    output, retcode = run(' '.join(cmd), shell=True, exit_on_error=False)
    if isinstance(retcode, int) and not retcode == 0:
        clara_exit(f"fail to get dependencies of software {software} :-( !")
    else:
        logging.debug(output)

    pattern = re.compile(r' \* \[([\sx])\] ([^ ]*\.eb) \(module: ([^\)]*)\)', re.DOTALL)
    # retrieve dependencies as (software path, module name) list
    match = pattern.findall(output)

    if match:
        dependencies = [(True if state == 'x' else False,module,version)
                        for state,module,version in match if software not in module]
        return dependencies
    else:
        if len(dependencies) == 0:
            _software = software.replace(".eb","")
            logging.info(f"software {_software} is already installed under {prefix}!")
            logging.debug(f"\n{output}")
        #
        return dependencies

def fetch(software, basedir, checksums):
    software = re.sub(r'/(\.)?', '-', software)
    if not software.endswith(".eb"):
        software = f"{software}.eb"

    _dry_run = '--dry-run' if dry_run and not checksums else ''
    cmd = [eb ,'--robot', basedir, _dry_run, '--hook',
           f'{basedir}/pre_fetch_hook.py', software, '--fetch']
    if checksums:
        cmd += ['--inject-checksums', '--force']

    output, retcode = run(' '.join(cmd), shell=True, exit_on_error=False)
    if isinstance(retcode, int) and not retcode == 0:
        logging.debug(output)
        clara_exit(f"fail to fetch source of software {software} :-( !")
    else:
        logging.info(f"successfully fetch software {software} source archive")
        logging.debug(f"output:\n{output}")
        return output

def install(software, prefix, basedir, buildpath, rebuild, only_dependencies, recurse, checksums, skip, options, container):
    # suppress, if need, ".eb" suffix
    name, match, _ = module_avail(software, prefix, rebuild=rebuild)
    if re.search(r"/|-", name) is None:
        clara_exit(f"Bad software name: {name}. PLS software must follow scheme <name>/<version>")
    software = re.sub(r'/(\.)?', '-', name)
    _software = f"{software}.eb"
    if match and not rebuild:
        message = f"\nsoftware {_software} already exist under {prefix}!"
        message += f"\nuse switch --force to install it again!"
        logging.info(message)
        return
    else:
        # retrieve software potential dependencies
        dependencies = get_dependencies(_software, prefix, basedir, rebuild or only_dependencies)

    # if need, retrieve newly installed software path
    if recurse:
        for installed, _, software in dependencies:
            if not installed or rebuild:
                install(software, prefix, basedir, rebuild, only_dependencies, recurse, checksums, skip, options, container)

    if not only_dependencies:
        fetch(_software, basedir, checksums)

    _dry_run = '--dry-run' if dry_run and not checksums else ''
    if not only_dependencies:
        cmd = [eb ,'--robot', basedir, _dry_run, '--hook', f'{basedir}/pre_fetch_hook.py', _software]
        cmd += ['--buildpath', buildpath, '--installpath', prefix, '--prefix', prefix]
        cmd += ['--containerpath', f"{prefix}/containers", '--packagepath', f"{prefix}/packages"]
        cmd += [_software]
        if rebuild:
            cmd += ['--rebuild']
        if skip:
            cmd += ['--skip']
        for option in options:
            cmd += [f"--{option}"]
        # use singularity container to avoid prefix realpath in builded easybuild software!
        if container and not prefix == os.path.realpath(prefix):
            cmd = ['singularity', 'exec', '-B', prefix, container] + cmd
        # enforce installation only in specified prefix directory
        # For instance to ensure no direct installation in prod
        # target destination path installation can be safely deploy later!
        os.environ["EASYBUILD_PREFIX"] = prefix
        output, retcode = run(' '.join(cmd), shell=True, exit_on_error=False)
        if isinstance(retcode, int) and not retcode == 0:
            logging.debug(output)
            clara_exit(f"fail to install software {_software} :-( !")
        else:
            logging.debug(output)

    if len(dependencies):
        logging.info(f"\nsoftware {name} need following dependencies:\n{dependencies}")
        if not dry_run:
            output, error = module('show', name)
            if error == 1:
                logging.debug(f"Either software {name} is not installed nor is hide! PLS, install or unhide it first!")
            else:
                pattern = re.compile(r' [/fs]?[\w]*(/.*\.lua):|EBROOT[^,]*,"([^"]*)"', re.DOTALL)
                match = pattern.findall(error)

                _modules = [x for _, _, x in dependencies]
                if match and len(_modules):
                    data = [i.strip() for x in match for i in ''.join(x).split('\n')]
                    if not only_dependencies:
                        logging.debug(error)
                    installpath = "".join([name for name in data if not name.endswith(".lua")])
                    logging.info(f"Create dependencies file {installpath}/.__dependencies.txt")
                    with open(f"{installpath}/.__dependencies.txt", 'w') as f:
                        f.write('\n'.join(_modules))
    else:
        logging.info(f"software {name} dont have any dependency!")

def module_versions(name, prefix):
    _name, match, _ = module_avail(name, prefix)
    if not match:
        clara_exit(f"no module named {name} under prefix {prefix}!")

    output, error = module('--show_hidden', 'spider', _name)

    pattern = re.compile(r': module load (.*?)\n\n|Versions:\n(.*)\n\n-', re.DOTALL)
    match = pattern.findall(error)

    if match:
        return _name, [i.strip() for x in match for i in ''.join(x).split('\n')]
    else:
        return _name, []

def get_tarball(path, software, extension, suffix):
    if not suffix == "":
        suffix = f"-{suffix}"
    return f"{path}/{software}{suffix}.tar.{extension}"

def tar(software, prefix, data, backupdir, extension, compresslevel, dereference, force, suffix, elapse):
    if not re.match(r'^/\w+', prefix):
        logging.debug(f"unsupported prefix {prefix}!")
        return
    packages_dir = f"{backupdir}/packages"
    if not os.path.isdir(packages_dir):
        os.mkdir(packages_dir)
    tarball = get_tarball(packages_dir, software, extension, suffix)
    now = datetime.now().timestamp()
    file_exists = os.path.isfile(tarball) and (now - os.stat(tarball).st_mtime > elapse)
    if (force and file_exists) or not os.path.isfile(tarball):
        logging.info(f"generate tarball {tarball}")
        with tarfile.open(tarball, f"w:{extension}", compresslevel=compresslevel, dereference=dereference) as tf:
            for name in data:
                tf.add(name, arcname=name.replace(f"{prefix}/",''))
    else:
        message = f"[WARN]\ntarball {tarball} already exist!"
        if force:
            logging.debug(f"{message}\nUse --elapse <elapse> to invalidate cache!")
        else:
            logging.warn(f"{message}\nUse --force to regenerate it!")

def backup(software, prefix, backupdir, versions, extension, compresslevel, dereference, force, recurse, suffix, elapse):
    # generate module, and it's eventuals dependencies, archives (under directory backupdir)
    if versions is None:
        _software, versions = module_versions(software, prefix)
    else:
        _software = software
    match = None
    if len(versions) == 0:
        clara_exit(f"No software {_software} installed! PLS, build it first!")
    elif len(versions) == 1:
        logging.info(f"working on software {versions[0]}")
        output, error = module('show', _software)
        if error == 1:
            clara_exit(f"No software {_software} installed! PLS, install it first!")
        pattern = re.compile(r' (.*\.lua):| [/fs]?[\w]*(/.*\.lua):|EBROOT[^,]*,"([^"]*)"', re.DOTALL)
        match = pattern.findall(error)
        if match:
            data = [re.sub(r'^(\/fs\w+)', '', i.strip()) for x in match for i in ''.join(x).split('\n')]
            installpath = "".join([name for name in data if not name.endswith(".lua")])
            if os.path.isfile(f"{installpath}/.__dependencies.txt") and recurse:
                data.insert(0, f"{installpath}/.__dependencies.txt")
            _software = versions[0].replace("/","-")
            software = "".join([name for name in data if name.endswith(".lua")])
            if os.path.islink(software):
                # replace if need trail /fs<cluster> prefix and add link real path to tar archive
                data.insert(1, re.sub(r'^(\/fs\w+)', '', os.path.realpath(software)))
            # retrieve automatically dependency software prefix
            _prefix = os.path.commonpath(data)
            logging.debug(f"software: {_software}\ndata: {data}\nprefix: {_prefix}\nbackupdir: {backupdir}\n")
            if backupdir is None:
                backupdir = _prefix
            tar(_software, _prefix, data, backupdir, extension, compresslevel, dereference, force, suffix, elapse)
            if os.path.isfile(f"{installpath}/.__dependencies.txt") and recurse:
                with open(f"{installpath}/.__dependencies.txt", 'r') as f:
                    for _software in [line.rstrip() for line in f]:
                        logging.info(f"working on dependency {_software} ...")
                        backup(_software, _prefix, backupdir, [_software], extension, compresslevel, dereference, recurse, recurse, suffix, elapse)
        else:
            print([])
    else:
        pprint(f"many packages found!: {versions}")

def replace_in_file(name, source, prefix):
    if not source == prefix:
        logging.debug(f"replace {source} by {prefix}\nin file {name}")
    with open(name, 'r') as f:
        data = f.read()
        data = re.sub(r'(\/fs\w+)', '', data.replace(source, prefix))

    with open(name, 'w') as f:
        f.write(data)

def restore(software, source, backupdir, prefix, extension, force, recurse, suffix, devel):
    _module = re.sub(r"([^-\/]+)[-\/](\.)?(.*)(\.eb)?", r"\1/\2\3", software)
    if re.search(r"/|-", _module) is None:
        clara_exit(f"Bad software name: {_module}. PLS software must follow scheme <name>/<version>")
    _software = software.replace("/","-")
    packages_dir = f"{backupdir}/packages"
    tarball = get_tarball(packages_dir, _software, extension, suffix)
    umask = os.umask(0o022)

    if os.path.isfile(tarball):
        logging.info(f"restore tarball {tarball}\nunder prefix {prefix}")
        total_bytes = os.stat(tarball).st_size
        with tarfile.open(tarball, f"r:{extension}") as tf:
            members = [member for member in tf.getmembers()]
            # support module like A1/A2/.../An, splitting it only per first and
            # last componant. For instance, intel compilers related modules.
            # for hidden module, we need to remove first dot on module version!
            _list = _module.split("/")
            if len(_list) > 1:
                _module_ = "/".join([re.sub(r"^\.","",x) for x in _list[::len(_list)-1]])
            else:
                _module_ = "/".join([re.sub(r"^\.","",x) for x in _list])
            version = re.search(r"([a-zA-Z0-9\.\-\_]+)", _module_.split("/")[-1]).group(1)
            basepath = "".join([member.name for member in members
                       if os.path.normpath(member.name).lower().endswith(version)
                       or member.name.endswith(version)])
            _modulepath = {}
            installpath = f"{prefix}/{basepath}"
            if basepath == '':
                message = f"Can't find module {_module_} in tarball {tarball}\n"
                message += f"archive base path: '{basepath}'"
                clara_exit(message)

            if os.path.isdir(installpath):
                message = f"Module {_module} is already installed under {installpath}!"
                message = f"{message}\nDo you want to install it again!?!"
                _tmpname = next(tempfile._get_candidate_names())
                _prefix = f"{prefix}/tmp/{_tmpname}"
                _installpath = f"{_prefix}/{basepath}"
                os.makedirs(_installpath)
                if not force:
                    if not yes_or_no(message):
                        logging.error(f"Abort software {software} installation!")
                        return
            else:
                _installpath = None
                _prefix = prefix
                _tmpname = None

            for member in members:
                # replace in lua file prefix by destination prefi_x
                _name = f"{_prefix}/{member.name}"
                if member.name.endswith(f"{version}/.__dependencies.txt"):
                    tf.extract(member, _prefix, set_attrs=False)
                    if os.path.isfile(_name) and recurse:
                        logging.info(f"working on dependencies file {_name} ...")
                        with open(_name, 'r') as f:
                            for _software in [line.rstrip() for line in f]:
                                logging.info(f"restore  software {_software} ...")
                                restore(_software, source, backupdir, prefix, extension, force, recurse, suffix, devel)
                elif member.name.endswith(f"{_module}.lua"):
                    _modulepath[_name] = None
                    if member.issym():
                        if os.path.islink(_name) and not os.path.exists(_name):
                            clara_exit(f"symbolic link {_name} is probably broken!")
                        link = member.linkname.replace(source, prefix)
                        # replace if need trail /fs<cluster> prefix
                        link = re.sub(r'^(\/fs\w+)', '', link)
                        logging.info(f"creating symbolic link {link} to file {_name}")
                        _parent = os.path.dirname(_name)
                        if not os.path.isdir(_parent):
                            os.makedirs(_parent)
                        if not os.path.islink(_name):
                            os.symlink(link, _name)
                    else:
                        logging.info(f"working on file {_name} ...")
                        tf.extract(member, _prefix, set_attrs=False)
                        if not os.path.islink(_name):
                            os.chmod(_name, member.mode)
                        replace_in_file(_name, source, prefix)
                elif not f"{version}/easybuild" in member.name or devel:
                    tf.extract(member, _prefix, set_attrs=False, filter='fully_trusted')
                    if not os.path.islink(_name):
                        os.chmod(_name, member.mode)

                if not f"{version}/easybuild" in member.name or devel:
                    try:
                        cmd = f"/bin/chmod go=u-w {_name}"
                        output, retcode = run(cmd, shell=True, exit_on_error=False, debug=False)
                    except:
                        logging.debug(output)

            os.umask(umask)  # Restore umask

            if os.path.isdir(installpath) and _installpath is not None:
                if os.path.isdir(_installpath):
                    backupdir = f"{prefix}/backups"
                    try:
                        umask = os.umask(0o022)
                        if not os.path.isdir(backupdir):
                            os.mkdir(backupdir)
                        time = datetime.now().strftime("%Y%m%d_%H%M%S")
                        _backupdir = f"{backupdir}/{time}/{_module.split('/')[0]}"
                        if not os.path.isdir(_backupdir):
                            os.makedirs(_backupdir)
                        os.umask(umask)  # Restore umask
                        logging.info(f"backup current installed directory {installpath}\n               moving it to {_backupdir}!")
                        shutil.move(installpath, _backupdir)
                        for _path in _modulepath:
                            if os.path.exists(_path):
                                path = _path.replace(_prefix, prefix)
                                destdir = os.path.dirname(path).replace(prefix, _backupdir)
                                os.makedirs(destdir, exist_ok=True)
                                if path.startswith(prefix) and (os.path.isfile(path) and os.path.isdir(destdir)):
                                    logging.info(f"restore current module file {path}\n               moving it to backup dir {destdir}!")
                                    shutil.move(path, destdir)
                    except EnvironmentError:
                        logging.error("Unable to move previously installed directory")
                    else:
                        try:
                            logging.info(f"restore temporary directory {_installpath}\n               to {installpath}!")
                            shutil.move(_installpath, installpath)
                            for _path in _modulepath:
                                if _path.startswith(_prefix) and (os.path.isfile(_path) or os.path.islink(_path)):
                                    path = _path.replace(_prefix, prefix)
                                    logging.info(f"restore temporary module file {_path}\n               moving it to {path}!")
                                    shutil.move(_path, path)
                        except EnvironmentError:
                            logging.error(f"Fail to move temporary installed directory to target one!")
                        else:
                            logging.info(f"module {_module} successfully restored in {installpath}!")
                    finally:
                        # ensure _prefix is directory stricly under prefix!
                        # we recall here previously declared _prefix value, for clarity!
                        _prefix = f"{prefix}/tmp/{_tmpname}"
                        if not _tmpname == None and re.match(rf"{prefix}/tmp/\w+", _prefix) and os.path.isdir(_prefix):
                            logging.info(f"suppress temporary installed directory {_prefix}")
                            shutil.rmtree(_prefix)
                else:
                    logging.info(f"directory {_installpath} don't exist!")
            else:
                logging.info(f"module {_module} successfully installed in {installpath}!")

    else:
        logging.warn(f"tarball {tarball} don't exist!")

def delete(software, prefix, force):
    _software, versions = module_versions(software, prefix)
    match = None
    if len(versions) == 0:
        clara_exit(f"No software {_software} installed!")
    elif len(versions) == 1:
        output, error = module('show', _software)
        if error == 1:
            clara_exit(f"Either software {_software} is not installed nor is hide! PLS, install or unhide it first!")
        pattern = re.compile(r' (.*\.lua):| [/fs]?[\w]*(/.*\.lua):|EBROOT[^,]*,"([^"]*)"', re.DOTALL)
        match = pattern.findall(error)
        if match:
            data = [i.strip() for x in match for i in ''.join(x).split('\n')]
            _data = '\n'.join(data)
            message = "\nAre you sure you want to remove bellow files/directory "
            message += "of software {}:\n\n{}\n\n".format(_software, _data)
            if not force:
                if not yes_or_no(message):
                    logging.info(f"You choose to no more removed software {_software}!")
                    return
            logging.debug(f"suppressing software {versions[0]} under path\n{_data}")
            for name in data:
                if name.endswith(".lua"):
                    if os.path.isfile(name):
                        if os.path.islink(name):
                            _name = os.path.realpath(name)
                            logging.info(f"suppressing link source file {_name}")
                            os.unlink(_name)
                            logging.info(f"suppressing symbolic link {name}")
                        else:
                            logging.info(f"suppressing file {name}")
                        os.unlink(name)
                    else:
                        logging.info(f"no file {name}!")
                elif not re.match(r'^/$', name.rstrip(os.sep)):
                    # suppress trailing end separator (like //)
                    # ensure name isn't root directory
                    if os.path.isdir(name):
                        logging.info(f"suppressing directory {name}")
                        shutil.rmtree(name)
                    else:
                        logging.warn(f"no directory {name}!")
                else:
                    clara_exit(f"can't suppress unneed {name} directory!")
        else:
            logging.error(f"can't figure out needful information about module {_software} :-(")
    else:
        pprint(f"too many packages found!: {versions}")
        logging.error("can't suppress many software/module at same time!")

def main():
    global dry_run, eb

    logging.debug(sys.argv)
    dargs = docopt.docopt(__doc__)

    dry_run = dargs['--dry-run']
    force = dargs['--force']
    recurse = dargs['--yes-i-really-really-mean-it']
    width = int(dargs['--width'])
    only_dependencies = dargs['--only-dependencies']
    extension = dargs['--extension']
    compresslevel = int(dargs['--compresslevel'])
    dereference = dargs['--dereference']
    devel = dargs['--devel']
    checksums = dargs['--inject-checksums']
    skip = dargs['--skip']
    elapse = int(dargs['--elapse'])

    if (dargs['delete'] or dargs['restore']) and not re.search(r"(admin|service|login)", os.uname()[1]):
        clara_exit("easybuild deployment or deletion is only supported on admin or service nodes!")

    if (dargs['install'] or dargs['delete']) and not (os.path.isfile("/usr/share/lmod/lmod/libexec/lmod")):
        clara_exit("required Lmod package seem's not installed!")

    homedir = os.environ["HOME"]

    # set default config file
    if os.geteuid() == 0:
        config = '/etc/clara/config.ini'
    else:
        config = os.path.abspath(f"{homedir}/.config/easybuild.ini")
    if conf.config is None and os.path.isfile(config):
        conf.config = config

    suffix = "" if dargs['--no-suffix'] else None
    if suffix is None:
        suffix = dargs['--suffix']
    if suffix is None:
        # default is to retrieve host name!
        suffix=os.uname()[1]
        try:
            # default is to retrieve host domain name!
            with open("/etc/resolv.conf", 'r') as f:
                for line in f.read().splitlines(True):
                    match = re.search(r"^search\s+([^\.]+)", line)
                    if match:
                        suffix = match.group().replace("search ","")
        except:
            pass

    suffix = get_from_config_or("easybuild", "suffix", default=suffix)

    eb = dargs['--eb']
    eb = get_from_config_or("easybuild", "binary", default=eb)

    software = dargs['<software>']
    if software is not None:
        software = software.replace(".eb","")

    prefix = dargs['--prefix']
    # set default directory to install easybuild software
    # we have go with three ways to provide this prefix
    if prefix is None:
        prefix = '/software/shared/easybuild'
    prefix = get_from_config_or("easybuild", "prefix", default=prefix)
    # ensure prefix is real path to enforce security and safety!

    buildpath = dargs['--buildpath']
    if buildpath is None:
        buildpath = "%s/build" % prefix
    buildpath= get_from_config_or("easybuild", "buildpath", default=buildpath)


    # set default easybuild custom configs base directory
    # standfor for copy of easybuid config file from example repository:
    # https://github.com/easybuilders/easybuild-easyconfigs
    basedir = dargs['--basedir']
    if basedir is None:
        basedir = f'{homedir}/easybuild'
    basedir = get_from_config_or("easybuild", "basedir", default=basedir)
    hook = f"{basedir}/pre_fetch_hook.py"
    if dargs['install']:
        if os.path.isdir(basedir):
            if not os.path.isfile(hook):
                logging.warn(f"file {hook} don't exist! Do you want us")
                message = f"to create for you default file {hook}?"
                if yes_or_no(message):
                    url = get_from_config_or("easybuild", "url", default=dargs['--url'])
                    if url is None:
                        message = "You must use switch --url to provide hook url\n"
                        message += f"or create file {hook} manually!"
                        clara_exit(message)
                    with open(hook, "w") as f:
                        f.write(f"""def pre_fetch_hook(self):
    "add custom url for source vua of pre-fetch hook"
    url = '{url}'
    path = '%(nameletterlower)s/%(name)s'
    self.log.info("[pre-fetch hook] add url %s !" % url)
    self.cfg['source_urls'] = self.cfg['source_urls'] + ['%s/%s' % (url, x) for x in ['', path, '%s/extensions' % path]]
                        \n""")
                else:
                    clara_exit("You must create it manually!")
        else:
            message = f"""basedir {basedir} is not a valid directory
It can be customized using either --basedir or config file, it should point
to easyconfigs from a custom repository or from the easybuild install.

It's recommended to create your own config file with:
basedir=<your base dir here>
cat <<EOF> {config}
[easybuild]
basedir=$basedir
EOF
{config} is the default config file. So no need to use --config!
                      """
            clara_exit(message)

    pythonpath = os.environ.get("PYTHONPATH",'')
    modulepath = os.environ.get("MODULEPATH",'')

    source = dargs['--source']
    if source is None:
        source = prefix
    source = get_from_config_or("easybuild", "source", default=source)

    backupdir =  dargs['--backupdir']
    if backupdir is None and dargs['restore']:
        backupdir = prefix
    backupdir = get_from_config_or("easybuild", "backupdir", default=backupdir)

    if not eb:
        eb = shutil.which('eb')

    if eb:
        if not (os.path.isfile(eb) and os.access(eb, os.X_OK)):
            clara_exit(f"easybuild binary {eb} isn't executable!")
        _path = os.path.dirname(eb)
        eb_root = os.path.dirname(_path)
        for _path in glob.glob(f"{eb_root}/lib/*/site-packages"):
            if not _path in os.environ:
                pythonpath += f":{_path}"
        _path = eb_root
        while True:
            _path = os.path.dirname(_path)
            if os.path.isdir(f"{_path}/modules"):
                modulepath += f":{_path}/modules/all"
                break
    elif dargs['install'] or dargs['search'] or dargs['fetch'] or dargs['copy']:
        clara_exit("no easybuild binary found in your path. PLS raise: module EasyBuild or provide easybuild binary via --eb switch")
    _path = shutil.which('python3')
    if _path:
        os.environ["EB_PYTHON"] = _path

    os.environ["PYTHONPATH"] = pythonpath

    if dargs['search']:
        search(software, basedir, width, force)
    elif dargs['show']:
        show(software, [prefix, f"{homedir}/.local/easybuild"])
    elif dargs['fetch']:
        fetch(software, basedir, checksums)
    elif dargs['install']:
        nocontainer = dargs['--no-container']
        container = get_from_config_or("easybuild", "container", default=dargs['--container'])
        if not nocontainer:
            if container is None and not prefix == os.path.realpath(prefix):
                # we try to find existent singularity image
                clara_exit("you must provide singularity image using switch --container=<singularity image>!")
            if container:
                if not shutil.which('singularity'):
                    clara_exit("can't found singularity binary :-(!")
                elif not os.path.exists(container):
                    clara_exit(f"singularity image {container} don't exist!")

        install(software, prefix, basedir, buildpath, force, only_dependencies, recurse, checksums, skip, dargs['<name>=<value>'], container)
    elif dargs['backup']:
        backup(software, prefix, backupdir, None, extension, compresslevel, dereference, force, recurse, suffix, elapse)
    elif dargs['restore']:
        restore(software, source, backupdir, prefix, extension, force, recurse, suffix, devel)
    elif dargs['delete']:
        delete(software, os.path.realpath(prefix), force)
    elif dargs['hide']:
        hide(software, prefix, dargs['--clean'])
    elif dargs['default']:
        default(software, prefix)
    elif dargs['copy']:
        copy(software, basedir, dargs['<target>'] if dargs['<target>'] else software)

if __name__ == '__main__':
    main()
