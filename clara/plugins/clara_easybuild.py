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
    clara easybuild install <software> [--force] [--rebuild] [options]
    clara easybuild backup  <software> [--force] [--backupdir=<backupdir>] [options]
    clara easybuild restore <software> [--force] [--source=<source>] [options]
    clara easybuild delete  <software> [options]
    clara easybuild search  <software> [--width=<width>] [options]
    clara easybuild show    <software> [options]
    clara easybuild -h | --help | help

Options:
    <software>                       software name, either like <name>-<version> or <name>/<version>
    --eb=<ebpath>                    easybuild binary path
    --basedir=<basedir>              easybuild custom repository directory
    --prefix=<prefix>                easybuild installation prefix directory
    --extension=<extension>          tar backup extension, like bz2, gz or xz [default: gz]
    --compresslevel=<compresslevel>  tar compression gz level, with max 9 [default: 6]
    --dereference                    add symbolic and hard links to the tar archive. Default: False
    --force                          Force install/backup/restore of existing software/archive
    --requirement-only               Only retrieve software dependencies
    --quiet                          Proceed silencely. Don't ask any question!
    --dry-run                        Just simulate migrate action! Don't really do anything
    --width=<width>                  Found easyconfigs files max characters per line [default: 100]
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

try:
    from prettytable import PrettyTable as prettytable
except:
    print("[WARN] PLS raise 'pip install prettytable' or install 'python3-prettytable' software!")
    pass

def module_path(prefix):
    if isinstance(prefix, str):
        modulepath = ":".join([ f"{prefix}/modules/{f.name}"
                     for f in os.scandir(f"{prefix}/modules") if f.is_dir() and not f.name=="all" ])
    elif isinstance(prefix, list):
        modulepath = ":".join([f"{x}/modules/{f.name}" for x in prefix
                     for f in os.scandir(f"{x}/modules") if f.is_dir() and not f.name=="all" ])
    else:
        clara_exit("prefix must be either string, or list!")

    os.environ["MODULEPATH"] = modulepath

def module_avail(name, prefix):

    # set MODULEPATH environment variable
    module_path(prefix)

    _name = name.replace("-","/").replace(".eb","")
    output, error = module(f"avail {_name}")
    return _name, re.search(_name, error), error

def show(software, prefix):
    name, match, output = module_avail(software, prefix)
    if match:
        print(output)
    else:
        logging.debug(f"No software {name} installed under prefix {prefix}!")

def search(software, basedir, width):
    cmd = [eb, '--hook', f'{basedir}/pre_fetch_hook.py',
            '--robot', basedir, '--search', software]
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

def get_dependencies(software, prefix, basedir, rebuild, dependencies=[]):
    cmd = [eb ,'--robot', basedir, '--dry-run', '--hook',
            f'{basedir}/pre_fetch_hook.py', software]

    output, _ = run(' '.join(cmd), shell=True)
    if rebuild:
        pattern = re.compile(r' \* \[[\sx]\] ([^ ]*\.eb) \(module: ([^\)]*)\)', re.DOTALL)
    else:
        pattern = re.compile(r' \* \[ \] ([^ ]*\.eb) \(module: ([^\)]*)\)', re.DOTALL)
    # retrieve dependencies as (software path, module name) list
    match = pattern.findall(output)

    if match:
        if software not in dependencies:
            _deplist = [name for name in match if name not in dependencies]
            if len(_deplist):
                dependencies += _deplist
                return list(itertools.chain(*[get_dependencies(_software, prefix, rebuild, dependencies) for _software, _ in _deplist]))
            else:
                return dependencies
    else:
        if len(dependencies) == 0:
            _software = software.replace(".eb","")
            logging.info(f"software {_software} is already installed under {prefix}!")
            logging.debug(f"\n{output}")
        #
        return dependencies

