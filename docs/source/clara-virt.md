% clara-virt(1)

# NAME

clara-virt - manages virtual machines

# SYNOPSIS

    clara virt list [--details] [--legacy] [--color] [--host=<host>] [--virt-config=<path>]
    clara virt define <vm_names> --host=<host> [--template=<template_name>] [--virt-config=<path>]
    clara virt undefine <vm_names> [--host=<host>] [--virt-config=<path>]
    clara virt start <vm_names> [--host=<host>] [--wipe] [--virt-config=<path>]
    clara virt stop <vm_names> [--host=<host>] [--hard] [--virt-config=<path>]
    clara virt migrate [<vm_names>] [--dest-host=<dest_host>] [--host=<host>] [--virt-config=<path>] [--dry-run] [--quiet] [--yes-i-really-really-mean-it] [--exclude=<exclude>] [--include=<include>]
    clara virt getmacs <vm_names> [--template=<template_name>] [--virt-config=<path>]
    clara virt -h | --help | help

Options:

    <vm_names>                     List of VM names (ClusterShell nodeset)
    <host>                         Physical host where the action should be applied
    --details                      Display details (hosts and volumes)
    --legacy                       Old School display
    --color                        Colorize or not output
    --wipe                         Wipe the content of the storage volume before starting
    --hard                         Perform a hard shutdown
    --dest-host=<dest_host>        Destination host of a migration
    --template=<template_name>     Use this template instead of the in config
    --virt-config=<path>           Path of the virt config file [default: /etc/clara/virt.ini]
    --quiet                        Proceed silencely. Don't ask any question!
    --dry-run                      Just simulate migrate action! Don't really do anything
    --yes-i-really-really-mean-it  Force migrate action execution without any further validation
    --exclude=<exclude>            Exclude pattern in VMs [default: service]
    --include=<include>            Include pattern in VMs

# DESCRIPTION

*clara virt* provides a simplified interface to manage virtual machines on a group of
physical hosts using libivirt. It does not support local storage, storage must be shared
between the hosts (with Ceph RBD for example).

This plugins requires LibVirt >= 10.2.9 (version in Debian 8).

# OPTIONS

    clara virt list [--details] [--legacy] [--color] \
                    [--host=<host>] [--virt-config=<path>]

List the KVM cluster machines in two way.\
The first one as *table*, as show bellow:

```
clara virt list
+------------+----------+---------+
|       Host | VM       |  State  |
+------------+----------+---------+
| centos7    |          | MISSING |
+------------+----------+---------+
| exservice1 |          |         |
+------------+----------+---------+
|            | exadmin1 | RUNNING |
|            | exbatch1 | RUNNING |
+------------+----------+---------+
| exservice2 |          |         |
+------------+----------+---------+
|            | exbatch2 | RUNNING |
|            | exp2p2   | SHUTOFF |
|            | exproxy1 | RUNNING |
+------------+----------+---------+
| exservice3 |          |         |
+------------+----------+---------+
|            | exp2p1   | RUNNING |
+------------+----------+---------+
```

The second way is available through switch *--legacy*:

```
clara virt list --legacy
VM:exadmin1         State:RUNNING      Host:exservice1
VM:exbatch1         State:RUNNING      Host:exservice1
VM:exbatch2         State:RUNNING      Host:exservice2
VM:exp2p2           State:SHUTOFF      Host:exservice2
VM:exproxy1         State:RUNNING      Host:exservice2
VM:exp2p1           State:RUNNING      Host:exservice3
VM:centos7          State:MISSING      Host:
```

. If *--details* is provided, bellow additional informations are given:
- where instances are running and storages volumes associated.
- machines (VMs) allocated memory and cpu.
- KVM server hosts total memory and cpu and addition \
  of memory and cpu on all hosted machines.

For instance, say a server host, exservice1, with 8 cpu and 16 Go of memory,\
with two machines:

    exadmin1: 4 allocated cpus and 4 Go of memory
    exbatch1: 6 cpus and 8 Go of memory

```
clara virt list --details --host=exservice1
+------------+----------+---------+---------+-------+-----------------+----------+----------+
|       Host | VM       |  State  |  memory |  cpus |        Volume   |   Pool   | Capacity |
+------------+----------+---------+---------+-------+-----------------+----------+----------+
| exservice1 |          |         |  12/8   | 10/8  |                 |          |          |
+------------+----------+---------+---------+-------+-----------------+----------+----------+
|            | exadmin1 | RUNNING |    4    |   4   | exadmin1_system | rbd-pool | 40.0 GB  |
|            | exbatch1 | RUNNING |    8    |   6   | exbatch1_system | rbd-pool | 100.0 GB |
+------------+----------+---------+---------+-------+-----------------+----------+----------+
```

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

    clara virt migrate [<vm_names>] [--dest-host=<dest_host>] \
    [--host=<host>] [--virt-config=<path>] [--dry-run] [--quiet] \
    [--yes-i-really-really-mean-it] [--exclude=<exclude>] [--include=<include>]

Moves a running VM from a host (*--host*) to another (*--dest-host*). The migration is done without
bringing down the VM. This command is synchronous and only returns when the migration ends.

Live migration can been simulated using optional switch *--dry-run*.

In another word, when machines involved in migration have been provided through *<vm_names>*,\
live migration are really done unless switch *--dry-run* have been raised!

