% clara-easybuild(1)

# NAME

clara-easybuild - Manage package installation via easybuild

# SYNOPSIS

    clara easybuild install <software> [--force] [--rebuild] [--skip] [--inject-checksums] [--url=<url>] [options]
    clara easybuild backup  <software> [--force] [--backupdir=<backupdir>] [--yes-i-really-really-mean-it] [--elapse <elapse>] [options]
    clara easybuild restore <software> [--force] [--backupdir=<backupdir>] [--source=<source>] [--yes-i-really-really-mean-it] [--devel] [options]
    clara easybuild delete  <software> [--force] [options]
    clara easybuild search  <software> [--force] [--width=<width>] [options]
    clara easybuild show    <software> [options]
    clara easybuild hide    <software> [options]
    clara easybuild fetch   <software> [--inject-checksums] [options]
    clara easybuild default <software> [options]
    clara easybuild copy    <software> [<target>] [options]
    clara easybuild -h | --help | help

Options:
    <software>                       software name, either like <name>-<version> or <name>/<version>
    --eb=<ebpath>                    easybuild binary path
    --basedir=<basedir>              easybuild custom repository directory
    --prefix=<prefix>                easybuild installation prefix directory
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
    --skip                           Installing additional extensions when combined with --rebuild
    --elapse <elapse>                Elapse time en seconds after which backup file can be regenerated [default: 300]

# DESCRIPTION

*clara easybuild* is a wrapper arround easybuild. It's provide a way to install software\
with easybuild, backup this software, and all it's neefull dependencies, as tar archive.\
This tar archive can be used to installation on another cluster!

# OPTIONS

    clara easybuild show <software> [options]

        Show easybuild software <software> infomartion

    clara easybuild search <software> [--width=<width>] [options]

        Search and retrieve all software retated to <software>
        print <width> characters per line

    clara easybuild delete  <software> [--force] [options]

        Delete easybuild software <software>.
        Use --force for unattended deletion.

    clara easybuild fetch <software> [options]

        Fetch easybuild software <software>

    clara easybuild install <software> [--force] [--rebuild] [--skip] [--inject-checksums] [--url=<url>] [options]

        Install easybuild software <software> under <prefix> directory.
        Use --rebuild to force re-installation.
        Use --yes-i-really-really-mean-it to force dependencies re-installation too!
        Use --force for unattended re-installation.
        Use --skip for extensions only installation (for Python, Perl).
        Use --inject-checksums to inject sources/patches checksums into easyconfig file(s)
        Use --url to locally fetch source archive files. Needful for switch --hook

    clara easybuild backup  <software> [--force] [--backupdir=<backupdir>] [--yes-i-really-really-mean-it] [--elapse <elapse>] [options]

        Backup easybuild software <software> under <prefix> directory to target <backupdir>.
        Use --backupdir for backup archive destination.
        Use --yes-i-really-really-mean-it to force dependencies backup too!
        Use --force for unattended software re-installation.
        Use --elapse to delay after which backup file can be regenerated

    clara easybuild restore <software> [--force] [--backupdir=<backupdir>] [--source=<source>] [--yes-i-really-really-mean-it] [--devel] [options]

        Restore easybuild software <software> under <prefix> directory, from <backupdir>.
        Use --backupdir for backup archive destination.
        Use --source to specify backup <prefix>. Default is <prefix>.
        Use --yes-i-really-really-mean-it to force dependencies restore too!
        Use --force for unattended existent installed software restore.
        Use --devel to restore easybuild develop module files. Default is not to restore.

    clara easybuild hide <software> [options]

        Hide easybuild software <software>

    clara easybuild default <software> [options]

        Set easybuild software <software> as default

    clara easybuild copy    <software> [<target>] [options]

        Copy easybuild software <software> to <target> name, under <basedir>.

Easybuild software <software> must follow either <name>-<version> or <name>/<version>\
name scheme. <version> is optional and trailing ".eb" suffix can be optionally added.

# EXAMPLES

To show software HelloWorld module information

    clara easybuild show HelloWorld
    clara easybuild show HelloWorld/0.0.1

