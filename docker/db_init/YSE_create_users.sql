CREATE USER 'django'@'%' IDENTIFIED WITH mysql_native_password BY '4Django!';
GRANT ALL PRIVILEGES ON YSE.* TO 'django'@'%' WITH GRANT OPTION;

CREATE USER 'django'@'localhost' IDENTIFIED WITH mysql_native_password BY '4Django!';
GRANT ALL PRIVILEGES ON YSE.* TO 'django'@'localhost' WITH GRANT OPTION;

CREATE USER 'explorer'@'%' IDENTIFIED WITH mysql_native_password BY '4Explor3R!';
GRANT SELECT ON YSE.* TO 'explorer'@'%';

CREATE USER 'explorer'@'localhost' IDENTIFIED WITH mysql_native_password BY '4Explor3R!';
GRANT SELECT ON YSE.* TO 'explorer'@'localhost';

FLUSH PRIVILEGES;