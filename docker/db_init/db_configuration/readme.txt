In this directory you will add a database settings file with connection string information:

    settings.ini

The contents should be structured like:

    [database]
    DATABASE_NAME: <your database schema name here>
    DATABASE_USER: <your username here (not root!!)>
    DATABASE_PASSWORD: <your user pwd>
    DATABASE_HOST: <database host -- if using docker-compose, this value is `db`>
    DATABASE_PORT: <database port -- probably should be 3306 unless you're doing something custom>

