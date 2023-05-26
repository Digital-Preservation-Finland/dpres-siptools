# vim:ft=spec

%define file_prefix M4_FILE_PREFIX
%define file_ext M4_FILE_EXT

%define file_version M4_FILE_VERSION
%define file_release_tag %{nil}M4_FILE_RELEASE_TAG
%define file_release_number M4_FILE_RELEASE_NUMBER
%define file_build_number M4_FILE_BUILD_NUMBER
%define file_commit_ref M4_FILE_COMMIT_REF

Name:           dpres-siptools
Version:        %{file_version}
Release:        %{file_release_number}%{file_release_tag}.%{file_build_number}.git%{file_commit_ref}%{?dist}
Summary:        Command line tools for creating Submission Information Packages (SIP) for preservation workflow
Group:          Applications/Archiving
License:        LGPLv3+
URL:            http://www.csc.fi
Source0:        %{file_prefix}-v%{file_version}%{?file_release_tag}-%{file_build_number}-g%{file_commit_ref}.%{file_ext}
BuildArch:      noarch

BuildRequires:  python3-devel
BuildRequires:  python3-dpres-ipt
BuildRequires:  python3-file-scraper-full
BuildRequires:  pyproject-rpm-macros
BuildRequires:  %{py3_dist pip}
BuildRequires:  %{py3_dist setuptools}
BuildRequires:  %{py3_dist wheel}
BuildRequires:  %{py3_dist pyopenssl}

%global _description %{expand:
Command line tools for creating Submission information packages (SIP) for preservation workflow.
}

%description %_description

%package -n python3-dpres-siptools
Summary: %{summary}

%description -n python3-dpres-siptools %_description

%prep
%autosetup -n %{file_prefix}-v%{file_version}%{?file_release_tag}-%{file_build_number}-g%{file_commit_ref}

%build
%pyproject_wheel

%install
%pyproject_install
%pyproject_save_files siptools

# TODO: executables with "-3" suffix are added to maintain compatibility with our systems.
# executables with "-3" suffix should be deprecated.
cp %{buildroot}%{_bindir}/compile-mets %{buildroot}%{_bindir}/compile-mets-3
cp %{buildroot}%{_bindir}/compile-structmap %{buildroot}%{_bindir}/compile-structmap-3
cp %{buildroot}%{_bindir}/compress %{buildroot}%{_bindir}/compress-3
cp %{buildroot}%{_bindir}/create-addml %{buildroot}%{_bindir}/create-addml-3
cp %{buildroot}%{_bindir}/create-agent %{buildroot}%{_bindir}/create-agent-3
cp %{buildroot}%{_bindir}/create-audiomd %{buildroot}%{_bindir}/create-audiomd-3
cp %{buildroot}%{_bindir}/create-mix %{buildroot}%{_bindir}/create-mix-3
cp %{buildroot}%{_bindir}/create-videomd %{buildroot}%{_bindir}/create-videomd-3
cp %{buildroot}%{_bindir}/define-xml-schemas %{buildroot}%{_bindir}/define-xml-schemas-3
cp %{buildroot}%{_bindir}/import-description %{buildroot}%{_bindir}/import-description-3
cp %{buildroot}%{_bindir}/import-object %{buildroot}%{_bindir}/import-object-3
cp %{buildroot}%{_bindir}/premis-event %{buildroot}%{_bindir}/premis-event-3
cp %{buildroot}%{_bindir}/sign-mets %{buildroot}%{_bindir}/sign-mets-3

%files -n python3-dpres-siptools -f %{pyproject_files}
%license LICENSE
%doc README.rst
%{_bindir}/compile-mets*
%{_bindir}/compile-struct-map*
%{_bindir}/compress*
%{_bindir}/create-addml*
%{_bindir}/create-agent*
%{_bindir}/create-audiomd*
%{_bindir}/create-mix*
%{_bindir}/create-videomd*
%{_bindir}/define-xml-schemas*
%{_bindir}/import-description*
%{_bindir}/import-object*
%{_bindir}/premis-event*
%{_bindir}/sign-mets-3*

# TODO: For now changelog must be last, because it is generated automatically
# from git log command. Appending should be fixed to happen only after %changelog macro
%changelog
