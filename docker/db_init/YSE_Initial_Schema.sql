USE YSE;

-- MySQL dump 10.13  Distrib 8.0.12, for macos10.13 (x86_64)
--
-- Host: 127.0.0.1    Database: YSE
-- ------------------------------------------------------
-- Server version	8.0.25

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
 SET NAMES utf8 ;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `YSE_App_alternatetransientnames`
--

DROP TABLE IF EXISTS `YSE_App_alternatetransientnames`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `YSE_App_alternatetransientnames` (
  `id` int NOT NULL AUTO_INCREMENT,
  `created_date` datetime(6) NOT NULL,
  `modified_date` datetime(6) NOT NULL,
  `name` varchar(64) NOT NULL,
  `description` longtext,
  `created_by_id` int NOT NULL,
  `modified_by_id` int NOT NULL,
  `obs_group_id` int DEFAULT NULL,
  `transient_id` int NOT NULL,
  `slug` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `slug` (`slug`),
  KEY `YSE_App_alternatetra_created_by_id_df0fb772_fk_auth_user` (`created_by_id`),
  KEY `YSE_App_alternatetra_modified_by_id_a7c52ab0_fk_auth_user` (`modified_by_id`),
  KEY `YSE_App_alternatetra_obs_group_id_f880c714_fk_YSE_App_o` (`obs_group_id`),
  KEY `YSE_App_alternatetra_transient_id_c3664e54_fk_YSE_App_t` (`transient_id`),
  CONSTRAINT `YSE_App_alternatetra_created_by_id_df0fb772_fk_auth_user` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `YSE_App_alternatetra_modified_by_id_a7c52ab0_fk_auth_user` FOREIGN KEY (`modified_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `YSE_App_alternatetra_obs_group_id_f880c714_fk_YSE_App_o` FOREIGN KEY (`obs_group_id`) REFERENCES `YSE_App_observationgroup` (`id`),
  CONSTRAINT `YSE_App_alternatetra_transient_id_c3664e54_fk_YSE_App_t` FOREIGN KEY (`transient_id`) REFERENCES `YSE_App_transient` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=64320 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `YSE_App_antaresclassification`
--

DROP TABLE IF EXISTS `YSE_App_antaresclassification`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `YSE_App_antaresclassification` (
  `id` int NOT NULL AUTO_INCREMENT,
  `created_date` datetime(6) NOT NULL,
  `modified_date` datetime(6) NOT NULL,
  `name` varchar(64) NOT NULL,
  `created_by_id` int NOT NULL,
  `modified_by_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `YSE_App_antaresclass_created_by_id_95e649ab_fk_auth_user` (`created_by_id`),
  KEY `YSE_App_antaresclass_modified_by_id_48636e88_fk_auth_user` (`modified_by_id`),
  CONSTRAINT `YSE_App_antaresclass_created_by_id_95e649ab_fk_auth_user` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `YSE_App_antaresclass_modified_by_id_48636e88_fk_auth_user` FOREIGN KEY (`modified_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `YSE_App_canvasfov`
--

DROP TABLE IF EXISTS `YSE_App_canvasfov`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `YSE_App_canvasfov` (
  `id` int NOT NULL AUTO_INCREMENT,
  `raCenter` double NOT NULL,
  `decCenter` double NOT NULL,
  `fovWidth` double NOT NULL,
  `canvas_x_grid_size` int NOT NULL,
  `canvas_y_grid_size` int NOT NULL,
  `created` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `YSE_App_classicalnighttype`
--

DROP TABLE IF EXISTS `YSE_App_classicalnighttype`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `YSE_App_classicalnighttype` (
  `id` int NOT NULL AUTO_INCREMENT,
  `created_date` datetime(6) NOT NULL,
  `modified_date` datetime(6) NOT NULL,
  `name` varchar(64) NOT NULL,
  `created_by_id` int NOT NULL,
  `modified_by_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `YSE_App_classicalnig_created_by_id_6f85155e_fk_auth_user` (`created_by_id`),
  KEY `YSE_App_classicalnig_modified_by_id_ed6d170c_fk_auth_user` (`modified_by_id`),
  CONSTRAINT `YSE_App_classicalnig_created_by_id_6f85155e_fk_auth_user` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `YSE_App_classicalnig_modified_by_id_ed6d170c_fk_auth_user` FOREIGN KEY (`modified_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `YSE_App_classicalobservingdate`
--

DROP TABLE IF EXISTS `YSE_App_classicalobservingdate`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `YSE_App_classicalobservingdate` (
  `id` int NOT NULL AUTO_INCREMENT,
  `created_date` datetime(6) NOT NULL,
  `modified_date` datetime(6) NOT NULL,
  `obs_date` datetime(6) NOT NULL,
  `created_by_id` int NOT NULL,
  `modified_by_id` int NOT NULL,
  `night_type_id` int NOT NULL,
  `resource_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `YSE_App_classicalobs_created_by_id_4f5b204a_fk_auth_user` (`created_by_id`),
  KEY `YSE_App_classicalobs_modified_by_id_a4ae4732_fk_auth_user` (`modified_by_id`),
  KEY `YSE_App_classicalobs_night_type_id_5a93d35e_fk_YSE_App_c` (`night_type_id`),
  KEY `YSE_App_classicalobs_resource_id_7de9bb6c_fk_YSE_App_c` (`resource_id`),
  CONSTRAINT `YSE_App_classicalobs_created_by_id_4f5b204a_fk_auth_user` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `YSE_App_classicalobs_modified_by_id_a4ae4732_fk_auth_user` FOREIGN KEY (`modified_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `YSE_App_classicalobs_night_type_id_5a93d35e_fk_YSE_App_c` FOREIGN KEY (`night_type_id`) REFERENCES `YSE_App_classicalnighttype` (`id`),
  CONSTRAINT `YSE_App_classicalobs_resource_id_7de9bb6c_fk_YSE_App_c` FOREIGN KEY (`resource_id`) REFERENCES `YSE_App_classicalresource` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1575 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `YSE_App_classicalresource`
--

DROP TABLE IF EXISTS `YSE_App_classicalresource`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `YSE_App_classicalresource` (
  `id` int NOT NULL AUTO_INCREMENT,
  `created_date` datetime(6) NOT NULL,
  `modified_date` datetime(6) NOT NULL,
  `begin_date_valid` datetime(6) NOT NULL,
  `end_date_valid` datetime(6) NOT NULL,
  `description` longtext,
  `created_by_id` int NOT NULL,
  `modified_by_id` int NOT NULL,
  `principal_investigator_id` int DEFAULT NULL,
  `telescope_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `YSE_App_classicalresource_created_by_id_7901d555_fk_auth_user_id` (`created_by_id`),
  KEY `YSE_App_classicalres_modified_by_id_b2e9b78c_fk_auth_user` (`modified_by_id`),
  KEY `YSE_App_classicalres_principal_investigat_58360b6c_fk_YSE_App_p` (`principal_investigator_id`),
  KEY `YSE_App_classicalres_telescope_id_49497cad_fk_YSE_App_t` (`telescope_id`),
  CONSTRAINT `YSE_App_classicalres_modified_by_id_b2e9b78c_fk_auth_user` FOREIGN KEY (`modified_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `YSE_App_classicalres_principal_investigat_58360b6c_fk_YSE_App_p` FOREIGN KEY (`principal_investigator_id`) REFERENCES `YSE_App_principalinvestigator` (`id`),
  CONSTRAINT `YSE_App_classicalres_telescope_id_49497cad_fk_YSE_App_t` FOREIGN KEY (`telescope_id`) REFERENCES `YSE_App_telescope` (`id`),
  CONSTRAINT `YSE_App_classicalresource_created_by_id_7901d555_fk_auth_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=674 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `YSE_App_classicalresource_groups`
--

DROP TABLE IF EXISTS `YSE_App_classicalresource_groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `YSE_App_classicalresource_groups` (
  `id` int NOT NULL AUTO_INCREMENT,
  `classicalresource_id` int NOT NULL,
  `group_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `YSE_App_classicalresourc_classicalresource_id_gro_3ebbb8df_uniq` (`classicalresource_id`,`group_id`),
  KEY `YSE_App_classicalres_group_id_0527ceea_fk_auth_grou` (`group_id`),
  CONSTRAINT `YSE_App_classicalres_classicalresource_id_0e18b606_fk_YSE_App_c` FOREIGN KEY (`classicalresource_id`) REFERENCES `YSE_App_classicalresource` (`id`),
  CONSTRAINT `YSE_App_classicalres_group_id_0527ceea_fk_auth_grou` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1969 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `YSE_App_configelement`
--

DROP TABLE IF EXISTS `YSE_App_configelement`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `YSE_App_configelement` (
  `id` int NOT NULL AUTO_INCREMENT,
  `created_date` datetime(6) NOT NULL,
  `modified_date` datetime(6) NOT NULL,
  `name` varchar(64) NOT NULL,
  `description` longtext,
  `created_by_id` int NOT NULL,
  `instrument_id` int NOT NULL,
  `modified_by_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `YSE_App_configelement_created_by_id_158c5577_fk_auth_user_id` (`created_by_id`),
  KEY `YSE_App_configelemen_instrument_id_0c02f7c7_fk_YSE_App_i` (`instrument_id`),
  KEY `YSE_App_configelement_modified_by_id_f795719a_fk_auth_user_id` (`modified_by_id`),
  CONSTRAINT `YSE_App_configelemen_instrument_id_0c02f7c7_fk_YSE_App_i` FOREIGN KEY (`instrument_id`) REFERENCES `YSE_App_instrument` (`id`),
  CONSTRAINT `YSE_App_configelement_created_by_id_158c5577_fk_auth_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `YSE_App_configelement_modified_by_id_f795719a_fk_auth_user_id` FOREIGN KEY (`modified_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `YSE_App_configelement_instrument_config`
--

DROP TABLE IF EXISTS `YSE_App_configelement_instrument_config`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `YSE_App_configelement_instrument_config` (
  `id` int NOT NULL AUTO_INCREMENT,
  `configelement_id` int NOT NULL,
  `instrumentconfig_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `YSE_App_configelement_in_configelement_id_instrum_a637a910_uniq` (`configelement_id`,`instrumentconfig_id`),
  KEY `YSE_App_configelemen_instrumentconfig_id_eb94dddb_fk_YSE_App_i` (`instrumentconfig_id`),
  CONSTRAINT `YSE_App_configelemen_configelement_id_4958b161_fk_YSE_App_c` FOREIGN KEY (`configelement_id`) REFERENCES `YSE_App_configelement` (`id`),
  CONSTRAINT `YSE_App_configelemen_instrumentconfig_id_eb94dddb_fk_YSE_App_i` FOREIGN KEY (`instrumentconfig_id`) REFERENCES `YSE_App_instrumentconfig` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `YSE_App_dataquality`
--

DROP TABLE IF EXISTS `YSE_App_dataquality`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `YSE_App_dataquality` (
  `id` int NOT NULL AUTO_INCREMENT,
  `created_date` datetime(6) NOT NULL,
  `modified_date` datetime(6) NOT NULL,
  `name` varchar(128) NOT NULL,
  `created_by_id` int NOT NULL,
  `modified_by_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `YSE_App_dataquality_created_by_id_4084dbd5_fk_auth_user_id` (`created_by_id`),
  KEY `YSE_App_dataquality_modified_by_id_83c3596d_fk_auth_user_id` (`modified_by_id`),
  CONSTRAINT `YSE_App_dataquality_created_by_id_4084dbd5_fk_auth_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `YSE_App_dataquality_modified_by_id_83c3596d_fk_auth_user_id` FOREIGN KEY (`modified_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `YSE_App_followupstatus`
--

DROP TABLE IF EXISTS `YSE_App_followupstatus`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `YSE_App_followupstatus` (
  `id` int NOT NULL AUTO_INCREMENT,
  `created_date` datetime(6) NOT NULL,
  `modified_date` datetime(6) NOT NULL,
  `name` varchar(64) NOT NULL,
  `created_by_id` int NOT NULL,
  `modified_by_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `YSE_App_followupstatus_created_by_id_5ce0bc45_fk_auth_user_id` (`created_by_id`),
  KEY `YSE_App_followupstatus_modified_by_id_12e30a06_fk_auth_user_id` (`modified_by_id`),
  CONSTRAINT `YSE_App_followupstatus_created_by_id_5ce0bc45_fk_auth_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `YSE_App_followupstatus_modified_by_id_12e30a06_fk_auth_user_id` FOREIGN KEY (`modified_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `YSE_App_gwcandidate`
--

DROP TABLE IF EXISTS `YSE_App_gwcandidate`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `YSE_App_gwcandidate` (
  `id` int NOT NULL AUTO_INCREMENT,
  `created_date` datetime(6) NOT NULL,
  `modified_date` datetime(6) NOT NULL,
  `field_name` varchar(64) NOT NULL,
  `candidate_id` varchar(64) NOT NULL,
  `name` varchar(64) NOT NULL,
  `websniff_url` varchar(256) DEFAULT NULL,
  `created_by_id` int NOT NULL,
  `modified_by_id` int NOT NULL,
  `transient_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `YSE_App_gwcandidate_created_by_id_08f1a9a1_fk_auth_user_id` (`created_by_id`),
  KEY `YSE_App_gwcandidate_modified_by_id_60cef670_fk_auth_user_id` (`modified_by_id`),
  KEY `YSE_App_gwcandidate_transient_id_42b55dcc_fk_YSE_App_t` (`transient_id`),
  CONSTRAINT `YSE_App_gwcandidate_created_by_id_08f1a9a1_fk_auth_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `YSE_App_gwcandidate_modified_by_id_60cef670_fk_auth_user_id` FOREIGN KEY (`modified_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `YSE_App_gwcandidate_transient_id_42b55dcc_fk_YSE_App_t` FOREIGN KEY (`transient_id`) REFERENCES `YSE_App_transient` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=15 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `YSE_App_gwcandidateimage`
--

DROP TABLE IF EXISTS `YSE_App_gwcandidateimage`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `YSE_App_gwcandidateimage` (
  `id` int NOT NULL AUTO_INCREMENT,
  `created_date` datetime(6) NOT NULL,
  `modified_date` datetime(6) NOT NULL,
  `image_filename` varchar(256) NOT NULL,
  `dophot_class` int DEFAULT NULL,
  `created_by_id` int NOT NULL,
  `gw_candidate_id` int NOT NULL,
  `image_filter_id` int NOT NULL,
  `modified_by_id` int NOT NULL,
  `obs_date` datetime(6) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `YSE_App_gwcandidateimage_created_by_id_b71b6036_fk_auth_user_id` (`created_by_id`),
  KEY `YSE_App_gwcandidatei_gw_candidate_id_f7aa1c3e_fk_YSE_App_g` (`gw_candidate_id`),
  KEY `YSE_App_gwcandidatei_image_filter_id_6e486be2_fk_YSE_App_p` (`image_filter_id`),
  KEY `YSE_App_gwcandidateimage_modified_by_id_f01daac9_fk_auth_user_id` (`modified_by_id`),
  CONSTRAINT `YSE_App_gwcandidatei_gw_candidate_id_f7aa1c3e_fk_YSE_App_g` FOREIGN KEY (`gw_candidate_id`) REFERENCES `YSE_App_gwcandidate` (`id`),
  CONSTRAINT `YSE_App_gwcandidatei_image_filter_id_6e486be2_fk_YSE_App_p` FOREIGN KEY (`image_filter_id`) REFERENCES `YSE_App_photometricband` (`id`),
  CONSTRAINT `YSE_App_gwcandidateimage_created_by_id_b71b6036_fk_auth_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `YSE_App_gwcandidateimage_modified_by_id_f01daac9_fk_auth_user_id` FOREIGN KEY (`modified_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=15 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `YSE_App_host`
--

DROP TABLE IF EXISTS `YSE_App_host`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `YSE_App_host` (
  `id` int NOT NULL AUTO_INCREMENT,
  `created_date` datetime(6) NOT NULL,
  `modified_date` datetime(6) NOT NULL,
  `ra` double NOT NULL,
  `dec` double NOT NULL,
  `name` varchar(64) DEFAULT NULL,
  `redshift` double DEFAULT NULL,
  `redshift_err` double DEFAULT NULL,
  `r_a` double DEFAULT NULL,
  `r_b` double DEFAULT NULL,
  `theta` double DEFAULT NULL,
  `eff_offset` double DEFAULT NULL,
  `photo_z` double DEFAULT NULL,
  `photo_z_err` double DEFAULT NULL,
  `photo_z_source` varchar(64) DEFAULT NULL,
  `transient_host_rank` int DEFAULT NULL,
  `band_sextract_id` int DEFAULT NULL,
  `best_spec_id` int DEFAULT NULL,
  `created_by_id` int NOT NULL,
  `host_morphology_id` int DEFAULT NULL,
  `host_sed_id` int DEFAULT NULL,
  `modified_by_id` int NOT NULL,
  `photo_z_err_internal` double DEFAULT NULL,
  `photo_z_internal` double DEFAULT NULL,
  `photo_z_PSCNN` double DEFAULT NULL,
  `photo_z_err_PSCNN` double DEFAULT NULL,
  `panstarrs_objid` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `YSE_App_host_band_sextract_id_22f9e30e_fk_YSE_App_p` (`band_sextract_id`),
  KEY `YSE_App_host_best_spec_id_c89361aa_fk_YSE_App_hostspectrum_id` (`best_spec_id`),
  KEY `YSE_App_host_created_by_id_09293e09_fk_auth_user_id` (`created_by_id`),
  KEY `YSE_App_host_host_morphology_id_a00ee48a_fk_YSE_App_h` (`host_morphology_id`),
  KEY `YSE_App_host_host_sed_id_975550b1_fk_YSE_App_hostsed_id` (`host_sed_id`),
  KEY `YSE_App_host_modified_by_id_964f0b3f_fk_auth_user_id` (`modified_by_id`),
  CONSTRAINT `YSE_App_host_band_sextract_id_22f9e30e_fk_YSE_App_p` FOREIGN KEY (`band_sextract_id`) REFERENCES `YSE_App_photometricband` (`id`),
  CONSTRAINT `YSE_App_host_best_spec_id_c89361aa_fk_YSE_App_hostspectrum_id` FOREIGN KEY (`best_spec_id`) REFERENCES `YSE_App_hostspectrum` (`id`),
  CONSTRAINT `YSE_App_host_created_by_id_09293e09_fk_auth_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `YSE_App_host_host_morphology_id_a00ee48a_fk_YSE_App_h` FOREIGN KEY (`host_morphology_id`) REFERENCES `YSE_App_hostmorphology` (`id`),
  CONSTRAINT `YSE_App_host_host_sed_id_975550b1_fk_YSE_App_hostsed_id` FOREIGN KEY (`host_sed_id`) REFERENCES `YSE_App_hostsed` (`id`),
  CONSTRAINT `YSE_App_host_modified_by_id_964f0b3f_fk_auth_user_id` FOREIGN KEY (`modified_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=65437 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `YSE_App_hostfollowup`
--

DROP TABLE IF EXISTS `YSE_App_hostfollowup`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `YSE_App_hostfollowup` (
  `id` int NOT NULL AUTO_INCREMENT,
  `created_date` datetime(6) NOT NULL,
  `modified_date` datetime(6) NOT NULL,
  `valid_start` datetime(6) NOT NULL,
  `valid_stop` datetime(6) NOT NULL,
  `spec_priority` int DEFAULT NULL,
  `phot_priority` int DEFAULT NULL,
  `offset_star_ra` double DEFAULT NULL,
  `offset_star_dec` double DEFAULT NULL,
  `offset_north` double DEFAULT NULL,
  `offset_east` double DEFAULT NULL,
  `classical_resource_id` int DEFAULT NULL,
  `created_by_id` int NOT NULL,
  `host_id` int NOT NULL,
  `modified_by_id` int NOT NULL,
  `queued_resource_id` int DEFAULT NULL,
  `status_id` int NOT NULL,
  `too_resource_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `YSE_App_hostfollowup_classical_resource_i_f25b9d0d_fk_YSE_App_c` (`classical_resource_id`),
  KEY `YSE_App_hostfollowup_created_by_id_bb0b38e2_fk_auth_user_id` (`created_by_id`),
  KEY `YSE_App_hostfollowup_host_id_ba8a6cef_fk_YSE_App_host_id` (`host_id`),
  KEY `YSE_App_hostfollowup_modified_by_id_a7122a36_fk_auth_user_id` (`modified_by_id`),
  KEY `YSE_App_hostfollowup_queued_resource_id_5d5b983c_fk_YSE_App_q` (`queued_resource_id`),
  KEY `YSE_App_hostfollowup_status_id_d992ae4d_fk_YSE_App_f` (`status_id`),
  KEY `YSE_App_hostfollowup_too_resource_id_576b6090_fk_YSE_App_t` (`too_resource_id`),
  CONSTRAINT `YSE_App_hostfollowup_classical_resource_i_f25b9d0d_fk_YSE_App_c` FOREIGN KEY (`classical_resource_id`) REFERENCES `YSE_App_classicalresource` (`id`),
  CONSTRAINT `YSE_App_hostfollowup_created_by_id_bb0b38e2_fk_auth_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `YSE_App_hostfollowup_host_id_ba8a6cef_fk_YSE_App_host_id` FOREIGN KEY (`host_id`) REFERENCES `YSE_App_host` (`id`),
  CONSTRAINT `YSE_App_hostfollowup_modified_by_id_a7122a36_fk_auth_user_id` FOREIGN KEY (`modified_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `YSE_App_hostfollowup_queued_resource_id_5d5b983c_fk_YSE_App_q` FOREIGN KEY (`queued_resource_id`) REFERENCES `YSE_App_queuedresource` (`id`),
  CONSTRAINT `YSE_App_hostfollowup_status_id_d992ae4d_fk_YSE_App_f` FOREIGN KEY (`status_id`) REFERENCES `YSE_App_followupstatus` (`id`),
  CONSTRAINT `YSE_App_hostfollowup_too_resource_id_576b6090_fk_YSE_App_t` FOREIGN KEY (`too_resource_id`) REFERENCES `YSE_App_tooresource` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `YSE_App_hostimage`
--

DROP TABLE IF EXISTS `YSE_App_hostimage`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `YSE_App_hostimage` (
  `id` int NOT NULL AUTO_INCREMENT,
  `created_date` datetime(6) NOT NULL,
  `modified_date` datetime(6) NOT NULL,
  `img_file` varchar(512) DEFAULT NULL,
  `zero_point` double DEFAULT NULL,
  `zero_point_err` double DEFAULT NULL,
  `sky` double DEFAULT NULL,
  `sky_rms` double DEFAULT NULL,
  `dcmp_file` longtext,
  `created_by_id` int NOT NULL,
  `modified_by_id` int NOT NULL,
  `phot_data_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `YSE_App_hostimage_created_by_id_e011ffe6_fk_auth_user_id` (`created_by_id`),
  KEY `YSE_App_hostimage_modified_by_id_61281796_fk_auth_user_id` (`modified_by_id`),
  KEY `YSE_App_hostimage_phot_data_id_e20d4301_fk_YSE_App_h` (`phot_data_id`),
  CONSTRAINT `YSE_App_hostimage_created_by_id_e011ffe6_fk_auth_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `YSE_App_hostimage_modified_by_id_61281796_fk_auth_user_id` FOREIGN KEY (`modified_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `YSE_App_hostimage_phot_data_id_e20d4301_fk_YSE_App_h` FOREIGN KEY (`phot_data_id`) REFERENCES `YSE_App_hostphotdata` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=136856 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `YSE_App_hostmorphology`
--

DROP TABLE IF EXISTS `YSE_App_hostmorphology`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `YSE_App_hostmorphology` (
  `id` int NOT NULL AUTO_INCREMENT,
  `created_date` datetime(6) NOT NULL,
  `modified_date` datetime(6) NOT NULL,
  `name` varchar(64) NOT NULL,
  `created_by_id` int NOT NULL,
  `modified_by_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `YSE_App_hostmorphology_created_by_id_62599dae_fk_auth_user_id` (`created_by_id`),
  KEY `YSE_App_hostmorphology_modified_by_id_39a64bd6_fk_auth_user_id` (`modified_by_id`),
  CONSTRAINT `YSE_App_hostmorphology_created_by_id_62599dae_fk_auth_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `YSE_App_hostmorphology_modified_by_id_39a64bd6_fk_auth_user_id` FOREIGN KEY (`modified_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `YSE_App_hostobservationtask`
--

DROP TABLE IF EXISTS `YSE_App_hostobservationtask`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `YSE_App_hostobservationtask` (
  `id` int NOT NULL AUTO_INCREMENT,
  `created_date` datetime(6) NOT NULL,
  `modified_date` datetime(6) NOT NULL,
  `exposure_time` double NOT NULL,
  `number_of_exposures` int NOT NULL,
  `desired_obs_date` datetime(6) NOT NULL,
  `actual_obs_date` datetime(6) DEFAULT NULL,
  `description` longtext,
  `created_by_id` int NOT NULL,
  `followup_id` int NOT NULL,
  `instrument_config_id` int NOT NULL,
  `modified_by_id` int NOT NULL,
  `status_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `YSE_App_hostobservat_created_by_id_44935fe2_fk_auth_user` (`created_by_id`),
  KEY `YSE_App_hostobservat_followup_id_4f6403bf_fk_YSE_App_h` (`followup_id`),
  KEY `YSE_App_hostobservat_instrument_config_id_58d00b75_fk_YSE_App_i` (`instrument_config_id`),
  KEY `YSE_App_hostobservat_modified_by_id_8621e170_fk_auth_user` (`modified_by_id`),
  KEY `YSE_App_hostobservat_status_id_a66e153b_fk_YSE_App_t` (`status_id`),
  CONSTRAINT `YSE_App_hostobservat_created_by_id_44935fe2_fk_auth_user` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `YSE_App_hostobservat_followup_id_4f6403bf_fk_YSE_App_h` FOREIGN KEY (`followup_id`) REFERENCES `YSE_App_hostfollowup` (`id`),
  CONSTRAINT `YSE_App_hostobservat_instrument_config_id_58d00b75_fk_YSE_App_i` FOREIGN KEY (`instrument_config_id`) REFERENCES `YSE_App_instrumentconfig` (`id`),
  CONSTRAINT `YSE_App_hostobservat_modified_by_id_8621e170_fk_auth_user` FOREIGN KEY (`modified_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `YSE_App_hostobservat_status_id_a66e153b_fk_YSE_App_t` FOREIGN KEY (`status_id`) REFERENCES `YSE_App_taskstatus` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `YSE_App_hostphotdata`
--

DROP TABLE IF EXISTS `YSE_App_hostphotdata`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `YSE_App_hostphotdata` (
  `id` int NOT NULL AUTO_INCREMENT,
  `created_date` datetime(6) NOT NULL,
  `modified_date` datetime(6) NOT NULL,
  `obs_date` datetime(6) NOT NULL,
  `flux_zero_point` double DEFAULT NULL,
  `flux` double DEFAULT NULL,
  `flux_err` double DEFAULT NULL,
  `mag` double DEFAULT NULL,
  `mag_err` double DEFAULT NULL,
  `forced` tinyint(1) DEFAULT NULL,
  `band_id` int NOT NULL,
  `created_by_id` int NOT NULL,
  `modified_by_id` int NOT NULL,
  `photometry_id` int NOT NULL,
  `unit_id` int DEFAULT NULL,
  `data_quality_id` int DEFAULT NULL,
  `diffim` tinyint(1) DEFAULT NULL,
  `zp_off` double DEFAULT NULL,
  `mag_sys_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `YSE_App_hostphotdata_band_id_81a13f79_fk_YSE_App_p` (`band_id`),
  KEY `YSE_App_hostphotdata_created_by_id_5f1e3dbe_fk_auth_user_id` (`created_by_id`),
  KEY `YSE_App_hostphotdata_modified_by_id_78cc811c_fk_auth_user_id` (`modified_by_id`),
  KEY `YSE_App_hostphotdata_photometry_id_b04ce33f_fk_YSE_App_h` (`photometry_id`),
  KEY `YSE_App_hostphotdata_unit_id_77a51e6b_fk_YSE_App_unit_id` (`unit_id`),
  KEY `YSE_App_hostphotdata_data_quality_id_6c96463d_fk_YSE_App_d` (`data_quality_id`),
  KEY `YSE_App_hostphotdata_mag_sys_id_fd405dc6_fk_YSE_App_magsystem_id` (`mag_sys_id`),
  CONSTRAINT `YSE_App_hostphotdata_band_id_81a13f79_fk_YSE_App_p` FOREIGN KEY (`band_id`) REFERENCES `YSE_App_photometricband` (`id`),
  CONSTRAINT `YSE_App_hostphotdata_created_by_id_5f1e3dbe_fk_auth_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `YSE_App_hostphotdata_data_quality_id_6c96463d_fk_YSE_App_d` FOREIGN KEY (`data_quality_id`) REFERENCES `YSE_App_dataquality` (`id`),
  CONSTRAINT `YSE_App_hostphotdata_mag_sys_id_fd405dc6_fk_YSE_App_magsystem_id` FOREIGN KEY (`mag_sys_id`) REFERENCES `YSE_App_magsystem` (`id`),
  CONSTRAINT `YSE_App_hostphotdata_modified_by_id_78cc811c_fk_auth_user_id` FOREIGN KEY (`modified_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `YSE_App_hostphotdata_photometry_id_b04ce33f_fk_YSE_App_h` FOREIGN KEY (`photometry_id`) REFERENCES `YSE_App_hostphotometry` (`id`),
  CONSTRAINT `YSE_App_hostphotdata_unit_id_77a51e6b_fk_YSE_App_unit_id` FOREIGN KEY (`unit_id`) REFERENCES `YSE_App_unit` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=140007 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `YSE_App_hostphotometry`
--

DROP TABLE IF EXISTS `YSE_App_hostphotometry`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `YSE_App_hostphotometry` (
  `id` int NOT NULL AUTO_INCREMENT,
  `created_date` datetime(6) NOT NULL,
  `modified_date` datetime(6) NOT NULL,
  `created_by_id` int NOT NULL,
  `followup_id` int DEFAULT NULL,
  `host_id` int NOT NULL,
  `instrument_id` int NOT NULL,
  `modified_by_id` int NOT NULL,
  `obs_group_id` int NOT NULL,
  `reference` varchar(512) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `YSE_App_hostphotometry_created_by_id_26df0ab7_fk_auth_user_id` (`created_by_id`),
  KEY `YSE_App_hostphotomet_followup_id_1f83a044_fk_YSE_App_h` (`followup_id`),
  KEY `YSE_App_hostphotometry_host_id_e18f55a8_fk_YSE_App_host_id` (`host_id`),
  KEY `YSE_App_hostphotomet_instrument_id_804edac7_fk_YSE_App_i` (`instrument_id`),
  KEY `YSE_App_hostphotometry_modified_by_id_4e11687f_fk_auth_user_id` (`modified_by_id`),
  KEY `YSE_App_hostphotomet_obs_group_id_cc42fe6a_fk_YSE_App_o` (`obs_group_id`),
  CONSTRAINT `YSE_App_hostphotomet_followup_id_1f83a044_fk_YSE_App_h` FOREIGN KEY (`followup_id`) REFERENCES `YSE_App_hostfollowup` (`id`),
  CONSTRAINT `YSE_App_hostphotomet_instrument_id_804edac7_fk_YSE_App_i` FOREIGN KEY (`instrument_id`) REFERENCES `YSE_App_instrument` (`id`),
  CONSTRAINT `YSE_App_hostphotomet_obs_group_id_cc42fe6a_fk_YSE_App_o` FOREIGN KEY (`obs_group_id`) REFERENCES `YSE_App_observationgroup` (`id`),
  CONSTRAINT `YSE_App_hostphotometry_created_by_id_26df0ab7_fk_auth_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `YSE_App_hostphotometry_host_id_e18f55a8_fk_YSE_App_host_id` FOREIGN KEY (`host_id`) REFERENCES `YSE_App_host` (`id`),
  CONSTRAINT `YSE_App_hostphotometry_modified_by_id_4e11687f_fk_auth_user_id` FOREIGN KEY (`modified_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=140007 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `YSE_App_hostphotometry_groups`
--

DROP TABLE IF EXISTS `YSE_App_hostphotometry_groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `YSE_App_hostphotometry_groups` (
  `id` int NOT NULL AUTO_INCREMENT,
  `hostphotometry_id` int NOT NULL,
  `group_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `YSE_App_hostphotometry_g_hostphotometry_id_group__681a4266_uniq` (`hostphotometry_id`,`group_id`),
  KEY `YSE_App_hostphotometry_groups_group_id_d0fdc88e_fk_auth_group_id` (`group_id`),
  CONSTRAINT `YSE_App_hostphotomet_hostphotometry_id_a64f1ae7_fk_YSE_App_h` FOREIGN KEY (`hostphotometry_id`) REFERENCES `YSE_App_hostphotometry` (`id`),
  CONSTRAINT `YSE_App_hostphotometry_groups_group_id_d0fdc88e_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `YSE_App_hostsed`
--

DROP TABLE IF EXISTS `YSE_App_hostsed`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `YSE_App_hostsed` (
  `id` int NOT NULL AUTO_INCREMENT,
  `created_date` datetime(6) NOT NULL,
  `modified_date` datetime(6) NOT NULL,
  `metalicity` double DEFAULT NULL,
  `metalicity_err` double DEFAULT NULL,
  `log_SFR` double DEFAULT NULL,
  `log_SFR_err` double DEFAULT NULL,
  `log_sSFR` double DEFAULT NULL,
  `log_sSFR_err` double DEFAULT NULL,
  `log_mass` double DEFAULT NULL,
  `log_mass_err` double DEFAULT NULL,
  `ebv` double DEFAULT NULL,
  `ebv_err` double DEFAULT NULL,
  `log_age` double DEFAULT NULL,
  `log_age_err` double DEFAULT NULL,
  `redshift` double DEFAULT NULL,
  `redshift_err` double DEFAULT NULL,
  `fit_chi2` double DEFAULT NULL,
  `fit_n` int DEFAULT NULL,
  `fit_plot_file` longtext,
  `created_by_id` int NOT NULL,
  `modified_by_id` int NOT NULL,
  `sed_type_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `YSE_App_hostsed_created_by_id_76100720_fk_auth_user_id` (`created_by_id`),
  KEY `YSE_App_hostsed_modified_by_id_883c1b13_fk_auth_user_id` (`modified_by_id`),
  KEY `YSE_App_hostsed_sed_type_id_602a552a_fk_YSE_App_sedtype_id` (`sed_type_id`),
  CONSTRAINT `YSE_App_hostsed_created_by_id_76100720_fk_auth_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `YSE_App_hostsed_modified_by_id_883c1b13_fk_auth_user_id` FOREIGN KEY (`modified_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `YSE_App_hostsed_sed_type_id_602a552a_fk_YSE_App_sedtype_id` FOREIGN KEY (`sed_type_id`) REFERENCES `YSE_App_sedtype` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `YSE_App_hostspecdata`
--

DROP TABLE IF EXISTS `YSE_App_hostspecdata`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `YSE_App_hostspecdata` (
  `id` int NOT NULL AUTO_INCREMENT,
  `created_date` datetime(6) NOT NULL,
  `modified_date` datetime(6) NOT NULL,
  `wavelength` double NOT NULL,
  `flux` double NOT NULL,
  `wavelength_err` double DEFAULT NULL,
  `flux_err` double DEFAULT NULL,
  `created_by_id` int NOT NULL,
  `modified_by_id` int NOT NULL,
  `spectrum_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `YSE_App_hostspecdata_created_by_id_ec8c234b_fk_auth_user_id` (`created_by_id`),
  KEY `YSE_App_hostspecdata_modified_by_id_34a3f0d2_fk_auth_user_id` (`modified_by_id`),
  KEY `YSE_App_hostspecdata_spectrum_id_efc9d128_fk_YSE_App_h` (`spectrum_id`),
  CONSTRAINT `YSE_App_hostspecdata_created_by_id_ec8c234b_fk_auth_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `YSE_App_hostspecdata_modified_by_id_34a3f0d2_fk_auth_user_id` FOREIGN KEY (`modified_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `YSE_App_hostspecdata_spectrum_id_efc9d128_fk_YSE_App_h` FOREIGN KEY (`spectrum_id`) REFERENCES `YSE_App_hostspectrum` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `YSE_App_hostspectrum`
--

DROP TABLE IF EXISTS `YSE_App_hostspectrum`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `YSE_App_hostspectrum` (
  `id` int NOT NULL AUTO_INCREMENT,
  `created_date` datetime(6) NOT NULL,
  `modified_date` datetime(6) NOT NULL,
  `ra` double NOT NULL,
  `dec` double NOT NULL,
  `obs_date` datetime(6) NOT NULL,
  `redshift` double DEFAULT NULL,
  `redshift_err` double DEFAULT NULL,
  `redshift_quality` tinyint(1) DEFAULT NULL,
  `spec_plot_file` varchar(512) DEFAULT NULL,
  `spec_data_file` varchar(512) DEFAULT NULL,
  `spectrum_notes` longtext,
  `tdr` double DEFAULT NULL,
  `created_by_id` int NOT NULL,
  `followup_id` int DEFAULT NULL,
  `host_id` int NOT NULL,
  `instrument_id` int NOT NULL,
  `modified_by_id` int NOT NULL,
  `obs_group_id` int NOT NULL,
  `unit_id` int DEFAULT NULL,
  `data_quality_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `YSE_App_hostspectrum_created_by_id_84a495b5_fk_auth_user_id` (`created_by_id`),
  KEY `YSE_App_hostspectrum_followup_id_3ccb9d5a_fk_YSE_App_h` (`followup_id`),
  KEY `YSE_App_hostspectrum_host_id_febaa670_fk_YSE_App_host_id` (`host_id`),
  KEY `YSE_App_hostspectrum_instrument_id_c34b97cc_fk_YSE_App_i` (`instrument_id`),
  KEY `YSE_App_hostspectrum_modified_by_id_e8c50cfb_fk_auth_user_id` (`modified_by_id`),
  KEY `YSE_App_hostspectrum_obs_group_id_bbcd2788_fk_YSE_App_o` (`obs_group_id`),
  KEY `YSE_App_hostspectrum_unit_id_282ef9ed_fk_YSE_App_unit_id` (`unit_id`),
  KEY `YSE_App_hostspectrum_data_quality_id_7b2b7b39_fk_YSE_App_d` (`data_quality_id`),
  CONSTRAINT `YSE_App_hostspectrum_created_by_id_84a495b5_fk_auth_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `YSE_App_hostspectrum_data_quality_id_7b2b7b39_fk_YSE_App_d` FOREIGN KEY (`data_quality_id`) REFERENCES `YSE_App_dataquality` (`id`),
  CONSTRAINT `YSE_App_hostspectrum_followup_id_3ccb9d5a_fk_YSE_App_h` FOREIGN KEY (`followup_id`) REFERENCES `YSE_App_hostfollowup` (`id`),
  CONSTRAINT `YSE_App_hostspectrum_host_id_febaa670_fk_YSE_App_host_id` FOREIGN KEY (`host_id`) REFERENCES `YSE_App_host` (`id`),
  CONSTRAINT `YSE_App_hostspectrum_instrument_id_c34b97cc_fk_YSE_App_i` FOREIGN KEY (`instrument_id`) REFERENCES `YSE_App_instrument` (`id`),
  CONSTRAINT `YSE_App_hostspectrum_modified_by_id_e8c50cfb_fk_auth_user_id` FOREIGN KEY (`modified_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `YSE_App_hostspectrum_obs_group_id_bbcd2788_fk_YSE_App_o` FOREIGN KEY (`obs_group_id`) REFERENCES `YSE_App_observationgroup` (`id`),
  CONSTRAINT `YSE_App_hostspectrum_unit_id_282ef9ed_fk_YSE_App_unit_id` FOREIGN KEY (`unit_id`) REFERENCES `YSE_App_unit` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `YSE_App_hostspectrum_groups`
--

DROP TABLE IF EXISTS `YSE_App_hostspectrum_groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `YSE_App_hostspectrum_groups` (
  `id` int NOT NULL AUTO_INCREMENT,
  `hostspectrum_id` int NOT NULL,
  `group_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `YSE_App_hostspectrum_gro_hostspectrum_id_group_id_a0b4b217_uniq` (`hostspectrum_id`,`group_id`),
  KEY `YSE_App_hostspectrum_groups_group_id_3040f111_fk_auth_group_id` (`group_id`),
  CONSTRAINT `YSE_App_hostspectrum_groups_group_id_3040f111_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`),
  CONSTRAINT `YSE_App_hostspectrum_hostspectrum_id_30a57dac_fk_YSE_App_h` FOREIGN KEY (`hostspectrum_id`) REFERENCES `YSE_App_hostspectrum` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `YSE_App_hostwebresource`
--

DROP TABLE IF EXISTS `YSE_App_hostwebresource`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `YSE_App_hostwebresource` (
  `id` int NOT NULL AUTO_INCREMENT,
  `created_date` datetime(6) NOT NULL,
  `modified_date` datetime(6) NOT NULL,
  `information_text` longtext NOT NULL,
  `resource_url` varchar(512) NOT NULL,
  `created_by_id` int NOT NULL,
  `host_id` int NOT NULL,
  `information_source_id` int NOT NULL,
  `modified_by_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `YSE_App_hostwebresource_created_by_id_54d3468b_fk_auth_user_id` (`created_by_id`),
  KEY `YSE_App_hostwebresource_host_id_8a13bbaf_fk_YSE_App_host_id` (`host_id`),
  KEY `YSE_App_hostwebresou_information_source_i_3a2a5dcf_fk_YSE_App_i` (`information_source_id`),
  KEY `YSE_App_hostwebresource_modified_by_id_0f75e2a5_fk_auth_user_id` (`modified_by_id`),
  CONSTRAINT `YSE_App_hostwebresou_information_source_i_3a2a5dcf_fk_YSE_App_i` FOREIGN KEY (`information_source_id`) REFERENCES `YSE_App_informationsource` (`id`),
  CONSTRAINT `YSE_App_hostwebresource_created_by_id_54d3468b_fk_auth_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `YSE_App_hostwebresource_host_id_8a13bbaf_fk_YSE_App_host_id` FOREIGN KEY (`host_id`) REFERENCES `YSE_App_host` (`id`),
  CONSTRAINT `YSE_App_hostwebresource_modified_by_id_0f75e2a5_fk_auth_user_id` FOREIGN KEY (`modified_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `YSE_App_informationsource`
--

DROP TABLE IF EXISTS `YSE_App_informationsource`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `YSE_App_informationsource` (
  `id` int NOT NULL AUTO_INCREMENT,
  `created_date` datetime(6) NOT NULL,
  `modified_date` datetime(6) NOT NULL,
  `name` varchar(64) NOT NULL,
  `created_by_id` int NOT NULL,
  `modified_by_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `YSE_App_informationsource_created_by_id_33f147b1_fk_auth_user_id` (`created_by_id`),
  KEY `YSE_App_informations_modified_by_id_408948be_fk_auth_user` (`modified_by_id`),
  CONSTRAINT `YSE_App_informations_modified_by_id_408948be_fk_auth_user` FOREIGN KEY (`modified_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `YSE_App_informationsource_created_by_id_33f147b1_fk_auth_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `YSE_App_instrument`
--

DROP TABLE IF EXISTS `YSE_App_instrument`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `YSE_App_instrument` (
  `id` int NOT NULL AUTO_INCREMENT,
  `created_date` datetime(6) NOT NULL,
  `modified_date` datetime(6) NOT NULL,
  `name` varchar(64) NOT NULL,
  `description` longtext,
  `created_by_id` int NOT NULL,
  `modified_by_id` int NOT NULL,
  `telescope_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `YSE_App_instrument_created_by_id_12a1051d_fk_auth_user_id` (`created_by_id`),
  KEY `YSE_App_instrument_modified_by_id_a83f4a0a_fk_auth_user_id` (`modified_by_id`),
  KEY `YSE_App_instrument_telescope_id_daa18b5e_fk_YSE_App_telescope_id` (`telescope_id`),
  CONSTRAINT `YSE_App_instrument_created_by_id_12a1051d_fk_auth_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `YSE_App_instrument_modified_by_id_a83f4a0a_fk_auth_user_id` FOREIGN KEY (`modified_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `YSE_App_instrument_telescope_id_daa18b5e_fk_YSE_App_telescope_id` FOREIGN KEY (`telescope_id`) REFERENCES `YSE_App_telescope` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=89 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `YSE_App_instrumentconfig`
--

DROP TABLE IF EXISTS `YSE_App_instrumentconfig`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `YSE_App_instrumentconfig` (
  `id` int NOT NULL AUTO_INCREMENT,
  `created_date` datetime(6) NOT NULL,
  `modified_date` datetime(6) NOT NULL,
  `name` varchar(64) NOT NULL,
  `created_by_id` int NOT NULL,
  `instrument_id` int NOT NULL,
  `modified_by_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `YSE_App_instrumentconfig_created_by_id_71414207_fk_auth_user_id` (`created_by_id`),
  KEY `YSE_App_instrumentco_instrument_id_3b7c27ed_fk_YSE_App_i` (`instrument_id`),
  KEY `YSE_App_instrumentconfig_modified_by_id_40421491_fk_auth_user_id` (`modified_by_id`),
  CONSTRAINT `YSE_App_instrumentco_instrument_id_3b7c27ed_fk_YSE_App_i` FOREIGN KEY (`instrument_id`) REFERENCES `YSE_App_instrument` (`id`),
  CONSTRAINT `YSE_App_instrumentconfig_created_by_id_71414207_fk_auth_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `YSE_App_instrumentconfig_modified_by_id_40421491_fk_auth_user_id` FOREIGN KEY (`modified_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `YSE_App_internalsurvey`
--

DROP TABLE IF EXISTS `YSE_App_internalsurvey`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `YSE_App_internalsurvey` (
  `id` int NOT NULL AUTO_INCREMENT,
  `created_date` datetime(6) NOT NULL,
  `modified_date` datetime(6) NOT NULL,
  `name` varchar(64) NOT NULL,
  `created_by_id` int NOT NULL,
  `modified_by_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `YSE_App_internalsurvey_created_by_id_1f99919b_fk_auth_user_id` (`created_by_id`),
  KEY `YSE_App_internalsurvey_modified_by_id_857b93ef_fk_auth_user_id` (`modified_by_id`),
  CONSTRAINT `YSE_App_internalsurvey_created_by_id_1f99919b_fk_auth_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `YSE_App_internalsurvey_modified_by_id_857b93ef_fk_auth_user_id` FOREIGN KEY (`modified_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `YSE_App_log`
--

DROP TABLE IF EXISTS `YSE_App_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `YSE_App_log` (
  `id` int NOT NULL AUTO_INCREMENT,
  `created_date` datetime(6) NOT NULL,
  `modified_date` datetime(6) NOT NULL,
  `comment` longtext NOT NULL,
  `config_element_id` int DEFAULT NULL,
  `created_by_id` int NOT NULL,
  `host_id` int DEFAULT NULL,
  `host_followup_id` int DEFAULT NULL,
  `host_image_id` int DEFAULT NULL,
  `host_observation_task_id` int DEFAULT NULL,
  `host_photometry_id` int DEFAULT NULL,
  `host_sed_id` int DEFAULT NULL,
  `host_spectrum_id` int DEFAULT NULL,
  `host_web_resource_id` int DEFAULT NULL,
  `instrument_id` int DEFAULT NULL,
  `instrument_config_id` int DEFAULT NULL,
  `modified_by_id` int NOT NULL,
  `transient_id` int DEFAULT NULL,
  `transient_followup_id` int DEFAULT NULL,
  `transient_image_id` int DEFAULT NULL,
  `transient_observation_task_id` int DEFAULT NULL,
  `transient_photometry_id` int DEFAULT NULL,
  `transient_spectrum_id` int DEFAULT NULL,
  `transient_web_resource_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `YSE_App_log_config_element_id_8a2bf842_fk_YSE_App_c` (`config_element_id`),
  KEY `YSE_App_log_created_by_id_37125e0b_fk_auth_user_id` (`created_by_id`),
  KEY `YSE_App_log_host_id_c9749a0e_fk_YSE_App_host_id` (`host_id`),
  KEY `YSE_App_log_host_followup_id_7c97a780_fk_YSE_App_hostfollowup_id` (`host_followup_id`),
  KEY `YSE_App_log_host_image_id_ac3fe6c1_fk_YSE_App_hostimage_id` (`host_image_id`),
  KEY `YSE_App_log_host_observation_tas_35a6efa1_fk_YSE_App_h` (`host_observation_task_id`),
  KEY `YSE_App_log_host_photometry_id_6e568b8d_fk_YSE_App_h` (`host_photometry_id`),
  KEY `YSE_App_log_host_sed_id_46cb11d9_fk_YSE_App_hostsed_id` (`host_sed_id`),
  KEY `YSE_App_log_host_spectrum_id_831fa1ef_fk_YSE_App_hostspectrum_id` (`host_spectrum_id`),
  KEY `YSE_App_log_host_web_resource_id_670c0d7e_fk_YSE_App_h` (`host_web_resource_id`),
  KEY `YSE_App_log_instrument_id_a38e57a5_fk_YSE_App_instrument_id` (`instrument_id`),
  KEY `YSE_App_log_instrument_config_id_fe671a01_fk_YSE_App_i` (`instrument_config_id`),
  KEY `YSE_App_log_modified_by_id_0f4db829_fk_auth_user_id` (`modified_by_id`),
  KEY `YSE_App_log_transient_id_92c2bd36_fk_YSE_App_transient_id` (`transient_id`),
  KEY `YSE_App_log_transient_followup_i_d7a8227c_fk_YSE_App_t` (`transient_followup_id`),
  KEY `YSE_App_log_transient_image_id_d4f2d854_fk_YSE_App_t` (`transient_image_id`),
  KEY `YSE_App_log_transient_observatio_4554d727_fk_YSE_App_t` (`transient_observation_task_id`),
  KEY `YSE_App_log_transient_photometry_3e3f27f3_fk_YSE_App_t` (`transient_photometry_id`),
  KEY `YSE_App_log_transient_spectrum_i_e665af30_fk_YSE_App_t` (`transient_spectrum_id`),
  KEY `YSE_App_log_transient_web_resour_b222a7b9_fk_YSE_App_t` (`transient_web_resource_id`),
  CONSTRAINT `YSE_App_log_config_element_id_8a2bf842_fk_YSE_App_c` FOREIGN KEY (`config_element_id`) REFERENCES `YSE_App_configelement` (`id`),
  CONSTRAINT `YSE_App_log_created_by_id_37125e0b_fk_auth_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `YSE_App_log_host_followup_id_7c97a780_fk_YSE_App_hostfollowup_id` FOREIGN KEY (`host_followup_id`) REFERENCES `YSE_App_hostfollowup` (`id`),
  CONSTRAINT `YSE_App_log_host_id_c9749a0e_fk_YSE_App_host_id` FOREIGN KEY (`host_id`) REFERENCES `YSE_App_host` (`id`),
  CONSTRAINT `YSE_App_log_host_image_id_ac3fe6c1_fk_YSE_App_hostimage_id` FOREIGN KEY (`host_image_id`) REFERENCES `YSE_App_hostimage` (`id`),
  CONSTRAINT `YSE_App_log_host_observation_tas_35a6efa1_fk_YSE_App_h` FOREIGN KEY (`host_observation_task_id`) REFERENCES `YSE_App_hostobservationtask` (`id`),
  CONSTRAINT `YSE_App_log_host_photometry_id_6e568b8d_fk_YSE_App_h` FOREIGN KEY (`host_photometry_id`) REFERENCES `YSE_App_hostphotometry` (`id`),
  CONSTRAINT `YSE_App_log_host_sed_id_46cb11d9_fk_YSE_App_hostsed_id` FOREIGN KEY (`host_sed_id`) REFERENCES `YSE_App_hostsed` (`id`),
  CONSTRAINT `YSE_App_log_host_spectrum_id_831fa1ef_fk_YSE_App_hostspectrum_id` FOREIGN KEY (`host_spectrum_id`) REFERENCES `YSE_App_hostspectrum` (`id`),
  CONSTRAINT `YSE_App_log_host_web_resource_id_670c0d7e_fk_YSE_App_h` FOREIGN KEY (`host_web_resource_id`) REFERENCES `YSE_App_hostwebresource` (`id`),
  CONSTRAINT `YSE_App_log_instrument_config_id_fe671a01_fk_YSE_App_i` FOREIGN KEY (`instrument_config_id`) REFERENCES `YSE_App_instrumentconfig` (`id`),
  CONSTRAINT `YSE_App_log_instrument_id_a38e57a5_fk_YSE_App_instrument_id` FOREIGN KEY (`instrument_id`) REFERENCES `YSE_App_instrument` (`id`),
  CONSTRAINT `YSE_App_log_modified_by_id_0f4db829_fk_auth_user_id` FOREIGN KEY (`modified_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `YSE_App_log_transient_followup_i_d7a8227c_fk_YSE_App_t` FOREIGN KEY (`transient_followup_id`) REFERENCES `YSE_App_transientfollowup` (`id`),
  CONSTRAINT `YSE_App_log_transient_id_92c2bd36_fk_YSE_App_transient_id` FOREIGN KEY (`transient_id`) REFERENCES `YSE_App_transient` (`id`),
  CONSTRAINT `YSE_App_log_transient_image_id_d4f2d854_fk_YSE_App_t` FOREIGN KEY (`transient_image_id`) REFERENCES `YSE_App_transientimage` (`id`),
  CONSTRAINT `YSE_App_log_transient_observatio_4554d727_fk_YSE_App_t` FOREIGN KEY (`transient_observation_task_id`) REFERENCES `YSE_App_transientobservationtask` (`id`),
  CONSTRAINT `YSE_App_log_transient_photometry_3e3f27f3_fk_YSE_App_t` FOREIGN KEY (`transient_photometry_id`) REFERENCES `YSE_App_transientphotometry` (`id`),
  CONSTRAINT `YSE_App_log_transient_spectrum_i_e665af30_fk_YSE_App_t` FOREIGN KEY (`transient_spectrum_id`) REFERENCES `YSE_App_transientspectrum` (`id`),
  CONSTRAINT `YSE_App_log_transient_web_resour_b222a7b9_fk_YSE_App_t` FOREIGN KEY (`transient_web_resource_id`) REFERENCES `YSE_App_transientwebresource` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5745 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `YSE_App_magsystem`
--

DROP TABLE IF EXISTS `YSE_App_magsystem`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `YSE_App_magsystem` (
  `id` int NOT NULL AUTO_INCREMENT,
  `created_date` datetime(6) NOT NULL,
  `modified_date` datetime(6) NOT NULL,
  `name` varchar(64) NOT NULL,
  `created_by_id` int NOT NULL,
  `modified_by_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `YSE_App_magsystem_created_by_id_24beae01_fk_auth_user_id` (`created_by_id`),
  KEY `YSE_App_magsystem_modified_by_id_273e1928_fk_auth_user_id` (`modified_by_id`),
  CONSTRAINT `YSE_App_magsystem_created_by_id_24beae01_fk_auth_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `YSE_App_magsystem_modified_by_id_273e1928_fk_auth_user_id` FOREIGN KEY (`modified_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `YSE_App_observationgroup`
--

DROP TABLE IF EXISTS `YSE_App_observationgroup`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `YSE_App_observationgroup` (
  `id` int NOT NULL AUTO_INCREMENT,
  `created_date` datetime(6) NOT NULL,
  `modified_date` datetime(6) NOT NULL,
  `name` varchar(64) NOT NULL,
  `created_by_id` int NOT NULL,
  `modified_by_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `YSE_App_observationgroup_created_by_id_175dc2da_fk_auth_user_id` (`created_by_id`),
  KEY `YSE_App_observationgroup_modified_by_id_33e336cc_fk_auth_user_id` (`modified_by_id`),
  CONSTRAINT `YSE_App_observationgroup_created_by_id_175dc2da_fk_auth_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `YSE_App_observationgroup_modified_by_id_33e336cc_fk_auth_user_id` FOREIGN KEY (`modified_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=102 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `YSE_App_observatory`
--

DROP TABLE IF EXISTS `YSE_App_observatory`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `YSE_App_observatory` (
  `id` int NOT NULL AUTO_INCREMENT,
  `created_date` datetime(6) NOT NULL,
  `modified_date` datetime(6) NOT NULL,
  `name` varchar(64) NOT NULL,
  `utc_offset` int NOT NULL,
  `tz_name` varchar(64) NOT NULL,
  `DLS_utc_offset` int DEFAULT NULL,
  `DLS_tz_name` varchar(64) DEFAULT NULL,
  `DLS_start` datetime(6) DEFAULT NULL,
  `DLS_end` datetime(6) DEFAULT NULL,
  `created_by_id` int NOT NULL,
  `modified_by_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `YSE_App_observatory_created_by_id_4ec07484_fk_auth_user_id` (`created_by_id`),
  KEY `YSE_App_observatory_modified_by_id_e748dfba_fk_auth_user_id` (`modified_by_id`),
  CONSTRAINT `YSE_App_observatory_created_by_id_4ec07484_fk_auth_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `YSE_App_observatory_modified_by_id_e748dfba_fk_auth_user_id` FOREIGN KEY (`modified_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=31 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `YSE_App_oncalldate`
--

DROP TABLE IF EXISTS `YSE_App_oncalldate`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `YSE_App_oncalldate` (
  `id` int NOT NULL AUTO_INCREMENT,
  `created_date` datetime(6) NOT NULL,
  `modified_date` datetime(6) NOT NULL,
  `on_call_date` datetime(6) NOT NULL,
  `created_by_id` int NOT NULL,
  `modified_by_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `YSE_App_oncalldate_created_by_id_3c068451_fk_auth_user_id` (`created_by_id`),
  KEY `YSE_App_oncalldate_modified_by_id_d263c786_fk_auth_user_id` (`modified_by_id`),
  CONSTRAINT `YSE_App_oncalldate_created_by_id_3c068451_fk_auth_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `YSE_App_oncalldate_modified_by_id_d263c786_fk_auth_user_id` FOREIGN KEY (`modified_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=217 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `YSE_App_oncalldate_user`
--

DROP TABLE IF EXISTS `YSE_App_oncalldate_user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `YSE_App_oncalldate_user` (
  `id` int NOT NULL AUTO_INCREMENT,
  `oncalldate_id` int NOT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `YSE_App_oncalldate_user_oncalldate_id_user_id_b7a896bf_uniq` (`oncalldate_id`,`user_id`),
  KEY `YSE_App_oncalldate_user_user_id_a9bc4e46_fk_auth_user_id` (`user_id`),
  CONSTRAINT `YSE_App_oncalldate_u_oncalldate_id_f3a1f024_fk_YSE_App_o` FOREIGN KEY (`oncalldate_id`) REFERENCES `YSE_App_oncalldate` (`id`),
  CONSTRAINT `YSE_App_oncalldate_user_user_id_a9bc4e46_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=518 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `YSE_App_phase`
--

DROP TABLE IF EXISTS `YSE_App_phase`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `YSE_App_phase` (
  `id` int NOT NULL AUTO_INCREMENT,
  `created_date` datetime(6) NOT NULL,
  `modified_date` datetime(6) NOT NULL,
  `name` varchar(64) NOT NULL,
  `created_by_id` int NOT NULL,
  `modified_by_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `YSE_App_phase_created_by_id_d7a37354_fk_auth_user_id` (`created_by_id`),
  KEY `YSE_App_phase_modified_by_id_55cb8946_fk_auth_user_id` (`modified_by_id`),
  CONSTRAINT `YSE_App_phase_created_by_id_d7a37354_fk_auth_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `YSE_App_phase_modified_by_id_55cb8946_fk_auth_user_id` FOREIGN KEY (`modified_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `YSE_App_photometricband`
--

DROP TABLE IF EXISTS `YSE_App_photometricband`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `YSE_App_photometricband` (
  `id` int NOT NULL AUTO_INCREMENT,
  `created_date` datetime(6) NOT NULL,
  `modified_date` datetime(6) NOT NULL,
  `name` varchar(64) NOT NULL,
  `lambda_eff` varchar(64) DEFAULT NULL,
  `throughput_file` varchar(512) DEFAULT NULL,
  `created_by_id` int NOT NULL,
  `instrument_id` int NOT NULL,
  `modified_by_id` int NOT NULL,
  `disp_color` varchar(32) DEFAULT NULL,
  `disp_symbol` varchar(32) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `YSE_App_photometricband_created_by_id_ef3b1bf1_fk_auth_user_id` (`created_by_id`),
  KEY `YSE_App_photometricb_instrument_id_31868fcf_fk_YSE_App_i` (`instrument_id`),
  KEY `YSE_App_photometricband_modified_by_id_66d86460_fk_auth_user_id` (`modified_by_id`),
  CONSTRAINT `YSE_App_photometricb_instrument_id_31868fcf_fk_YSE_App_i` FOREIGN KEY (`instrument_id`) REFERENCES `YSE_App_instrument` (`id`),
  CONSTRAINT `YSE_App_photometricband_created_by_id_ef3b1bf1_fk_auth_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `YSE_App_photometricband_modified_by_id_66d86460_fk_auth_user_id` FOREIGN KEY (`modified_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=222 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `YSE_App_principalinvestigator`
--

DROP TABLE IF EXISTS `YSE_App_principalinvestigator`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `YSE_App_principalinvestigator` (
  `id` int NOT NULL AUTO_INCREMENT,
  `created_date` datetime(6) NOT NULL,
  `modified_date` datetime(6) NOT NULL,
  `name` varchar(64) NOT NULL,
  `phone` varchar(64) NOT NULL,
  `email` varchar(254) NOT NULL,
  `institution` varchar(64) NOT NULL,
  `description` longtext,
  `created_by_id` int NOT NULL,
  `modified_by_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `YSE_App_principalinv_created_by_id_f78343e2_fk_auth_user` (`created_by_id`),
  KEY `YSE_App_principalinv_modified_by_id_2e5793d0_fk_auth_user` (`modified_by_id`),
  CONSTRAINT `YSE_App_principalinv_created_by_id_f78343e2_fk_auth_user` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `YSE_App_principalinv_modified_by_id_2e5793d0_fk_auth_user` FOREIGN KEY (`modified_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=21 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `YSE_App_principalinvestigator_obs_group`
--

DROP TABLE IF EXISTS `YSE_App_principalinvestigator_obs_group`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `YSE_App_principalinvestigator_obs_group` (
  `id` int NOT NULL AUTO_INCREMENT,
  `principalinvestigator_id` int NOT NULL,
  `observationgroup_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `YSE_App_principalinvesti_principalinvestigator_id_fb219e97_uniq` (`principalinvestigator_id`,`observationgroup_id`),
  KEY `YSE_App_principalinv_observationgroup_id_5131ac44_fk_YSE_App_o` (`observationgroup_id`),
  CONSTRAINT `YSE_App_principalinv_observationgroup_id_5131ac44_fk_YSE_App_o` FOREIGN KEY (`observationgroup_id`) REFERENCES `YSE_App_observationgroup` (`id`),
  CONSTRAINT `YSE_App_principalinv_principalinvestigato_286afc12_fk_YSE_App_p` FOREIGN KEY (`principalinvestigator_id`) REFERENCES `YSE_App_principalinvestigator` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=21 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `YSE_App_profile`
--

DROP TABLE IF EXISTS `YSE_App_profile`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `YSE_App_profile` (
  `id` int NOT NULL AUTO_INCREMENT,
  `created_date` datetime(6) NOT NULL,
  `modified_date` datetime(6) NOT NULL,
  `phone_country_code` varchar(16) NOT NULL,
  `phone_area` varchar(3) NOT NULL,
  `phone_first_three` varchar(3) NOT NULL,
  `phone_last_four` varchar(4) NOT NULL,
  `phone_provider_str` varchar(16) NOT NULL,
  `created_by_id` int NOT NULL,
  `modified_by_id` int NOT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`),
  KEY `YSE_App_profile_created_by_id_6fa7e489_fk_auth_user_id` (`created_by_id`),
  KEY `YSE_App_profile_modified_by_id_161596d6_fk_auth_user_id` (`modified_by_id`),
  CONSTRAINT `YSE_App_profile_created_by_id_6fa7e489_fk_auth_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `YSE_App_profile_modified_by_id_161596d6_fk_auth_user_id` FOREIGN KEY (`modified_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `YSE_App_profile_user_id_6b2703b1_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `YSE_App_queuedresource`
--

DROP TABLE IF EXISTS `YSE_App_queuedresource`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `YSE_App_queuedresource` (
  `id` int NOT NULL AUTO_INCREMENT,
  `created_date` datetime(6) NOT NULL,
  `modified_date` datetime(6) NOT NULL,
  `begin_date_valid` datetime(6) NOT NULL,
  `end_date_valid` datetime(6) NOT NULL,
  `description` longtext,
  `awarded_hours` double DEFAULT NULL,
  `used_hours` double DEFAULT NULL,
  `created_by_id` int NOT NULL,
  `modified_by_id` int NOT NULL,
  `principal_investigator_id` int DEFAULT NULL,
  `telescope_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `YSE_App_queuedresource_created_by_id_1728990f_fk_auth_user_id` (`created_by_id`),
  KEY `YSE_App_queuedresource_modified_by_id_4967df46_fk_auth_user_id` (`modified_by_id`),
  KEY `YSE_App_queuedresour_principal_investigat_693f90c1_fk_YSE_App_p` (`principal_investigator_id`),
  KEY `YSE_App_queuedresour_telescope_id_776f3911_fk_YSE_App_t` (`telescope_id`),
  CONSTRAINT `YSE_App_queuedresour_principal_investigat_693f90c1_fk_YSE_App_p` FOREIGN KEY (`principal_investigator_id`) REFERENCES `YSE_App_principalinvestigator` (`id`),
  CONSTRAINT `YSE_App_queuedresour_telescope_id_776f3911_fk_YSE_App_t` FOREIGN KEY (`telescope_id`) REFERENCES `YSE_App_telescope` (`id`),
  CONSTRAINT `YSE_App_queuedresource_created_by_id_1728990f_fk_auth_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `YSE_App_queuedresource_modified_by_id_4967df46_fk_auth_user_id` FOREIGN KEY (`modified_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `YSE_App_queuedresource_groups`
--

DROP TABLE IF EXISTS `YSE_App_queuedresource_groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `YSE_App_queuedresource_groups` (
  `id` int NOT NULL AUTO_INCREMENT,
  `queuedresource_id` int NOT NULL,
  `group_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `YSE_App_queuedresource_g_queuedresource_id_group__a9848c1e_uniq` (`queuedresource_id`,`group_id`),
  KEY `YSE_App_queuedresource_groups_group_id_73e15d35_fk_auth_group_id` (`group_id`),
  CONSTRAINT `YSE_App_queuedresour_queuedresource_id_c1aa62a5_fk_YSE_App_q` FOREIGN KEY (`queuedresource_id`) REFERENCES `YSE_App_queuedresource` (`id`),
  CONSTRAINT `YSE_App_queuedresource_groups_group_id_73e15d35_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=51 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `YSE_App_sedtype`
--

DROP TABLE IF EXISTS `YSE_App_sedtype`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `YSE_App_sedtype` (
  `id` int NOT NULL AUTO_INCREMENT,
  `created_date` datetime(6) NOT NULL,
  `modified_date` datetime(6) NOT NULL,
  `name` varchar(64) NOT NULL,
  `created_by_id` int NOT NULL,
  `modified_by_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `YSE_App_sedtype_created_by_id_22767bca_fk_auth_user_id` (`created_by_id`),
  KEY `YSE_App_sedtype_modified_by_id_06d5b4c4_fk_auth_user_id` (`modified_by_id`),
  CONSTRAINT `YSE_App_sedtype_created_by_id_22767bca_fk_auth_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `YSE_App_sedtype_modified_by_id_06d5b4c4_fk_auth_user_id` FOREIGN KEY (`modified_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `YSE_App_surveyfield`
--

DROP TABLE IF EXISTS `YSE_App_surveyfield`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `YSE_App_surveyfield` (
  `id` int NOT NULL AUTO_INCREMENT,
  `created_date` datetime(6) NOT NULL,
  `modified_date` datetime(6) NOT NULL,
  `field_id` varchar(64) NOT NULL,
  `cadence` double DEFAULT NULL,
  `ra_cen` double NOT NULL,
  `dec_cen` double NOT NULL,
  `width_deg` double NOT NULL,
  `height_deg` double NOT NULL,
  `created_by_id` int NOT NULL,
  `instrument_id` int NOT NULL,
  `modified_by_id` int NOT NULL,
  `obs_group_id` int NOT NULL,
  `ztf_field_id` varchar(64) DEFAULT NULL,
  `active` tinyint(1) DEFAULT NULL,
  `targeted_galaxies` longtext,
  PRIMARY KEY (`id`),
  KEY `YSE_App_surveyfield_created_by_id_c07f4466_fk_auth_user_id` (`created_by_id`),
  KEY `YSE_App_surveyfield_instrument_id_152179d0_fk_YSE_App_i` (`instrument_id`),
  KEY `YSE_App_surveyfield_modified_by_id_b812791e_fk_auth_user_id` (`modified_by_id`),
  KEY `YSE_App_surveyfield_obs_group_id_167a25fb_fk_YSE_App_o` (`obs_group_id`),
  CONSTRAINT `YSE_App_surveyfield_created_by_id_c07f4466_fk_auth_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `YSE_App_surveyfield_instrument_id_152179d0_fk_YSE_App_i` FOREIGN KEY (`instrument_id`) REFERENCES `YSE_App_instrument` (`id`),
  CONSTRAINT `YSE_App_surveyfield_modified_by_id_b812791e_fk_auth_user_id` FOREIGN KEY (`modified_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `YSE_App_surveyfield_obs_group_id_167a25fb_fk_YSE_App_o` FOREIGN KEY (`obs_group_id`) REFERENCES `YSE_App_observationgroup` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1170 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `YSE_App_surveyfield_targeted_transients`
--

DROP TABLE IF EXISTS `YSE_App_surveyfield_targeted_transients`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `YSE_App_surveyfield_targeted_transients` (
  `id` int NOT NULL AUTO_INCREMENT,
  `surveyfield_id` int NOT NULL,
  `transient_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `YSE_App_surveyfield_targ_surveyfield_id_transient_df3111d3_uniq` (`surveyfield_id`,`transient_id`),
  KEY `YSE_App_surveyfield__transient_id_c6d99ff8_fk_YSE_App_t` (`transient_id`),
  CONSTRAINT `YSE_App_surveyfield__surveyfield_id_7e7df9b9_fk_YSE_App_s` FOREIGN KEY (`surveyfield_id`) REFERENCES `YSE_App_surveyfield` (`id`),
  CONSTRAINT `YSE_App_surveyfield__transient_id_c6d99ff8_fk_YSE_App_t` FOREIGN KEY (`transient_id`) REFERENCES `YSE_App_transient` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `YSE_App_surveyfieldmsb`
--

DROP TABLE IF EXISTS `YSE_App_surveyfieldmsb`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `YSE_App_surveyfieldmsb` (
  `id` int NOT NULL AUTO_INCREMENT,
  `created_date` datetime(6) NOT NULL,
  `modified_date` datetime(6) NOT NULL,
  `name` varchar(64) NOT NULL,
  `created_by_id` int NOT NULL,
  `modified_by_id` int NOT NULL,
  `obs_group_id` int NOT NULL,
  `active` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `YSE_App_surveyfieldmsb_created_by_id_1b0d5288_fk_auth_user_id` (`created_by_id`),
  KEY `YSE_App_surveyfieldmsb_modified_by_id_2c40e714_fk_auth_user_id` (`modified_by_id`),
  KEY `YSE_App_surveyfieldm_obs_group_id_057160ab_fk_YSE_App_o` (`obs_group_id`),
  CONSTRAINT `YSE_App_surveyfieldm_obs_group_id_057160ab_fk_YSE_App_o` FOREIGN KEY (`obs_group_id`) REFERENCES `YSE_App_observationgroup` (`id`),
  CONSTRAINT `YSE_App_surveyfieldmsb_created_by_id_1b0d5288_fk_auth_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `YSE_App_surveyfieldmsb_modified_by_id_2c40e714_fk_auth_user_id` FOREIGN KEY (`modified_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=42 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `YSE_App_surveyfieldmsb_survey_fields`
--

DROP TABLE IF EXISTS `YSE_App_surveyfieldmsb_survey_fields`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `YSE_App_surveyfieldmsb_survey_fields` (
  `id` int NOT NULL AUTO_INCREMENT,
  `surveyfieldmsb_id` int NOT NULL,
  `surveyfield_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `YSE_App_surveyfieldmsb_s_surveyfieldmsb_id_survey_e4489a5e_uniq` (`surveyfieldmsb_id`,`surveyfield_id`),
  KEY `YSE_App_surveyfieldm_surveyfield_id_99ffe0a3_fk_YSE_App_s` (`surveyfield_id`),
  CONSTRAINT `YSE_App_surveyfieldm_surveyfield_id_99ffe0a3_fk_YSE_App_s` FOREIGN KEY (`surveyfield_id`) REFERENCES `YSE_App_surveyfield` (`id`),
  CONSTRAINT `YSE_App_surveyfieldm_surveyfieldmsb_id_23d6a841_fk_YSE_App_s` FOREIGN KEY (`surveyfieldmsb_id`) REFERENCES `YSE_App_surveyfieldmsb` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=278 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `YSE_App_surveyobservation`
--

DROP TABLE IF EXISTS `YSE_App_surveyobservation`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `YSE_App_surveyobservation` (
  `id` int NOT NULL AUTO_INCREMENT,
  `created_date` datetime(6) NOT NULL,
  `modified_date` datetime(6) NOT NULL,
  `obs_mjd` double DEFAULT NULL,
  `exposure_time` double NOT NULL,
  `pos_angle_deg` double DEFAULT NULL,
  `fwhm_major` double DEFAULT NULL,
  `eccentricity` double DEFAULT NULL,
  `airmass` double DEFAULT NULL,
  `image_id` varchar(128) DEFAULT NULL,
  `created_by_id` int NOT NULL,
  `modified_by_id` int NOT NULL,
  `photometric_band_id` int NOT NULL,
  `status_id` int NOT NULL,
  `mjd_requested` double DEFAULT NULL,
  `survey_field_id` int NOT NULL,
  `mag_lim` double DEFAULT NULL,
  `n_good_skycell` int DEFAULT NULL,
  `quality` int DEFAULT NULL,
  `zpt_obs` double DEFAULT NULL,
  `diff_id` varchar(128) DEFAULT NULL,
  `stack_id` varchar(128) DEFAULT NULL,
  `warp_id` varchar(128) DEFAULT NULL,
  `msb_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `YSE_App_surveyobservation_created_by_id_0d8a6c2a_fk_auth_user_id` (`created_by_id`),
  KEY `YSE_App_surveyobserv_modified_by_id_2db2f1a9_fk_auth_user` (`modified_by_id`),
  KEY `YSE_App_surveyobserv_photometric_band_id_6fc3965f_fk_YSE_App_p` (`photometric_band_id`),
  KEY `YSE_App_surveyobserv_status_id_5d2d8c53_fk_YSE_App_t` (`status_id`),
  KEY `YSE_App_surveyobserv_survey_field_id_679387e0_fk_YSE_App_s` (`survey_field_id`),
  KEY `YSE_App_surveyobserv_msb_id_e0aff21d_fk_YSE_App_s` (`msb_id`),
  CONSTRAINT `YSE_App_surveyobserv_modified_by_id_2db2f1a9_fk_auth_user` FOREIGN KEY (`modified_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `YSE_App_surveyobserv_msb_id_e0aff21d_fk_YSE_App_s` FOREIGN KEY (`msb_id`) REFERENCES `YSE_App_surveyfieldmsb` (`id`),
  CONSTRAINT `YSE_App_surveyobserv_photometric_band_id_6fc3965f_fk_YSE_App_p` FOREIGN KEY (`photometric_band_id`) REFERENCES `YSE_App_photometricband` (`id`),
  CONSTRAINT `YSE_App_surveyobserv_status_id_5d2d8c53_fk_YSE_App_t` FOREIGN KEY (`status_id`) REFERENCES `YSE_App_taskstatus` (`id`),
  CONSTRAINT `YSE_App_surveyobserv_survey_field_id_679387e0_fk_YSE_App_s` FOREIGN KEY (`survey_field_id`) REFERENCES `YSE_App_surveyfield` (`id`),
  CONSTRAINT `YSE_App_surveyobservation_created_by_id_0d8a6c2a_fk_auth_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=82182 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `YSE_App_taskstatus`
--

DROP TABLE IF EXISTS `YSE_App_taskstatus`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `YSE_App_taskstatus` (
  `id` int NOT NULL AUTO_INCREMENT,
  `created_date` datetime(6) NOT NULL,
  `modified_date` datetime(6) NOT NULL,
  `name` varchar(64) NOT NULL,
  `created_by_id` int NOT NULL,
  `modified_by_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `YSE_App_taskstatus_created_by_id_3fffb74d_fk_auth_user_id` (`created_by_id`),
  KEY `YSE_App_taskstatus_modified_by_id_4d9532b5_fk_auth_user_id` (`modified_by_id`),
  CONSTRAINT `YSE_App_taskstatus_created_by_id_3fffb74d_fk_auth_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `YSE_App_taskstatus_modified_by_id_4d9532b5_fk_auth_user_id` FOREIGN KEY (`modified_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `YSE_App_telescope`
--

DROP TABLE IF EXISTS `YSE_App_telescope`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `YSE_App_telescope` (
  `id` int NOT NULL AUTO_INCREMENT,
  `created_date` datetime(6) NOT NULL,
  `modified_date` datetime(6) NOT NULL,
  `name` varchar(64) NOT NULL,
  `latitude` double NOT NULL,
  `longitude` double NOT NULL,
  `elevation` double NOT NULL,
  `created_by_id` int NOT NULL,
  `modified_by_id` int NOT NULL,
  `observatory_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `YSE_App_telescope_created_by_id_932366a5_fk_auth_user_id` (`created_by_id`),
  KEY `YSE_App_telescope_modified_by_id_eecdf506_fk_auth_user_id` (`modified_by_id`),
  KEY `YSE_App_telescope_observatory_id_a1120a5b_fk_YSE_App_o` (`observatory_id`),
  CONSTRAINT `YSE_App_telescope_created_by_id_932366a5_fk_auth_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `YSE_App_telescope_modified_by_id_eecdf506_fk_auth_user_id` FOREIGN KEY (`modified_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `YSE_App_telescope_observatory_id_a1120a5b_fk_YSE_App_o` FOREIGN KEY (`observatory_id`) REFERENCES `YSE_App_observatory` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=70 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `YSE_App_tooresource`
--

DROP TABLE IF EXISTS `YSE_App_tooresource`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `YSE_App_tooresource` (
  `id` int NOT NULL AUTO_INCREMENT,
  `created_date` datetime(6) NOT NULL,
  `modified_date` datetime(6) NOT NULL,
  `begin_date_valid` datetime(6) NOT NULL,
  `end_date_valid` datetime(6) NOT NULL,
  `description` longtext,
  `awarded_too_hours` double DEFAULT NULL,
  `used_too_hours` double DEFAULT NULL,
  `created_by_id` int NOT NULL,
  `modified_by_id` int NOT NULL,
  `principal_investigator_id` int DEFAULT NULL,
  `telescope_id` int NOT NULL,
  `awarded_too_triggers` double DEFAULT NULL,
  `used_too_triggers` double DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `YSE_App_tooresource_created_by_id_ef7f6b9b_fk_auth_user_id` (`created_by_id`),
  KEY `YSE_App_tooresource_modified_by_id_8617de00_fk_auth_user_id` (`modified_by_id`),
  KEY `YSE_App_tooresource_principal_investigat_242f95b8_fk_YSE_App_p` (`principal_investigator_id`),
  KEY `YSE_App_tooresource_telescope_id_27630c7e_fk_YSE_App_t` (`telescope_id`),
  CONSTRAINT `YSE_App_tooresource_created_by_id_ef7f6b9b_fk_auth_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `YSE_App_tooresource_modified_by_id_8617de00_fk_auth_user_id` FOREIGN KEY (`modified_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `YSE_App_tooresource_principal_investigat_242f95b8_fk_YSE_App_p` FOREIGN KEY (`principal_investigator_id`) REFERENCES `YSE_App_principalinvestigator` (`id`),
  CONSTRAINT `YSE_App_tooresource_telescope_id_27630c7e_fk_YSE_App_t` FOREIGN KEY (`telescope_id`) REFERENCES `YSE_App_telescope` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=30 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `YSE_App_tooresource_groups`
--

DROP TABLE IF EXISTS `YSE_App_tooresource_groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `YSE_App_tooresource_groups` (
  `id` int NOT NULL AUTO_INCREMENT,
  `tooresource_id` int NOT NULL,
  `group_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `YSE_App_tooresource_groups_tooresource_id_group_id_16728839_uniq` (`tooresource_id`,`group_id`),
  KEY `YSE_App_tooresource_groups_group_id_4fffb229_fk_auth_group_id` (`group_id`),
  CONSTRAINT `YSE_App_tooresource__tooresource_id_fa0705bc_fk_YSE_App_t` FOREIGN KEY (`tooresource_id`) REFERENCES `YSE_App_tooresource` (`id`),
  CONSTRAINT `YSE_App_tooresource_groups_group_id_4fffb229_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=46 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `YSE_App_transient`
--

DROP TABLE IF EXISTS `YSE_App_transient`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `YSE_App_transient` (
  `id` int NOT NULL AUTO_INCREMENT,
  `created_date` datetime(6) NOT NULL,
  `modified_date` datetime(6) NOT NULL,
  `name` varchar(64) NOT NULL,
  `ra` double NOT NULL,
  `dec` double NOT NULL,
  `disc_date` datetime(6) DEFAULT NULL,
  `candidate_hosts` longtext,
  `redshift` double DEFAULT NULL,
  `redshift_err` double DEFAULT NULL,
  `redshift_source` varchar(64) DEFAULT NULL,
  `non_detect_date` datetime(6) DEFAULT NULL,
  `non_detect_limit` double DEFAULT NULL,
  `mw_ebv` double DEFAULT NULL,
  `abs_mag_peak` double DEFAULT NULL,
  `abs_mag_peak_date` datetime(6) DEFAULT NULL,
  `postage_stamp_file` varchar(512) DEFAULT NULL,
  `abs_mag_peak_band_id` int DEFAULT NULL,
  `antares_classification_id` int DEFAULT NULL,
  `best_spec_class_id` int DEFAULT NULL,
  `best_spectrum_id` int DEFAULT NULL,
  `created_by_id` int NOT NULL,
  `host_id` int DEFAULT NULL,
  `internal_survey_id` int DEFAULT NULL,
  `modified_by_id` int NOT NULL,
  `non_detect_band_id` int DEFAULT NULL,
  `obs_group_id` int NOT NULL,
  `photo_class_id` int DEFAULT NULL,
  `status_id` int NOT NULL,
  `k2_validated` tinyint(1) DEFAULT NULL,
  `k2_msg` longtext,
  `TNS_spec_class` varchar(64) DEFAULT NULL,
  `slug` varchar(50) DEFAULT NULL,
  `point_source_probability` double DEFAULT NULL,
  `postage_stamp_diff` varchar(512) DEFAULT NULL,
  `postage_stamp_ref` varchar(512) DEFAULT NULL,
  `postage_stamp_diff_fits` varchar(512) DEFAULT NULL,
  `postage_stamp_file_fits` varchar(512) DEFAULT NULL,
  `postage_stamp_ref_fits` varchar(512) DEFAULT NULL,
  `context_class_id` int DEFAULT NULL,
  `has_chandra` tinyint(1) DEFAULT NULL,
  `has_hst` tinyint(1) DEFAULT NULL,
  `has_spitzer` tinyint(1) DEFAULT NULL,
  `dec_err` double DEFAULT NULL,
  `ra_err` double DEFAULT NULL,
  `real_bogus_score` double DEFAULT NULL,
  `alt_status` varchar(64) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `slug` (`slug`),
  KEY `YSE_App_transient_abs_mag_peak_band_id_33f1b41f_fk_YSE_App_p` (`abs_mag_peak_band_id`),
  KEY `YSE_App_transient_antares_classificati_3f4bb186_fk_YSE_App_a` (`antares_classification_id`),
  KEY `YSE_App_transient_best_spec_class_id_690c1b73_fk_YSE_App_t` (`best_spec_class_id`),
  KEY `YSE_App_transient_best_spectrum_id_fdea12be_fk_YSE_App_t` (`best_spectrum_id`),
  KEY `YSE_App_transient_created_by_id_a88cfdaf_fk_auth_user_id` (`created_by_id`),
  KEY `YSE_App_transient_host_id_37b222be_fk_YSE_App_host_id` (`host_id`),
  KEY `YSE_App_transient_modified_by_id_1e55aa1d_fk_auth_user_id` (`modified_by_id`),
  KEY `YSE_App_transient_non_detect_band_id_1dd41034_fk_YSE_App_p` (`non_detect_band_id`),
  KEY `YSE_App_transient_obs_group_id_c7570b67_fk_YSE_App_o` (`obs_group_id`),
  KEY `YSE_App_transient_photo_class_id_3e395faa_fk_YSE_App_t` (`photo_class_id`),
  KEY `YSE_App_transient_status_id_997b80b0_fk_YSE_App_t` (`status_id`),
  KEY `YSE_App_transient_internal_survey_id_c2cac32b_fk_YSE_App_i` (`internal_survey_id`),
  KEY `YSE_App_transient_context_class_id_c8833d9b_fk_YSE_App_t` (`context_class_id`),
  CONSTRAINT `YSE_App_transient_abs_mag_peak_band_id_33f1b41f_fk_YSE_App_p` FOREIGN KEY (`abs_mag_peak_band_id`) REFERENCES `YSE_App_photometricband` (`id`),
  CONSTRAINT `YSE_App_transient_antares_classificati_3f4bb186_fk_YSE_App_a` FOREIGN KEY (`antares_classification_id`) REFERENCES `YSE_App_antaresclassification` (`id`),
  CONSTRAINT `YSE_App_transient_best_spec_class_id_690c1b73_fk_YSE_App_t` FOREIGN KEY (`best_spec_class_id`) REFERENCES `YSE_App_transientclass` (`id`),
  CONSTRAINT `YSE_App_transient_best_spectrum_id_fdea12be_fk_YSE_App_t` FOREIGN KEY (`best_spectrum_id`) REFERENCES `YSE_App_transientspectrum` (`id`),
  CONSTRAINT `YSE_App_transient_context_class_id_c8833d9b_fk_YSE_App_t` FOREIGN KEY (`context_class_id`) REFERENCES `YSE_App_transientclass` (`id`),
  CONSTRAINT `YSE_App_transient_created_by_id_a88cfdaf_fk_auth_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `YSE_App_transient_host_id_37b222be_fk_YSE_App_host_id` FOREIGN KEY (`host_id`) REFERENCES `YSE_App_host` (`id`),
  CONSTRAINT `YSE_App_transient_internal_survey_id_c2cac32b_fk_YSE_App_i` FOREIGN KEY (`internal_survey_id`) REFERENCES `YSE_App_internalsurvey` (`id`),
  CONSTRAINT `YSE_App_transient_modified_by_id_1e55aa1d_fk_auth_user_id` FOREIGN KEY (`modified_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `YSE_App_transient_non_detect_band_id_1dd41034_fk_YSE_App_p` FOREIGN KEY (`non_detect_band_id`) REFERENCES `YSE_App_photometricband` (`id`),
  CONSTRAINT `YSE_App_transient_obs_group_id_c7570b67_fk_YSE_App_o` FOREIGN KEY (`obs_group_id`) REFERENCES `YSE_App_observationgroup` (`id`),
  CONSTRAINT `YSE_App_transient_photo_class_id_3e395faa_fk_YSE_App_t` FOREIGN KEY (`photo_class_id`) REFERENCES `YSE_App_transientclass` (`id`),
  CONSTRAINT `YSE_App_transient_status_id_997b80b0_fk_YSE_App_t` FOREIGN KEY (`status_id`) REFERENCES `YSE_App_transientstatus` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=105543 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `YSE_App_transient_tags`
--

DROP TABLE IF EXISTS `YSE_App_transient_tags`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `YSE_App_transient_tags` (
  `id` int NOT NULL AUTO_INCREMENT,
  `transient_id` int NOT NULL,
  `transienttag_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `YSE_App_transient_tags_transient_id_transientta_072a9823_uniq` (`transient_id`,`transienttag_id`),
  KEY `YSE_App_transient_ta_transienttag_id_26eb4c68_fk_YSE_App_t` (`transienttag_id`),
  CONSTRAINT `YSE_App_transient_ta_transient_id_c697b853_fk_YSE_App_t` FOREIGN KEY (`transient_id`) REFERENCES `YSE_App_transient` (`id`),
  CONSTRAINT `YSE_App_transient_ta_transienttag_id_26eb4c68_fk_YSE_App_t` FOREIGN KEY (`transienttag_id`) REFERENCES `YSE_App_transienttag` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=372763 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `YSE_App_transientclass`
--

DROP TABLE IF EXISTS `YSE_App_transientclass`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `YSE_App_transientclass` (
  `id` int NOT NULL AUTO_INCREMENT,
  `created_date` datetime(6) NOT NULL,
  `modified_date` datetime(6) NOT NULL,
  `name` varchar(64) NOT NULL,
  `created_by_id` int NOT NULL,
  `modified_by_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `YSE_App_transientclass_created_by_id_a2d578e8_fk_auth_user_id` (`created_by_id`),
  KEY `YSE_App_transientclass_modified_by_id_2efadc2a_fk_auth_user_id` (`modified_by_id`),
  CONSTRAINT `YSE_App_transientclass_created_by_id_a2d578e8_fk_auth_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `YSE_App_transientclass_modified_by_id_2efadc2a_fk_auth_user_id` FOREIGN KEY (`modified_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=66 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `YSE_App_transientdiffimage`
--

DROP TABLE IF EXISTS `YSE_App_transientdiffimage`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `YSE_App_transientdiffimage` (
  `id` int NOT NULL AUTO_INCREMENT,
  `created_date` datetime(6) NOT NULL,
  `modified_date` datetime(6) NOT NULL,
  `postage_stamp_file` varchar(512) DEFAULT NULL,
  `postage_stamp_ref` varchar(512) DEFAULT NULL,
  `postage_stamp_diff` varchar(512) DEFAULT NULL,
  `postage_stamp_file_fits` varchar(512) DEFAULT NULL,
  `postage_stamp_ref_fits` varchar(512) DEFAULT NULL,
  `postage_stamp_diff_fits` varchar(512) DEFAULT NULL,
  `diff_zero_point` double DEFAULT NULL,
  `diff_zero_point_err` double DEFAULT NULL,
  `diff_sky` double DEFAULT NULL,
  `diff_sky_rms` double DEFAULT NULL,
  `diff_dcmp_file` longtext,
  `created_by_id` int NOT NULL,
  `modified_by_id` int NOT NULL,
  `phot_data_id` int NOT NULL,
  `valid_pixels` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `YSE_App_transientdif_created_by_id_df8c582e_fk_auth_user` (`created_by_id`),
  KEY `YSE_App_transientdif_modified_by_id_7fc68617_fk_auth_user` (`modified_by_id`),
  KEY `YSE_App_transientdif_phot_data_id_651babe7_fk_YSE_App_t` (`phot_data_id`),
  CONSTRAINT `YSE_App_transientdif_created_by_id_df8c582e_fk_auth_user` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `YSE_App_transientdif_modified_by_id_7fc68617_fk_auth_user` FOREIGN KEY (`modified_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `YSE_App_transientdif_phot_data_id_651babe7_fk_YSE_App_t` FOREIGN KEY (`phot_data_id`) REFERENCES `YSE_App_transientphotdata` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=28570 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `YSE_App_transientfollowup`
--

DROP TABLE IF EXISTS `YSE_App_transientfollowup`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `YSE_App_transientfollowup` (
  `id` int NOT NULL AUTO_INCREMENT,
  `created_date` datetime(6) NOT NULL,
  `modified_date` datetime(6) NOT NULL,
  `valid_start` datetime(6) NOT NULL,
  `valid_stop` datetime(6) NOT NULL,
  `spec_priority` int DEFAULT NULL,
  `phot_priority` int DEFAULT NULL,
  `offset_star_ra` double DEFAULT NULL,
  `offset_star_dec` double DEFAULT NULL,
  `offset_north` double DEFAULT NULL,
  `offset_east` double DEFAULT NULL,
  `classical_resource_id` int DEFAULT NULL,
  `created_by_id` int NOT NULL,
  `modified_by_id` int NOT NULL,
  `queued_resource_id` int DEFAULT NULL,
  `status_id` int NOT NULL,
  `too_resource_id` int DEFAULT NULL,
  `transient_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `YSE_App_transientfol_classical_resource_i_adca8489_fk_YSE_App_c` (`classical_resource_id`),
  KEY `YSE_App_transientfollowup_created_by_id_88ed3877_fk_auth_user_id` (`created_by_id`),
  KEY `YSE_App_transientfol_modified_by_id_86c4b7f8_fk_auth_user` (`modified_by_id`),
  KEY `YSE_App_transientfol_queued_resource_id_102c0e22_fk_YSE_App_q` (`queued_resource_id`),
  KEY `YSE_App_transientfol_status_id_cf965adb_fk_YSE_App_f` (`status_id`),
  KEY `YSE_App_transientfol_too_resource_id_f469e882_fk_YSE_App_t` (`too_resource_id`),
  KEY `YSE_App_transientfol_transient_id_3f62e706_fk_YSE_App_t` (`transient_id`),
  CONSTRAINT `YSE_App_transientfol_classical_resource_i_adca8489_fk_YSE_App_c` FOREIGN KEY (`classical_resource_id`) REFERENCES `YSE_App_classicalresource` (`id`),
  CONSTRAINT `YSE_App_transientfol_modified_by_id_86c4b7f8_fk_auth_user` FOREIGN KEY (`modified_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `YSE_App_transientfol_queued_resource_id_102c0e22_fk_YSE_App_q` FOREIGN KEY (`queued_resource_id`) REFERENCES `YSE_App_queuedresource` (`id`),
  CONSTRAINT `YSE_App_transientfol_status_id_cf965adb_fk_YSE_App_f` FOREIGN KEY (`status_id`) REFERENCES `YSE_App_followupstatus` (`id`),
  CONSTRAINT `YSE_App_transientfol_too_resource_id_f469e882_fk_YSE_App_t` FOREIGN KEY (`too_resource_id`) REFERENCES `YSE_App_tooresource` (`id`),
  CONSTRAINT `YSE_App_transientfol_transient_id_3f62e706_fk_YSE_App_t` FOREIGN KEY (`transient_id`) REFERENCES `YSE_App_transient` (`id`),
  CONSTRAINT `YSE_App_transientfollowup_created_by_id_88ed3877_fk_auth_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=6987 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `YSE_App_transientimage`
--

DROP TABLE IF EXISTS `YSE_App_transientimage`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `YSE_App_transientimage` (
  `id` int NOT NULL AUTO_INCREMENT,
  `created_date` datetime(6) NOT NULL,
  `modified_date` datetime(6) NOT NULL,
  `img_file` varchar(512) DEFAULT NULL,
  `zero_point` double DEFAULT NULL,
  `zero_point_err` double DEFAULT NULL,
  `sky` double DEFAULT NULL,
  `sky_rms` double DEFAULT NULL,
  `dcmp_file` longtext,
  `created_by_id` int NOT NULL,
  `modified_by_id` int NOT NULL,
  `phot_data_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `YSE_App_transientimage_created_by_id_71bc7091_fk_auth_user_id` (`created_by_id`),
  KEY `YSE_App_transientimage_modified_by_id_5b592cc2_fk_auth_user_id` (`modified_by_id`),
  KEY `YSE_App_transientima_phot_data_id_80832dbb_fk_YSE_App_t` (`phot_data_id`),
  CONSTRAINT `YSE_App_transientima_phot_data_id_80832dbb_fk_YSE_App_t` FOREIGN KEY (`phot_data_id`) REFERENCES `YSE_App_transientphotdata` (`id`),
  CONSTRAINT `YSE_App_transientimage_created_by_id_71bc7091_fk_auth_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `YSE_App_transientimage_modified_by_id_5b592cc2_fk_auth_user_id` FOREIGN KEY (`modified_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `YSE_App_transientobservationtask`
--

DROP TABLE IF EXISTS `YSE_App_transientobservationtask`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `YSE_App_transientobservationtask` (
  `id` int NOT NULL AUTO_INCREMENT,
  `created_date` datetime(6) NOT NULL,
  `modified_date` datetime(6) NOT NULL,
  `exposure_time` double NOT NULL,
  `number_of_exposures` int NOT NULL,
  `desired_obs_date` datetime(6) NOT NULL,
  `actual_obs_date` datetime(6) DEFAULT NULL,
  `description` longtext,
  `created_by_id` int NOT NULL,
  `followup_id` int NOT NULL,
  `instrument_config_id` int NOT NULL,
  `modified_by_id` int NOT NULL,
  `status_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `YSE_App_transientobs_created_by_id_80ae469f_fk_auth_user` (`created_by_id`),
  KEY `YSE_App_transientobs_followup_id_50ec980f_fk_YSE_App_t` (`followup_id`),
  KEY `YSE_App_transientobs_instrument_config_id_d49cd29d_fk_YSE_App_i` (`instrument_config_id`),
  KEY `YSE_App_transientobs_modified_by_id_6a66105e_fk_auth_user` (`modified_by_id`),
  KEY `YSE_App_transientobs_status_id_8e50d6f9_fk_YSE_App_t` (`status_id`),
  CONSTRAINT `YSE_App_transientobs_created_by_id_80ae469f_fk_auth_user` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `YSE_App_transientobs_followup_id_50ec980f_fk_YSE_App_t` FOREIGN KEY (`followup_id`) REFERENCES `YSE_App_transientfollowup` (`id`),
  CONSTRAINT `YSE_App_transientobs_instrument_config_id_d49cd29d_fk_YSE_App_i` FOREIGN KEY (`instrument_config_id`) REFERENCES `YSE_App_instrumentconfig` (`id`),
  CONSTRAINT `YSE_App_transientobs_modified_by_id_6a66105e_fk_auth_user` FOREIGN KEY (`modified_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `YSE_App_transientobs_status_id_8e50d6f9_fk_YSE_App_t` FOREIGN KEY (`status_id`) REFERENCES `YSE_App_taskstatus` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `YSE_App_transientphotdata`
--

DROP TABLE IF EXISTS `YSE_App_transientphotdata`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `YSE_App_transientphotdata` (
  `id` int NOT NULL AUTO_INCREMENT,
  `created_date` datetime(6) NOT NULL,
  `modified_date` datetime(6) NOT NULL,
  `obs_date` datetime(6) NOT NULL,
  `flux_zero_point` double DEFAULT NULL,
  `flux` double DEFAULT NULL,
  `flux_err` double DEFAULT NULL,
  `mag` double DEFAULT NULL,
  `mag_err` double DEFAULT NULL,
  `forced` tinyint(1) DEFAULT NULL,
  `band_id` int NOT NULL,
  `created_by_id` int NOT NULL,
  `modified_by_id` int NOT NULL,
  `photometry_id` int NOT NULL,
  `discovery_point` tinyint(1) DEFAULT NULL,
  `unit_id` int DEFAULT NULL,
  `data_quality_id` int DEFAULT NULL,
  `diffim` tinyint(1) DEFAULT NULL,
  `zp_off` double DEFAULT NULL,
  `mag_sys_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `YSE_App_transientpho_band_id_ba0c5fc2_fk_YSE_App_p` (`band_id`),
  KEY `YSE_App_transientphotdata_created_by_id_cfdfa466_fk_auth_user_id` (`created_by_id`),
  KEY `YSE_App_transientpho_modified_by_id_6eeed5db_fk_auth_user` (`modified_by_id`),
  KEY `YSE_App_transientpho_photometry_id_fbc5dfd2_fk_YSE_App_t` (`photometry_id`),
  KEY `YSE_App_transientphotdata_unit_id_22ad2703_fk_YSE_App_unit_id` (`unit_id`),
  KEY `YSE_App_transientpho_data_quality_id_42c5683e_fk_YSE_App_d` (`data_quality_id`),
  KEY `YSE_App_transientpho_mag_sys_id_2f6411d4_fk_YSE_App_m` (`mag_sys_id`),
  CONSTRAINT `YSE_App_transientpho_band_id_ba0c5fc2_fk_YSE_App_p` FOREIGN KEY (`band_id`) REFERENCES `YSE_App_photometricband` (`id`),
  CONSTRAINT `YSE_App_transientpho_data_quality_id_42c5683e_fk_YSE_App_d` FOREIGN KEY (`data_quality_id`) REFERENCES `YSE_App_dataquality` (`id`),
  CONSTRAINT `YSE_App_transientpho_mag_sys_id_2f6411d4_fk_YSE_App_m` FOREIGN KEY (`mag_sys_id`) REFERENCES `YSE_App_magsystem` (`id`),
  CONSTRAINT `YSE_App_transientpho_modified_by_id_6eeed5db_fk_auth_user` FOREIGN KEY (`modified_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `YSE_App_transientpho_photometry_id_fbc5dfd2_fk_YSE_App_t` FOREIGN KEY (`photometry_id`) REFERENCES `YSE_App_transientphotometry` (`id`),
  CONSTRAINT `YSE_App_transientphotdata_created_by_id_cfdfa466_fk_auth_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `YSE_App_transientphotdata_unit_id_22ad2703_fk_YSE_App_unit_id` FOREIGN KEY (`unit_id`) REFERENCES `YSE_App_unit` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3170270 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `YSE_App_transientphotometry`
--

DROP TABLE IF EXISTS `YSE_App_transientphotometry`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `YSE_App_transientphotometry` (
  `id` int NOT NULL AUTO_INCREMENT,
  `created_date` datetime(6) NOT NULL,
  `modified_date` datetime(6) NOT NULL,
  `created_by_id` int NOT NULL,
  `followup_id` int DEFAULT NULL,
  `host_id` int DEFAULT NULL,
  `instrument_id` int NOT NULL,
  `modified_by_id` int NOT NULL,
  `obs_group_id` int NOT NULL,
  `transient_id` int NOT NULL,
  `reference` varchar(512) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `YSE_App_transientpho_created_by_id_c7f15528_fk_auth_user` (`created_by_id`),
  KEY `YSE_App_transientpho_followup_id_bd69bcf4_fk_YSE_App_t` (`followup_id`),
  KEY `YSE_App_transientphotometry_host_id_58b364c2_fk_YSE_App_host_id` (`host_id`),
  KEY `YSE_App_transientpho_instrument_id_0ed542ce_fk_YSE_App_i` (`instrument_id`),
  KEY `YSE_App_transientpho_modified_by_id_79ee7170_fk_auth_user` (`modified_by_id`),
  KEY `YSE_App_transientpho_obs_group_id_f44df2ae_fk_YSE_App_o` (`obs_group_id`),
  KEY `YSE_App_transientpho_transient_id_9770bdf2_fk_YSE_App_t` (`transient_id`),
  CONSTRAINT `YSE_App_transientpho_created_by_id_c7f15528_fk_auth_user` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `YSE_App_transientpho_followup_id_bd69bcf4_fk_YSE_App_t` FOREIGN KEY (`followup_id`) REFERENCES `YSE_App_transientfollowup` (`id`),
  CONSTRAINT `YSE_App_transientpho_instrument_id_0ed542ce_fk_YSE_App_i` FOREIGN KEY (`instrument_id`) REFERENCES `YSE_App_instrument` (`id`),
  CONSTRAINT `YSE_App_transientpho_modified_by_id_79ee7170_fk_auth_user` FOREIGN KEY (`modified_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `YSE_App_transientpho_obs_group_id_f44df2ae_fk_YSE_App_o` FOREIGN KEY (`obs_group_id`) REFERENCES `YSE_App_observationgroup` (`id`),
  CONSTRAINT `YSE_App_transientpho_transient_id_9770bdf2_fk_YSE_App_t` FOREIGN KEY (`transient_id`) REFERENCES `YSE_App_transient` (`id`),
  CONSTRAINT `YSE_App_transientphotometry_host_id_58b364c2_fk_YSE_App_host_id` FOREIGN KEY (`host_id`) REFERENCES `YSE_App_host` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=267225 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `YSE_App_transientphotometry_groups`
--

DROP TABLE IF EXISTS `YSE_App_transientphotometry_groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `YSE_App_transientphotometry_groups` (
  `id` int NOT NULL AUTO_INCREMENT,
  `transientphotometry_id` int NOT NULL,
  `group_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `YSE_App_transientphotome_transientphotometry_id_g_0d4f2923_uniq` (`transientphotometry_id`,`group_id`),
  KEY `YSE_App_transientpho_group_id_c87c261d_fk_auth_grou` (`group_id`),
  CONSTRAINT `YSE_App_transientpho_group_id_c87c261d_fk_auth_grou` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`),
  CONSTRAINT `YSE_App_transientpho_transientphotometry__fa0e9f96_fk_YSE_App_t` FOREIGN KEY (`transientphotometry_id`) REFERENCES `YSE_App_transientphotometry` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=30690 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `YSE_App_transientspecdata`
--

DROP TABLE IF EXISTS `YSE_App_transientspecdata`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `YSE_App_transientspecdata` (
  `id` int NOT NULL AUTO_INCREMENT,
  `created_date` datetime(6) NOT NULL,
  `modified_date` datetime(6) NOT NULL,
  `wavelength` double NOT NULL,
  `flux` double NOT NULL,
  `wavelength_err` double DEFAULT NULL,
  `flux_err` double DEFAULT NULL,
  `created_by_id` int NOT NULL,
  `modified_by_id` int NOT NULL,
  `spectrum_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `YSE_App_transientspecdata_created_by_id_50b88791_fk_auth_user_id` (`created_by_id`),
  KEY `YSE_App_transientspe_modified_by_id_8f85bce2_fk_auth_user` (`modified_by_id`),
  KEY `YSE_App_transientspe_spectrum_id_57afac6c_fk_YSE_App_t` (`spectrum_id`),
  CONSTRAINT `YSE_App_transientspe_modified_by_id_8f85bce2_fk_auth_user` FOREIGN KEY (`modified_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `YSE_App_transientspe_spectrum_id_57afac6c_fk_YSE_App_t` FOREIGN KEY (`spectrum_id`) REFERENCES `YSE_App_transientspectrum` (`id`),
  CONSTRAINT `YSE_App_transientspecdata_created_by_id_50b88791_fk_auth_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=138252388 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `YSE_App_transientspectrum`
--

DROP TABLE IF EXISTS `YSE_App_transientspectrum`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `YSE_App_transientspectrum` (
  `id` int NOT NULL AUTO_INCREMENT,
  `created_date` datetime(6) NOT NULL,
  `modified_date` datetime(6) NOT NULL,
  `ra` double NOT NULL,
  `dec` double NOT NULL,
  `obs_date` datetime(6) NOT NULL,
  `redshift` double DEFAULT NULL,
  `redshift_err` double DEFAULT NULL,
  `redshift_quality` tinyint(1) DEFAULT NULL,
  `spec_plot_file` varchar(512) DEFAULT NULL,
  `spec_data_file` varchar(512) DEFAULT NULL,
  `spectrum_notes` longtext,
  `rlap` double DEFAULT NULL,
  `snid_plot_file` varchar(512) DEFAULT NULL,
  `created_by_id` int NOT NULL,
  `followup_id` int DEFAULT NULL,
  `instrument_id` int NOT NULL,
  `modified_by_id` int NOT NULL,
  `obs_group_id` int NOT NULL,
  `spec_phase` double DEFAULT NULL,
  `transient_id` int NOT NULL,
  `unit_id` int DEFAULT NULL,
  `data_quality_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `YSE_App_transientspectrum_created_by_id_9c3a247e_fk_auth_user_id` (`created_by_id`),
  KEY `YSE_App_transientspe_followup_id_3052a379_fk_YSE_App_t` (`followup_id`),
  KEY `YSE_App_transientspe_instrument_id_e484c746_fk_YSE_App_i` (`instrument_id`),
  KEY `YSE_App_transientspe_modified_by_id_3b605817_fk_auth_user` (`modified_by_id`),
  KEY `YSE_App_transientspe_obs_group_id_14bc781d_fk_YSE_App_o` (`obs_group_id`),
  KEY `YSE_App_transientspe_transient_id_3d4fe5ec_fk_YSE_App_t` (`transient_id`),
  KEY `YSE_App_transientspectrum_unit_id_dfdc44ef_fk_YSE_App_unit_id` (`unit_id`),
  KEY `YSE_App_transientspe_data_quality_id_dc019acc_fk_YSE_App_d` (`data_quality_id`),
  CONSTRAINT `YSE_App_transientspe_data_quality_id_dc019acc_fk_YSE_App_d` FOREIGN KEY (`data_quality_id`) REFERENCES `YSE_App_dataquality` (`id`),
  CONSTRAINT `YSE_App_transientspe_followup_id_3052a379_fk_YSE_App_t` FOREIGN KEY (`followup_id`) REFERENCES `YSE_App_transientfollowup` (`id`),
  CONSTRAINT `YSE_App_transientspe_instrument_id_e484c746_fk_YSE_App_i` FOREIGN KEY (`instrument_id`) REFERENCES `YSE_App_instrument` (`id`),
  CONSTRAINT `YSE_App_transientspe_modified_by_id_3b605817_fk_auth_user` FOREIGN KEY (`modified_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `YSE_App_transientspe_obs_group_id_14bc781d_fk_YSE_App_o` FOREIGN KEY (`obs_group_id`) REFERENCES `YSE_App_observationgroup` (`id`),
  CONSTRAINT `YSE_App_transientspe_transient_id_3d4fe5ec_fk_YSE_App_t` FOREIGN KEY (`transient_id`) REFERENCES `YSE_App_transient` (`id`),
  CONSTRAINT `YSE_App_transientspectrum_created_by_id_9c3a247e_fk_auth_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `YSE_App_transientspectrum_unit_id_dfdc44ef_fk_YSE_App_unit_id` FOREIGN KEY (`unit_id`) REFERENCES `YSE_App_unit` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=12639 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `YSE_App_transientspectrum_groups`
--

DROP TABLE IF EXISTS `YSE_App_transientspectrum_groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `YSE_App_transientspectrum_groups` (
  `id` int NOT NULL AUTO_INCREMENT,
  `transientspectrum_id` int NOT NULL,
  `group_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `YSE_App_transientspectru_transientspectrum_id_gro_c0c456d2_uniq` (`transientspectrum_id`,`group_id`),
  KEY `YSE_App_transientspe_group_id_7690a3d6_fk_auth_grou` (`group_id`),
  CONSTRAINT `YSE_App_transientspe_group_id_7690a3d6_fk_auth_grou` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`),
  CONSTRAINT `YSE_App_transientspe_transientspectrum_id_3f4247f2_fk_YSE_App_t` FOREIGN KEY (`transientspectrum_id`) REFERENCES `YSE_App_transientspectrum` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5309 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `YSE_App_transientstatus`
--

DROP TABLE IF EXISTS `YSE_App_transientstatus`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `YSE_App_transientstatus` (
  `id` int NOT NULL AUTO_INCREMENT,
  `created_date` datetime(6) NOT NULL,
  `modified_date` datetime(6) NOT NULL,
  `name` varchar(64) NOT NULL,
  `created_by_id` int NOT NULL,
  `modified_by_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `YSE_App_transientstatus_created_by_id_220821be_fk_auth_user_id` (`created_by_id`),
  KEY `YSE_App_transientstatus_modified_by_id_2b1e70d3_fk_auth_user_id` (`modified_by_id`),
  CONSTRAINT `YSE_App_transientstatus_created_by_id_220821be_fk_auth_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `YSE_App_transientstatus_modified_by_id_2b1e70d3_fk_auth_user_id` FOREIGN KEY (`modified_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `YSE_App_transienttag`
--

DROP TABLE IF EXISTS `YSE_App_transienttag`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `YSE_App_transienttag` (
  `id` int NOT NULL AUTO_INCREMENT,
  `created_date` datetime(6) NOT NULL,
  `modified_date` datetime(6) NOT NULL,
  `name` varchar(256) NOT NULL,
  `created_by_id` int NOT NULL,
  `modified_by_id` int NOT NULL,
  `color_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `YSE_App_transienttag_created_by_id_41af3fc7_fk_auth_user_id` (`created_by_id`),
  KEY `YSE_App_transienttag_modified_by_id_fedac1c5_fk_auth_user_id` (`modified_by_id`),
  KEY `YSE_App_transienttag_color_id_49e18ea2_fk_YSE_App_webappcolor_id` (`color_id`),
  CONSTRAINT `YSE_App_transienttag_color_id_49e18ea2_fk_YSE_App_webappcolor_id` FOREIGN KEY (`color_id`) REFERENCES `YSE_App_webappcolor` (`id`),
  CONSTRAINT `YSE_App_transienttag_created_by_id_41af3fc7_fk_auth_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `YSE_App_transienttag_modified_by_id_fedac1c5_fk_auth_user_id` FOREIGN KEY (`modified_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=97 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `YSE_App_transientwebresource`
--

DROP TABLE IF EXISTS `YSE_App_transientwebresource`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `YSE_App_transientwebresource` (
  `id` int NOT NULL AUTO_INCREMENT,
  `created_date` datetime(6) NOT NULL,
  `modified_date` datetime(6) NOT NULL,
  `information_text` longtext NOT NULL,
  `resource_url` varchar(512) NOT NULL,
  `created_by_id` int NOT NULL,
  `information_source_id` int NOT NULL,
  `modified_by_id` int NOT NULL,
  `transient_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `YSE_App_transientweb_created_by_id_9eb4dc98_fk_auth_user` (`created_by_id`),
  KEY `YSE_App_transientweb_information_source_i_5be7de18_fk_YSE_App_i` (`information_source_id`),
  KEY `YSE_App_transientweb_modified_by_id_408d8050_fk_auth_user` (`modified_by_id`),
  KEY `YSE_App_transientweb_transient_id_8492918a_fk_YSE_App_t` (`transient_id`),
  CONSTRAINT `YSE_App_transientweb_created_by_id_9eb4dc98_fk_auth_user` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `YSE_App_transientweb_information_source_i_5be7de18_fk_YSE_App_i` FOREIGN KEY (`information_source_id`) REFERENCES `YSE_App_informationsource` (`id`),
  CONSTRAINT `YSE_App_transientweb_modified_by_id_408d8050_fk_auth_user` FOREIGN KEY (`modified_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `YSE_App_transientweb_transient_id_8492918a_fk_YSE_App_t` FOREIGN KEY (`transient_id`) REFERENCES `YSE_App_transient` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `YSE_App_unit`
--

DROP TABLE IF EXISTS `YSE_App_unit`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `YSE_App_unit` (
  `id` int NOT NULL AUTO_INCREMENT,
  `created_date` datetime(6) NOT NULL,
  `modified_date` datetime(6) NOT NULL,
  `name` varchar(128) NOT NULL,
  `created_by_id` int NOT NULL,
  `modified_by_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `YSE_App_unit_created_by_id_3ac1de47_fk_auth_user_id` (`created_by_id`),
  KEY `YSE_App_unit_modified_by_id_adb1b747_fk_auth_user_id` (`modified_by_id`),
  CONSTRAINT `YSE_App_unit_created_by_id_3ac1de47_fk_auth_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `YSE_App_unit_modified_by_id_adb1b747_fk_auth_user_id` FOREIGN KEY (`modified_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `YSE_App_userquery`
--

DROP TABLE IF EXISTS `YSE_App_userquery`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `YSE_App_userquery` (
  `id` int NOT NULL AUTO_INCREMENT,
  `created_date` datetime(6) NOT NULL,
  `modified_date` datetime(6) NOT NULL,
  `created_by_id` int NOT NULL,
  `modified_by_id` int NOT NULL,
  `query_id` int DEFAULT NULL,
  `user_id` int NOT NULL,
  `python_query` varchar(64) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `YSE_App_userquery_created_by_id_01a9b691_fk_auth_user_id` (`created_by_id`),
  KEY `YSE_App_userquery_modified_by_id_2b2dac1c_fk_auth_user_id` (`modified_by_id`),
  KEY `YSE_App_userquery_user_id_dec9170e_fk_auth_user_id` (`user_id`),
  KEY `YSE_App_userquery_query_id_c91fced5_fk_explorer_query_id` (`query_id`),
  CONSTRAINT `YSE_App_userquery_created_by_id_01a9b691_fk_auth_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `YSE_App_userquery_modified_by_id_2b2dac1c_fk_auth_user_id` FOREIGN KEY (`modified_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `YSE_App_userquery_query_id_c91fced5_fk_explorer_query_id` FOREIGN KEY (`query_id`) REFERENCES `explorer_query` (`id`),
  CONSTRAINT `YSE_App_userquery_user_id_dec9170e_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=329 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `YSE_App_usertelescopetofollow`
--

DROP TABLE IF EXISTS `YSE_App_usertelescopetofollow`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `YSE_App_usertelescopetofollow` (
  `id` int NOT NULL AUTO_INCREMENT,
  `created_date` datetime(6) NOT NULL,
  `modified_date` datetime(6) NOT NULL,
  `created_by_id` int NOT NULL,
  `modified_by_id` int NOT NULL,
  `profile_id` int NOT NULL,
  `telescope_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `YSE_App_usertelescop_created_by_id_51d33069_fk_auth_user` (`created_by_id`),
  KEY `YSE_App_usertelescop_modified_by_id_712ea431_fk_auth_user` (`modified_by_id`),
  KEY `YSE_App_usertelescop_profile_id_fc802a72_fk_YSE_App_p` (`profile_id`),
  KEY `YSE_App_usertelescop_telescope_id_8b7471d3_fk_YSE_App_t` (`telescope_id`),
  CONSTRAINT `YSE_App_usertelescop_created_by_id_51d33069_fk_auth_user` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `YSE_App_usertelescop_modified_by_id_712ea431_fk_auth_user` FOREIGN KEY (`modified_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `YSE_App_usertelescop_profile_id_fc802a72_fk_YSE_App_p` FOREIGN KEY (`profile_id`) REFERENCES `YSE_App_profile` (`id`),
  CONSTRAINT `YSE_App_usertelescop_telescope_id_8b7471d3_fk_YSE_App_t` FOREIGN KEY (`telescope_id`) REFERENCES `YSE_App_telescope` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `YSE_App_webappcolor`
--

DROP TABLE IF EXISTS `YSE_App_webappcolor`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `YSE_App_webappcolor` (
  `id` int NOT NULL AUTO_INCREMENT,
  `created_date` datetime(6) NOT NULL,
  `modified_date` datetime(6) NOT NULL,
  `color` varchar(64) NOT NULL,
  `created_by_id` int NOT NULL,
  `modified_by_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `YSE_App_webappcolor_created_by_id_30a26673_fk_auth_user_id` (`created_by_id`),
  KEY `YSE_App_webappcolor_modified_by_id_503e0fb6_fk_auth_user_id` (`modified_by_id`),
  CONSTRAINT `YSE_App_webappcolor_created_by_id_30a26673_fk_auth_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `YSE_App_webappcolor_modified_by_id_503e0fb6_fk_auth_user_id` FOREIGN KEY (`modified_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=14 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `YSE_App_yseoncalldate`
--

DROP TABLE IF EXISTS `YSE_App_yseoncalldate`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `YSE_App_yseoncalldate` (
  `id` int NOT NULL AUTO_INCREMENT,
  `created_date` datetime(6) NOT NULL,
  `modified_date` datetime(6) NOT NULL,
  `on_call_date` datetime(6) NOT NULL,
  `created_by_id` int NOT NULL,
  `modified_by_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `YSE_App_yseoncalldate_created_by_id_0f0b8842_fk_auth_user_id` (`created_by_id`),
  KEY `YSE_App_yseoncalldate_modified_by_id_9c33d0c5_fk_auth_user_id` (`modified_by_id`),
  CONSTRAINT `YSE_App_yseoncalldate_created_by_id_0f0b8842_fk_auth_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `YSE_App_yseoncalldate_modified_by_id_9c33d0c5_fk_auth_user_id` FOREIGN KEY (`modified_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=161 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `YSE_App_yseoncalldate_user`
--

DROP TABLE IF EXISTS `YSE_App_yseoncalldate_user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `YSE_App_yseoncalldate_user` (
  `id` int NOT NULL AUTO_INCREMENT,
  `yseoncalldate_id` int NOT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `YSE_App_yseoncalldate_us_yseoncalldate_id_user_id_d133e492_uniq` (`yseoncalldate_id`,`user_id`),
  KEY `YSE_App_yseoncalldate_user_user_id_ac65eec4_fk_auth_user_id` (`user_id`),
  CONSTRAINT `YSE_App_yseoncalldat_yseoncalldate_id_5274b751_fk_YSE_App_y` FOREIGN KEY (`yseoncalldate_id`) REFERENCES `YSE_App_yseoncalldate` (`id`),
  CONSTRAINT `YSE_App_yseoncalldate_user_user_id_ac65eec4_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=174 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `auditlog_logentry`
--

DROP TABLE IF EXISTS `auditlog_logentry`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `auditlog_logentry` (
  `id` int NOT NULL AUTO_INCREMENT,
  `object_pk` varchar(255) NOT NULL,
  `object_id` bigint DEFAULT NULL,
  `object_repr` longtext NOT NULL,
  `action` smallint unsigned NOT NULL,
  `changes` longtext NOT NULL,
  `timestamp` datetime(6) NOT NULL,
  `actor_id` int DEFAULT NULL,
  `content_type_id` int NOT NULL,
  `remote_addr` char(39) DEFAULT NULL,
  `additional_data` longtext,
  PRIMARY KEY (`id`),
  KEY `auditlog_logentry_actor_id_959271d2_fk_auth_user_id` (`actor_id`),
  KEY `auditlog_logentry_content_type_id_75830218_fk_django_co` (`content_type_id`),
  KEY `auditlog_logentry_object_id_09c2eee8` (`object_id`),
  KEY `auditlog_logentry_object_pk_6e3219c0` (`object_pk`),
  CONSTRAINT `auditlog_logentry_actor_id_959271d2_fk_auth_user_id` FOREIGN KEY (`actor_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `auditlog_logentry_content_type_id_75830218_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=61477 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `auth_group`
--

DROP TABLE IF EXISTS `auth_group`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `auth_group` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(150) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=14 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `auth_group_permissions`
--

DROP TABLE IF EXISTS `auth_group_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `auth_group_permissions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `group_id` int NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_group_permissions_group_id_permission_id_0cd325b0_uniq` (`group_id`,`permission_id`),
  KEY `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_group_permissions_group_id_b120cbf9_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `auth_permission`
--

DROP TABLE IF EXISTS `auth_permission`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `auth_permission` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `content_type_id` int NOT NULL,
  `codename` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id`,`codename`),
  CONSTRAINT `auth_permission_content_type_id_2f476e4b_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=305 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `auth_user`
--

DROP TABLE IF EXISTS `auth_user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `auth_user` (
  `id` int NOT NULL AUTO_INCREMENT,
  `password` varchar(128) NOT NULL,
  `last_login` datetime(6) DEFAULT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `username` varchar(150) NOT NULL,
  `first_name` varchar(150) NOT NULL,
  `last_name` varchar(150) NOT NULL,
  `email` varchar(254) NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `date_joined` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=189 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `auth_user_groups`
--

DROP TABLE IF EXISTS `auth_user_groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `auth_user_groups` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `group_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_user_groups_user_id_group_id_94350c0c_uniq` (`user_id`,`group_id`),
  KEY `auth_user_groups_group_id_97559544_fk_auth_group_id` (`group_id`),
  CONSTRAINT `auth_user_groups_group_id_97559544_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`),
  CONSTRAINT `auth_user_groups_user_id_6a12ed8b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=607 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `auth_user_user_permissions`
--

DROP TABLE IF EXISTS `auth_user_user_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `auth_user_user_permissions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_user_user_permissions_user_id_permission_id_14a6b632_uniq` (`user_id`,`permission_id`),
  KEY `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_user_user_permissions_user_id_a95ead1b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=217 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `authtoken_token`
--

DROP TABLE IF EXISTS `authtoken_token`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `authtoken_token` (
  `key` varchar(40) NOT NULL,
  `created` datetime(6) NOT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`key`),
  UNIQUE KEY `user_id` (`user_id`),
  CONSTRAINT `authtoken_token_user_id_35299eff_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `django_admin_log`
--

DROP TABLE IF EXISTS `django_admin_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `django_admin_log` (
  `id` int NOT NULL AUTO_INCREMENT,
  `action_time` datetime(6) NOT NULL,
  `object_id` longtext,
  `object_repr` varchar(200) NOT NULL,
  `action_flag` smallint unsigned NOT NULL,
  `change_message` longtext NOT NULL,
  `content_type_id` int DEFAULT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `django_admin_log_content_type_id_c4bce8eb_fk_django_co` (`content_type_id`),
  KEY `django_admin_log_user_id_c564eba6_fk_auth_user_id` (`user_id`),
  CONSTRAINT `django_admin_log_content_type_id_c4bce8eb_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `django_admin_log_user_id_c564eba6_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=8129 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `django_content_type`
--

DROP TABLE IF EXISTS `django_content_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `django_content_type` (
  `id` int NOT NULL AUTO_INCREMENT,
  `app_label` varchar(100) NOT NULL,
  `model` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `django_content_type_app_label_model_76bd3d3b_uniq` (`app_label`,`model`)
) ENGINE=InnoDB AUTO_INCREMENT=78 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `django_cron_cronjoblog`
--

DROP TABLE IF EXISTS `django_cron_cronjoblog`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `django_cron_cronjoblog` (
  `id` int NOT NULL AUTO_INCREMENT,
  `code` varchar(64) NOT NULL,
  `start_time` datetime(6) NOT NULL,
  `end_time` datetime(6) NOT NULL,
  `is_success` tinyint(1) NOT NULL,
  `message` longtext NOT NULL,
  `ran_at_time` time(6) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `django_cron_cronjoblog_code_start_time_ran_at_time_8b50b8fa_idx` (`code`,`start_time`,`ran_at_time`),
  KEY `django_cron_cronjoblog_code_start_time_4fc78f9d_idx` (`code`,`start_time`),
  KEY `django_cron_cronjoblog_code_is_success_ran_at_time_84da9606_idx` (`code`,`is_success`,`ran_at_time`),
  KEY `django_cron_cronjoblog_code_48865653` (`code`),
  KEY `django_cron_cronjoblog_start_time_d68c0dd9` (`start_time`),
  KEY `django_cron_cronjoblog_end_time_7918602a` (`end_time`),
  KEY `django_cron_cronjoblog_ran_at_time_7fed2751` (`ran_at_time`)
) ENGINE=InnoDB AUTO_INCREMENT=511725 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `django_migrations`
--

DROP TABLE IF EXISTS `django_migrations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `django_migrations` (
  `id` int NOT NULL AUTO_INCREMENT,
  `app` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `applied` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=121 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `django_session`
--

DROP TABLE IF EXISTS `django_session`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `django_session` (
  `session_key` varchar(40) NOT NULL,
  `session_data` longtext NOT NULL,
  `expire_date` datetime(6) NOT NULL,
  PRIMARY KEY (`session_key`),
  KEY `django_session_expire_date_a5c62663` (`expire_date`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `explorer_query`
--

DROP TABLE IF EXISTS `explorer_query`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `explorer_query` (
  `id` int NOT NULL AUTO_INCREMENT,
  `title` varchar(255) NOT NULL,
  `sql` longtext NOT NULL,
  `description` longtext,
  `created_at` datetime(6) NOT NULL,
  `last_run_date` datetime(6) NOT NULL,
  `created_by_user_id` int DEFAULT NULL,
  `snapshot` tinyint(1) NOT NULL,
  `connection` varchar(128) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `explorer_query_created_by_user_id_182dd868_fk_auth_user_id` (`created_by_user_id`),
  CONSTRAINT `explorer_query_created_by_user_id_182dd868_fk_auth_user_id` FOREIGN KEY (`created_by_user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=335 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `explorer_querylog`
--

DROP TABLE IF EXISTS `explorer_querylog`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `explorer_querylog` (
  `id` int NOT NULL AUTO_INCREMENT,
  `sql` longtext,
  `run_at` datetime(6) NOT NULL,
  `query_id` int DEFAULT NULL,
  `run_by_user_id` int DEFAULT NULL,
  `duration` double DEFAULT NULL,
  `connection` varchar(128) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `explorer_querylog_query_id_1635a6b4_fk_explorer_query_id` (`query_id`),
  KEY `explorer_querylog_run_by_user_id_cf26a49f_fk_auth_user_id` (`run_by_user_id`),
  CONSTRAINT `explorer_querylog_query_id_1635a6b4_fk_explorer_query_id` FOREIGN KEY (`query_id`) REFERENCES `explorer_query` (`id`),
  CONSTRAINT `explorer_querylog_run_by_user_id_cf26a49f_fk_auth_user_id` FOREIGN KEY (`run_by_user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=13970 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `silk_profile`
--

DROP TABLE IF EXISTS `silk_profile`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `silk_profile` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(300) NOT NULL,
  `start_time` datetime(6) NOT NULL,
  `end_time` datetime(6) DEFAULT NULL,
  `time_taken` double DEFAULT NULL,
  `file_path` varchar(300) NOT NULL,
  `line_num` int DEFAULT NULL,
  `end_line_num` int DEFAULT NULL,
  `func_name` varchar(300) NOT NULL,
  `exception_raised` tinyint(1) NOT NULL,
  `dynamic` tinyint(1) NOT NULL,
  `request_id` varchar(36) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `silk_profile_request_id_7b81bd69_fk_silk_request_id` (`request_id`),
  CONSTRAINT `silk_profile_request_id_7b81bd69_fk_silk_request_id` FOREIGN KEY (`request_id`) REFERENCES `silk_request` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `silk_profile_queries`
--

DROP TABLE IF EXISTS `silk_profile_queries`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `silk_profile_queries` (
  `id` int NOT NULL AUTO_INCREMENT,
  `profile_id` int NOT NULL,
  `sqlquery_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `silk_profile_queries_profile_id_sqlquery_id_b2403d9b_uniq` (`profile_id`,`sqlquery_id`),
  KEY `silk_profile_queries_sqlquery_id_155df455_fk_silk_sqlquery_id` (`sqlquery_id`),
  CONSTRAINT `silk_profile_queries_profile_id_a3d76db8_fk_silk_profile_id` FOREIGN KEY (`profile_id`) REFERENCES `silk_profile` (`id`),
  CONSTRAINT `silk_profile_queries_sqlquery_id_155df455_fk_silk_sqlquery_id` FOREIGN KEY (`sqlquery_id`) REFERENCES `silk_sqlquery` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `silk_request`
--

DROP TABLE IF EXISTS `silk_request`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `silk_request` (
  `id` varchar(36) NOT NULL,
  `path` varchar(190) NOT NULL,
  `query_params` longtext NOT NULL,
  `raw_body` longtext NOT NULL,
  `body` longtext NOT NULL,
  `method` varchar(10) NOT NULL,
  `start_time` datetime(6) NOT NULL,
  `view_name` varchar(190) DEFAULT NULL,
  `end_time` datetime(6) DEFAULT NULL,
  `time_taken` double DEFAULT NULL,
  `encoded_headers` longtext NOT NULL,
  `meta_time` double DEFAULT NULL,
  `meta_num_queries` int DEFAULT NULL,
  `meta_time_spent_queries` double DEFAULT NULL,
  `pyprofile` longtext NOT NULL,
  `num_sql_queries` int NOT NULL,
  `prof_file` varchar(300) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `silk_request_path_9f3d798e` (`path`),
  KEY `silk_request_start_time_1300bc58` (`start_time`),
  KEY `silk_request_view_name_68559f7b` (`view_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `silk_response`
--

DROP TABLE IF EXISTS `silk_response`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `silk_response` (
  `id` varchar(36) NOT NULL,
  `status_code` int NOT NULL,
  `raw_body` longtext NOT NULL,
  `body` longtext NOT NULL,
  `encoded_headers` longtext NOT NULL,
  `request_id` varchar(36) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `request_id` (`request_id`),
  CONSTRAINT `silk_response_request_id_1e8e2776_fk_silk_request_id` FOREIGN KEY (`request_id`) REFERENCES `silk_request` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `silk_sqlquery`
--

DROP TABLE IF EXISTS `silk_sqlquery`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
 SET character_set_client = utf8mb4 ;
CREATE TABLE `silk_sqlquery` (
  `id` int NOT NULL AUTO_INCREMENT,
  `query` longtext NOT NULL,
  `start_time` datetime(6) DEFAULT NULL,
  `end_time` datetime(6) DEFAULT NULL,
  `time_taken` double DEFAULT NULL,
  `traceback` longtext NOT NULL,
  `request_id` varchar(36) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `silk_sqlquery_request_id_6f8f0527_fk_silk_request_id` (`request_id`),
  CONSTRAINT `silk_sqlquery_request_id_6f8f0527_fk_silk_request_id` FOREIGN KEY (`request_id`) REFERENCES `silk_request` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=25292 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2022-04-04 15:42:10