def install(software, prefix, basedir, rebuild, requirement_only):
    # suppress, if need, ".eb" suffix
    name, match, _ = module_avail(software, prefix)
    _software = f"{name.replace('/','-')}.eb"
    if match:
        if rebuild:
            # module already exist under prefix
            # rewrite needful syntax for eb software
            # ensure infinite recursive loop!
            sys.setrecursionlimit(150)
            # retrieve software potential dependencies
            dependencies = get_dependencies(_software, prefix, basedir, rebuild)

            # suppress duplicates
            dependencies = list(dict.fromkeys(dependencies))
            if len(dependencies):
                logging.info(f"software {_software} need following dependencies:\n{dependencies}")
        else:
            message = f"\nsoftware {_software} already exist under {prefix}!"
            message += f"\nuse switch --rebuild to install it again!"
            logging.info(message)
            return
    else:
        dependencies = []
        logging.debug(f"No software {name} installed under prefix {prefix}!")
    #
    if not dry_run:
        if not requirement_only:
            cmd = [eb ,'--robot', basedir, '--hook', f'{basedir}/pre_fetch_hook.py', _software]
            if rebuild:
                cmd += ['--rebuild']
            # enforce installation only in specified prefix directory
            # For instance to ensure no direct installation in prod
            # target destination path installation can be safely deploy later!
            os.environ["EASYBUILD_PREFIX"] = prefix
            run(cmd)
        # if need, retrieve newly installed software path
        if len(dependencies):
            output, error = module(f"show {name}")
            pattern = re.compile(r' [/fs]?[\w]*(/.*\.lua):|EBROOT[^,]*,"([^"]*)"', re.DOTALL)
            match = pattern.findall(error)

            _modules = [x for _, x in dependencies if not x.startswith(name.split("/")[0])]
            if match and len(_modules):
                data = [i.strip() for x in match for i in ''.join(x).split('\n')]
                logging.info(error)
                installpath = "".join([name for name in data if not name.endswith(".lua")])
                with open(f"{installpath}/requirements.txt", 'w') as f:
                    f.write('\n'.join(_modules))

def module_versions(name, prefix):
    _name, match, _ = module_avail(name, prefix)
    if not match:
        clara_exit(f"no module named {_name} under prefix {prefix}!")

    output, error = module(f"spider {_name}")

    pattern = re.compile(r': module load (.*)\n\n|Versions:\n(.*)\n\n-', re.DOTALL)
    match = pattern.findall(error)

    if match:
        return _name, [i.strip() for x in match for i in ''.join(x).split('\n')]
    else:
        return _name, []

def tar(software, prefix, data, backupdir, extension, compresslevel, dereference, force):
    if not re.match(r'^/\w+', prefix):
        logging.debug(f"unsupported prefix {prefix}!")
        return
    packages_dir = f"{backupdir}/kwame"
    if not os.path.isdir(packages_dir):
        os.mkdir(packages_dir)
    tarball = f"{packages_dir}/{software}.tar.{extension}"
    if not os.path.isfile(tarball) or force:
        logging.info(f"generate tarball {tarball}")
        with tarfile.open(tarball, f"w:{extension}", compresslevel=compresslevel, dereference=dereference) as tf:
            for name in data:
                tf.add(name, arcname=name.replace(f"{prefix}/",''))
    else:
        logging.warn(f"[WARN]\ntarball {tarball} already exist!\nUse --force to regenerate it!")

def backup(software, prefix, backupdir, versions, extension, compresslevel, dereference, force):
    # generate module, and it's eventuals dependencies, archives (under directory backupdir)
    if versions is None:
        _software, versions = module_versions(software, prefix)
    match = None
    if len(versions) == 0:
        clara_exit(f"No software {_software} installed! PLS, build it first!")
    elif len(versions) == 1:
        logging.debug(f"working in software {versions[0]}")
        output, error = module(f"show {_software}")
        pattern = re.compile(r' (.*\.lua):| [/fs]?[\w]*(/.*\.lua):|EBROOT[^,]*,"([^"]*)"', re.DOTALL)
        match = pattern.findall(error)
        if match:
            data = [i.strip() for x in match for i in ''.join(x).split('\n')]
            _software = versions[0].replace("/","-")
            software = "".join([name for name in data if name.endswith(".lua")])
            # retrieve automatically dependency software prefix
            _prefix = os.path.commonpath(data)
            logging.debug(f"software: {_software}\ndata: {data}\nprefix: {_prefix}\nbackupdir: {backupdir}\n")
            if backupdir is None:
                backupdir = _prefix
            tar(_software, _prefix, data, backupdir, extension, compresslevel, dereference, force)
            installpath = "".join([name for name in data if not name.endswith(".lua")])
            if os.path.isfile(f"{installpath}/requirements.txt"):
                with open(f"{installpath}/requirements.txt", 'r') as f:
                    for _software in [line.rstrip() for line in f]:
                        logging.info(f"working on dependency {_software} ...")
                        backup(_software, _prefix, backupdir, [_software], extension, compresslevel, dereference, force)
        else:
            print([])
    else:
        pprint(f"many packages found!: {versions}")

