%define haproxy_user    haproxy
%define haproxy_uid     188
%define haproxy_group   haproxy
%define haproxy_gid     188
%define haproxy_home    %{_localstatedir}/lib/haproxy
%define haproxy_confdir %{_sysconfdir}/haproxy
%define haproxy_datadir %{_datadir}/doc/haproxy-%{version}

Name: haproxy
Summary: HA-Proxy is a TCP/HTTP reverse proxy for high availability environments
Version: 1.7.3
Release: 1%{?dist}
License: GPLv2+
URL: http://haproxy.org/
Group: System Environment/Daemons

Source0: http://www.haproxy.org/download/1.6/src/haproxy-%{version}.tar.gz
Source1: haproxy.init
Source2: haproxy.cfg
Source3: haproxy.logrotate

Requires(pre): %{_sbindir}/groupadd
Requires(pre): %{_sbindir}/useradd
%if 0%{rhel} == 6
Requires(post): /sbin/chkconfig
Requires(preun): /sbin/chkconfig
Requires(preun): /sbin/service
Requires(postun): /sbin/service
%endif
%if 0%{rhel} == 7
Requires: /bin/systemctl
%endif

BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildRequires: pcre-devel
BuildRequires: openssl-devel
BuildRequires: zlib-devel
%if 0%{rhel} == 7
BuildRequires: systemd-devel
%endif
Requires: pcre
Requires: openssl
Requires: zlib
Requires: setup >= 2.8.14-14

%description
HAProxy is a free, fast and reliable solution offering high
availability, load balancing, and proxying for TCP and HTTP-based
applications. It is particularly suited for web sites crawling under
very high loads while needing persistence or Layer7 processing.
Supporting tens of thousands of connections is clearly realistic with
modern hardware. Its mode of operation makes integration with existing
architectures very easy and riskless, while still offering the
possibility not to expose fragile web servers to the net.

%prep
%setup -q

%build
%ifarch %ix86 x86_64
use_regparm="USE_REGPARM=1"
%endif

make %{?_smp_mflags} ARCH="x86_64" CPU="generic" TARGET="linux2628" USE_ZLIB=1 USE_PCRE=1 USE_OPENSSL=1 ${use_regparm}

pushd contrib/halog
make halog
popd

%if 0%{rhel} == 7
pushd contrib/systemd
sed -e 's:@SBINDIR@:%{_sbindir}:' haproxy.service.in > haproxy.service
popd
%endif

%install
rm -rf %{buildroot}
make install-bin DESTDIR=%{buildroot} PREFIX=%{_prefix}
make install-man DESTDIR=%{buildroot} PREFIX=%{_prefix}

