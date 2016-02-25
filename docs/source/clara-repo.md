% clara-repo(1)

# NAME

clara-repo - creates, updates and synchronizes local Debian repositories

# SYNOPSIS

    clara repo key
    clara repo init <dist>
    clara repo sync (all|<dist> [<suites>...])
    clara repo add <dist> <file>... [--reprepro-flags="list of flags"...]
    clara repo del <dist> <name>...
    clara repo list (all|<dist>)
    clara repo search <keyword>
    clara repo copy <dist> <package> <from-dist>
    clara repo -h | --help | help

Options:

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

    clara repo init <dist>

        Create the initial configuration for reprepro for our local repository and makes
        the first export.

    clara repo sync (all|<dist> [<suites>...])

        Mirror locally a Debian suite. We can choose a single suite such as wheezy,
        wheezy-backports, calibre8, etc; we can choose all the suites with the parameter
        'all' or just all the suites used by a distribution.

    clara repo add <dist> <file>... [--reprepro-flags="list of flags"...]

        Add packages to the local repository.
        <file> can be one or more *.deb binaries, *.changes files or *.dsc files.
        For the --reprepro-flags, check the documentation of reprepro.

    clara repo del <dist> <name>...

        Remove package to the local repository.
        <name> is the package to remove, if the package is a source name, it'll also
        remove all the associated binaries.

    clara repo list (all|<dist>)

        Lists all the contents of every repository with the argument "all"
        or only the conrent of a given distribution.

    clara repo search <keyword>

        Search for the name of a given package in every repository controlled by clara.

    clara repo copy <dist> <package> <from-dist>

        Copy to the given distribution a package from another distribution.
        Note that both repositories must be handled by clara.

This distribution in <dist> must be listed in the field "allowed_distributions" from the section [common].

# EXAMPLES

To mirror locally all the suites from calibre8:

    clara repo sync calibre8

To mirror locally Debian backports for Wheezy:

    clara repo sync calibre8 wheezy-backports

To create a local repository and add packages to it:

    clara repo key
    clara repo init calibre8
    clara repo add calibre8 mypackage_1-2.dsc

# SEE ALSO

clara(1), clara-images(1), clara-ipmi(1), clara-p2p(1), clara-slurm(1), clara-enc(1), clara-build(1)
