Clara, a set of Cluster Administration Tools
============================================

Clara provides the following commands:
* ```repo```     creates, updates and synchronizes local Debian repositories
* ```nodes```    manages and get the status from the nodes of a cluster
* ```slurm```    shows information from SLURM
* ```images```   creates and updates the images of installation of a cluster
* ```p2p```      makes torrent images and seeds them via BitTorrent

## module 'repo' ##
* ```clara repo key```

Install the secret GPG key to use in the repository.

* ```clara repo init```

Create the initial configuration for reprepro for our local repository and
makes the first export.

* ```clara repo sync [create]```

Synchronize all the local Debian repositories with the canonical repositories.
If it's the first time we're syncing, we need to add the option [create] to
also create the repository locally.

* ```clara repo (add|del) <package>```

Add or remove a package to the local repository.


## module 'nodes' ##
* ```clara nodes connect <hostlist>```

Connect to IMM serial console, including video, keyboard and mouse control

* ```clara nodes (on|off|reboot) <hostlist>```

Power off | on | reboot the target node using the IMM device

* ```clara nodes status <hostlist>```

Get target node power status using the IMM device

* ```clara nodes setpwd <hostlist>```

Set up IMM user id/password on a new device

* ```clara nodes getmac <hostlist>```

Get node mac addresses using the IMM device

* ```clara nodes pxe <hostlist>```

Use IMM to perform a network boot on the next reboot

* ```clara nodes disk <hostlist>```

Use IMM to perform a disk boot on the next reboot

* ```clara nodes ping <hostlist>```

Use fping to check status of the machines

* ```clara nodes blink <hostlist>```

Make chassis blink to help on-site admins to identify the machine

* ```clara nodes immdhcp <hostlist>```

Set selected ipmi interfaces to grab an IP via DHCP

* ```clara nodes bios <hostlist>```

Make selected machines go directly into BIOS on next reboot


## module 'slurm' ##
* ```clara slurm drain```

Display nodes that are drained

* ```clara slurm down```

Display nodes that are down

* ```clara slurm health <hostlist>```

Display nodes that are down

## module 'images' ##
* ```clara images genimg```

Create a new squashfs image to use as operating system on the cluster
nodes, it will also create a new torrent file and start seeding it.

* ```clara images (unpack|repack <directory>)```

Unpack and repack the squashfs file providing the image.

* ```clara images apply_config2img```

Apply a new configuration to the current image (packages and files),
it will also renew the torrent file and start seeding it.

* ```clara images initrd```

Create a new initrd image to boot the cluster nodes.

## module 'p2p' ##

* ```clara p2p status```

Check the status of the BitTorrent trackers and seeders

* ```clara p2p restart```

Restart the BitTorrent trackers and seeders

* ```clara p2p mktorrent  [--image=<path>]```

Create a new torrent file for the squashfs image and restart
trackers and initial seeders.

EDF S.A. 2014 - http://www.edf.fr/
