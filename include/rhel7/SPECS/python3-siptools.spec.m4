# vim:ft=spec

%define file_prefix M4_FILE_PREFIX
%define file_ext M4_FILE_EXT

%define file_version M4_FILE_VERSION
%define file_release_tag %{nil}M4_FILE_RELEASE_TAG
%define file_release_number M4_FILE_RELEASE_NUMBER
%define file_build_number M4_FILE_BUILD_NUMBER
%define file_commit_ref M4_FILE_COMMIT_REF

Name:           python3-dpres-siptools
Version:        %{file_version}
Release:        %{file_release_number}%{file_release_tag}.%{file_build_number}.git%{file_commit_ref}%{?dist}
Summary:        Command line tools for creating Submission Information Packages (SIP) for preservation workflow
Group:          Applications/Archiving
License:        LGPLv3+
URL:            https://www.digitalpreservation.fi
Source0:        %{file_prefix}-v%{file_version}%{?file_release_tag}-%{file_build_number}-g%{file_commit_ref}.%{file_ext}
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildArch:      noarch

Requires:       python3 python3-dpres-signature python3-xml-helpers
Requires:       python3-mets python3-premis python3-nisomix python3-addml
Requires:       python3-audiomd python3-videomd python3-file-scraper-core
Requires:       python3-magic python36-six python36-click
BuildRequires:  python3-file-scraper-full
BuildRequires:  python3-setuptools openssl-devel

%description
Command line tools for creating Submission information packages (SIP) for preservation workflow.

%prep
%setup -n %{file_prefix}-v%{file_version}%{?file_release_tag}-%{file_build_number}-g%{file_commit_ref}

%build

%install
rm -rf $RPM_BUILD_ROOT
make install3 PREFIX="%{_prefix}" ROOT="%{buildroot}"

# Rename executables to prevent naming collision with Python 2 RPM
mv %{buildroot}%{_bindir}/compile-mets %{buildroot}%{_bindir}/compile-mets-3
mv %{buildroot}%{_bindir}/compile-structmap %{buildroot}%{_bindir}/compile-structmap-3
mv %{buildroot}%{_bindir}/compress %{buildroot}%{_bindir}/compress-3
mv %{buildroot}%{_bindir}/create-addml %{buildroot}%{_bindir}/create-addml-3
mv %{buildroot}%{_bindir}/create-agent %{buildroot}%{_bindir}/create-agent-3
mv %{buildroot}%{_bindir}/create-audiomd %{buildroot}%{_bindir}/create-audiomd-3
mv %{buildroot}%{_bindir}/create-mix %{buildroot}%{_bindir}/create-mix-3
mv %{buildroot}%{_bindir}/create-videomd %{buildroot}%{_bindir}/create-videomd-3
mv %{buildroot}%{_bindir}/define-xml-schemas %{buildroot}%{_bindir}/define-xml-schemas-3
mv %{buildroot}%{_bindir}/import-description %{buildroot}%{_bindir}/import-description-3
mv %{buildroot}%{_bindir}/import-object %{buildroot}%{_bindir}/import-object-3
mv %{buildroot}%{_bindir}/premis-event %{buildroot}%{_bindir}/premis-event-3
mv %{buildroot}%{_bindir}/sign-mets %{buildroot}%{_bindir}/sign-mets-3
sed -ie '/^\/usr\/bin/ s/$/-3/g' INSTALLED_FILES

%clean
rm -rf $RPM_BUILD_ROOT

%files -f INSTALLED_FILES
%defattr(-,root,root,-)
/usr/bin/*-3

# TODO: For now changelog must be last, because it is generated automatically
# from git log command. Appending should be fixed to happen only after %changelog macro
%changelog
