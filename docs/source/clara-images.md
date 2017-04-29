% clara-images(1)

# NAME

clara-images - creates and updates the images of installation of a cluster

# SYNOPSIS

    clara images create [--no-sync] <dist> [<image>] [--keep-chroot-dir]
    clara images unpack ( <dist> | --image=<path> )
    clara images repack <directory> ( <dist> | --image=<path> )
    clara images edit <dist> [<image>]
    clara images initrd [--no-sync] <dist> [--output=<dirpath>]
    clara images -h | --help | help

Options:

    --image=<path>  Path to squashfs image.

# DESCRIPTION

*clara images* makes easy to create and update the images to boot the nodes of a cluster.

# OPTIONS

    clara images create [--no-sync] <dist> [<image>] [--keep-chroot-dir]

        Create a new squashfs image to use as operating system on the cluster nodes.
        By default it unpacks the default image but the user can provide the path to a
        different file.
        The option --keep-chroot-dir allows to create the chroot used to generate
        the image. By default, this chroot directory is deleted.
        The user can choose to not sync files over the network with --no-sync.

    clara images unpack ( <dist> | --image=<path> )

        Unpack the squashfs file. By default it unpacks the default image but the user can
        provide the path to a different file.

    clara images repack <directory> ( <dist> | --image=<path> )

        Repack the squashfs file providing the image.  By default it repacks and replace
        the default image but the user can choose to provide a path to save it with a different
        name.

    clara images edit <dist> [<image>]

        Unpacks the image for editing, spawns a bash to make the changes and repacks
        the image again after. By default it edits the default image but the user can
        provide the path to a different image.

    clara images initrd [--no-sync] <dist> [--output=<dirpath>]

        Create a new initrd image to boot the cluster nodes.
        The user can use the --output option to select a directory different to the default
        one to save the generated initrd.
        The user can choose to not sync files over the network with --no-sync.

This distribution in <dist> must be listed in the field "allowed_distributions" from the section [common].

# EXAMPLES

To create a image for calibre8 and store it in /tmp/c8.squashfs

    clara images create calibre8 /tmp/c8.squashfs

To edit the image

    clara images edit calibre8

To create a initrd for the default distribution image:

     clara images initrd calibre8

# SEE ALSO

clara(1), clara-ipmi(1), clara-p2p(1), clara-repo(1), clara-slurm(1), clara-enc(1), clara-build(1), clara-virt(1), clara-chroot(1)