def replace_in_file(name, source, prefix):
    logging.debug(f"replace {source} by {prefix}\nin file {name}")
    with open(name, 'r') as f:
        data = f.read()
        data = data.replace(source, prefix)

    with open(name, 'w') as f:
        f.write(data)

def restore(software, source, backupdir, prefix, extension):
    _module = software.replace("-","/").replace(".eb","")
    _software = software.replace("/","-")
    packages_dir = f"{backupdir}/kwame"
    tarball = f"{packages_dir}/{_software}.tar.{extension}"
    if os.path.isfile(tarball):
        logging.info(f"restore tarball {tarball}\nunder prefix {prefix}")
        total_bytes = os.stat(tarball).st_size
        with tarfile.open(tarball, f"r:{extension}") as tf:
            members = [member for member in tf.getmembers()]
            # for hidden module, we need to remove first dot on module mervsion!
            _module_ = "/".join([re.sub(r"^\.","",x) for x in _module.split("/")])
            basepath = "".join([member.name for member in members
                       if os.path.normpath(member.name).lower().endswith(_module_)
                       or member.name.endswith(_module_)])
            installpath = f"{prefix}/{basepath}"
            if basepath == '':
                clara_exit(f"Can't find module {_module} in tarball {tarball}")

            if os.path.isdir(installpath):
                message = f"Module {_module} already installed under {installpath}!"
                message = f"{message}\nDo you want to install it again!?!"
                _tmpname = next(tempfile._get_candidate_names())
                _prefix = f"{prefix}/{_tmpname}"
                _installpath = f"{_prefix}/{basepath}"
                os.mkdir(_prefix)
                if not force:
                    if not yes_or_no(message):
                        logging.error("Abort software {software} installation!")
                        return
            else:
                _installpath = None
                _prefix = prefix

            for member in members:
                # replace in lua file prefix by destination prefi_x
                if member.name.endswith(f"{_module}.lua"):
                    #tf.extract(member, _prefix)
                    _name = f"{_prefix}/{member.name}"
                    logging.info(f"working on file {_name} ...")
                    #replace_in_file(_name, source, prefix)
                elif member.name.endswith("requirements.txt"):
                    #tf.extract(member, _prefix)
                    _name = f"{_prefix}/{member.name}"
                    logging.info(f"working on file {_name} ...")
                    if os.path.isfile(_name):
                        with open(_name, 'r') as f:
                            for _software in [line.rstrip() for line in f]:
                                logging.info(f"restore  software {_software} ...")
                                _software = _software.replace("/","-")
                                restore(_software, source, backupdir, prefix, extension)
                else:
                    tf.extract(member, _prefix)

            return
            if os.path.isdir(installpath) and _installpath is not None:
                if os.path.isdir(_installpath):
                    backupdir = f"{prefix}/backups"
                    logging.info(f"backup previously installed in directory\n{_installpath} to {backupdir}!")
                    try:
                        if not os.path.isdir(backupdir):
                            os.mkdir(backupdir)
                        _backupdir = f"{backupdir}/{_module.split('/')[0]}"
                        if not os.path.isdir(_backupdir):
                            os.mkdir(_backupdir)
                        shutil.move(installpath, _backupdir)
                    except EnvironmentError:
                        logging.error("Unable to move previously installed directory")
                    else:
                        logging.info(f"moving temporary install directory {_installpath}\nto {installpath}!")
                        try:
                            shutil.move(_installpath, installpath)
                        except EnvironmentError:
                            logging.error(f"Fail to move temporary installed directory to target one!")
                        else:
                            logging.info(f"module {_module} successfully restored in {installpath}!")
                    finally:
                        if os.path.isdir(_installpath):
                            logging.info(f"remove temporary installed directory {_installpath}")
                            shutil.rmtree(_installpath)
                else:
                    logging.info(f"directory {_installpath} don't exist!")

    else:
        logging.warn(f"tarball {tarball} don't exist!")

