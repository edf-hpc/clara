% clara-p2p(1)

# NAME

clara-p2p - makes torrent images and seeds them via BitTorrent

# SYNOPSIS

    clara p2p status
    clara p2p restart
    clara p2p mktorrent <dist> [--image=<path>]
    clara p2p -h | --help | help

# DESCRIPTION

*clara p2p* eases creating torrent files for the cluster installation images
and controlling the seeders and trackers of the cluster to see the new torrent file.

# OPTIONS

    clara p2p status

        Check the status of the BitTorrent trackers and seeders

    clara p2p restart

        Restart the BitTorrent trackers and seeders

    clara p2p mktorrent <dist> [--image=<path>]

        Create a new torrent file for the squashfs image and restart trackers 
        and initial seeders. The distribution in <dist> must be listed in the
        field "allowed_distributions" from the section [common]

# EXAMPLES

To create a torrent file for the images placed at /tmp/calibre9.squashfs

    clara p2p mktorrent calibre9 --image=/tmp/calibre9.squashfs

# SEE ALSO

clara(1), clara-images(1), clara-ipmi(1), clara-repo(1), clara-slurm(1), clara-enc(1), clara-build(1), clara-virt(1), clara-chroot(1)
