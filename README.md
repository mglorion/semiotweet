# <img src="viewer/static/images/semiotweet.jpg" width="60" height="60" alt = "Logo"/> Semiotweet
Tweets analysis from politics.

[![Build Status](https://travis-ci.org/jjerphan/semiotweet.svg?branch=master)](https://travis-ci.org/jjerphan/semiotweet)
[![Code Climate](https://codeclimate.com/github/jjerphan/semiotweet/badges/gpa.svg)](https://codeclimate.com/github/jjerphan/semiotweet)
[![Test Coverage](https://codeclimate.com/github/jjerphan/semiotweet/badges/coverage.svg)](https://codeclimate.com/github/jjerphan/semiotweet/coverage)
[![Issue Count](https://codeclimate.com/github/jjerphan/semiotweet/badges/issue_count.svg)](https://codeclimate.com/github/jjerphan/semiotweet)


**⚠ This project is no longer maintained. ⚠**

## What's the goal

_Semiotweet_ aims to better understand the tweets posted by politics.
It shows what are the most commons words in those tweets, and what are the different semantic fields related to them.


## Stack :
 - Django as framework,
 - PostGreSQL for the database,
 - Twitter API as data provider,
 - TreeTagger & gensim for tweets' analysis,
 - chart.js for visualization

## Architecture, data structures & models

There's two apps called `viewer` and `api`.

`urls.py` directly redirects to this first app (`viewer`).

`api` is a classic REST API for the website.

The one from `extraction.py` catch the tweets, those in `semantic_analysis.py` process the analysis.
The analysis is based on *LDA (Latent Dirichlet allocation)*.

Templates are directly put in `viewer/templates/` and not as usual in `viewer/templates/viewer` as it can be the case in
 most of Django apps.

## How to install

### Virtual environment

Clone it. Go to the folder and create a virtual environment:

```bash
$ python -m venv venv
$ source venv/bin/activate
```

**In the following, all the `export` lines can be put at the end of the file /venv3/bin/activate`. It is easier to 
define the env variables that way since those lines are executed when lauching the venv.**

You have to set some variables in yout virtual env.
First, the "secret key" for the app (needed by Django). You can use [this site](http://www.miniwebtool.com/django-secret-key-generator) to generate one.
```bashs
$ export SECRET_KEY='someLongStringToImagine'
```

### TreeTagger

_TreeTagger_ is one of the main library used for the project. You have to install it with the french parameter file in
your home directory by refering to the official docummentation (see [here](http://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/))

You have to specify the folder in which you install _TreeTagger_ with the `LOCALTAGDIR` variable :
```bash
$ export LOCALTAGDIR='/path/to/tree-tagger/'
```

### Credentials for Twitter API
Then the credentials (for user and consumer)for your app in order to use Twitter API.
In order to have those string, you need to create a Twitter App (see [here](https://apps.twitter.com/app/13440041/show))
 ; then you can copy-paste them to set them in your virtual env.
```bash
$ export CONSUMER_KEY='someLongStringToImagine'
$ export CONSUMER_SECRET='someLongStringToImagine'
$ export KEY='someLongStringToImagine'
$ export SECRET='someLongStringToImagine'
```

### Requirements
Then install the requirements
```bash
$ pip install -r requirements.txt
```
If you have the error `pg_config not found` just install the `libpq_dev` package.
If you have the error `could not run curl-config` install the `libcurl4-openssl-dev` package.
Then re-install the requirements


You have to create a `local_settings.py` in the same folder as `setting.py` in order to extend this file (see the end of
 `setting.py`) ; this is useful for managing different
data base between local development and deployement :
```bash
$ touch local_settings.py
```
In this file are the settings set to use the local database (`DEBUG` is set to True for dev', false for production.) :

```python
# Local settings : used for local development.
from __future__ import absolute_import
from .settings import PROJECT_ROOT, BASE_DIR
import os

DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

```
Then you have to run this in order to set up the models and the database :
```bash
$ python manage.py makemigrations
$ python manage.py makemigrations viewer
$ python manage.py migrate
```

Finally, to run the server locally:
```bash
$ python manage.py runserver
```

## Getting users data and tweets

Once the server is running, you can extact the data concerning the users and their tweets using the api:

[`http://127.0.0.1:8000/api/v1.0/getData/`](`http://127.0.0.1:8000/api/v1.0/getData/`)


## Usefull Ressources

  - Logo from [graphicdesignblg](https://www.instagram.com/graphicdesignblg/ "graphicdesignblg on Instagram")
  - [Twitter API documentation](https://dev.twitter.com/ "Twitter API documentation")
  - [Map of a Twitter Status Object](http://www.slaw.ca/wp-content/uploads/2011/11/map-of-a-tweet-copy.pdf
  "Map of a Twitter Status"), Raffi Krikorian
  - Marco Bonzanini, [Mining Twitter Data with Python](https://marcobonzanini.com/2015/03/02/mining-twitter-data-with-python-part-1/
  "Mining Twitter Data with Python")
  - [Migrating Your Django Project to Heroku](https://realpython.com/blog/python/migrating-your-django-project-to-heroku/
  "Migrating Your Django Project to Heroku")
  - [TreeTagger](http://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/) for the tagging, tokenization and
  lemmatization of french documents

## License
  This project is under [GNU General Public License (Version 3, 29 June 2007)](https://github.com/jjerphan/semiotweet/blob/master/LICENSE).
  Feel free to contact us and to fork or to patch this project.
