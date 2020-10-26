# FTA

[![Build Status](https://travis-ci.org/mozilla/fta.svg?branch=main)](https://travis-ci.org/mozilla/fta)


Fathom Training App - Utils to help with training fathom

## Dev instructions

### Setup

Requires:
* Postgres

Setup instructions
* Make a conda or virtual environment - only python 3.8 has been tested - and activate.
* `pip install -r requirements/local.txt`
* `pre-commit install`
* `createdb <dbname> -U postgres --password <password>`
* make a .env file, and add line `export DATABASE_URL=postgres://postgres:<password>@127.0.0.1:5432/<dbname>`
* `./manage.py migrate`
* `./manage.py runserver`

Server should now be running at [localhost](http://localhost:8000)


### Useful commands

* To create a superuser account: `./manage.py createsuperuser`
* To update static files: `./manage.py collectstatic`


### Linting and testing

Linting should run on pre-commit, or with:
* `flake8`
* `black .`
* `isort`

To run the tests, check your test coverage, and generate an HTML coverage report::

    $ coverage run -m pytest
    $ coverage html
    $ open htmlcov/index.html

Running tests with py.test

  $ pytest

## Deployment

The following details how to deploy this application.
