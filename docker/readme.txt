In this directory you will add a .env settings file:

    .env

The contents should be structured like:

    VOL=<local path to the root of this repo -- will be mapped to /app in the docker web img>
    VOL_DB=<local path to the mysql files, e.g.: "local proj path/docker_mysql/8.0">
    VOL_DB_CONFIG=<local path to the db config file, e.g.: "local proj path/db_configuration">
    DB_PWD=<root db pwd>
    REL_DB_CONFIG=/opt/project/db_configuration
    STATIC_VOL=<path YSE_PZ app's static directory>
    DB_INIT=<path to "DatabaseInitialization" directory>


TO UPDATE PACKAGES AND/OR GENERATE A NEW WEB DOCKER IMAGE:
Add you requirements file to build a new web image at ./Requirements/. Naming conventions should be:

    ./Requirements/requirements_1.txt
    ./Requirements/requirements_2.txt
...

However, you should only need 1 file unless you have conflicting dependencies.


LOCAL DOCKER (recommended):
See CONTRIBUTING.md in the repo root for workflow, pruning, and collectstatic.

Quick reference from the repo root:

    ./docker/scripts/yse-docker.sh up             # start stack, light prune
    ./docker/scripts/yse-docker.sh collectstatic  # if admin/CSS assets are missing
    ./docker/scripts/yse-docker.sh pull           # pull web image, aggressive prune
    ./docker/scripts/yse-docker.sh rebuild        # local dev image build
    ./docker/scripts/yse-docker.sh prune            # prune only
    ./docker/scripts/yse-docker.sh down             # stop (keeps DB)

Set YSE_DOCKER_PRUNE=0 to skip pruning for one command.