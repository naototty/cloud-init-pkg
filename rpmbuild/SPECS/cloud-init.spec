%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

%define use_systemd (0%{?fedora} && 0%{?fedora} >= 18) || (0%{?rhel} && 0%{?rhel} >= 7)

%if %{use_systemd}
%define init_system systemd
%else
%define init_system sysvinit
%endif

# See: http://www.zarb.org/~jasonc/macros.php
# Or: http://fedoraproject.org/wiki/Packaging:ScriptletSnippets
# Or: http://www.rpm.org/max-rpm/ch-rpm-inside.html

Name:           cloud-init
Version:        18.1+7.gf9f7ffd7
## Release:        1%%{?dist}
##Release:        1.1%%{?dist}
Release:        1.2%{?dist}
Summary:        Cloud instance init scripts

Group:          System Environment/Base
License:        Dual-licesed GPLv3 or Apache 2.0
URL:            http://launchpad.net/cloud-init

Source0:        cloud-init-18.1-7-gf9f7ffd7.tar.gz
BuildArch:      noarch
BuildRoot:      %{_tmppath}

#  cp cloud-init-079-rhel/cloud-init-tmpfiles.conf SOURCES/cloud-init-tmpfiles.conf-rhel-run-tmp
#  cp /etc/cloud/cloud.cfg SOURCES/cloud-init-cloud.cfg-ZCOM-ENT
Source10001:    cloud-init-tmpfiles.conf-rhel-run-tmp
Source10002:    cloud-init-cloud.cfg-ZCOM-ENT

Patch10011:     cloud-init-18.1-7-git-cloud-init-local.patch

%if "%{?el6}" == "1"
BuildRequires:  python-argparse
%endif
%if %{use_systemd}
Requires:           systemd
BuildRequires:      systemd
Requires:           systemd-units
BuildRequires:      systemd-units
%else
Requires:           initscripts >= 8.36
Requires(postun):   initscripts
Requires(post):     chkconfig
Requires(preun):    chkconfig
%endif

# These are runtime dependencies, but declared as BuildRequires so that
# - tests can be run here.
# - parts of cloud-init such (setup.py) use these dependencies.
BuildRequires:  python-configobj
BuildRequires:  python-oauthlib
BuildRequires:  python-six
BuildRequires:  PyYAML
BuildRequires:  python-jsonpatch
BuildRequires:  python-jinja2
BuildRequires:  python-jsonschema
BuildRequires:  python-requests
BuildRequires:  e2fsprogs
BuildRequires:  iproute
BuildRequires:  net-tools
BuildRequires:  procps
BuildRequires:  rsyslog
BuildRequires:  shadow-utils
BuildRequires:  sudo
BuildRequires:  python-devel
BuildRequires:  python-setuptools

# System util packages needed
%ifarch %{?ix86} x86_64 ia64
Requires:       dmidecode
%endif

# python2.6 needs argparse
%if "%{?el6}" == "1"
Requires:  python-argparse
%endif


# Install 'dynamic' runtime reqs from *requirements.txt and pkg-deps.json
Requires:       python-configobj
Requires:       python-oauthlib
Requires:       python-six
Requires:       PyYAML
Requires:       python-jsonpatch
Requires:       python-jinja2
Requires:       python-jsonschema
Requires:       python-requests
Requires:       e2fsprogs
Requires:       iproute
Requires:       net-tools
Requires:       procps
Requires:       rsyslog
Requires:       shadow-utils
Requires:       sudo
Requires:       python-devel
Requires:       python-setuptools

# Custom patches

%if "%{init_system}" == "systemd"
Requires(post):       systemd
Requires(preun):      systemd
Requires(postun):     systemd
%else
Requires(post):       chkconfig
Requires(postun):     initscripts
Requires(preun):      chkconfig
Requires(preun):      initscripts
%endif

%description
Cloud-init is a set of init scripts for cloud instances.  Cloud instances
need special scripts to run during initialization to retrieve and install
ssh keys and to let the user run various scripts.

%prep
%setup -q -n cloud-init-18.1-7-gf9f7ffd7

%patch10011 -p1

# Custom patches activation

%build
%{__python} setup.py build

%install

%{__python} setup.py install -O1 \
            --skip-build --root $RPM_BUILD_ROOT \
            --init-system=%{init_system}

mkdir -p $RPM_BUILD_ROOT/var/lib/cloud

# /run/cloud-init needs a tmpfiles.d entry
mkdir -p $RPM_BUILD_ROOT/run/cloud-init
mkdir -p $RPM_BUILD_ROOT/%{_tmpfilesdir}
%if "%{?el6}" != "1"
cp -p %{SOURCE10001} $RPM_BUILD_ROOT/%{_tmpfilesdir}/%{name}.conf
%endif

# Note that /etc/rsyslog.d didn't exist by default until F15.
# el6 request: https://bugzilla.redhat.com/show_bug.cgi?id=740420
install -D -m755 tools/net-convert.py $RPM_BUILD_ROOT/%{_bindir}/net-convert.py
sed -i -e 's/python3/python/g' $RPM_BUILD_ROOT/%{_bindir}/net-convert.py

