% clara-slurm(1)

# NAME

clara-slurm - performs tasks using SLURM's controller

# SYNOPSIS

    clara slurm health <nodeset>
    clara slurm resume <nodeset>
    clara slurm drain [<nodeset>] [<reason>...]
    clara slurm undrain <nodeset>
    clara slurm fail [<nodeset>] [<reason>...]
    clara slurm down [<nodeset>]
    clara slurm power <state> <nodeset>
    clara slurm <cmd> <subject> [<op>] [<spec>...]
    clara slurm -h | --help

Options:
    <state> must be either 'up' or 'down'

    <op> is one of the following ones: show, create, update and delete.

    <cmd> is one of the following ones: job, node, steps, frontend,
    partition, reservation, block and submp.


# DESCRIPTION

*clara slurm* provides a simplified interface to the most useful commands from SLURM.

# OPTIONS

    clara slurm health <nodeset>

        Show nodes' health

    clara slurm resume <nodeset>

        Resume the nodes.

    clara slurm drain [<nodeset>] [<reason>...]

        Shows drained nodes and reason why they have been drained, when used without arguments.
        When it is given a nodeset, it drains the specified nodes.

    clara slurm undrain <nodeset>

        Clears the node from being drained (like "RESUME"), but will not change the node's base state (e.g. "DOWN").

    clara slurm fail [<nodeset>] [<reason>...]

        Shows failed nodes and reason why they have been set as failed, when used without arguments.
        When it is given a nodeset, it sets as failed the specified nodes.

    clara slurm power <state> <nodeset>

        This command will use the configured SuspendProg and ResumeProg programs in slurm.conf to explicitly place a node in or out of a power saving mode.

    clara slurm down [<nodeset>]

        Shows nodes down when used without arguments.
        When it is given a nodeset, it puts down the specified nodes.

    clara slurm <cmd> <subject> [<op>] [<spec>...]

        Simplified interface for scontrol.
        Not all the <op> options are compatible with any <cmd> option but clara 
        will warn you of not allowed combinations.

# EXAMPLES

Put the nodes node[3-6] down

    clara slurm down node[3-6]

# SEE ALSO

clara(1), clara-images(1), clara-ipmi(1), clara-p2p(1), clara-repo(1), clara-enc(1), clara-build(1), clara-virt(1), clara-chroot(1), clara-redfish(1)
