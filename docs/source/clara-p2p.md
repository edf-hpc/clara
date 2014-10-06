% clara-p2p(1)

# NAME

clara-p2p - makes torrent images and seeds them via BitTorrent

# SYNOPSIS

    clara p2p status
    clara p2p restart
    clara p2p mktorrent [--image=<path>]
    clara p2p -h | --help | help

# DESCRIPTION

*clara p2p* eases creating torrent files for the cluster installation images
and controlling the seeders and trackers of the cluster to see the new torrent file.

# OPTIONS

    clara p2p status

        Check the status of the BitTorrent trackers and seeders

    clara p2p restart

        Restart the BitTorrent trackers and seeders

    clara p2p mktorrent [--image=<path>]

        Create a new torrent file for the squashfs image and restart trackers and initial seeders.

# EXAMPLE

TODO

# SEE ALSO

clara(1), clara-images(1), clara-ipmi(1), clara-repo(1), clara-slurm(1), clara-enc(1)
