% Clara User's Guide
% Ana Guerrero Lopez
% March 2, 2014

# What's Clara?

Clara is a set of cluster administration tools created to help in the
installation and maintenance of clusters at EDF.

The different tools are written as independent plugins that can be added,
removed and modified independently.

Clara is distributed under the CeCILL-C Free Software License Agreement version
1.0. You can find more information about the CeCILL licenses at
[http://www.cecill.info/index.en.html](http://www.cecill.info/index.en.html).


# Obtaining, building and installing Clara

Clara's code is available at GitHub [https://github.com/edf-hpc/clara](https://github.com/edf-hpc/clara).
You can obtain a copy using *git*:

    $ git clone https://github.com/edf-hpc/clara.git

Clara is developed and probably only useful in a Debian or a Debian derivative
system. The debian packaging files are included, so you only need to build
a Debian package and install it.
Before building the package, you will need to install the following packages:

    # apt-get install debhelper python-all python-setuptools pandoc bash-completion dpkg-dev

And then from the root directory of your git copy, you can run:

    # dpkg-buildpackage

This will create a package you can install with dpkg.

If you're not using Debian, Clara provides a setuptools script for its installation.
Just run:

    # python setup.py install

If you chose to install manually, you also will need to install the runtime
dependencies. The dependencies common to all plugins are:
[python](http://www.python.org), [docopt](http://docopt.org/) and [clustershell](http://cea-hpc.github.io/clustershell/).

The remaining dependencies, listed by plugin, are:

+ slurm: [slurm-client](http://slurm.schedmd.com/)

+ repo: [reprepro](http://mirrorer.alioth.debian.org/), [gnupg](https://www.gnupg.org/), [debmirror](https://packages.debian.org/sid/debmirror)

+ impi: [fping](http://fping.org/), [ipmitool](http://sourceforge.net/projects/ipmitool/)

+ images: [debootstrap](https://packages.debian.org/sid/debootstrap), [squashfs-tools](http://squashfs.sourceforge.net/)

+ p2p: [mktorrent](http://mktorrent.sourceforge.net/)

+ build: [cowbuilder](https://wiki.debian.org/cowbuilder)

# Getting started

Clara itself is not a tool, but rather provides a common interface to several
tools. To see the list of available tools, just type `clara` like in the following
example.

    # clara

    Usage: clara [options] <plugin> [<args>...]
           clara help <plugin>
           clara [--version]
           clara [--help]

    Options:
        -d                 Enable debug output
        --config=<file>    Provide a configuration file

    Clara provides the following plugins:
       repo     Creates, updates and synchronizes local Debian repositories.
       ipmi     Manages and get the status from the nodes of a cluster.
       slurm    Performs tasks using SLURM's controller.
       images   Creates and updates the images of installation of a cluster.
       p2p      Makes torrent images and seeds them via BitTorrent.
       enc      Interact with encrypted files using configurable methods
       build    Builds Debian packages

    See 'clara help <plugin>' for detailed help on a plugin
    and 'clara <plugin> --help' for a quick list of options of a plugin.


Then to use the tool *repo*, just type `clara repo` and it'll show you the
options of *repo*:

    # clara repo
    Usage:
        clara repo key
        clara repo init <dist>
        clara repo sync (all|<dist> [<suites>...])
        clara repo add <dist> <file>... [--reprepro-flags="list of flags"...]
        clara repo del <dist> <name>...
        clara repo list <dist>
        clara repo -h | --help | help


You can check quickly the help of the tool *repo* invoking the manpage:
`man clara-repo` or just typing `clara help repo`.

# Configuration file

The configuration file of Clara is installed at `/etc/clara/config.ini` and it
is a simple text file using the [INI file format](http://en.wikipedia.org/wiki/INI_file).
This file has a basic structure composed of sections, properties, and values.
For example, a portion from the Clara's configuration file is copied:

    [common]
    ; File: Contains the usernames and passwords needed by the scripts
    master_passwd_file=/srv/clara/data/master_pwd
    ; List: Posible distributions to be used if we're using multi-distro
    allowed_distributions=calibre8,calibre9
    ; String: Name of your Debian derivative by default
    default_distribution=calibre8
    ; String: Name of the team or departament maintaining the repository
    ; It's only used by reprepro
    origin=HPC

    [repo]
    ; String: Name of your cluster or project.
    clustername=cluster
    ; String: Version number of your debian derivative
    version=8.0.0
    ; Path: Directory containing all the configuration files for the local repository
    repo_dir=/srv/clara/calibre8/local-mirror


The lines starting with a semi-colon are commentaries and they're ignored.

`[common]` and `[repo]` indicate the begin of a section and its name.

The remaining lines contain properties. Every property has a name and a value,
delimited by an equals sign (=). The name appears to the left of the equals sign
and the value appears to the right. All properties listed after a section
declaration are associated with that section.

The section `[common]` is common to all the plugins and then every plugin
can add a section with the name of the plugin.

Sometimes, we want to add specific values for different distros and in that case
we'll need to add the name of the plugin, a hyphen `-` followed by the name of
the distribution. For example, if we want to add different configurations
values for the plugin `repo` for calibre8 and calibre9, we'll need to add them
under the sections `[repo-calibre8]` and `[repo-calibre9]`.


# Plugins

## Plugin 'repo'

*clara repo* offers simple commands to create a local Debian repository with
reprepro and update, add and remove files from them. It also provides the
possibility of making mirror of remote Debian repositories locally.

### Sypnosis

    clara repo key
    clara repo init <dist>
    clara repo sync (all|<dist> [<suites>...])
    clara repo add <dist> <file>... [--reprepro-flags="list of flags"...]
    clara repo del <dist> <name>...
    clara repo list <dist>
    clara repo -h | --help | help

Options:

    <file> can be one or more *.deb binaries, *.changes files or *.dsc files.

    <name> is the package to remove, if the package is a source name, it'll
    remove all the associated binaries

### Options

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
`<file>` can be one or more *.deb binaries, *.changes files or *.dsc files.
For the --reprepro-flags, check the documentation of reprepro.

    clara repo del <dist> <name>...

Remove package to the local repository.
`<name>` is the package to remove, if the package is a source name, it'll also
remove all the associated binaries.

    clara repo list <dist>

Lists all contents of the repository.

This distribution in <dist> must be listed in the field "allowed_distributions"
from the section [common].

### Examples

To mirror locally all the suites from calibre8:

    # clara repo sync calibre8

To mirror locally Debian backports for Wheezy:

    # clara repo sync calibre8 wheezy-backports

To create a local repository and add packages to it:

    # clara repo key
    # clara repo init calibre8
    # clara repo add calibre8 mypackage_1-2.dsc

## Plugin 'ipmi'

*clara ipmi* offers a simplified interface of ipmitool, an utility for controlling
IPMI-enabled devices. The username and password needed by ipmitool are handled
automatically.

### Sypnosis

    clara ipmi connect [-jf] <host>
    clara ipmi deconnect <hostlist>
    clara ipmi (on|off|reboot) <hostlist>
    clara ipmi status <hostlist>
    clara ipmi setpwd <hostlist>
    clara ipmi getmac <hostlist>
    clara ipmi pxe <hostlist>
    clara ipmi disk <hostlist>
    clara ipmi ping <hostlist>
    clara ipmi blink <hostlist>
    clara ipmi immdhcp <hostlist>
    clara ipmi bios <hostlist>
    clara ipmi reset <hostlist>
    clara ipmi -h | --help

    clara ipmi <host> connect [-jf]
    clara ipmi <hostlist> deconnect
    clara ipmi <hostlist> (on|off|reboot)
    clara ipmi <hostlist> status
    clara ipmi <hostlist> setpwd
    clara ipmi <hostlist> getmac
    clara ipmi <hostlist> pxe
    clara ipmi <hostlist> disk
    clara ipmi <hostlist> ping
    clara ipmi <hostlist> blink
    clara ipmi <hostlist> immdhcp
    clara ipmi <hostlist> bios
    clara ipmi <hostlist> reset

### Options

    clara ipmi connect [-jf] <host>

Connect to IMM serial console, including video, keyboard and mouse controlling
The flag -j joins the connection and the flag -f forces it.

    clara ipmi deconnect <host>

Deconnect from a IMM serial console

    clara ipmi on <hostlist>

Power up chassis

    clara ipmi off <hostlist>

Power down chassis into soft off. WARNING: it does do a clean shutdown of the OS.

    clara ipmi reboot <hostlist>

This command will perform a hard reset

    clara ipmi status <hostlist>

Get target node power status using the IMM device

    clara ipmi setpwd <hostlist>

Set up IMM user id/password on a new device

    clara ipmi getmac <hostlist>

Get node MAC addresses using the IMM device

    clara ipmi pxe <hostlist>

Use IMM to perform a network boot on the next reboot

    clara ipmi disk <hostlist>

Use IMM to perform a disk boot on the next reboot

    clara ipmi ping <hostlist>

Use fping to check status of the machines

    clara ipmi blink <hostlist>

Make chassis blink to help on-site admins to identify the machine

    clara ipmi immdhcp <hostlist>

Set selected ipmi interfaces to grab an IP via DHCP

    clara ipmi bios <hostlist>

Make selected machines go directly into BIOS on next reboot

    clara ipmi reset <hostlist>

Reset the IMM device (cold reset)


### Examples

This command will ping all hosts nodes from node12 to n99:

    # clara ipmi ping node[12-99]

To check the status from node13:

    # clara ipmi status node13

Or also:

    # clara ipmi node13 status

## Plugin 'slurm'

*clara slurm* provides a simplified interface to the most useful commands from
SLURM.

### Sypnosis

    clara slurm health <nodeset>
    clara slurm resume <nodeset>
    clara slurm drain [<nodeset>] [<reason>...]
    clara slurm down [<nodeset>]
    clara slurm <cmd> <subject> [<op>] [<spec>...]
    clara slurm -h | --help

Options:
    <op> is one of the following ones: show, create, update and delete.

    <cmd> is one of the following ones: job, node, steps, frontend,
    partition, reservation, block and submp.

### Options

    clara slurm health <nodeset>

Show nodes' health

    clara slurm resume <nodeset>

Resume the nodes.

    clara slurm drain [<nodeset>] [<reason>...]

Shows drained nodes and reason why they have been drained, when used without arguments.
When it is given a nodeset, it drains the specified nodes.

    clara slurm down [<nodeset>]

Shows nodes down when used without arguments.
When it is given a nodeset, it puts down the specified nodes.

    clara slurm <cmd> <subject> [<op>] [<spec>...]

Simplified interface for scontrol.
Not all the <op> options are compatible with any `<cmd>` option but clara
will warn you of not allowed combinations.

### Examples

Put the nodes node[3-6] down

    # clara slurm down node[3-6]

## Plugin 'images'

*clara images* makes easy to create and update the images to boot the nodes of
a cluster.

### Sypnosis

    clara images create <dist> [<image>] [--keep-chroot-dir]
    clara images unpack ( <dist> | --image=<path> )
    clara images repack <directory> ( <dist> | --image=<path> )
    clara images edit <dist> [<image>]
    clara images initrd <dist> [--output=<dirpath>]
    clara images -h | --help | help

Options:

    --image=<path>  Path to squashfs image.

### Options

    clara images create <dist> [<image>] [--keep-chroot-dir]

Create a new squashfs image to use as operating system on the cluster nodes.
By default it unpacks the default image but the user can provide the path to a
different file.
The option `--keep-chroot-dir` allows to create the chroot used to generate
the image. By default, this chroot directory is deleted.

    clara images unpack ( <dist> | --image=<path> )

Unpack the squashfs file. By default it unpacks the default image but the user
can provide the path to a different file.

    clara images repack <directory> ( <dist> | --image=<path> )

Repack the squashfs file providing the image.  By default it repacks and replace
the default image but the user can choose to provide a path to save it with a
different name.

    clara images edit <dist> [<image>]

Unpacks the image for editing, spawns a bash to make the changes and repacks
the image again after. By default it edits the default image but the user can
provide the path to a different image.

    clara images initrd <dist> [--output=<dirpath>]

Create a new initrd image to boot the cluster nodes.
The user can use the `--output` option to select a directory different to the
default one to save the generated initrd.

This distribution in <dist> must be listed in the field "allowed_distributions"
from the section [common].


### Examples

To create a image for calibre8 and store it in `/tmp/c8.squashfs`

    # clara images create calibre8 /tmp/c8.squashfs

To edit the default distribution image

    # clara images edit calibre8

To create a initrd for the default distribution image:

     # clara images initrd calibre8

## Plugin 'p2p'

*clara p2p* eases creating torrent files for the cluster installation images
and controlling the seeders and trackers of the cluster to see the new torrent
file.

### Synopsis

    clara p2p status
    clara p2p restart
    clara p2p mktorrent <dist> [--image=<path>]
    clara p2p -h | --help | help

### Options

    clara p2p status

Check the status of the BitTorrent trackers and seeders

    clara p2p restart

Restart the BitTorrent trackers and seeders

    clara p2p mktorrent <dist> [--image=<path>]

Create a new torrent file for the squashfs image and restart trackers
and initial seeders. The distribution in <dist> must be listed in the field
"allowed_distributions" from the section [common].

### Examples

To create a torrent file for the images placed at `/tmp/calibre9.squashfs`

    # clara p2p mktorrent calibre9 --image=/tmp/calibre9.squashfs

## Plugin 'enc'

*clara enc* shows, edits and creates encrypted files using configurable methods
to get the encryption key and encrypt/decrypt files.

### Synopsis

    clara enc show <file>
    clara enc edit <file>
    clara enc encode <file>
    clara enc decode <file>
    clara enc -h | --help | help

### Options

    clara enc show <file>

Shows a encoded filed in plain in the terminal. It'll use `$PAGER` to show it.

    clara enc edit <file>

Allows to create or edit a file that will be automatically encoded after closing
the editor and the copy in plain text will be erased. It'll use `$EDITOR` to edit it.

    clara enc encode <file>

It will encode a file. The resulting file will have the same name than
the original appendix the suffix ".enc"

    clara enc decode <file>

It will decode a encrypted file. The encrypted file must have the suffix ".enc"
in its name. The resulting file will have the same name than the original without
the suffix ".enc"

### Examples

To create an encrypted file in `/data/mydata.enc`:

    # clara enc edit /data/mydata.enc

To see quickly the contents of an encrypted file:

    # clara enc show this_is_my_file.enc

To create a plain text copy of an encrypted file:

     # clara en decode this_is_my_file.enc

This will create an unencrypted file "this_is_my_file"


## Plugin 'build'

*clara build* allows to build packages for any of the custom distributions
and also rebuild a package that's already in the local repository of another
custom distribution.
This plugin requires *cowbuilder* installed and configured.


### Synopsis

    clara build source <dist> <dsc_file>
    clara build repo <dist> <origin_dist> <package_name>
    clara build -h | --help | help

### Options

    clara build source <dist> <dsc_file>

Build a source package targetting the distro indicated.

    clara build repo <dist> <origin_dist> <package_name>

Rebuilds a package from the local repository of the "origin_dist" for the distro
indicated. The repository must contain the source package of the package we want
to rebuild.


### Examples

To build the source package of calibre-hpc for calibre8 that is at /tmp/calibre-hpc_1.2.dsc

    # clara build calibre8 /tmp/calibre-hpc_1.2.dsc

To rebuild the same package for calibre9 using the package in the local repository
of calibre8:

    # clara build calibre8 calibre9 calibre-hpc
