Clara, a set of Cluster Administration Tools
============================================

!! Warning: this code is compatible only with Python3

## Overview

[clara](https://github.com/edf-hpc/clara/blob/master/docs/source/clara.md) is a set of cluster administration tools.  The different tools are written as plugins that can be added or removed independently.

Clara provides the following plugins:
* [repo](https://github.com/edf-hpc/clara/blob/master/docs/source/clara-repo.md)     creates, updates and synchronizes local Debian repositories
* [ipmi](https://github.com/edf-hpc/clara/blob/master/docs/source/clara-ipmi.md)    manages and get the status from the nodes of a cluster
* [slurm](https://github.com/edf-hpc/clara/blob/master/docs/source/clara-slurm.md)    performs tasks using SLURM's controller
* [images](https://github.com/edf-hpc/clara/blob/master/docs/source/clara-images.md)   creates and updates the images of installation of a cluster
* [p2p](https://github.com/edf-hpc/clara/blob/master/docs/source/clara-p2p.md)      makes torrent images and seeds them via BitTorrent
* [enc](https://github.com/edf-hpc/clara/blob/master/docs/source/clara-enc.md)     interact with encrypted files using configurable methods
* [build](https://github.com/edf-hpc/clara/blob/master/docs/source/clara-build.md)     builds Debian packages
* [virt](https://github.com/edf-hpc/clara/blob/master/docs/source/clara-virt.md)     manages virtual machines
* [redfish](https://github.com/edf-hpc/clara/blob/master/docs/source/clara-redfish.md)    manages the nodes of a cluster like ipmi to eventually replace it
* [easybuild](https://github.com/edf-hpc/clara/blob/master/docs/source/clara-easybuild.md)    manages package installation via easybuild
Read the full [user's guide](http://edf-hpc.github.io/clara/).

## Release

Steps to produce release `$VERSION` (ex: `0.19700101`):

1. Update `CHANGELOG.md` to move entries under the `[Unrelease]` into a new
   release section.
2. Bump version number in `clara/version.py`
3. Then run:

```
git add CHANGELOG.md
git commit -m "Release $VERSION"
git tag -a v$VERSION -m "Release $VERSION"
```

4. Finally push all the branches and tags.

To generate a tarball, run:

```
git archive --format=tar.gz --prefix=clara-$VERSION/ \
    v$VERSION > ../clara-$VERSION.tar.gz
```

## Tests

For running tests please install: `pytest pytest-mock mock` and then run:

```buildoutcfg
pytest
```
Under the project directory
