CREATE USER 'dev'@'%' IDENTIFIED WITH mysql_native_password BY 'devpass';
GRANT ALL PRIVILEGES ON YSE.* TO 'dev'@'%' WITH GRANT OPTION;
GRANT CREATE, DROP ON *.* TO 'dev'@'%';
GRANT ALL PRIVILEGES ON `test_YSE`.* TO 'dev'@'%';

CREATE USER 'dev'@'localhost' IDENTIFIED WITH mysql_native_password BY 'devpass';
GRANT ALL PRIVILEGES ON YSE.* TO 'dev'@'localhost' WITH GRANT OPTION;
GRANT CREATE, DROP ON *.* TO 'dev'@'localhost';
GRANT ALL PRIVILEGES ON `test_YSE`.* TO 'dev'@'localhost';

CREATE USER 'dev_explorer'@'%' IDENTIFIED WITH mysql_native_password BY 'dev_explorerpass';
GRANT SELECT ON YSE.* TO 'dev_explorer'@'%';

CREATE USER 'dev_explorer'@'localhost' IDENTIFIED WITH mysql_native_password BY 'dev_explorerpass';
GRANT SELECT ON YSE.* TO 'dev_explorer'@'localhost';

FLUSH PRIVILEGES;