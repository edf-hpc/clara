% clara-images(1)

# NAME

clara-images - creates and updates the images of installation of a cluster

# SYNOPSIS

    clara images genimg [--dist=<name>]
    clara images (unpack|repack <directory>) [--dist=<name>]
    clara images editimg [<image>] [--dist=<name>]
    clara images initrd [--dist=<name>]
    clara images -h | --help | help

Options:

    --image=<path>  Path to squashfs image.

# DESCRIPTION

*clara images* makes easy to create and update the images to boot the nodes of a cluster.

# OPTIONS

    clara images genimg [--dist=<name>]

        Create a new squashfs image to use as operating system on the cluster nodes, it will also create a new torrent file and start seeding it.

    clara images (unpack|repack <directory>) [--dist=<name>]

        Unpack and repack the squashfs file providing the image.

    clara images editimg [<image>] [--dist=<name>]

        Unpacks the image for editing, spawns a bash to make the changes and repacks the image again after.

    clara images initrd [--dist=<name>]

        Create a new initrd image to boot the cluster nodes.

The option [--dist=<name>] allows to select a distribution different to the default one.
This distribution must be listed in the field "distributions" from the section [common].

# EXAMPLES

TODO

# SEE ALSO

clara(1), clara-nodes(1), clara-p2p(1), clara-repo(1), clara-slurm(1)
