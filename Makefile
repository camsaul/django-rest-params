.PHONY: upload

# Run steps to upload updated version to PyPI
upload:
	pip install -U wheel twine
	python setup.py sdist
	python setup.py bdist_wheel --universal
	python setup.py register
	twine upload dist/*
