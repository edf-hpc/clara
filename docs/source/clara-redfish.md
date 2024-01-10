% clara-redfish(1)

# NAME

clara-redfish - manages the nodes of a cluster like ipmi to eventually replace it

# SYNOPSIS

    clara redfish getmac <hostlist>
    clara redfish [--p=<level>] (on|off|reboot) <hostlist>
    clara redfish [--p=<level>] status <hostlist>
    clara redfish [--p=<level>] ping <hostlist>
    clara redfish [--p=<level>] pxe <hostlist>
    clara redfish [--p=<level>] disk <hostlist>
    clara redfish [--p=<level>] dflt <hostlist>
    clara redfish [--p=<level>] bios <hostlist>
    clara redfish [--p=<level>] sellist <hostlist>
    clara redfish [--p=<level>] selclear <hostlist>
    clara redfish -h | --help
Alternative:
    clara redfish <hostlist> getmac
    clara redfish [--p=<level>] <hostlist> (on|off|reboot)
    clara redfish [--p=<level>] <hostlist> status
    clara redfish [--p=<level>] <hostlist> ping
    clara redfish [--p=<level>] <hostlist> pxe
    clara redfish [--p=<level>] <hostlist> dflt
    clara redfish [--p=<level>] <hostlist> disk
    clara redfish [--p=<level>] <hostlist> bios
    clara redfish [--p=<level>] <hostlist> sellist
    clara redfish [--p=<level>] <hostlist> selclear

# DESCRIPTION

*clara redfish* offers a simplified interface like ipmi. 


# OPTIONS
    
    clara redfish off <hostlist>
        
        Power up chassis

    clara redfish off <hostlist>

        Power down chassis into soft off. WARNING: it does do a clean shutdown of the OS.

    clara redfish reboot <hostlist>

        This command will perform a hard reset

    clara redfish status <hostlist>

        Get target node power status 

    clara redfish getmac <hostlist>

        Get node MAC addresses 

    clara redfish ping <hostlist>

        Use fping to check status of the machines

    clara redfish pxe <hostlist>

        Perform a network boot on the next reboot

    clara redfish dflt <hostlist>

        Perform a boot with none option on the next reboot

    clara redfish disk <hostlist>

        Perform a disk boot on the next reboot

    clara redfish bios <hostlist>

        Make selected machines go directly into BIOS on next reboot

    clara redfish sellist <hostlist>

        Display the entire content of the System Event Log (SEL).

    clara redfish selclear <hostlist>

        Clear the contents of the System Event Log (SEL). It cannot be undone so be careful.

For the commands that allow to interact multiple nodes at the same time.

# EXAMPLES

This command will ping all hosts nodes from node12 to n99:

    clara redfish ping node[12-99]

To check the status from node13:

    clara redfish status node13

Or also:

    clara redfish node13 status

# SEE ALSO

clara(1), clara-images(1), clara-p2p(1), clara-repo(1), clara-slurm(1), clara-enc(1), clara-build(1), clara-virt(1), clara-chroot(1), clara-ipmi(1)
