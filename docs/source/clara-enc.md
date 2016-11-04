% clara-enc(1)

# NAME

clara-enc - interact with encrypted files using configurable methods

# SYNOPSIS

    clara enc show <file>
    clara enc edit <file>
    clara enc encode <file>
    clara enc decode <file>
    clara enc -h | --help | help

# DESCRIPTION

*clara enc* shows, edits and creates encrypted files using configurable methods
to get the encryption key and encrypt/decrypt files.

# OPTIONS

    clara enc show <file>

        Shows a encoded filed in plain in the terminal. It'll use $PAGER to show it.

    clara enc edit <file>

        Allows to create or edit a file that will be automatically encoded after closing
        the editor and the copy in plain text will be erased. It'll use $EDITOR to edit it.

    clara enc encode <file>

        It will encode a file. The resulting file will have the same name than
        the original appendix the suffix ".enc"

    clara enc decode <file>

        It will decode a encrypted file. The encrypted file must have the suffix ".enc"
        in its name. The resulting file will have the same name than the original without
        the suffix ".enc"

# EXAMPLES

To create an encrypted file in /data/mydata.enc:

    clara enc edit /data/mydata.enc

To see quickly the contents of an encrypted file:

    clara enc show this_is_my_file.enc

To create a plain text copy of an encrypted file:

     clara en decode this_is_my_file.enc

This will create an unencrypted file "this_is_my_file"

# SEE ALSO

clara(1), clara-images(1), clara-ipmi(1), clara-repo(1), clara-slurm(1), clara-p2p(1), clara-build(1), clara-virt(1), clara-chroot(1)
