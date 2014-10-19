.PHONY: upload test

# Run steps to upload updated version to PyPI
upload:
	rm -rf dist/*
	pip install -U wheel twine
	python setup.py sdist
	python setup.py bdist_wheel --universal
	python setup.py register
	twine upload dist/*

test:
	pip install django djangorestframework
	python -m tests.tests
