% clara-virt(1)

# NAME

clara-virt - manages virtual machines

# SYNOPSIS

    clara virt list [--details] [--virt-config=<path>]
    clara virt define <vm_names> --host=<host> [--template=<template_name>] [--virt-config=<path>]
    clara virt undefine <vm_names> [--host=<host>] [--virt-config=<path>]
    clara virt start <vm_names> [--host=<host>] [--wipe] [--virt-config=<path>]
    clara virt stop <vm_names> [--host=<host>] [--hard] [--virt-config=<path>]
    clara virt migrate <vm_names> --dest-host=<dest_host> [--host=<host>] [--virt-config=<path>]
    clara virt getmacs <vm_names> [--template=<template_name>] [--virt-config=<path>]
    clara virt -h | --help | help

Options:
    <vm_names>                  List of VM names (ClusterShell nodeset)
    <host>                      Physical host where the action should be applied
    --details                   Display details (hosts and volumes)
    --wipe                      Wipe the content of the storage volume before starting
    --hard                      Perform a hard shutdown
    --dest-host=<dest_host>     Destination host of a migration
    --template=<template_name>  Use this template instead of the in config
    --virt-config=<path>        Path of the virt config file [default: /etc/clara/virt.ini]

# DESCRIPTION

*clara virt* provides a simplified interface to manage virtual machines on a group of
physical hosts using libivirt. It does not support local storage, storage must be shared
between the hosts (with Ceph RBD for example).

This plugins requires LibVirt >= 10.2.9 (version in Debian 8).

# OPTIONS

    clara virt list [--details] [--virt-config=<path>]

List the machines. If *--details* is provided: where instances are running and storages
volumes associated.

    clara virt define <vm_names> --host=<host> [--template=<template_name>] [--virt-config=<path>]

Define a VM on *host*, the description of the vm is read from a template in the configuration.
The template is chosen in this order: *--template* argument, name matching in the conf, template
with the default attribute.

    clara virt undefine <vm_names> [--host=<host>] [--virt-config=<path>]

Remove the virtual machine from the configuration of host, this does not remove the storage
volume.

    clara virt start <vm_names> [--host=<host>] [--wipe] [--virt-config=<path>]

Starts a defined VM, if the *--wipe* parameter is passed. The storage volumes are erased before
starting the virtual machine. This triggers a PXE boot.

    clara virt stop <vm_names> [--host=<host>] [--hard] [--virt-config=<path>]

Stops a running VM by requesting a clean shutdown. If this does not succeed, it is possible to
use the *--hard* flag to force the shutdown.

    clara virt migrate <vm_names> --dest-host=<dest_host> [--host=<host>] [--virt-config=<path>]

Moves a running VM from a host (*--host*) to another (*--dest-host*). The migration is done without
bringing down the VM. This command is synchronous and only returns when the migration ends.

    clara virt getmacs <vm_names> [--template=<template_name>] [--virt-config=<path>]

Print the MAC addresses of all network interfaces of the VM that Clara set in the VM definition
file.

# SEE ALSO

clara(1), clara-images(1), clara-ipmi(1), clara-p2p(1), clara-repo(1), clara-enc(1), clara-build(1), clara-slurm(1), clara-virt(1), clara-chroot(1)