def delete(software, prefix):
    _software, versions = module_versions(software, prefix)
    match = None
    if len(versions) == 0:
        clara_exit(f"No software {_software} installed!")
    elif len(versions) == 1:
        output, error = module(f"show {_software}")
        pattern = re.compile(r' (.*\.lua):| [/fs]?[\w]*(/.*\.lua):|EBROOT[^,]*,"([^"]*)"', re.DOTALL)
        match = pattern.findall(error)
        if match:
            message = f"Are you sure you want to remove software {_software},\nunder prefix {prefix} ?"
            if not yes_or_no(message):
                logging.error(f"You choose to no more removed software {_software}!")
                return
            logging.debug(f"delete software {versions[0]}")
            data = [i.strip() for x in match for i in ''.join(x).split('\n')]
            #_prefix = os.path.commonpath(data)
            for name in data:
                if name.endswith(".lua"):
                    logging.info(f"suppressing file {name}")
                    if os.path.isfile(name):
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
    width = int(dargs['--width'])
    rebuild = dargs['--rebuild']
    requirement_only = dargs['--requirement-only']
    extension = dargs['--extension']
    compresslevel = int(dargs['--compresslevel'])
    dereference = dargs['--dereference']

    homedir = os.environ["HOME"]

    # set default config file
    _path = os.path.abspath(f"{homedir}/.config/easybuild.ini")
    if conf.config is None and os.path.isfile(_path):
        conf.config = _path

    eb = dargs['--eb']
    eb = get_from_config_or("easybuild", "binary", default=eb)

    software = dargs['<software>']
    if software is not None:
        software = software.replace(".eb","")

    prefix = dargs['--prefix']
    # set default directory to install easybuild software
    # we have go with three ways to provide this prefix
    if prefix is None:
        if dargs['delete'] or dargs['restore']:
                prefix = '/software/shared/easybuild'
        else:
            prefix = f"{homedir}/.local/easybuild"
    prefix = get_from_config_or("easybuild", "prefix", default=prefix)

    # set default easybuild custom configs base directory
    # standfor for copy of easybuid config file from example repository:
    # https://github.com/easybuilders/easybuild-easyconfigs
    basedir = dargs['--basedir']
    if basedir is None:
        basedir = f'{homedir}/easybuild'
    basedir = get_from_config_or("easybuild", "basedir", default=basedir)
    _path = f"{basedir}/pre_fetch_hook.py"
    if not (os.path.isdir(basedir) and os.path.isfile(_path)):
        message = f"""\nyou must use either switch --basedir nor config file
Indeed, either base directory {basedir}
or file {_path} don't exist!
It's recommended to create your own config file with:
basedir=<your base dir here>
cat <<EOF>> ~/.config/easybuild.ini
basedir=$basedir
EOF
~/.config/easybuild.ini it's the default config file. So no need to use --config!
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
        backupdir = f"{prefix}/packages"
    backupdir = get_from_config_or("easybuild", "backupdir", default=backupdir)

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
    else:
        if shutil.which('eb'):
            eb = 'eb'
        else:
            clara_exit("no easybuild binary found in your path. PLS provide one with --eb switch")
    _path = shutil.which('python3')
    if _path:
        os.environ["EB_PYTHON"] = _path

    os.environ["PYTHONPATH"] = pythonpath

    if dargs['search']:
        search(software, basedir, width)
    elif dargs['show']:
        show(software, ["/software/shared/easybuild", f"{homedir}/.local/easybuild"])
    elif dargs['install']:
        install(software, prefix, basedir, rebuild, requirement_only)
    elif dargs['backup']:
        backup(software, prefix, backupdir, None, extension, compresslevel, dereference, force)
    elif dargs['restore']:
        restore(software, source, backupdir, prefix, extension)
    elif dargs['delete']:
        delete(software, prefix)

if __name__ == '__main__':
    main()