```
--------------------------------------------- ~/.local/easybuild/modules/tools ---------------------------------------------
   HelloWorld/0.0.1 (D)

--------------------------------------------- ~/.local/easybuild/modules/base ----------------------------------------------
   HelloWorld/0.0.1

  Où:
   D:  Default Module

Utilisez "module spider" pour trouver tous les modules possibles.
Utilisez "module keyword key1 key2 ..." pour chercher tous les modules possibles qui correspondent à l'une des clés (key1, key2).
```

To search all easyconfigs file related to software HelloWorld

    clara easybuild search HelloWorld/0.0.1

```
+---------------------------------------------------+
| easyconfig files                                  |
+---------------------------------------------------+
| ~/repository/edf-easybuild/o/OpenMPI |
+---------------------------------------------------+
| openmpi-5.0.5.eb                                  |
+---------------------------------------------------+
```

    clara easybuild search openmpi-4.1.5

```
+---------------------------------------------------------------------------------------------------+
| easyconfig files                                                                                  |
+---------------------------------------------------------------------------------------------------+
| ~/repository/edf-easybuild/o/OpenMPI                                                 |
+---------------------------------------------------------------------------------------------------+
| openmpi-4.1.5.eb                                                                                  |
+---------------------------------------------------------------------------------------------------+
| ~/.local/easybuild/software/EasyBuild/4.9.2/easybuild/easyconfigs/o/OpenMPI          |
+---------------------------------------------------------------------------------------------------+
| OpenMPI-4.1.5-GCC-12.2.0.eb OpenMPI-4.1.5-GCC-12.3.0.eb OpenMPI-4.1.5-intel-compilers-2023.1.0.eb |
+---------------------------------------------------------------------------------------------------+
```

To delete easybuild software HelloWorld

    clara easybuild delete HelloWorld/0.0.1
    clara easybuild delete HelloWorld/0.0.1 --force

To install easybuild software HelloWorld

    clara easybuild install HelloWorld/0.0.1
    clara easybuild install HelloWorld/0.0.1 --force
    clara easybuild install HelloWorld/0.0.1 --force --skip
    clara easybuild install HelloWorld/0.0.1 --rebuild
    clara easybuild install HelloWorld/0.0.1 --yes-i-really-really-mean-it
    clara easybuild install HelloWorld/0.0.1 --yes-i-really-really-mean-it --force
    clara easybuild install HelloWorld/0.0.1 --inject-checksums

To backup easybuild software HelloWorld

    clara easybuild backup HelloWorld/0.0.1
    clara easybuild backup HelloWorld/0.0.1 --backupdir /tmp
    clara easybuild backup HelloWorld/0.0.1 --force
    clara easybuild backup HelloWorld/0.0.1 --elaspe 20
    clara easybuild backup HelloWorld/0.0.1 --yes-i-really-really-mean-it
    clara easybuild backup HelloWorld/0.0.1 --yes-i-really-really-mean-it --force

To restore easybuild software HelloWorld

    clara easybuild restore HelloWorld/0.0.1
    clara easybuild restore HelloWorld/0.0.1 --backupdir /tmp
    clara easybuild restore HelloWorld/0.0.1 --force
    clara easybuild retsore HelloWorld/0.0.1 --yes-i-really-really-mean-it
    clara easybuild retsore HelloWorld/0.0.1 --yes-i-really-really-mean-it --force
    clara easybuild restore HelloWorld/0.0.1 --devel
    clara easybuild restore HelloWorld/0.0.1 --source $HOME/.local/easybuild

To hide easybuild software HelloWorld

    clara easybuild hide HelloWorld/0.0.1

To fetch easybuild software HelloWorld

    clara easybuild fetch HelloWorld/0.0.1

To default easybuild software HelloWorld

    clara easybuild default HelloWorld/0.0.1

To copy easybuild software HelloWorld

    clara easybuild copy HelloWorld-0.0.1.eb
    clara easybuild copy HelloWorld-0.0.1.eb HelloWorld-0.0.2.eb
    clara easybuild copy HelloWorld-0.0.1.eb /tmp



# SEE ALSO

clara(1), clara-images(1), clara-ipmi(1), clara-p2p(1), clara-slurm(1), clara-enc(1), clara-build(1), clara-virt(1), clara-chroot(1), clara-redfish(1), clara-easybuild(1)
