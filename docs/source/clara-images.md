% clara-images(1)

# NAME

clara-images - creates and updates the images of installation of a cluster

# SYNOPSIS

    clara images create [<image>] [--dist=<name>]
    clara images unpack [<image>] [--dist=<name>]
    clara images repack <directory> [<image>] [--dist=<name>]
    clara images edit [<image>] [--dist=<name>]
    clara images initrd [--dist=<name>]
    clara images -h | --help | help

Options:

    --image=<path>  Path to squashfs image.

# DESCRIPTION

*clara images* makes easy to create and update the images to boot the nodes of a cluster.

# OPTIONS

    clara images create [<image>] [--dist=<name>]

        Create a new squashfs image to use as operating system on the cluster nodes.
        By default it unpacks the default image but the user can provide  the path to a
        different file.

    clara images unpack [<image>] [--dist=<name>]

        Unpack the squashfs file. By default it unpacks the default image but the user can
        provide the path to a different file.

    clara images repack <directory> [<image>] [--dist=<name>]

        Repack the squashfs file providing the image.  By default it repacks and replace
        the default image but the user can choose to provide a path to save it with a different
        name.

    clara images edit [<image>] [--dist=<name>]

        Unpacks the image for editing, spawns a bash to make the changes and repacks
        the image again after. By default it edits the default image but the user can
        provide the path to a different image.

    clara images initrd [--dist=<name>]

        Create a new initrd image to boot the cluster nodes.

The option [--dist=<name>] allows to select a distribution different to the default one.
This distribution must be listed in the field "allowed_distributions" from the section [common].

# EXAMPLES

TODO

# SEE ALSO

clara(1), clara-ipmi(1), clara-p2p(1), clara-repo(1), clara-slurm(1), clara-enc(1)
