In this directory you will add a .env settings file:

    .env

The contents should be structured like:

    VOL=<this should point to the fully qualified local root of the repo>
    VOL_DB=<you can define this path wherever you want, but within that path needs to be [wherever]/docker_mysql/8.0>8.0
    DB_PWD=<a root DB pwd that you choose>
    STATIC_VOL=<this is the fully qualified path to the /static folder in the app. Ex: [your local root pro path]/YSE_PZ/static >
    LOCAL_DB_PORT=<whatever local port you want to use to serve MySQL Server. Default is 3306>
    LOCAL_HTTP_PORT=<whatever local HTTP port you want to use to serve the web app via nginx. Default is 80>


TO UPDATE PACKAGES AND/OR GENERATE A NEW WEB DOCKER IMAGE:
Add your pip package to the `requirements.web.dev` like:

    <package name>==<package version>

Next, use docker-compose to bring up `docker-compose.dev.yml` instead of the default docker-compose.yml like:

   docker-compose -f docker-compose.dev.yml up

This should build the Dockerfile.web.dev file using the docker-compose.dev.yml, creating a local image called, `local/yse_pz_web:dev`. If you want to run with a PyCharm debugger attached, you can temporarily point the `image` property of the `web` service to this new image name.

Finally, to commit this package dependency and have it incorporated into the main YSE Web image, ONLY CHECK-IN the `requirements.web.dev`. DO NOT CHECK-IN changes to the docker-compose files. Thanks!
