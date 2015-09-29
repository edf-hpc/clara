% clara-ipmi(1)

# NAME

clara-ipmi - manages and get the status from the nodes of a cluster

# SYNOPSIS

    clara ipmi connect [-jf] <host>
    clara ipmi getmac <hostlist>
    clara ipmi [-p] deconnect <hostlist>
    clara ipmi [-p] (on|off|reboot) <hostlist>
    clara ipmi [-p] status <hostlist>
    clara ipmi [-p] setpwd <hostlist>
    clara ipmi [-p] pxe <hostlist>
    clara ipmi [-p] disk <hostlist>
    clara ipmi [-p] ping <hostlist>
    clara ipmi [-p] blink <hostlist>
    clara ipmi [-p] immdhcp <hostlist>
    clara ipmi [-p] bios <hostlist>
    clara ipmi [-p] reset <hostlist>
    clara ipmi [-p] sellist <hostlist>
    clara ipmi [-p] selclear <hostlist>
    clara ipmi -h | --help
Alternative:
    clara ipmi <host> connect [-jf]
    clara ipmi <hostlist> getmac
    clara ipmi [-p] <hostlist> deconnect
    clara ipmi [-p] <hostlist> (on|off|reboot)
    clara ipmi [-p] <hostlist> status
    clara ipmi [-p] <hostlist> setpwd
    clara ipmi [-p] <hostlist> pxe
    clara ipmi [-p] <hostlist> disk
    clara ipmi [-p] <hostlist> ping
    clara ipmi [-p] <hostlist> blink
    clara ipmi [-p] <hostlist> immdhcp
    clara ipmi [-p] <hostlist> bios
    clara ipmi [-p] <hostlist> reset
    clara ipmi [-p] <hostlist> sellist
    clara ipmi [-p] <hostlist> selclear

# DESCRIPTION

*clara ipmi* offers a simplified interface of ipmitool, an utility for controlling
IPMI-enabled devices. The username and password needed by ipmitool are handled
automatically.

# OPTIONS

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

    clara ipmi sellist <hostlist>

        Display the entire content of the System Event Log (SEL).

    clara ipmi selclear <hostlist>

        Clear the contents of the System Event Log (SEL). It cannot be undone so be careful.

    clara ipmi reset <hostlist>

        Reset the IMM device (cold reset)

# EXAMPLES

This command will ping all hosts nodes from node12 to n99:

    clara ipmi ping node[12-99]

To check the status from node13:

    clara ipmi status node13

Or also:

    clara ipmi node13 status

TODO

# SEE ALSO

clara(1), clara-images(1), clara-p2p(1), clara-repo(1), clara-slurm(1), clara-enc(1), clara-build(1)
