% clara-nodes(1)

# NAME

clara-nodes - manages and get the status from the nodes of a cluster

# SYNOPSIS

    clara nodes connect <host>
    clara nodes (on|off|reboot) <hostlist>
    clara nodes status <hostlist>
    clara nodes setpwd <hostlist>
    clara nodes getmac <hostlist>
    clara nodes pxe <hostlist>
    clara nodes disk <hostlist>
    clara nodes ping <hostlist>
    clara nodes blink <hostlist>
    clara nodes immdhcp <hostlist>
    clara nodes bios <hostlist>
    clara nodes -h | --help

    clara nodes <host> connect
    clara nodes <hostlist> (on|off|reboot)
    clara nodes <hostlist> status
    clara nodes <hostlist> setpwd
    clara nodes <hostlist> getmac
    clara nodes <hostlist> pxe
    clara nodes <hostlist> disk
    clara nodes <hostlist> ping
    clara nodes <hostlist> blink
    clara nodes <hostlist> immdhcp
    clara nodes <hostlist> bios

# DESCRIPTION

*clara nodes* offers a simplified interface of impitool, an utility for controlling IPMI-enabled devices. The username and password needed by impitool are handled automatically.

# OPTIONS

    clara nodes connect <host>

        Connect to IMM serial console, including video, keyboard and mouse controlling

    clara nodes on <hostlist>

        Power up chassis

    clara nodes off <hostlist>

        Power down chassis into soft off. WARNING: it does do a clean shutdown of the OS.

    clara nodes reboot <hostlist>

        This command will perform a hard reset

    clara nodes status <hostlist>

        Get target node power status using the IMM device

    clara nodes setpwd <hostlist>

        Set up IMM user id/password on a new device

    clara nodes getmac <hostlist>

        Get node MAC addresses using the IMM device

    clara nodes pxe <hostlist>

        Use IMM to perform a network boot on the next reboot

    clara nodes disk <hostlist>

        Use IMM to perform a disk boot on the next reboot

    clara nodes ping <hostlist>

        Use fping to check status of the machines

    clara nodes blink <hostlist>

        Make chassis blink to help on-site admins to identify the machine

    clara nodes immdhcp <hostlist>

        Set selected ipmi interfaces to grab an IP via DHCP

    clara nodes bios <hostlist>

        Make selected machines go directly into BIOS on next reboot

# EXAMPLES

This command will ping all hosts nodes from node12 to n99:

    clara nodes ping node[12-99]

To check the status from node13:

    clara nodes status node13

Or also:

    clara nodes node13 status

TODO

# SEE ALSO

clara(1), clara-images(1), clara-p2p(1), clara-repo(1), clara-slurm(1)
