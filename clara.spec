# Configuration Logic
%define name clara
%define version 0.20200617
%define unmangled_version 0.20200617
%define unmangled_version 0.20200617
%define debug_package %{nil}

# Main preamble
Summary: Clara, a set of Cluster Administration Tools
Name: %{name}
Version: %{version}
Release:  1%{?dist}.edf
Source0: %{name}-%{unmangled_version}.tar.gz
License: GPLv3
Group: Application/System
Prefix: %{_prefix}
Vendor: EDF CCN HPC <dsp-cspito-ccn-hpc@edf.fr>
Url: https://github.com/scibian/%{__name}

BuildRequires: git python36 python3-setuptools pandoc texlive-latex
Requires: clara-core clara-plugin-chroot clara-plugin-enc
Requires: clara-plugin-images clara-plugin-ipmi clara-plugin-p2p
Requires: clara-plugin-show clara-plugin-repo clara-plugin-slurm
Requires: clara-plugin-virt

%description
This is a meta-package that provides Clara software.
Clara is a set of Cluster Administration Tools.

#########################################
# Prep, Setup, Build, Install & clean   #
#########################################

%prep
%setup -q

# Build Section
%build
python3 setup.py build
mkdir docs/man
make --directory=docs

# Install & clean sections
%install
python3 setup.py install --single-version-externally-managed -O1 --root=%{buildroot}
install -d %{buildroot}/etc/clara
install -d %{buildroot}/etc/clara/templates/vm
install -d %{buildroot}/etc/clara/templates/volume
install -d %{buildroot}/etc/bash_completion.d
install -m 644 example-conf/config.ini %{buildroot}/etc/clara
install -m 644 example-conf/virt.ini %{buildroot}/etc/clara
install -m 644 contribs/bash-completion %{buildroot}/etc/bash_completion.d/clara
install -m 644 example-conf/templates/vm/default.xml %{buildroot}/etc/clara/templates/vm
install -m 644 example-conf/templates/volume/default.xml %{buildroot}/etc/clara/templates/volume

%clean
rm -rf %{buildroot}

#############
# Preambles #
#############

# clara-core package preamble
%package core
Summary: This package provides the core engine of Clara.
Group: Application/System
Requires: python36 python3-docopt python3-clustershell
%description core
Cluster administration tools core engine.
Clara is a set of tools to help administering and installing clusters.

# clara-plugin-build package preamble
# deprecated pacakage that could be removed.
# It requires cowbuilder that is no available as rpm.
%package plugin-build
Summary: This package provides the build plugin of Clara.
Group: Application/System
Requires: clara-core
Recommends: cowbuilder
%description plugin-build
Cluster administration tools build plugin
Clara is a set of tools to help administering and installing clusters.

# clara-plugin-chroot package preamble
%package plugin-chroot
Summary: This package provides the chroot plugin of Clara.
Group: Application/System
Requires: clara-core debootstrap squashfs-tools
%description plugin-chroot
Cluster administration tools chroot plugin
Clara is a set of tools to help administering and installing clusters.

# clara-plugin-enc package preamble
%package plugin-enc
Summary: This package provides the enc plugin of Clara.
Group: Application/System
Requires: clara-core
%description plugin-enc
Cluster administration tools enc plugin
Clara is a set of tools to help administering and installing clusters.

# clara-plugin-image package preamble
%package plugin-images
Summary: This package provides the images plugin of Clara.
Group: Application/System
Requires: clara-core debootstrap squashfs-tools python3-paramiko
%description plugin-images
Cluster administration tools image plugin
Clara is a set of tools to help administering and installing clusters.

# clara-plugin-ipmi package preamble
%package plugin-ipmi
Summary: This package provides the ipmi plugin of Clara.
Group: Application/System
Requires: clara-core fping ipmitool sshpass
%description plugin-ipmi
Cluster administration tools ipmi plugin
Clara is a set of tools to help administering and installing clusters.

# clara-plugin-p2p package preamble
%package plugin-p2p
Summary: This package provides the p2p plugin of Clara.
Group: Application/System
Requires: clara-core mktorrent python3-paramiko
%description plugin-p2p
Cluster administration tools p2p plugin
Clara is a set of tools to help administering and installing clusters.


# clara-plugin-repo package preamble
%package plugin-repo
Summary: This package provides the repo plugin of Clara.
Group: Application/System
Requires: clara-core gnupg debmirror
Recommends: reprepro
%description plugin-repo
Cluster administration tools repo plugin
Clara is a set of tools to help administering and installing clusters.