## EL6 disabled growroot
touch $RPM_BUILD_ROOT/%{_sysconfdir}/growroot-disabled

mkdir -p $RPM_BUILD_ROOT/%{_sysconfdir}/rsyslog.d
cp -p tools/21-cloudinit.conf \
      $RPM_BUILD_ROOT/%{_sysconfdir}/rsyslog.d/21-cloudinit.conf

# Remove the tests
rm -rf $RPM_BUILD_ROOT%{python_sitelib}/tests

# Required dirs...
mkdir -p $RPM_BUILD_ROOT/%{_sharedstatedir}/cloud
mkdir -p $RPM_BUILD_ROOT/%{_libexecdir}/%{name}

mv  $RPM_BUILD_ROOT/%{_sysconfdir}/cloud/cloud.cfg $RPM_BUILD_ROOT/%{_sysconfdir}/cloud/cloud.cfg-ORIG
install -D -m755 %{SOURCE10002} $RPM_BUILD_ROOT/%{_sysconfdir}/cloud/cloud.cfg

## tools change python3 to python
find ./tools/ -type f -print0 | xargs -0 sed -i -e 's/python3/python/g'

%clean
rm -rf $RPM_BUILD_ROOT

%post

%if "%{init_system}" == "systemd"
if [ $1 -eq 1 ]
then
    /bin/systemctl enable cloud-config.service     >/dev/null 2>&1 || :
    /bin/systemctl enable cloud-final.service      >/dev/null 2>&1 || :
    /bin/systemctl enable cloud-init.service       >/dev/null 2>&1 || :
    /bin/systemctl enable cloud-init-local.service >/dev/null 2>&1 || :
fi
%else
/sbin/chkconfig --add %{_initrddir}/cloud-init-local
/sbin/chkconfig --add %{_initrddir}/cloud-init
/sbin/chkconfig --add %{_initrddir}/cloud-config
/sbin/chkconfig --add %{_initrddir}/cloud-final
%endif

%preun

%if "%{init_system}" == "systemd"
if [ $1 -eq 0 ]
then
    /bin/systemctl --no-reload disable cloud-config.service >/dev/null 2>&1 || :
    /bin/systemctl --no-reload disable cloud-final.service  >/dev/null 2>&1 || :
    /bin/systemctl --no-reload disable cloud-init.service   >/dev/null 2>&1 || :
    /bin/systemctl --no-reload disable cloud-init-local.service >/dev/null 2>&1 || :
fi
%else
if [ $1 -eq 0 ]
then
    /sbin/service cloud-init stop >/dev/null 2>&1 || :
    /sbin/chkconfig --del cloud-init || :
    /sbin/service cloud-init-local stop >/dev/null 2>&1 || :
    /sbin/chkconfig --del cloud-init-local || :
    /sbin/service cloud-config stop >/dev/null 2>&1 || :
    /sbin/chkconfig --del cloud-config || :
    /sbin/service cloud-final stop >/dev/null 2>&1 || :
    /sbin/chkconfig --del cloud-final || :
fi
%endif

%postun

%if "%{init_system}" == "systemd"
/bin/systemctl daemon-reload >/dev/null 2>&1 || :
%endif

%files

/lib/udev/rules.d/66-azure-ephemeral.rules

%if "%{init_system}" == "systemd"
/usr/lib/systemd/system-generators/cloud-init-generator
%{_unitdir}/cloud-*
%else
%attr(0755, root, root) %{_initddir}/cloud-config
%attr(0755, root, root) %{_initddir}/cloud-final
%attr(0755, root, root) %{_initddir}/cloud-init-local
%attr(0755, root, root) %{_initddir}/cloud-init
%endif

%{_sysconfdir}/NetworkManager/dispatcher.d/hook-network-manager
%{_sysconfdir}/dhcp/dhclient-exit-hooks.d/hook-dhclient

# Program binaries
%{_bindir}/cloud-init*
%{_bindir}/net-convert.py

