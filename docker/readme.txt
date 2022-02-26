In this directory you will add a .env settings file:

    .env

The contents should be structured like:

    VOL=<local path to the root of this repo -- will be mapped to /app in the docker web img>
    VOL_DB=<local path to the mysql files, e.g.: "local proj path/docker_mysql/8.0">
    VOL_DB_CONFIG=<local path to the db config file, e.g.: "local proj path/db_configuration">
    DB_PWD=<root db pwd>
    REL_DB_CONFIG=/opt/project/db_configuration
