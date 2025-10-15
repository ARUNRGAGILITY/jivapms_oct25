# JIVAPMS (Project and Product Management System)

This repository contains a Django project scaffold for JIVAPMS with an opinionated directory layout:

- `project_jivapms/` Django project (settings, urls, manage.py)
- `apps/app_<appname>/mod_<modname>/` Django apps and their modules
  - `app_0/mod_0` holds shared primitives (BaseModelImpl)
- Utility folders: `auto/`, `build/`, `config/`, `dev/`, `docs/`, `run/`

## Quick start

- Python 3.13 and Django 5.1
- Local DB: sqlite (file under `project_jivapms/db.sqlite3`)

## Dev commands

Use manage.py under `project_jivapms/`.
