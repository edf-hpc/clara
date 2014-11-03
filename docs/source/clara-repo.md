% clara-repo(1)

# NAME

clara-repo - creates, updates and synchronizes local Debian repositories

# SYNOPSIS

    clara repo key
    clara repo init [--dist=<name>]
    clara repo sync (all|<suite>...|--dist=<name>)
    clara repo add <file>... [--dist=<name>] [--reprepro-flags="list of flags"...]
    clara repo del <name>...[--dist=<name>]
    clara repo list [--dist=<name>]
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

        Create the initial configuration for reprepro for our local repository and makes
        the first export.

    clara repo sync (all|<suite>...|--dist=<name>)

        Mirror locally a Debian suite. We can choose a single suite such as wheezy,
        wheezy-backports, calibre8, etc; we can choose all the suites with the parameter
        'all' or just all the suites used by a distribution with --dist=<name>.

    clara repo add <file>... [--dist=<name>] [--reprepro-flags="list of flags"...]

        Add packages to the local repository.
        <file> can be one or more *.deb binaries, *.changes files or *.dsc files.
        For the --reprepro-flags, check the documentation of reprepro.

    clara repo del <name>...[--dist=<name>]

        Remove package to the local repository.
        <name> is the package to remove, if the package is a source name, it'll also
        remove all the associated binaries.

    clara repo list [--dist=<name>]

        Lists all contents of the repository.

The option [--dist=<name>] allows to select a distribution different to the default one.
This distribution must be listed in the field "allowed_distributions" from the section [common].

# EXAMPLES

To mirror locally Debian backports for Wheezy:

    clara repo sync wheezy-backports

To create a local repository and add packages to it:

    clara repo key
    clara repo init
    clara repo add mypackage_1-2.dsc

# SEE ALSO

clara(1), clara-images(1), clara-ipmi(1), clara-p2p(1), clara-slurm(1), clara-enc(1)
