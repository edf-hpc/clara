% clara-chroot(1)

# NAME

clara-chroot - creates and updates a chroot

# SYNOPSIS

    clara chroot create <dist> [<chroot_dir>] [--keep-chroot-dir]
    clara chroot edit <dist> [<chroot_dir>]
    clara chroot install <dist> [<packages>]
    clara chroot remove <dist> [<packages>]
    clara chroot reconfig <dist>
    clara chroot -h | --help | help

# DESCRIPTION

*clara chroot* makes easy to create and update a chroot directory.

# OPTIONS

    clara chroot create <dist> [<chroot_dir>] [--keep-chroot-dir]

        Create a new directory with a chroot system.
        By default, it will use the directory indicated as 'trg_dir'
        in the configuration file.

    clara chroot edit <dist> [<chroot_dir>]

        Spawn a bash into the chroot directory to make the changes.
        By default, it will use the directory indicated as 'trg_dir'
        in the configuration file.

    clara chroot install <dist> [<packages>]

        Install the packages indicated into chroot directory. Packages names
        must be separated by ','.

    clara chroot remove <dist> [<packages>]

        Remove the packages indicated from chroot directory. Packages names
        must be separated by ','.

    clara chroot reconfig <dist>

        Reinstall configuration file on an existing chroot, it would update
        apt configuration as an example of use


This distribution in <dist> must be listed in the field "allowed_distributions" from the section [common].

# EXAMPLES

To create a image for calibre8

    clara chroot create calibre8

To edit the chroot

    clara chroot edit calibre8

# SEE ALSO

clara(1), clara-ipmi(1), clara-p2p(1), clara-repo(1), clara-slurm(1), clara-enc(1), clara-build(1), clara-virt(1), clara-images(1), clara-redfish(1)