# clara-plugin-slurm package preamble
%package plugin-slurm
Summary: This package provides the slurm plugin of Clara.
Group: Application/System
# slurm-client is provided by slurm package
Requires: clara-core slurm
%description plugin-slurm
Cluster administration tools slurm plugin
Clara is a set of tools to help administering and installing clusters.

# clara-plugin-virt package preamble
%package plugin-virt
Summary: This package provides the virt plugin of Clara.
Group: Application/System
Requires: clara-core python3-libvirt python3-jinja2 python3-humanize
%description plugin-virt
Cluster administration tools virt plugin
Clara is a set of tools to help administering and installing clusters.

# clara-plugin-show package preamble
%package plugin-show
Summary: This package provides the virt plugin of Clara.
Group: Application/System
Requires: clara-core 
%description plugin-show
Cluster administration tools show plugin
Clara is a set of tools to help administering and installing clusters.

##################
# Files Sections #
##################

# Main meta-package
%files

# core
%files core
%defattr(-,root,root,-)
%doc README.md
%doc /docs/users_guide.pdf
%config /etc/clara/config.ini
/etc/bash_completion.d/clara
/usr/bin/clara
%{python3_sitelib}/clara/*.py
%{python3_sitelib}/clara/plugins/__init__.py
%{python3_sitelib}/*.egg-info
%{python3_sitelib}/clara/__pycache__/*.pyc
%{python3_sitelib}/clara/plugins/__pycache__/__init__.cpython-36.pyc
%{python3_sitelib}/clara/plugins/__pycache__/__init__.cpython-36.opt-1.pyc

# plugin-build
%files plugin-build
%defattr(-,root,root,-)
%doc /docs/man/clara-build.1
%{python3_sitelib}/clara/plugins/clara_build.py
%{python3_sitelib}/clara/plugins/__pycache__/clara_build.*


# plugin-chroot
%files plugin-chroot
%defattr(-,root,root,-)
%doc /docs/man/clara-chroot.1
%{python3_sitelib}/clara/plugins/clara_chroot.py
%{python3_sitelib}/clara/plugins/__pycache__/clara_chroot.*

# plugin-enc
%files plugin-enc
%defattr(-,root,root,-)
%doc /docs/man/clara-enc.1
%{python3_sitelib}/clara/plugins/clara_enc.py
%{python3_sitelib}/clara/plugins/__pycache__/clara_enc.*

# plugin-images
%files plugin-images
%defattr(-,root,root,-)
%doc /docs/man/clara-images.1
%{python3_sitelib}/clara/plugins/clara_images.py
%{python3_sitelib}/clara/plugins/__pycache__/clara_images.*

# plugin-ipmi
%files plugin-ipmi
%defattr(-,root,root,-)
%doc /docs/man/clara-ipmi.1
%{python3_sitelib}/clara/plugins/clara_ipmi.py
%{python3_sitelib}/clara/plugins/__pycache__/clara_ipmi.*

# plugin-p2p
%files plugin-p2p
%defattr(-,root,root,-)
%doc /docs/man/clara-p2p.1
%{python3_sitelib}/clara/plugins/clara_p2p.py
%{python3_sitelib}/clara/plugins/__pycache__/clara_p2p.*

# plugin-show
%files plugin-show
%defattr(-,root,root,-)
%doc /docs/man/clara-show.1
%{python3_sitelib}/clara/plugins/clara_show.py
%{python3_sitelib}/clara/plugins/__pycache__/clara_show.*

# plugin-repo
%files plugin-repo
%defattr(-,root,root,-)
%doc /docs/man/clara-repo.1
%{python3_sitelib}/clara/plugins/clara_repo.py
%{python3_sitelib}/clara/plugins/__pycache__/clara_repo.*

# plugin-slurm
%files plugin-slurm
%defattr(-,root,root,-)
%doc /docs/man/clara-slurm.1
%{python3_sitelib}/clara/plugins/clara_slurm.py
%{python3_sitelib}/clara/plugins/__pycache__/clara_slurm.*

# plugin-virt
%files plugin-virt
%defattr(-,root,root,-)
%doc /docs/man/clara-virt.1
%{python3_sitelib}/clara/plugins/clara_virt.py
%{python3_sitelib}/clara/virt
%{python3_sitelib}/clara/plugins/__pycache__/clara_virt.*
/etc/clara/virt.ini
/etc/clara/templates/vm/default.xml
/etc/clara/templates/volume/default.xml


%changelog
* Thu Jun 30 2020 Pierre Trespeuch <pierre-externe.trespeuch@edf.fr> - 0.20200617-1el8.edf
- Initial RPM release