# Docs
%doc LICENSE ChangeLog TODO.rst requirements.txt
%doc tools doc tests
%doc %{_defaultdocdir}/cloud-init/*

## added
%if "%{?el6}" != "1"
%{_tmpfilesdir}/%{name}.conf
%endif
%dir /run/cloud-init

# Configs
%config                 %{_sysconfdir}/growroot-disabled

%config(noreplace)      %{_sysconfdir}/cloud/cloud.cfg
%config                 %{_sysconfdir}/cloud/cloud.cfg-ORIG
%dir                    %{_sysconfdir}/cloud/cloud.cfg.d
%config(noreplace)      %{_sysconfdir}/cloud/cloud.cfg.d/*.cfg
%config(noreplace)      %{_sysconfdir}/cloud/cloud.cfg.d/README
%dir                    %{_sysconfdir}/cloud/templates
%config(noreplace)      %{_sysconfdir}/cloud/templates/*
%config(noreplace) %{_sysconfdir}/rsyslog.d/21-cloudinit.conf

%{_libexecdir}/%{name}
%dir %{_sharedstatedir}/cloud

# Python code is here...
%{python_sitelib}/*


%changelog
* Fri Apr  7 2018 Naoto Gohko <naoto-gohko@gmo.jp> 18.1-1.2
- change flag: /etc/cloud/cloud.cfg; growpart: {mode: false}
- fixed instance uuid workarround by cloud-init-local init script
- change purege

* Wed Mar  7 2018 Naoto Gohko <naoto-gohko@gmo.jp> 18.1-1.1
- update base 18.1-1(git)

* Tue Sep  5 2017 Karanbir Singh <kbsingh@centos.org> 0.7.9-9.el7.centos.1
- Roll in CentOS Branding
- set default user to centos
- assume Red Hat compatibility

* Thu Jun 22 2017 Lars Kellogg-Stedman <lars@redhat.com> 0.7.9-9
- RHEL/CentOS: Fix default routes for IPv4/IPv6 configuration. (rhbz#1438082)
- azure: ensure that networkmanager hook script runs (rhbz#1440831 rhbz#1460206)
- Fix ipv6 subnet detection (rhbz#1438082)

* Tue May 23 2017 Lars Kellogg-Stedman <lars@redhat.com> 0.7.9-8
- Update patches

* Mon May 22 2017 Lars Kellogg-Stedman <lars@redhat.com> 0.7.9-7
- Add missing sysconfig unit test data (rhbz#1438082)
- Fix dual stack IPv4/IPv6 configuration for RHEL (rhbz#1438082)
- sysconfig: Raise ValueError when multiple default gateways are present. (rhbz#1438082)
- Bounce network interface for Azure when using the built-in path. (rhbz#1434109)
- Do not write NM_CONTROLLED=no in generated interface config files (rhbz#1385172)

* Wed May 10 2017 Lars Kellogg-Stedman <lars@redhat.com> 0.7.9-6
- add power-state-change module to cloud_final_modules (rhbz#1252477)
- remove 'tee' command from logging configuration (rhbz#1424612)
- limit permissions on def_log_file (rhbz#1424612)
- Bounce network interface for Azure when using the built-in path. (rhbz#1434109)
- OpenStack: add 'dvs' to the list of physical link types. (rhbz#1442783)

* Wed May 10 2017 Lars Kellogg-Stedman <lars@redhat.com> 0.7.9-5
- systemd: replace generator with unit conditionals (rhbz#1440831)

* Thu Apr 13 2017 Charalampos Stratakis <cstratak@redhat.com> 0.7.9-4
- Import to RHEL 7
Resolves: rhbz#1427280

* Tue Mar 07 2017 Lars Kellogg-Stedman <lars@redhat.com> 0.7.9-3
- fixes for network config generation
- avoid dependency cycle at boot (rhbz#1420946)

* Tue Jan 17 2017 Lars Kellogg-Stedman <lars@redhat.com> 0.7.9-2
- use timeout from datasource config in openstack get_data (rhbz#1408589)

* Thu Dec 01 2016 Lars Kellogg-Stedman <lars@redhat.com> - 0.7.9-1
- Rebased on upstream 0.7.9.
- Remove dependency on run-parts

* Wed Jan 06 2016 Lars Kellogg-Stedman <lars@redhat.com> - 0.7.6-8
- make rh_subscription plugin do nothing in the absence of a valid
  configuration [RH:1295953]
- move rh_subscription module to cloud_config stage

* Wed Jan 06 2016 Lars Kellogg-Stedman <lars@redhat.com> - 0.7.6-7
- correct permissions on /etc/ssh/sshd_config [RH:1296191]

* Thu Sep 03 2015 Lars Kellogg-Stedman <lars@redhat.com> - 0.7.6-6
- rebuild for ppc64le

* Tue Jul 07 2015 Lars Kellogg-Stedman <lars@redhat.com> - 0.7.6-5
- bump revision for new build

* Tue Jul 07 2015 Lars Kellogg-Stedman <lars@redhat.com> - 0.7.6-4
- ensure rh_subscription plugin is enabled by default

* Wed Apr 29 2015 Lars Kellogg-Stedman <lars@redhat.com> - 0.7.6-3
- added dependency on python-jinja2 [RH:1215913]
- added rhn_subscription plugin [RH:1227393]
- require pyserial to support smartos data source [RH:1226187]

* Fri Jan 16 2015 Lars Kellogg-Stedman <lars@redhat.com> - 0.7.6-2
- Rebased RHEL version to Fedora rawhide
- Backported fix for https://bugs.launchpad.net/cloud-init/+bug/1246485
- Backported fix for https://bugs.launchpad.net/cloud-init/+bug/1411829

* Fri Nov 14 2014 Colin Walters <walters@redhat.com> - 0.7.6-1
- New upstream version [RH:974327]
- Drop python-cheetah dependency (same as above bug)

