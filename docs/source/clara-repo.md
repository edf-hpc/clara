% clara-repo(1)

# NAME

clara-repo - creates, updates and synchronizes local Debian or RedHat like repositories

# SYNOPSIS

    clara repo key
    clara repo init <dist>
    clara repo sync (all|<dist> [<suites>...])
    clara repo push [<dist>]
    clara repo add <dist> <file>... [--reprepro-flags="list of flags"...] [--no-push]
    clara repo del <dist> <name>... [--no-push]
    clara repo search <keyword> [rpm|deb]
    clara repo list (all|rpm|deb|<dist>)
    clara repo copy <dist> <package> <from-dist> [--no-push]
    clara repo move <dist> <package> <from-dist> [--no-push]
    clara repo jenkins (list|<dist>) <job> [--source=<arch>] [--reprepro-flags="list of flags"...] [--build=<build>]
    clara repo -h | --help | help

Options:

    <file> can be one or more *.(deb|rpm) binaries, *.changes files or *.dsc files.

    <name> is the package to remove, if the package is a source name, it'll
    remove all the associated binaries

# DESCRIPTION

*clara repo* offers simple commands to create a local Debian or RedHat like repository\
with reprepro or repoquery and update, add and remove files from them. It also provides\
the possibility of making mirror of remote Debian repositories locally.

# OPTIONS

    clara repo key

        Install the secret GPG key to use in the repository.

    clara repo init <dist>

        Create the initial configuration with reprepro or repoquery
        for our local repository and makes the first export.

    clara repo sync (all|<dist> [<suites>...])

        Mirror locally a Debian suite. We can choose a single suite such as wheezy,
        wheezy-backports, calibre8, etc; we can choose all the suites with the parameter
        'all' or just all the suites used by a distribution.

    clara repo add <dist> <file>... [--reprepro-flags="list of flags"...]

        Add packages to the local repository.
        <file> can be one or more *.(deb|rpm) binaries, *.changes files or *.dsc files.
        For the --reprepro-flags, check the documentation of reprepro.

    clara repo del <dist> <name>...

        Remove package to the local repository.
        <name> is the package to remove, if the package is a source name, it'll also
        remove all the associated binaries.

    clara repo list (all|rpm|deb|<dist>)

        Lists all the contents of every repository with the argument "all", or only
        rpm repository, or deb one, or only the content of a given distribution.

    clara repo search <keyword> [rpm|deb]

        Search for the name of a given package in every repository controlled by clara.

    clara repo copy <dist> <package> <from-dist>

        Copy to the given distribution a package from another distribution.
        Note that both repositories must be handled by clara.

    clara repo move <dist> <package> <from-dist>

        Copy to the given distribution a package from another distribution
        and remove the package from the origin repository.
        Note that both repositories must be handled by clara.

    clara repo jenkins (list|<dist>) <job> [--source=<arch>] [--reprepro-flags="list of flags"...] [--build=<build>]

        List or copy package from specify jenkins provided job name and distribution.

This distribution in <dist> must be listed in the field "allowed_distributions" from the section [common].

Underline Linux distribution is retrieve from <dist> name:

- if <dist> start with *scibian* or *calibre*, is associated to Debian
- else Redhat-like, if its start with *rhel*, *rocky*, *almalinux*, *centos*

Arbitrar <dist> name can been also provided, but needfull <distro> key must be set in config file,\
in *repo* section.

# EXAMPLES

To mirror locally all the suites from calibre8:

    clara repo sync calibre8

To mirror locally Debian backports for Wheezy:

    clara repo sync calibre8 wheezy-backports

To create a local repository and add packages to it:

    clara repo key
    clara repo init calibre8
    clara repo init rocky8
    clara repo init almalinux9
    clara repo add calibre8 mypackage_1-2.dsc
    clara repo add rocky8 mypackage_1-2.rpm

To search a specific package in a local repository:

    clara repo search clara

