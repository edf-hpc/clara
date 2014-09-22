% clara-repo(1)

# NAME

clara-repo - creates, updates and synchronizes local Debian repositories

# SYNOPSIS

    clara repo key
    clara repo init [--dist=<name>]
    clara repo sync [create] [--dist=<name>]
    clara repo add <file>... [--dist=<name>]
    clara repo del <name>...[--dist=<name>]
    clara repo -h | --help | help

Options:

    --dist=<name>  Distribution target [default is set on distribution field
                   at the file config.ini].

    <file> can be one or more *.deb binaries, *.changes files or *.dsc files.

    <name> is the package to remove, if the package is a source name, it'll

    remove all the associated binaries

# DESCRIPTION

*clara repo* offers simple commands to create a local Debian repository with reprepro and
update, add and remove files from them. It also provides the possibility of making mirror
of remote Debian repositories locally.

# OPTIONS

    clara repo key

        Install the secret GPG key to use in the repository.

    clara repo init [--dist=<name>]

        Create the initial configuration for reprepro for our local repository and makes the first export.

    clara repo sync [create] [--dist=<name>]

        Synchronize all the local Debian repositories with the canonical repositories.
        If it's the first time we're syncing, we need to add the option [create] to also create the repository locally.

    clara repo add <file>... [--dist=<name>]

        Add packages to the local repository.
        <file> can be one or more *.deb binaries, *.changes files or *.dsc files.

    clara repo del <name>...[--dist=<name>]

        Remove package to the local repository.
        <name> is the package to remove, if the package is a source name, it'll remove all the associated binaries.



The option [--dist=<name>] allows to select a distribution different to the default one.
This distribution must be listed in the field "distributions" from the section [common].

# EXAMPLES

TODO

# SEE ALSO

clara(1), clara-images(1), clara-nodes(1), clara-p2p(1), clara-slurm(1)
