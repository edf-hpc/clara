% clara-build (1)

# NAME

clara-build - builds Debian packages

# SYNOPSIS

    clara build source <dist> <dsc_file>
    clara build repo <dist> <origin_dist> <package_name>
    clara build -h | --help | help


# DESCRIPTION

*clara build* allows one to build packages for any of the custom distributions
and also rebuild a package that's already in the local repository of another
custom distribution.
This plugin requires *cowbuilder* installed and configured.

# OPTIONS

    clara build source <dist> <dsc_file> 

        Build a source package targetting the distro indicated.

    clara build repo <dist> <origin_dist> <package_name>

        Rebuilds a package from the local repository of the "origin_dist"
        for the distro indicated. The repository must contain the source package
        of the package we want to rebuild.


# EXAMPLES

To build the source package of calibre-hpc for calibre8 that is at /tmp/calibre-hpc_1.2.dsc

    clara build calibre8 /tmp/calibre-hpc_1.2.dsc

To rebuild the same package for calibre9 using the package in the local repository
of calibre8:

    clara build calibre8 calibre9 calibre-hpc


# SEE ALSO

clara(1), clara-images(1), clara-ipmi(1), clara-repo(1), clara-slurm(1), clara-enc(1), clara-p2p(1), clara-virt(1), clara-chroot(1)
