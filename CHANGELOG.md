# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/).

## [Unreleased]

## [0.20240104] - 2024-01-04

### Added
- plugin redfish: add boot param functions
- plugin redfish: add functions to reboot, stop and start node
- plugin redfish: add function clear log
- plugin redfish: adapt for different version of firmware redfish
- config: add support to redhat-like repositories

## [0.20240102] - 2024-01-02

### Added
- docs: add support to redhat-like repositories
- add a bunch of new lines for clarity

### Fixed
- plugin repo: fix with multiple unneed createrepo

## [0.20240101] - 2024-01-01

### Added
- docs: add support to redhat-like repositories
- docs: automatic VM live migrate and dry run mode
- docs: migrate to automatic pick destination host
- docs: enhanced virt plugin with cpu/mem details
- docs: add forgotten show plugin
- virt: new function to retrieve possible dest host
- plugin repo: support jenkins jobs list
- plugin repo: support rpm packages jenkins job

### Fixed
- virt: fix bad migrate destination host issue

## [0.20231201] - 2023-12-01

### Added
- plugin virt: migrate vm from any to any host
- plugin virt: add more filter for migrate action
- plugin virt: automatic VM selection and dry run
- virt: add support to live migration dry run mode
- plugin virt: support automatic dest host election
- virt: add automatic dest host election function
- utils: introduce yes or not function

## [0.20231130] - 2023-11-30

### Added
- plugin virt: add VM relative VM placement rule
- plugin virt: colorize vm state & cpu,memory conso
- utils: introduce colorize class to color output
- plugin virt: support memory and CPU info details
- virt: func host&vm and memory & cpu related info
- virt: fix undefined domain issue returning None
- plugin virt: add horizontal lines to pretty table
- plugin virt: add pretty way to list VM as table

### Changed
- plugin virt: merge show_<hosts|volume> to details

## [0.20231109] - 2023-11-09

### Fixed
- images: fix issue with python3.5 print format
- images: fix issue with scibian distro
- bin: enforce python3 in the shebang

## [0.20231003] - 2023-10-03

### Added
- images: add support to dnf through proxy
- images: support unexistent gpg_keyring creation
- images: add support to redhat like distribution

### Fixed
- images: fix dns name resolution issue in chroot

### Changed
- config: update default redhat like distribution
- docs: add support to redhat like distribution

## [0.20230103] - 2023-01-03