Migration source host is, by default, the host on which `clara virt migrate` command \
have been raised. But you can also raised it from any cluster KVM server host!

At another part, if not provided, destination host, invoked by *--dest-host* switch,\
can be picked automatically, as the cluster host with lower running VM!

Let's illustrate it with machine *exbatch2* currently running on server *exservice3*:

```
clara virt migrate exbatch2
clara virt list
+------------+----------+---------+
|       Host | VM       |  State  |
+------------+----------+---------+
| centos7    |          | MISSING |
+------------+----------+---------+
| exservice1 |          |         |
+------------+----------+---------+
|            | exadmin1 | RUNNING |
|            | exbatch1 | RUNNING |
+------------+----------+---------+
| exservice2 |          |         |
+------------+----------+---------+
|            | exp2p2   | SHUTOFF |
|            | exproxy1 | RUNNING |
+------------+----------+---------+
| exservice3 |          |         |
+------------+----------+---------+
|            | exbatch2 | RUNNING |
|            | exp2p1   | RUNNING |
+------------+----------+---------+
```

Raising command: `clara virt migrate exbatch2 --dest-host exservice3` would have given same result!

Machines involved in live migration are optional and when not provided, all running
machines will be migrated off KVM server on witch command have been raised.
This can be seen as a kind of machines *evacuation*!

For instance, see bellow result when raising *evacuation* of KVM server *exservice3* host:

```
clara virt migrate --yes-i-really-really-mean-it
clara virt list
+------------+----------+---------+
|       Host | VM       |  State  |
+------------+----------+---------+
| centos7    |          | MISSING |
+------------+----------+---------+
| exservice1 |          |         |
+------------+----------+---------+
|            | exadmin1 | RUNNING |
|            | exbatch1 | RUNNING |
+------------+----------+---------+
| exservice2 |          |         |
+------------+----------+---------+
|            | exbatch2 | RUNNING |
|            | exp2p1   | RUNNING |
|            | exp2p2   | SHUTOFF |
|            | exproxy1 | RUNNING |
+------------+----------+---------+
```

As you could notice, switch *--yes-i-really-really-mean-it* is need to really perform *evacuation*
Without this option, no action is perform. Default is to raise in dry run mode (*--dry-run*)

Machine can be included with *--include* switch and excluded with *--exclude*.
For instance, to migrate all machines ended with number '2' off of *exservice2*:

```
clara virt migrate --include '2*' --yes-i-really-really-mean-it --host exservice2
clara virt list
+------------+----------+---------+
|       Host | VM       |  State  |
+------------+----------+---------+
| centos7    |          | MISSING |
+------------+----------+---------+
| exservice1 |          |         |
+------------+----------+---------+
|            | exadmin1 | RUNNING |
|            | exbatch1 | RUNNING |
+------------+----------+---------+
| exservice2 |          |         |
+------------+----------+---------+
|            | exp2p1   | RUNNING |
|            | exp2p2   | SHUTOFF |
|            | exproxy1 | RUNNING |
+------------+----------+---------+
| exservice2 |          |         |
+------------+----------+---------+
|            | exbatch2 | RUNNING |
+------------+----------+---------+
```

As you can notice, only *RUNNING* machines are involved in live migration.

Let us take another example with *--exclude* switch:

```
clara virt migrate --exclude 'p2p' --yes-i-really-really-mean-it --host exservice2
clara virt list
+------------+----------+---------+
|       Host | VM       |  State  |
+------------+----------+---------+
| centos7    |          | MISSING |
+------------+----------+---------+
| exservice1 |          |         |
+------------+----------+---------+
|            | exadmin1 | RUNNING |
|            | exbatch1 | RUNNING |
+------------+----------+---------+
| exservice2 |          |         |
+------------+----------+---------+
|            | exp2p1   | RUNNING |
|            | exp2p2   | SHUTOFF |
+------------+----------+---------+
| exservice2 |          |         |
+------------+----------+---------+
|            | exbatch2 | RUNNING |
|            | exproxy1 | RUNNING |
+------------+----------+---------+
```

Finally, involved machines can been provided as *inline* json, as shown by bellow example:

```
clara virt migrate "{ exbatch1: exservice2, exproxy1: exservice1 }"
clara virt list
+------------+----------+---------+
|       Host | VM       |  State  |
+------------+----------+---------+
| centos7    |          | MISSING |
+------------+----------+---------+
| exservice1 |          |         |
+------------+----------+---------+
|            | exadmin1 | RUNNING |
|            | exproxy1 | RUNNING |
+------------+----------+---------+
| exservice2 |          |         |
+------------+----------+---------+
|            | exbatch1 | RUNNING |
|            | exp2p1   | RUNNING |
|            | exp2p2   | SHUTOFF |
+------------+----------+---------+
| exservice2 |          |         |
+------------+----------+---------+
|            | exbatch2 | RUNNING |
+------------+----------+---------+
```

    clara virt getmacs <vm_names> [--template=<template_name>] [--virt-config=<path>]

Print the MAC addresses of all network interfaces of the VM that Clara set in the VM definition
file.

# SEE ALSO

clara(1), clara-images(1), clara-ipmi(1), clara-p2p(1), clara-repo(1), clara-enc(1), clara-build(1), clara-slurm(1), clara-virt(1), clara-chroot(1)
