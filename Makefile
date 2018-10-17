MOCK_CONFIG=stable-7-x86_64
ROOT=/
PREFIX=/usr

install:
	# Cleanup temporary files
	rm -f INSTALLED_FILES
	# Install with setuptools
	python setup.py build ; python ./setup.py install -O1 --prefix="${PREFIX}" --root="${ROOT}" --record=INSTALLED_FILES
	# Remove egg-info directory from INSTALLED_FILES to avoid listing its
	# contents twice when creating RPM package
	sed -i '/\.egg-info$$/d' INSTALLED_FILES


test:
	py.test -svvvv --junitprefix=dpres-siptools --junitxml=junit.xml tests

coverage:
	py.test tests --cov=siptools --cov-report=html
	coverage report -m
	coverage html
	coverage xml

clean: clean-rpm
	find . -iname '*.pyc' -type f -delete
	find . -iname '__pycache__' -exec rm -rf '{}' \; | true

clean-rpm:
	rm -rf rpmbuild

rpm: clean-rpm
	create-archive.sh
	preprocess-spec-m4-macros.sh include/rhel7
	build-rpm.sh ${MOCK_CONFIG}