### Fixed
- images: create local directories for squashfs with mode 0o0755 recursively
  whatever the current umask (#136).
- p2p: enforce mode 0644 on SFTP pushed torrent file (#137).
- sftp: create remote directory with mode 755 by default to avoid umask effect.

## [0.20221222] - 2022-12-22

### Added
- repo: support of openssl password derivation key

### Fixed
- repo: fix issue with unexistant variable dist

## [0.20221026] - 2022-10-26

### Added
- images: support optional dnf/yum priorities in list\_repos

### Fixed
- images: fix format of dists hash and centos/rhel sources loop for appstream
- images: fix group/extra packages installation order

### Changed
- images: bootstrap RPM images with generated dnf/yum repos files

## [0.20220125] - 2022-01-25

### Added
- utils: add functions to get OS information
- enc: enable key derivation except on debian<=9
- images: support GPG keyring in RPM/dnf repos

### Fixed
- all: fix python3 port by replacing raw\_input() with input()
- enc: use $EDITOR and $PAGER instead of sensible-\* debianisms
- images: bind-mount /run in chroot if it is a mount point to support more packages installations
- images: remove duplicate yum repos conf generation
- enc: avoid spurious msg for default digest type

## [0.20210511] - 2021-05-11

### Fixed
- chroot: fix tedious shell glitches in clara chroot using real shell
- chroot: fix stupid variable name error

## [0.20210305] - 2021-03-05

### Fixed
- ipmi: make sure the escape sequence is the same whether or not a jump host is used
- ipmi: use localhost as the conman destination when using a jump host
- ipmi: fix a missing import

## [0.20210224] - 2021-02-24

### Added
- ipmi: Option to use an ssh connexion as a relay to the conman server, set to true by default
- images: ensure user's read access to /var/lib/rpm on rhel-based generated images

## [0.20201203] - 2020-12-03

### Fixed

- images: Improve Yum/DNF support
- repo: control digest used to decode repos signature key

## [0.20201015] - 2020-10-15

### Fixed
- clara: fix symlink run and var/run
- clara: fix input function for python3

## [0.20201007] - 2020-10-07

### Added
- images: Add list_repos feature for rhel distrib to support multiple repos
- images: symlink run -> var/run

## [0.20200707] - 2020-07-07

### Added
- images: add support for centos8 image creation

## [0.20200617] - 2020-06-17

### Added
- clara: add pytest unitary tests

### Changed
- clara: port from Python2 to Python3.

## [0.20200106] - 2020-01-06

### Fixed
- clara: fix exception in case of undefined digest type
### Removed
- clara: remove digest_type parameter from config.ini
### Added
- clara: add digest_type parameter in config_default.ini

## [0.20191210] - 2019-12-10

### Fixed
- enc: fix digest type used for the calculation of the encryption key.
  Define digest type in config.ini instead of using the default digest of the operating system,
  and use sha256 in case of invalid or undefined digest type (fix #118)

## [0.20190424] - 2019-04-24

### Fixed
- p2p: fix restricted rights on torrent files and their directories
- images: create local squash directory if it doesn't exist before making squash file

## [0.20190321] - 2019-03-21

### Added
- virt: add parameter host
- images: add push to force push of images
- clara: add pluging show
- clara: add default conf file in /usr/share/clara
- chroot: add reconfig to reinstall files
### Fix
- images: fix initrd fail because /proc is busy
- repo: Set the correct umask in repository modifications
- repo: fix the failure of clara repo sync all
- repo: fix the case where init fails but creates the repository anyway
- images: fix default path for trg_dir and trg_img in the case where they are empty or NONE
- clara: hide warn about unset extra_bind_mount

## [0.20190116] - 2019-01-16

### Added
- chroot: add gpg\_check and gpg\_keyring parameters
- images: add gpg\_check and gpg\_keyring parameters
- utils: Add get\_bool\_from\_config\_or function
- utils: add exit\_on\_error optional argument to run() function for raising
  RuntimeError in case of cmd non-zero exit code.
- images: add tmp\_dir option to control tmp build directory (fix #92)

### Changed
- chroot: Install files before installing packages
- images: Setup files before installing packages
- chroot: Set owner of apt keys to support \_apt (scibian9)

### Fixed
- ipmi: fallback to ipmitool if conman client fails (fix #78)
- images: apt clean before renaming previous image file (fix #77)
- repo: avoid error with unknown variable when changesfile not found in jenkins

## [0.20180123] - 2018-01-23

### Added
- doc: add documentation about the release process in README.md

### Changed
- core: move bash-completion file out of debian/ tree
- core: reference version number is now in clara/version.py, not in
  debian/changelog anymore as the debian directory has been removed.
- images: use variable path to refer to policy-rc directory for chmod

### Fixed
- images: ensure mode of base install created files instead of relying on umask
  (fix #108)

### Removed
- core: remove debian/ packaging code, clara is now managed as a pure upstream
  code base with nothing nothing related to distro packaging.

## [0.20171114] - 2017-11-14

### Changed
- repo: update jenkins path.

## [0.20170617] - 2017-06-17

### Added
- Add 'clara slurm power' sub-command
- Add 'clara slurm undrain' and 'clara slurm fail' sub-commands
- Add Sftp module
- Add two helpers in clara.utils to check configuration items and
  handle default values
- repo: Add a 'push' post-command to publish modifications
- p2p: Add ability to sync generated .torrent files over SFTP
- images: add ability to sync produced files over SFTP
- ipmi: add support for suffix parameter (fix #96)
- virt: display human readable capacity (fix #87)

### Changed
- ipmi: ask for confirmation before doing reset (fix #90)
- ipmi: Do not emit a warning when parallel parameter is not set (fix #60)

## [0.20170413.1] - 2017-04-13

### Fixed
- images: add missing dash

## [0.20170413] - 2017-04-13

### Fixed
- images: make sure the created image is fully up-to-date (fix #83)
- repo: some code refactoring (fix #98)
- utils: create logging directory if it doesn't exist (fix #95)
- utils: fix error parsing value from file with equals (fix #100)

### Added
- virt: introduce getmacs action (fix #88)
- impi: add clara impi soft (fix #82)
- repo: add clara repo move (fix #99)

## [0.20161223] - 2016-12-23

### Changed
- repo: force command to look for _amd64.sources unless another option is given
  with --source=<arch> (fix #80)

## [0.20161220] - 2016-12-20

### Changed
- chroot: remove -keep-chroot-dir, always keep modifications when editing chroot
- chroot: better detection of mounted filesystems
- chroot: always update dpkg database before installing packages

### Fixed
- chroot: fix path for ssl key and crt

### Added
- chroot: add possibility to use foreign dpkg archs
- images: add possibility to use foreign dpkg archs when creating images

## [0.20161130] - 2016-11-30

### Changed
- virt: use nodeset for vm_names.
- virt: more compact list output by default add --details

## [0.20161129] - 2016-11-29

### Changed
- repo: check if the job exists in jenkins before looking for changes file.
- code: update copyright years in headers.

### Fixed
- repo: fix check for repos.ini when syncing

## [0.20161108] - 2016-11-08

### Added
- chroot: Add plugin chroot.

## [0.20161013] - 2016-10-13

### Changed
- repo: copy packages fron a jenkins job into the given repository. This
  feature might evolve in the future or even go to its own plugin (fix #57).

### Added
- virt: new plugin introduced

## [0.20161004] - 2016-10-04

### Added
- ipmi: allow to configure the prefix for the BMC interfaces (fix #70)

### Changed
- ipmi: update string to show errno and strerr (fix #71)
- images: show an error when the squashfs file doesn't exist (fix #72)

### Fixed
- repo: some naming fixes in repos.ini
- images: do not fail if package_file is not in config.ini (fix #74)
- core: check if the config file provided in the command line exists (fix #73)
- repos: check if /etc/clara/repos.ini is there before opening it.

## [0.20160405] - 2016-04-05

### Fixed
- ipmi: fix ipmi_run() on python <=2.6

## [0.20160311] - 2016-03-14

### Changed
- repos: temove parameter "group" from repos.ini (fix #61, #62).

## [0.20160226] - 2016-02-26

### Added
- repo: add option to list the packages in all the repositories.
- repo: new option to search a package in all the repositories.
- repo: add option to copy packages from a distribution to another.

### Changed
- repo: reimplentation of sync action, code is now less dependent of the calibre
  infra and all the repositories information is now in a new configuration file
  named repos.ini.
- repo: configuration parameter info_suites has been replaced by suites and it
  is only a list of suites now.
- repo: new file repos.ini with the configuration for every suite. Global values
  can still be set in config.ini and an override can be added in a specific
  section of repos.ini when needed.

## [0.20160219] - 2016-02-19

### Added
- ipmi: add a SSH option, this allows to run a command through the SSH interface
  of the IMM.

### Changed
- core: update the dependency on clustershell to version >= 1.7.
- ipmi: add new dependency on sshpass.
- doc: update user guide.

## [0.20151117] - 2015-11-17

### Added
- repo: add a configuration parameter to choose the method that debmirror
  should use to download files.

### Changed
- impmi: make do_ipmi fully parallel and allow to choose the level of
  parallelism with --p=<level>.

## [0.20150929] - 2015-09-29

### Added
- ipmi: add the option -p to run the ipmi commands in parallel.

### Changed
- doc: various updates.

## [0.20150915] - 2015-09-15

### Fixed
- core: fix compatibility with Python2.6

# [0.20150911] - 2015-09-11

### Changed
- p2p: use the same format in the configuration file for 'seeders'
  that the one used for 'trackers'.

## [0.20150903] - 2015-09-03

### Fixed
- p2p: trackers needed to be update somewhere else after the configuration
  updates to include torrent files. Fixed now.

## [0.20150825] - 2015-08-25

### Added
- ipmi: add commands sellist and selclear.

### Fixed
- add build-depends on texlive-fonts-recommended.

## [0.20150612] - 2015-06-12

### Added
- core: write the version number as a string from setup.py in debian/version,
  thanks to P. LAMARE.
- p2p: add configuration parameters for the tracking and seeding services.

### Changed
- p2p: the configuration parameter 'trackers' contains now pairs of tracker
  servers and the torrent files they should serve.

### Fixed
- ipmi: fix mac address parsing for getmac action

## [0.20150310] - 2015-03-10

### Added
- p2p:  allow to configure in config.ini the string format to check the status,
  stop and start the service. This allows to use systemctl (systemd) or service
  (system V).

### Changed
- repo: rework syntax for sync (fix #53)

### Fixed
- core: Re-add and update bash-completion (fix #37).

## [0.20150212] - 2015-02-12

### Fixed
- enc: do not log passwords.
- build: fix handling of native versions.

## [0.20150204] - 2015-02-04

### Fixed
- ipmi: convert port string in an integer.
- build: set the proper directory when looking for a library source in the
  reprepro pool.

## [0.20150128] - 2015-01-28

### Added
- build: plugin introduction (fix #51).
- ipmi: add conmand port in the config.ini

## [0.20150127] - 2015-01-27

### Changed
- ipmi: check for remote conman server instead of assuming that's running
  locally (fix #52).

## [0.20150126] - 2015-01-26

### Added
- ipmi: re-add setpwd (fix #49).
- ipmi: implements the raw cold reset (fix #50).

## [0.20141216] - 2014-12-16

### Added
- core: add debugging output with "-dd" for all the third party software
  (continues #48)

## [0.20141215] - 2014-12-15

### Added
- repo: add archs and sections as configuration parameters for sync.
- core: Add the flag -dd to  display the debug output from third party
  applications in addition to the debug output from clara (-d). Currently, this
  only works with debmirror. Remaining third party applications needs to be
  added after evaluating when it's useful (fix #48).

### Removed
- core: disable the bash_completion for clara. After all the last syntax
  changes it is not useful anymore.

## [0.20141211] - 2014-12-11

### Changed
- p2p: replace completely mldonkey with opentracker.
- p2p: the 'dist' parameter is now mandatory for mktorrent.

## [0.20141205] - 2014-12-05

### Added
- ipmi: add also flags in alternative connect commands (fix #43)

### Changed
- repo: also sync debian-installer section (fix #47)
- core: update build-depends to build the new documentation in pdf.
- images: edit asks now the user how to proceed instead of looking for
  /IGNORE (fix #46).
- images: the 'dist' parameter is now mandatory (fix #45)
- repo: the 'dist' parameter is now mandatory (fix #44)
- doc: various updates

## [0.20141118] - 2014-11-18

### Added
- doc: add Clara's user guide.

### Changed
- core: update minimal Python version to 2.7 (Jessie's default)
- core: move the creation of the documents to the build step.

## [0.20141110] - 2014-11-10

### Added
- slurm: make health check program configurable (fix #42).
- ipmi: add the possibility to pass -j and -f cli flags to conman (fix #41).

## [0.20141106] - 2014-11-06

### Changed
- images: make 'package_file' and 'preseed_file' optional (fix #40).
- images: remove mkinitrfs and initramfsc. We'll use the system's mkinitramfs
  and the configuration is installed by a package.

### Fixed
- images: several bugfixes.

## [0.20141105] - 2014-11-05

### Changed
- doc: update manpages
- core: update depends on slurm-llnl to slurm-client.

## [0.20141031] - 2014-10-31

### Added
- core: Add initial bash_completion file (fix #37).

### Changed
- ipmi: fallback to ipmtool directly for connect when the host is provided
  using an IP address (fix #39).

## [0.20141021] - 2014-10-21

### Added
- ipmi: add deconnect command

### Changed
- images: always set the root password to 'clara', this is a temporary password
  anyway (fix #38).

### Fixed
- core:A bunch of bugfixes.

## [0.20141014] - 2014-10-14

### Added
- core: add to all the temp files and dirs the prefix 'tmpClara'

### Changed
- p2p: prevent services from starting automatically when creating an image.
- images: add option --keep-chroot-dir to not remove temp chroot (fix #36)

## [0.20141013] - 2014-10-13

### Added
- core: add logging to clara (fix #26)
- core: run sudo if you launch clara as a normal user

### Changed
- impi do not append 'imm' when host is an IP address (fix #35)
- images: only stop puppet and dbus daemons if they're installed.

## [0.20141010] - 2014-10-10

### Added
- images: add a way to not regenerate the image if we want to dismiss our
  changes (fix #30)

### Changed
- images: Rename important_packages as extra_packages_image (fix #31)
- images: make sure puppet and dbus are stopped before unmounting the chroot.

### Fixed
- repo: bugfix.

## [0.20141009] - 2014-10-09

### Added
- images: allow to specify the path of the generated files (fix #33)
- repo: add option to pass reprepro flags (fix #27)

### Changed
- ipmi: getmac() show an error when the host doesn't exist
- images: use ":" to separate ip/hostnames instead of "," (fix #34)
- images: do not assume that the mirror has the format server+"/debian"

### Removed
- doc: remove the file FEATURES, this information is now in the manpages.

## [0.20141008] - 2014-10-08

### Added
- core: add debug mode with option "-d" in bin/clara that shows all the command
  run by the plugins, with a new class Conf for runtime configuration
  parameters based in initial patch by @rezib (fix #8)
- core: now we can provide a config.ini file from the command line (fix #32)

### Removed
- core: remove the possibility to have a user config file in ~/config/clara/.
  It's better to prevent confusion to provide a file explicitily in the command
  line when the user doesn't want to use the default one.

## [0.2014100702] - 2014-10-07

### Added
- images: add the option to install an extra list of packages when creating the
  initrd. The list is provided in config.ini with the parameter 'packages_initrd'
- imates: modify prompt to add the distribution (fix #29)

### Changed
- repo: remove hard-coded parameters, they're now in info_suites in config.ini
  (fix #25)

## [0.20141007] - 2014-10-07

### Added
- enc: add command clara enc edit.
- enc: now we can declare the plugin done (fix #6)

### Changed
- doc: update manpage with commands and examples
- doc: update the manpages for 'clara images' and 'clara repo'
- core: in config.ini file, rename some parameters: 'distribution' to
  'default_distribution' and 'distributions' to 'allowed_distributions'

## [0.20141006-2] - 2014-10-06

### Added
- repo: add clara repo list.
- enc: initial plugin release

### Fixed
- core: Several bugfixes.

## [0.20141006-1] - 2014-10-06

### Added
- repo: add 'clara repo sync all' that will sync all suites.
- repo: allow to sync any suite no matter what's the default distribution set.
- images: allow to change the name of the output image. Now 'clara images
  create', 'clara images repack' and 'clara images unpack' will take an
  argument with the name of the image if we want to use something different to
  the name by default.
- images: add the possibility to run a script after the image creation. The
  path to the script must be added in the config.ini

### Changed
- doc: some updates in the manpages.
- core: update the Depends line. And add a Recommends on gnupg-agent.
- core: refresh the long description.
- images: remove work_dir upon exit using atexit.
- images: do not install recommended packages
- images: missing files are treated as Warnings and not Errors
- images: run mkinitramfs inside the target image.

## [0.20141003] - 2014-10-03

### Changed
- ipmi: rename plugin nodes as ipmi.
- core: create docs/man directory at build time.
- images:'editimg' is now 'edit' and 'genimg' is now 'create'.

## [0.20140924] - 2014-09-24

### Added
- repo: allow selecting which suites the user want to mirror locally.
  Alternativaly, just add --dist=distribution to mirror all the suites used by
  the default distribution. This feature contains hardcodes variables and it
  needs to be fixed once we update serveurs.c.e.f (fix #24)

### Changed
- images: check if partitions are mounted before unmounting them.
- images: make sure /proc/sys/fs/binfmt_misc is unmounted (fix #22)

### Removed
- core: Remove from config.ini remote_modules and local_modules. They are now
  obsolete.

## [0.20140922] - 2014-09-22

### Added
- doc: add manpages

### Changed
- core: update packaging to build manpages in build time with a b-d on pandoc.
- core: Make "clara help <plugin>" show the manpage of the plugin and "clara
  help", the generic manpage of clara.

## [0.20140917] - 2014-09-17

### Added
- ipmi: add alternative order of options in the plugin nodes (fix #21)
- core: add clara/version.py. This file is updated automatically by setup.py
  and it's used by bin/clara to show the versin (fix #11)

### Changed
- core: update debian/rules to always remove the *.egg directory.

### Removed
- images: Remove obsolete option "images apply_config2img", it has been
- core: delete unnecesary code. The file decoding is done by Puppet (fix #15).

## [0.20140916] - 2014-09-16

### Changed
- ipmi: rename PASSWD to IMMPASSWORD to avoid confusion (fix #12)
- core: dosmetic changes (fix #13)
- ipmi: supress output from "service conman status" (fix #18)
- core: change behavior when a value is not in the config file (fix #10)

### Fixed
- ipmi: fix ipmitool calls (fix #14, #20)
- ipmi: connect can only use one host/node (fix #16)
- ipmi: conman returns 3 when is not running if we use systemd (fix #19)

### Removed
- core: remove obsolete option, now it's in a separate plugin (fix #17)

## [0.201400818] - 2014-08-18

### Added
- repo: add support for multi-distribution, read in the FEATURES file how this
  works (fix #7).

## [0.201400814] - 2014-08-14

### Added
- repo: add command now handles multiple *.dsc *.changes and *.deb in the same
  command. clara repo del has been updated accordingly (fix #2).

## [0.201400812] - 2014-08-12

### Added
- images: Add command "editimg" to the plugin (fix #5)
- core: Add a [common] section in configuration file
- doc: document configuration parameters

### Changed
- slurm: update the commands in the plugin slurm (fix #4)

## [0.201400807] - 2014-08-07

### Changed
- images: remove the temporary files in case of failure while building the image.
- core: add some checks to make sure the files and the directories from the config
  file really exist (fix #1)

## [0.201400806] - 2014-08-06

### Changed
- p2p: split commands in a different plugin p2p.

## [0.201400805] - 2014-08-05

### Changed
-slurm: split slurm as a separate plugin.

## [0.201400804] - 2014-08-04

### Changed
- images: date package dabatase before dpkg --set-selections. See #703092

## [0.201400606] - 2014-06-06

### Added
core: initial Release.