```
+----------------------+-----------------------+------------+---------------------+
| Packages             |               Version | Repository | Archs               |
+----------------------+-----------------------+------------+---------------------+
| clara                |      0.20231201-3.el8 | rhel8      | x86_64              |
| clara-plugin-build   |      0.20231201-3.el8 | rhel8      | x86_64              |
| clara-plugin-chroot  |      0.20231201-3.el8 | rhel8      | x86_64              |
| clara-plugin-enc     |      0.20231201-3.el8 | rhel8      | x86_64              |
| clara-plugin-images  |      0.20231201-3.el8 | rhel8      | x86_64              |
| clara-plugin-ipmi    |      0.20231201-3.el8 | rhel8      | x86_64              |
| clara-plugin-p2p     |      0.20231201-3.el8 | rhel8      | x86_64              |
| clara-plugin-redfish |      0.20231201-3.el8 | rhel8      | x86_64              |
| clara-plugin-repo    |      0.20231201-3.el8 | rhel8      | x86_64              |
| clara-plugin-show    |      0.20231201-3.el8 | rhel8      | x86_64              |
| clara-plugin-slurm   |      0.20231201-3.el8 | rhel8      | x86_64              |
| clara-plugin-virt    |      0.20231201-3.el8 | rhel8      | x86_64              |
| clara                |   0.20231201-0sci10u1 | scibian10  | amd64, i386, source |
+----------------------+-----------------------+------------+---------------------+
```

To list known jenkins jobs:

    clara repo jenkins list

```
+---------------------------------+-----------------------+---------------------+----------------------------------------------+
| Job                             | Path                  |        Build        | Package                                      |
+---------------------------------+-----------------------+---------------------+----------------------------------------------+
| hpc-config-binaries             | builds                | lastSuccessfulBuild | hpc-config-apply_2.0.3-0sci8u1_all.deb       |
|                                 |                       |                     | hpc-config-push_2.0.3-0sci8u1_all.deb        |
|                                 |                       |                     | hpc-config_2.0.3-0sci8u1.debian.tar.xz       |
|                                 |                       |                     | hpc-config_2.0.3-0sci8u1.dsc                 |
|                                 |                       |                     | hpc-config_2.0.3-0sci8u1_amd64.changes       |
|                                 |                       |                     | hpc-config_2.0.3-0sci8u1_source.changes      |
|                                 |                       |                     | hpc-config_2.0.3.orig.tar.gz                 |
|                                 |                       |                     | lintian.txt                                  |
+---------------------------------+-----------------------+---------------------+----------------------------------------------+
| hpc-config-rpm-7-sourcerpm      | builds                | lastSuccessfulBuild | hpc-config-2.0.5-2.src.rpm                   |
+---------------------------------+-----------------------+---------------------+----------------------------------------------+
| hpc-config-rpm-8-binariesrpm    | configurations/builds | lastSuccessfulBuild | hpc-config-3.1.1-5.el8.edf.src.rpm           |
|                                 |                       |                     | hpc-config-apply-3.1.1-5.el8.edf.x86_64.rpm  |
|                                 |                       |                     | hpc-config-common-3.1.1-5.el8.edf.x86_64.rpm |
|                                 |                       |                     | hpc-config-push-3.1.1-5.el8.edf.x86_64.rpm   |
+---------------------------------+-----------------------+---------------------+----------------------------------------------+
| hpc-config-rpm-8-sourcerpm      | builds                | lastSuccessfulBuild | hpc-config-3.1.1-5.edf.src.rpm               |
+---------------------------------+-----------------------+---------------------+----------------------------------------------+
| hpc-config-source               | builds                | lastSuccessfulBuild | hpc-config_2.0.3-0sci8u1.debian.tar.xz       |
|                                 |                       |                     | hpc-config_2.0.3-0sci8u1.dsc                 |
|                                 |                       |                     | hpc-config_2.0.3-0sci8u1_source.changes      |
|                                 |                       |                     | hpc-config_2.0.3.orig.tar.gz                 |
|                                 |                       |                     | lintian.txt                                  |
+---------------------------------+-----------------------+---------------------+----------------------------------------------+
| hpc-config-upstream-binariesrpm | configurations/builds | lastSuccessfulBuild | hpc-config-1.1.6-1.el7.src.rpm               |
|                                 |                       |                     | hpc-config-apply-1.1.6-1.el7.x86_64.rpm      |
|                                 |                       |                     | hpc-config-debuginfo-1.1.6-1.el7.x86_64.rpm  |
+---------------------------------+-----------------------+---------------------+----------------------------------------------+
| hpc-config-upstream-sourcerpm   | builds                | lastSuccessfulBuild | hpc-config-1.1.6-1.src.rpm                   |
+---------------------------------+-----------------------+---------------------+----------------------------------------------+
```

To copy all package from jenkins job:

    clara repo jenkins scibian8 hpc-config-binaries


# SEE ALSO

clara(1), clara-images(1), clara-ipmi(1), clara-p2p(1), clara-slurm(1), clara-enc(1), clara-build(1), clara-virt(1), clara-chroot(1)
