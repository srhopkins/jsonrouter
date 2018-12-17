#!/bin/bash

if [ -z "${1}" ]; then
	cat .bumpversion.cfg
	echo include major, minor or patch for bumpversion
	exit 1
fi

bumpversion "${1}" || exit

rm -rf jsonrouter.egg-info dist build

python3 setup.py sdist bdist_wheel
twine upload dist/*

git push
git push --tags