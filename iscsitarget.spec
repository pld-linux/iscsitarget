#
# Conditional build:
%bcond_without	dist_kernel	# allow non-distribution kernel
%bcond_without	kernel		# don't build kernel modules
%bcond_without	smp		# don't build SMP module
%bcond_without	userspace	# don't build userspace module
%bcond_with	verbose		# verbose build (V=1)
#
%ifarch sparc
%undefine	with_smp
%endif
#
Summary:	iSCSI target - SCSI over IP
Summary(pl):	iSCSI target - SCSI po IP
Name:		iscsitarget
Version:	0.4.11
%define		_rel 2
Release:	%{_rel}
License:	GPL
Group:		Base/Kernel
Source0:	http://dl.sourceforge.net/iscsitarget/%{name}-%{version}.tar.gz
# Source0-md5:	93ef992ba47a571b9772dccd4800cc52
Source1:	%{name}.init
Source2:	%{name}.sysconfig
URL:		http://iscsitarget.sourceforge.net/
%{?with_dist_kernel:BuildRequires:	kernel-module-build >= 2.6.0}
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)

%define		_sbindir	/sbin

%description
An Open Source iSCSI target with aim to have professional features,
work well in enterprise environment under real workload, and be
scalable and versatile enough to meet the challenge of future storage
needs and developements.

%description -l pl
Sterownik iSCSI o otwartych ¼ród³ach, którego celem jest posiadanie
profesjonalnych mo¿liwo¶ci, poprawna praca w ¶rodowisku enterprise pod
prawdziwym obci±¿eniem oraz skalowalno¶æ i wszechstronno¶æ pozwalaj±ca
na sprostanie wyzwaniom przysz³ych potrzeb i rozwoju sk³adowania
danych.

%package -n kernel-targetiscsi
Summary:	iSCSI kernel module
Summary(pl):	Modu³ j±dra iSCSI
Release:	%{_rel}@%{_kernel_ver_str}
Group:		Base/Kernel
Requires:	%{name} = %{version}-%{_rel}

%description -n kernel-targetiscsi
IP over SCSI Target kernel module.

%description -n kernel-targetiscsi -l pl
Modu³ j±dra dla protoko³u IP over SCSI (Target).

%package -n kernel-smp-targetiscsi
Summary:	iSCSI SMP kernel module
Summary(pl):	Modu³ j±dra SMP iSCSI
Release:	%{_rel}@%{_kernel_ver_str}
Group:		Base/Kernel
Requires:	%{name} = %{version}-%{_rel}

%description -n kernel-smp-targetiscsi
IP over SCSI Target SMP kernel module.

%description -n kernel-smp-targetiscsi -l pl
Modu³ j±dra SMP dla protoko³u IP over SCSI (Target).

%prep
%setup -q

%build
%if %{with kernel}
cd kernel
# kernel module(s)
for cfg in %{?with_dist_kernel:%{?with_smp:smp} up}%{!?with_dist_kernel:nondist}; do
    if [ ! -r "%{_kernelsrcdir}/config-$cfg" ]; then
        exit 1
    fi
    rm -rf include
    install -d include/{linux,config}
    ln -sf %{_kernelsrcdir}/config-$cfg .config
    ln -sf %{_kernelsrcdir}/include/linux/autoconf-$cfg.h include/linux/autoconf.h
%ifarch ppc ppc64
    install -d include/asm
    [ ! -d %{_kernelsrcdir}/include/asm-powerpc ] || ln -sf %{_kernelsrcdir}/include/asm-powerpc/* include/asm
    [ ! -d %{_kernelsrcdir}/include/asm-%{_target_base_arch} ] || ln -snf %{_kernelsrcdir}/include/asm-%{_target_base_arch}/* include/asm
%else
    ln -sf %{_kernelsrcdir}/include/asm-%{_target_base_arch} include/asm
%endif
    ln -sf %{_kernelsrcdir}/Module.symvers-$cfg Module.symvers
    touch include/config/MARKER

    %{__make} -C %{_kernelsrcdir} clean \
        RCS_FIND_IGNORE="-name '*.ko' -o" \
        M=$PWD O=$PWD \
        %{?with_verbose:V=1}
    %{__make} -C %{_kernelsrcdir} modules \
	CC="%{__cc}" \
        M=$PWD O=$PWD \
        %{?with_verbose:V=1}
    mv iscsi_trgt{,-$cfg}.ko
done
cd ..
%endif

%if %{with userspace}
%{__make} -C usr \
	CC="%{__cc}" \
	CFLAGS="%{rpmcflags} -fno-inline -Wall -I../include"
%endif

%install
rm -rf $RPM_BUILD_ROOT
install -d $RPM_BUILD_ROOT{%{_sbindir},%{_mandir}/man{1,5,8},/etc/{rc.d/init.d,sysconfig}}

%if %{with kernel}
install -d $RPM_BUILD_ROOT/lib/modules/%{_kernel_ver}{,smp}/misc
install kernel/iscsi_trgt-%{?with_dist_kernel:up}%{!?with_dist_kernel:nondist}.ko \
        $RPM_BUILD_ROOT/lib/modules/%{_kernel_ver}/misc/iscsi_trgt.ko
%if %{with smp} && %{with dist_kernel}
install kernel/iscsi_trgt-smp.ko \
        $RPM_BUILD_ROOT/lib/modules/%{_kernel_ver}smp/misc/iscsi_trgt.ko
%endif
%endif

%if %{with userspace}
install %{SOURCE1} $RPM_BUILD_ROOT/etc/rc.d/init.d/targetiscsi
install %{SOURCE2} $RPM_BUILD_ROOT/etc/sysconfig/targetiscsi

install etc/ietd.conf $RPM_BUILD_ROOT/etc

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

%post -n kernel-smp-targetiscsi
%depmod %{_kernel_ver}smp

%postun -n kernel-smp-targetiscsi
%depmod %{_kernel_ver}smp

%post
/sbin/chkconfig --add targetiscsi
#if [ -f /var/lock/subsys/targetiscsi ]; then
#	/etc/rc.d/init.d/targetiscsi restart 1>&2
#else
#	echo "Type \"/etc/rc.d/init.d/targetiscsi start\" to start target iscsi" 1>&2
#fi

%preun
if [ "$1" = "0" ]; then
#	if [ -f /var/lock/subsys/targetiscsi ]; then
#		/etc/rc.d/init.d/targetiscsi stop >&2
#	fi
        /sbin/chkconfig --del targetiscsi
fi

%if %{with userspace}
%files
%defattr(644,root,root,755)
%doc ChangeLog
%attr(755,root,root) %{_sbindir}/*
%attr(750,root,root) %config(noreplace) %verify(not md5 mtime size) %{_sysconfdir}/ietd.conf
%attr(644,root,root) %{_mandir}/man?/*
%attr(754,root,root) /etc/rc.d/init.d/targetiscsi
%attr(640,root,root) %config(noreplace) %verify(not md5 mtime size) /etc/sysconfig/targetiscsi
%endif

%if %{with kernel}
%files -n kernel-targetiscsi
%defattr(644,root,root,755)
%attr(644,root,root) /lib/modules/%{_kernel_ver}/misc/*

%if %{with smp} && %{with dist_kernel}
%files -n kernel-smp-targetiscsi
%defattr(644,root,root,755)
%attr(644,root,root) /lib/modules/%{_kernel_ver}smp/misc/*
%endif
%endif
