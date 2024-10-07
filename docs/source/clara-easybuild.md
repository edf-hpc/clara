% clara-easybuild(1)

# NAME

clara-easybuild - Manage package installation via easybuild

# SYNOPSIS

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

    clara easybuild delete <software> [options]

        Delete easybuild software <software>

    clara easybuild install <software> [--force] [--rebuild] [options]

        Add packages to the local easybuildsitory.
        <file> can be one or more *.(deb|rpm) binaries, *.changes files or *.dsc files.
        For the --reprepro-flags, check the documentation of reprepro.

    clara easybuild backup  <software> [--force] [--backupdir=<backupdir>] [options]

        Remove package to the local easybuildsitory.
        <name> is the package to remove, if the package is a source name, it'll also
        remove all the associated binaries.

    clara easybuild restore <software> [--force] [--source=<source>] [options]

        Lists all the contents of every easybuildsitory with the argument "all", or only
        rpm easybuildsitory, or deb one, or only the content of a given distribution.

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

To install easybuild software HelloWorld

    clara easybuild install HelloWorld/0.0.1

To backup easybuild software HelloWorld

    clara easybuild backup HelloWorld/0.0.1

To restore easybuild software HelloWorld

    clara easybuild restore HelloWorld/0.0.1


# SEE ALSO

clara(1), clara-images(1), clara-ipmi(1), clara-p2p(1), clara-slurm(1), clara-enc(1), clara-build(1), clara-virt(1), clara-chroot(1), clara-redfish(1), clara-easybuild(1)
