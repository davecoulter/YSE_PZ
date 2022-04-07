USE YSE;
-- MySQL dump 10.13  Distrib 8.0.12, for macos10.13 (x86_64)
--
-- Host: 127.0.0.1    Database: YSE
-- ------------------------------------------------------
-- Server version	8.0.25

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */; SET NAMES utf8 ;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Dumping data for table `django_migrations`
--

LOCK TABLES `django_migrations` WRITE;
/*!40000 ALTER TABLE `django_migrations` DISABLE KEYS */; INSERT INTO `django_migrations` VALUES
   (1,'contenttypes','0001_initial','2017-12-04 21:07:59.755586'),
   (2,'auth','0001_initial','2017-12-04 21:08:01.937569'),(3,'YSE_App','0001_initial','2017-12-04 21:09:17.420714'),
   (4,'admin','0001_initial','2017-12-04 21:09:18.564366'),
   (5,'admin','0002_logentry_remove_auto_add','2017-12-04 21:09:18.763597'),
   (6,'contenttypes','0002_remove_content_type_name','2017-12-04 21:09:19.293034'),
   (7,'auth','0002_alter_permission_name_max_length','2017-12-04 21:09:19.339587'),
   (8,'auth','0003_alter_user_email_max_length','2017-12-04 21:09:19.528422'),
   (9,'auth','0004_alter_user_username_opts','2017-12-04 21:09:19.723257'),
   (10,'auth','0005_alter_user_last_login_null','2017-12-04 21:09:20.065233'),
   (11,'auth','0006_require_contenttypes_0002','2017-12-04 21:09:20.102426'),
   (12,'auth','0007_alter_validators_add_error_messages','2017-12-04 21:09:20.224017'),
   (13,'auth','0008_alter_user_username_max_length','2017-12-04 21:09:20.433012'),
   (14,'authtoken','0001_initial','2017-12-04 21:09:20.862987'),
   (15,'authtoken','0002_auto_20160226_1747','2017-12-04 21:09:21.741890'),
   (16,'sessions','0001_initial','2017-12-04 21:09:21.922647'),
   (35,'auth','0009_alter_user_last_name_max_length','2018-04-27 02:27:37.666689'),
   (39,'explorer','0001_initial','2018-06-19 23:01:42.520844'),
   (40,'explorer','0002_auto_20150501_1515','2018-06-19 23:01:43.209353'),
   (41,'explorer','0003_query_snapshot','2018-06-19 23:01:43.536897'),
   (42,'explorer','0004_querylog_duration','2018-06-19 23:01:43.859045'),
   (43,'explorer','0005_auto_20160105_2052','2018-06-19 23:01:44.131953'),
   (44,'explorer','0006_query_connection','2018-06-19 23:01:45.978097'),
   (45,'explorer','0007_querylog_connection','2018-06-19 23:01:46.310179'),
   (51,'django_cron','0001_initial','2019-03-07 04:07:58.207173'),
   (52,'django_cron','0002_remove_max_length_from_CronJobLog_message','2019-03-07 04:07:58.230324'),
   (61,'silk','0001_initial','2019-11-04 21:59:29.534456'),
   (62,'silk','0002_auto_update_uuid4_id_field','2019-11-04 21:59:29.587478'),
   (63,'silk','0003_request_prof_file','2019-11-04 21:59:29.813455'),
   (64,'silk','0004_request_prof_file_storage','2019-11-04 21:59:29.855611'),
   (65,'silk','0005_increase_request_prof_file_length','2019-11-04 21:59:29.976724'),
   (66,'silk','0006_fix_request_prof_file_blank','2019-11-04 21:59:30.481741'),
   (78,'explorer','0008_auto_20191112_0349','2019-11-19 20:20:23.899075'),
   (85,'admin','0003_logentry_add_action_flag_choices','2020-02-20 22:00:50.938082'),
   (86,'auth','0010_alter_group_name_max_length','2020-02-20 22:00:51.193150'),
   (87,'auth','0011_update_proxy_permissions','2020-02-20 22:00:51.448622'),
   (88,'explorer','0008_auto_20190308_1642','2020-02-20 22:00:51.494961'),
   (102,'explorer','0008_auto_20210516_0116','2021-05-16 01:16:57.094688'),
   (103,'explorer','0008_auto_20210521_1654','2021-06-30 23:03:00.808731'),
   (104,'auditlog','0001_initial','2021-10-20 22:34:02.101307'),
   (105,'auditlog','0002_auto_support_long_primary_keys','2021-10-20 22:34:02.714146'),
   (106,'auditlog','0003_logentry_remote_addr','2021-10-20 22:34:02.973668'),
   (107,'auditlog','0004_logentry_detailed_object_repr','2021-10-20 22:34:03.249847'),
   (108,'auditlog','0005_logentry_additional_data_verbose_name','2021-10-20 22:34:03.511113'),
   (109,'auditlog','0006_object_pk_index','2021-10-20 22:34:04.252852'),
   (110,'auditlog','0007_object_pk_type','2021-10-20 22:34:04.362448'),
   (115,'auth','0012_alter_user_first_name_max_length','2021-12-21 18:25:02.078631'),
   (116,'authtoken','0003_tokenproxy','2021-12-21 18:25:02.128574'),
   (117,'explorer','0009_auto_20201009_0547','2021-12-21 18:25:26.697585'),
   (118,'explorer','0010_sql_required','2021-12-21 18:25:26.973322'),
   (119,'explorer','0011_merge_0008_auto_20210521_1654_0010_sql_required','2021-12-21 18:25:27.009778'),
   (120,'explorer','0012_alter_query_connection','2021-12-23 19:35:15.669801');
/*!40000 ALTER TABLE `django_migrations` ENABLE KEYS */; UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2022-04-04 17:18:18
