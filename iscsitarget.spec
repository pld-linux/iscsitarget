#
# Conditional build:
%bcond_without	dist_kernel	# allow non-distribution kernel
%bcond_without	kernel		# don't build kernel modules
%bcond_without	userspace	# don't build userspace module
%bcond_with	verbose		# verbose build (V=1)
#
%define		_rel 16
Summary:	iSCSI target - SCSI over IP
Summary(pl.UTF-8):	iSCSI target - SCSI po IP
Name:		iscsitarget
Version:	1.4.20.2
Release:	%{_rel}
License:	GPL
Group:		Base/Kernel
Source0:	http://dl.sourceforge.net/iscsitarget/%{name}-%{version}.tar.gz
# Source0-md5:	2f23c0bfe124d79f5c20e34ef2aaff82
Source1:	%{name}.init
Source2:	%{name}.sysconfig
Patch0:		iscsitarget-2.6.37.patch
Patch1:		iscsitarget-2.6.38.patch
URL:		http://iscsitarget.sourceforge.net/
BuildRequires:	rpmbuild(macros) >= 1.379
BuildRequires:	openssl-devel
%if %{with kernel}
%{?with_dist_kernel:BuildRequires:	kernel%{_alt_kernel}-module-build >= 3:2.6.20.2}
%endif
Requires(post,preun):	/sbin/chkconfig
Requires:	rc-scripts
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)

%define		_sbindir	/sbin

%description
An Open Source iSCSI target with aim to have professional features,
work well in enterprise environment under real workload, and be
scalable and versatile enough to meet the challenge of future storage
needs and developements.

%description -l pl.UTF-8
Sterownik iSCSI o otwartych źródłach, którego celem jest posiadanie
profesjonalnych możliwości, poprawna praca w środowisku enterprise pod
prawdziwym obciążeniem oraz skalowalność i wszechstronność pozwalająca
na sprostanie wyzwaniom przyszłych potrzeb i rozwoju składowania
danych.

%package -n kernel-targetiscsi
Summary:	iSCSI kernel module
Summary(pl.UTF-8):	Moduł jądra iSCSI
Release:	%{_rel}@%{_kernel_ver_str}
Group:		Base/Kernel
Requires:	%{name} = %{version}-%{_rel}

%description -n kernel-targetiscsi
IP over SCSI Target kernel module.

%description -n kernel-targetiscsi -l pl.UTF-8
Moduł jądra dla protokołu IP over SCSI (Target).

%prep
%setup -q
%patch0 -p1
%patch1 -p1

%build
%if %{with kernel}
%build_kernel_modules -C kernel -m iscsi_trgt
%endif

%if %{with userspace}
%{__make} -C usr \
	CC="%{__cc}" \
	CFLAGS="%{rpmcflags} %{rpmcppflags} -fno-inline -Wall -I../include -D_GNU_SOURCE"
%endif

%install
rm -rf $RPM_BUILD_ROOT
install -d $RPM_BUILD_ROOT{%{_sbindir},%{_mandir}/man{1,5,8},/etc/{rc.d/init.d,sysconfig}}

%if %{with kernel}
%install_kernel_modules -m kernel/iscsi_trgt -d misc
%endif

%if %{with userspace}
install %{SOURCE1} $RPM_BUILD_ROOT/etc/rc.d/init.d/targetiscsi
install %{SOURCE2} $RPM_BUILD_ROOT/etc/sysconfig/targetiscsi

install etc/ietd.conf $RPM_BUILD_ROOT%{_sysconfdir}

install usr/ietd usr/ietadm $RPM_BUILD_ROOT%{_sbindir}
install doc/manpages/*.5 $RPM_BUILD_ROOT%{_mandir}/man5
install doc/manpages/*.8 $RPM_BUILD_ROOT%{_mandir}/man8
%endif

%clean
rm -rf $RPM_BUILD_ROOT

%post -n kernel-targetiscsi
%depmod %{_kernel_ver}

%postun -n kernel-targetiscsi
%depmod %{_kernel_ver}

%post
/sbin/chkconfig --add targetiscsi

%preun
if [ "$1" = "0" ]; then
	%service targetiscsi stop
	/sbin/chkconfig --del targetiscsi
fi

%if %{with userspace}
%files
%defattr(644,root,root,755)
%doc ChangeLog
%attr(755,root,root) %{_sbindir}/*
%attr(640,root,root) %config(noreplace) %verify(not md5 mtime size) %{_sysconfdir}/ietd.conf
%{_mandir}/man?/*
%attr(754,root,root) /etc/rc.d/init.d/targetiscsi
%attr(640,root,root) %config(noreplace) %verify(not md5 mtime size) /etc/sysconfig/targetiscsi
%endif

%if %{with kernel}
%files -n kernel-targetiscsi
%defattr(644,root,root,755)
/lib/modules/%{_kernel_ver}/misc/*
%endif
