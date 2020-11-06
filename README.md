# FTA

[![Build
Status](https://travis-ci.org/mozilla-applied-ml/fta.svg?branch=main)](https://travis-ci.org/mozilla-applied-ml/fta)


Fathom Training App - Utils to help with training fathom

## Dev instructions

### Setup

Requires:

* Postgres

Setup instructions:

* Make a conda or virtual environment - only python 3.8 has been tested - and activate.
* `pip install -r requirements/local.txt`
* `pre-commit install`
* `createdb <dbname> -U postgres --password <password>`
* make a `.env` file, and add line `export DATABASE_URL=postgres://postgres:<password>@127.0.0.1:5432/<dbname>`
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

Setup a google storage bucket and set acl for `gsutil acl -r ch -u AllUsers:R gs://BUCKET/FOLDER`

#### To run production environment locally

Install production requirements `pip install -r requirements/production.txt`

Set environment variable `DJANGO_SETTINGS_MODULE` to `config.settings.production` to ensure that we're using production settings.

Need a `.env` file with, at least, the following entries:
  * DJANGO_SECRET_KEY
  * DB_NAME
  * DB_USERNAME
  * DB_PASSWORD
  * CLOUD_SQL_INSTANCE_ID
  * DJANGO_SECURE_SSL_REDIRECT=False  (otherwise will have a hard time running locally)
  * DJANGO_ALLOWED_HOSTS=localhost,
  * DJANGO_GCP_STORAGE_BUCKET_NAME

Production settings will look for a cloudsql database. If you want to connect to the production database or a test cloud database you've setup, use [cloud sql proxy](https://cloud.google.com/sql/docs/mysql/sql-proxy). The settings are currently setup to expect the proxy port to be at 5454, so set cloud sql proxy appropriately (`./cloud_sql_proxy -instances="<instance id\>"=tcp:5454`)

With all that setup, should be able to run `manage.py runserver` and check things are working as expected (ish).

Tip: If you forgot to set DJANGO_SECURE_SSL_REDIRECT locally and ran the local server and got a message like "You're accessing the development server over HTTPS, but it only supports HTTP", make sure you clear browser cache before attempting to re-access having set the environment variable as the https redirect will be saved.

#### Normal deployment via CI

Deployment is generally handled on Travis.

Need a `.env` file with, at least, the following entries:
  * DJANGO_SECRET_KEY
  * DB_NAME
  * DB_USERNAME
  * DB_PASSWORD
  * CLOUD_SQL_INSTANCE_ID
  * DJANGO_GCP_STORAGE_BUCKET_NAME

To find the `CLOUD_SQL_INSTANCE_ID` run `gcloud sql instances describe <instance_id> | grep connectionName` (where
instance_id is from in https://console.cloud.google.com/sql/instances.)


The `deploy/pre_deploy_script.py`:

(a) Compiles a requirements.txt file (because the GAE docker file, looks for that first before copying all the app files over)

(b) Builds the app.yaml

(b) Builds a `.env` file with production variables from TravisCI encrypted variables.

It then uses Travis' built in GAE deployment integration to effectively call `gcloud app deploy`.

If there are db migrations necessary, then these must be manually.

If db migrations are necessary, use the appropriate steps from "To run production environment locally" and run `./manage.py migrate`.


#### Manual deployment locally

Run:

* `python deploy/pre_deploy_script.py`
* `gcloud app deploy

If new static files to update:

* `./manage.py collectstatic`
* `gsutil rsync -r staticfiles gs://BUCKET/FOLDER`

If trying to debug, the `--verbosity=debug` flag is very useful.

If db migrations are necessary, use the appropriate steps from "To run production environment locally" and run `./manage.py migrate`.


#### Notes

On Google, needed a service account with:

* App Engine Admin
* Cloud Build Service Account
* Storage Adming

Following articles were useful:

* https://codeburst.io/beginners-guide-to-deploying-a-django-postgresql-project-on-google-cloud-s-flexible-app-engine-e3357b601b91
* https://cloud.google.com/solutions/continuous-delivery-with-travis-ci#create_a_service_account
* https://medium.com/coinmonks/continuous-integration-with-google-application-engine-and-travis-d822b751fb47
