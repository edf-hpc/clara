% clara(1)

# NAME

clara -  set of cluster administration tools

# SYNOPSIS

    clara [-d | -dd] [options] <plugin> [<args>...]
    clara help <plugin>
    clara [--version]
    clara [--help]

Options:

	-d			Enable debug output
	-dd 			Enable debug output for third party applications
	--config=<file>		Provide a configuration file

# DESCRIPTION

clara is a set of cluster administration tools. The different tools are written
as plugins that can be added or removed independently.

# OPTIONS

Clara provides the following plugins:

    repo     Creates, updates and synchronizes local Debian repositories.
    ipmi     Manages and get the status from the nodes of a cluster.
    slurm    Performs tasks using SLURM's controller.
    images   Creates and updates the images of installation of a cluster.
    p2p      Makes torrent images and seeds them via BitTorrent.
    enc      Interact with encrypted files using configurable methods.
    build    Builds Debian packages.

# SEE ALSO

clara-images(1), clara-ipmi(1), clara-p2p(1), clara-repo(1), clara-slurm(1), clara-enc(1), clara-build(1)