%{__install} -p -D -m 0644 %{SOURCE2} %{buildroot}%{haproxy_confdir}/%{name}.cfg
%{__install} -p -D -m 0644 %{SOURCE3} %{buildroot}%{_sysconfdir}/logrotate.d/%{name}
%{__install} -d -m 0755 %{buildroot}%{haproxy_home}
%{__install} -d -m 0755 %{buildroot}%{haproxy_datadir}
%{__install} -d -m 0755 %{buildroot}%{_bindir}
%{__install} -p -m 0755 ./contrib/halog/halog %{buildroot}%{_bindir}/halog
%{__install} -p -m 0644 ./examples/errorfiles/* %{buildroot}%{haproxy_datadir}
%if 0%{rhel} == 6
%{__install} -p -D -m 0755 %{SOURCE1} %{buildroot}%{_initrddir}/%{name}
%endif
%if 0%{rhel} == 7
%{__install} -p -m 0755 haproxy-systemd-wrapper %{buildroot}%{_sbindir}
%{__install} -d -m 0755 %{buildroot}%{_unitdir}
%{__install} -p -m 0644 ./contrib/systemd/haproxy.service %{buildroot}%{_unitdir}
%endif

find %{buildroot}

for file in $(find . -type f -name '*.txt') ; do
    iconv -f ISO-8859-1 -t UTF-8 -o $file.new $file && \
    touch -r $file $file.new && \
    mv $file.new $file
done

%clean
rm -rf %{buildroot}

%pre
%{_sbindir}/groupadd -g %{haproxy_gid} -r %{haproxy_group} 2>/dev/null || :
%{_sbindir}/useradd -u %{haproxy_uid} -g %{haproxy_group} -d %{haproxy_home} -s /sbin/nologin -r %{haproxy_user} 2>/dev/null || :

%post
%if 0%{rhel} == 6
/sbin/chkconfig --add haproxy
%endif
%if 0%{rhel} == 7
/bin/systemctl daemon-reload
%endif

%preun
%if 0%{rhel} == 6
if [ "$1" -eq 0 ]; then
	/sbin/service haproxy stop >/dev/null 2>&1
	/sbin/chkconfig --del haproxy
fi
%endif
%if 0%{rhel} == 7
if [ "$1" -eq 0 ]; then
	/bin/systemctl disable haproxy
	/bin/systemctl stop haproxy
fi
%endif

%postun
%if 0%{rhel} == 6
if [ "$1" -ge 1 ]; then
    /sbin/service haproxy condrestart >/dev/null 2>&1 || :
fi
%endif
%if 0%{rhel} == 7
if [ "$1" -ge 1 ]; then
    /bin/systemctl restart haproxy >/dev/null 2>&1 || :
fi
%endif

%files
%defattr(-,root,root,-)
%doc CHANGELOG LICENSE README doc/*
%doc examples/*.cfg
%dir %{haproxy_datadir}
%dir %{haproxy_confdir}
%config(noreplace) %{haproxy_confdir}/%{name}.cfg
%config(noreplace) %{_sysconfdir}/logrotate.d/%{name}
%{_sbindir}/%{name}
%{_bindir}/halog
%{_mandir}/man1/%{name}.1.gz
%if 0%{rhel} == 6
%{_initrddir}/%{name}
%endif
%if 0%{rhel} == 7
%{_sbindir}/%{name}-systemd-wrapper
%{_unitdir}/%{name}.service
%endif
%attr(-,%{haproxy_user},%{haproxy_group}) %dir %{haproxy_home}

%changelog
* Thu Mar 02 2017 Steven Haigh <netwiz@crc.id.au> - 1.7.3-1
- Update to upstream 1.7.3

* Mon Feb 20 2017 Steven Haigh <netwiz@crc.id.au> - 1.7.2-1
- Update to upstream 1.7.2

* Sat Aug 06 2016 Steven Haigh <netwiz@crc.id.au> - 1.6.7-1
- Update to upstream 1.6.7
- Enable building for el7 with systemd.

* Thu Jan 07 2016 Steven Haigh <netwiz@crc.id.au> - 1.6.3-1
- Update to upstream 1.6.3

* Wed Oct 21 2015 Steven Haigh <netwiz@crc.id.au> - 1.6.1-1
- Update to upstream 1.6.1

* Wed Aug 26 2015 Steven Haigh <netwiz@crc.id.au> - 1.5.14-1
- Update to upstream 1.5.14

* Wed Sep 03 2014 Steven Haigh <netwiz@crc.id.au> - 1.5.4-1
- Update to upstream 1.5.4
        - BUG: config: error in http-response replace-header number of arguments
        - BUG/MINOR: Fix search for -p argument in systemd wrapper.
        - BUG/MEDIUM: auth: fix segfault with http-auth and a configuration with an unknown encryption algorithm
        - BUG/MEDIUM: config: userlists should ensure that encrypted passwords are supported
        - MEDIUM: connection: add new bit in Proxy Protocol V2
        - BUG/MINOR: server: move the directive #endif to the end of file
        - BUG/MEDIUM: http: tarpit timeout is reset
        - BUG/MAJOR: tcp: fix a possible busy spinning loop in content track-sc*
        - BUG/MEDIUM: http: fix inverted condition in pat_match_meth()
        - BUG/MEDIUM: http: fix improper parsing of HTTP methods for use with ACLs
        - BUG/MINOR: pattern: remove useless allocation of unused trash in pat_parse_reg()
        - BUG/MEDIUM: acl: correctly compute the output type when a converter is used
        - CLEANUP: acl: cleanup some of the redundancy and spaghetti after last fix
        - BUG/CRITICAL: http: don't update msg->sov once data start to leave the buffer

* Wed Aug 19 2014 Steven Haigh <netwiz@crc.id.au> - 1.5.3-2
- Update to upstream 1.5.3
- Enabled zlib compression.

* Wed Jul 16 2014 Steven Haigh <netwiz@crc.id.au> - 1.5.2-1
- Update to upstream 1.5.2
- Import RH package based on 1.4.24

* Wed Jul 10 2013 Ryan O'Hara <rohara@redhat.com> - 1.4.24-2
- Drop supplementary groups after setuid/setgid calls.
  Resolves: rhbz#903303

* Wed Jul 10 2013 Ryan O'Hara <rohara@redhat.com> - 1.4.24-1
- Rebase to upstream version 1.4.24.
  Resolves: rhbz#947987
- Rewrite rules flaw can lead to arbitrary code execution (CVE-2013-1912).
  Resolves: rhbz#947701
- Fix possible crash when using negative header occurrences (CVE-2013-2175).
  Resolves: rhbz#974263
- Enable TPROXY support.
  Resolves: rhbz#921064

* Tue Oct 02 2012 Ryan O'Hara <rohara@redhat.com> - 1.4.22-3
- Use static uid/gid.
  Resolves: rhbz#846067

* Fri Sep 21 2012 Ryan O'Hara <rohara@redhat.com> - 1.4.22-2
- Bump release number.
  Resolves: rhbz#846067

* Thu Sep 20 2012 Ryan O'Hara <rohara@redhat.com> - 1.4.22-1
- Initial build.
  Resolves: rhbz#846067