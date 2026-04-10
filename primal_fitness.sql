mysqldump: [Warning] Using a password on the command line interface can be insecure.
-- MySQL dump 10.13  Distrib 8.0.43, for Win64 (x86_64)
--
-- Host: localhost    Database: primal_fitness
-- ------------------------------------------------------
-- Server version	8.0.43

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `admins`
--

DROP TABLE IF EXISTS `admins`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `admins` (
  `admin_id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `last_updated` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`admin_id`),
  UNIQUE KEY `user_id` (`user_id`),
  CONSTRAINT `fk_admins_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `admins`
--

LOCK TABLES `admins` WRITE;
/*!40000 ALTER TABLE `admins` DISABLE KEYS */;
INSERT INTO `admins` VALUES (1,14,'2024-01-01 13:05:00','2024-01-01 13:05:00'),(2,15,'2024-01-02 13:05:00','2024-01-02 13:05:00');
/*!40000 ALTER TABLE `admins` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_admins_audit_insert` AFTER INSERT ON `admins` FOR EACH ROW BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, new_values)
    VALUES ('Admins', NEW.admin_id, 'INSERT', @current_user_id,
        JSON_OBJECT('user_id', NEW.user_id));
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_admins_last_updated` BEFORE UPDATE ON `admins` FOR EACH ROW SET NEW.last_updated = NOW() */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_admins_audit_delete` AFTER DELETE ON `admins` FOR EACH ROW BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, old_values)
    VALUES ('Admins', OLD.admin_id, 'DELETE', @current_user_id,
        JSON_OBJECT('user_id', OLD.user_id));
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `audit_log`
--

DROP TABLE IF EXISTS `audit_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `audit_log` (
  `audit_id` int NOT NULL AUTO_INCREMENT,
  `table_name` varchar(64) NOT NULL,
  `record_id` int NOT NULL,
  `action` enum('INSERT','UPDATE','DELETE') NOT NULL,
  `changed_by` int DEFAULT NULL,
  `old_values` json DEFAULT NULL,
  `new_values` json DEFAULT NULL,
  `changed_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`audit_id`),
  KEY `fk_audit_log_user` (`changed_by`),
  KEY `idx_audit_table_record` (`table_name`,`record_id`),
  KEY `idx_audit_changed_at` (`changed_at`),
  CONSTRAINT `fk_audit_log_user` FOREIGN KEY (`changed_by`) REFERENCES `users` (`user_id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=262 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `audit_log`
--

LOCK TABLES `audit_log` WRITE;
/*!40000 ALTER TABLE `audit_log` DISABLE KEYS */;
INSERT INTO `audit_log` VALUES (1,'Users',1,'INSERT',NULL,NULL,'{\"role\": \"client\", \"email\": \"alice.johnson@email.com\", \"auth0_sub\": \"auth0|user001\"}','2026-03-05 04:18:36'),(2,'Users',2,'INSERT',NULL,NULL,'{\"role\": \"client\", \"email\": \"bob.smith@email.com\", \"auth0_sub\": \"auth0|user002\"}','2026-03-05 04:18:36'),(3,'Users',3,'INSERT',NULL,NULL,'{\"role\": \"client\", \"email\": \"carol.white@email.com\", \"auth0_sub\": \"auth0|user003\"}','2026-03-05 04:18:36'),(4,'Users',4,'INSERT',NULL,NULL,'{\"role\": \"client\", \"email\": \"david.brown@email.com\", \"auth0_sub\": \"auth0|user004\"}','2026-03-05 04:18:36'),(5,'Users',5,'INSERT',NULL,NULL,'{\"role\": \"client\", \"email\": \"eva.martinez@email.com\", \"auth0_sub\": \"auth0|user005\"}','2026-03-05 04:18:36'),(6,'Users',6,'INSERT',NULL,NULL,'{\"role\": \"client\", \"email\": \"frank.lee@email.com\", \"auth0_sub\": \"auth0|user006\"}','2026-03-05 04:18:36'),(7,'Users',7,'INSERT',NULL,NULL,'{\"role\": \"client\", \"email\": \"grace.kim@email.com\", \"auth0_sub\": \"auth0|user007\"}','2026-03-05 04:18:36'),(8,'Users',8,'INSERT',NULL,NULL,'{\"role\": \"client\", \"email\": \"henry.nguyen@email.com\", \"auth0_sub\": \"auth0|user008\"}','2026-03-05 04:18:36'),(9,'Users',9,'INSERT',NULL,NULL,'{\"role\": \"client\", \"email\": \"isabella.clark@email.com\", \"auth0_sub\": \"auth0|user009\"}','2026-03-05 04:18:36'),(10,'Users',10,'INSERT',NULL,NULL,'{\"role\": \"client\", \"email\": \"james.wilson@email.com\", \"auth0_sub\": \"auth0|user010\"}','2026-03-05 04:18:36'),(11,'Users',11,'INSERT',NULL,NULL,'{\"role\": \"coach\", \"email\": \"karen.taylor@email.com\", \"auth0_sub\": \"auth0|user011\"}','2026-03-05 04:18:36'),(12,'Users',12,'INSERT',NULL,NULL,'{\"role\": \"coach\", \"email\": \"liam.anderson@email.com\", \"auth0_sub\": \"auth0|user012\"}','2026-03-05 04:18:36'),(13,'Users',13,'INSERT',NULL,NULL,'{\"role\": \"coach\", \"email\": \"mia.thompson@email.com\", \"auth0_sub\": \"auth0|user013\"}','2026-03-05 04:18:36'),(14,'Users',14,'INSERT',NULL,NULL,'{\"role\": \"admin\", \"email\": \"noah.harris@email.com\", \"auth0_sub\": \"auth0|user014\"}','2026-03-05 04:18:36'),(15,'Users',15,'INSERT',NULL,NULL,'{\"role\": \"admin\", \"email\": \"olivia.martin@email.com\", \"auth0_sub\": \"auth0|user015\"}','2026-03-05 04:18:36'),(16,'Users',16,'INSERT',NULL,NULL,'{\"role\": \"coach\", \"email\": \"derek.ross@email.com\", \"auth0_sub\": \"auth0|user016\"}','2026-03-05 04:18:36'),(17,'Clients',1,'INSERT',NULL,NULL,'{\"DOB\": \"1995-03-12\", \"user_id\": 1}','2026-03-05 04:18:36'),(18,'Clients',2,'INSERT',NULL,NULL,'{\"DOB\": \"1988-07-25\", \"user_id\": 2}','2026-03-05 04:18:36'),(19,'Clients',3,'INSERT',NULL,NULL,'{\"DOB\": \"2000-11-03\", \"user_id\": 3}','2026-03-05 04:18:36'),(20,'Clients',4,'INSERT',NULL,NULL,'{\"DOB\": \"1992-04-18\", \"user_id\": 4}','2026-03-05 04:18:36'),(21,'Clients',5,'INSERT',NULL,NULL,'{\"DOB\": \"1997-09-30\", \"user_id\": 5}','2026-03-05 04:18:36'),(22,'Clients',6,'INSERT',NULL,NULL,'{\"DOB\": \"1985-12-07\", \"user_id\": 6}','2026-03-05 04:18:36'),(23,'Clients',7,'INSERT',NULL,NULL,'{\"DOB\": \"2001-06-14\", \"user_id\": 7}','2026-03-05 04:18:36'),(24,'Clients',8,'INSERT',NULL,NULL,'{\"DOB\": \"1990-02-22\", \"user_id\": 8}','2026-03-05 04:18:36'),(25,'Clients',9,'INSERT',NULL,NULL,'{\"DOB\": \"1998-08-11\", \"user_id\": 9}','2026-03-05 04:18:36'),(26,'Clients',10,'INSERT',NULL,NULL,'{\"DOB\": \"1993-01-29\", \"user_id\": 10}','2026-03-05 04:18:36'),(27,'Coaches',1,'INSERT',NULL,NULL,'{\"user_id\": 11, \"status_id\": 2, \"is_trainer\": 1, \"hourly_rate\": 75.00, \"max_clients\": 20, \"is_nutritionist\": 0, \"years_of_experience\": 8}','2026-03-05 04:18:36'),(28,'Coaches',2,'INSERT',NULL,NULL,'{\"user_id\": 12, \"status_id\": 2, \"is_trainer\": 1, \"hourly_rate\": 90.00, \"max_clients\": 15, \"is_nutritionist\": 1, \"years_of_experience\": 12}','2026-03-05 04:18:36'),(29,'Coaches',3,'INSERT',NULL,NULL,'{\"user_id\": 13, \"status_id\": 2, \"is_trainer\": 0, \"hourly_rate\": 65.00, \"max_clients\": 25, \"is_nutritionist\": 1, \"years_of_experience\": 5}','2026-03-05 04:18:36'),(30,'Coaches',4,'INSERT',NULL,NULL,'{\"user_id\": 16, \"status_id\": 3, \"is_trainer\": 1, \"hourly_rate\": 70.00, \"max_clients\": 20, \"is_nutritionist\": 0, \"years_of_experience\": 6}','2026-03-05 04:18:36'),(31,'Admins',1,'INSERT',NULL,NULL,'{\"user_id\": 14}','2026-03-05 04:18:36'),(32,'Admins',2,'INSERT',NULL,NULL,'{\"user_id\": 15}','2026-03-05 04:18:36'),(33,'Coach_Availability',1,'INSERT',NULL,NULL,'{\"coach_id\": 1, \"end_time\": \"12:00:00.000000\", \"start_time\": \"07:00:00.000000\", \"day_of_week\": \"MON\"}','2026-03-05 04:18:36'),(34,'Coach_Availability',2,'INSERT',NULL,NULL,'{\"coach_id\": 1, \"end_time\": \"12:00:00.000000\", \"start_time\": \"07:00:00.000000\", \"day_of_week\": \"WED\"}','2026-03-05 04:18:36'),(35,'Coach_Availability',3,'INSERT',NULL,NULL,'{\"coach_id\": 1, \"end_time\": \"12:00:00.000000\", \"start_time\": \"07:00:00.000000\", \"day_of_week\": \"FRI\"}','2026-03-05 04:18:36'),(36,'Coach_Availability',4,'INSERT',NULL,NULL,'{\"coach_id\": 1, \"end_time\": \"14:00:00.000000\", \"start_time\": \"09:00:00.000000\", \"day_of_week\": \"SAT\"}','2026-03-05 04:18:36'),(37,'Coach_Availability',5,'INSERT',NULL,NULL,'{\"coach_id\": 2, \"end_time\": \"14:00:00.000000\", \"start_time\": \"06:00:00.000000\", \"day_of_week\": \"MON\"}','2026-03-05 04:18:36'),(38,'Coach_Availability',6,'INSERT',NULL,NULL,'{\"coach_id\": 2, \"end_time\": \"14:00:00.000000\", \"start_time\": \"06:00:00.000000\", \"day_of_week\": \"TUE\"}','2026-03-05 04:18:36'),(39,'Coach_Availability',7,'INSERT',NULL,NULL,'{\"coach_id\": 2, \"end_time\": \"14:00:00.000000\", \"start_time\": \"06:00:00.000000\", \"day_of_week\": \"THU\"}','2026-03-05 04:18:36'),(40,'Coach_Availability',8,'INSERT',NULL,NULL,'{\"coach_id\": 3, \"end_time\": \"18:00:00.000000\", \"start_time\": \"10:00:00.000000\", \"day_of_week\": \"TUE\"}','2026-03-05 04:18:36'),(41,'Coach_Availability',9,'INSERT',NULL,NULL,'{\"coach_id\": 3, \"end_time\": \"18:00:00.000000\", \"start_time\": \"10:00:00.000000\", \"day_of_week\": \"WED\"}','2026-03-05 04:18:36'),(42,'Coach_Availability',10,'INSERT',NULL,NULL,'{\"coach_id\": 3, \"end_time\": \"16:00:00.000000\", \"start_time\": \"08:00:00.000000\", \"day_of_week\": \"SAT\"}','2026-03-05 04:18:36'),(43,'Goals',1,'INSERT',NULL,NULL,'{\"user_id\": 1, \"goal_type_id\": 1}','2026-03-05 04:18:36'),(44,'Goals',2,'INSERT',NULL,NULL,'{\"user_id\": 2, \"goal_type_id\": 2}','2026-03-05 04:18:36'),(45,'Goals',3,'INSERT',NULL,NULL,'{\"user_id\": 3, \"goal_type_id\": 4}','2026-03-05 04:18:36'),(46,'Goals',4,'INSERT',NULL,NULL,'{\"user_id\": 4, \"goal_type_id\": 2}','2026-03-05 04:18:36'),(47,'Goals',5,'INSERT',NULL,NULL,'{\"user_id\": 5, \"goal_type_id\": 1}','2026-03-05 04:18:36'),(48,'Goals',6,'INSERT',NULL,NULL,'{\"user_id\": 6, \"goal_type_id\": 3}','2026-03-05 04:18:36'),(49,'Goals',7,'INSERT',NULL,NULL,'{\"user_id\": 7, \"goal_type_id\": 4}','2026-03-05 04:18:36'),(50,'Goals',8,'INSERT',NULL,NULL,'{\"user_id\": 8, \"goal_type_id\": 2}','2026-03-05 04:18:36'),(51,'Goals',9,'INSERT',NULL,NULL,'{\"user_id\": 9, \"goal_type_id\": 1}','2026-03-05 04:18:36'),(52,'Goals',10,'INSERT',NULL,NULL,'{\"user_id\": 10, \"goal_type_id\": 3}','2026-03-05 04:18:36'),(53,'Exercises',1,'INSERT',NULL,NULL,'{\"name\": \"Barbell Back Squat\", \"category_id\": 1, \"experience_level_id\": 2}','2026-03-05 04:18:36'),(54,'Exercises',2,'INSERT',NULL,NULL,'{\"name\": \"Bench Press\", \"category_id\": 1, \"experience_level_id\": 2}','2026-03-05 04:18:36'),(55,'Exercises',3,'INSERT',NULL,NULL,'{\"name\": \"Deadlift\", \"category_id\": 1, \"experience_level_id\": 3}','2026-03-05 04:18:36'),(56,'Exercises',4,'INSERT',NULL,NULL,'{\"name\": \"Pull-Up\", \"category_id\": 1, \"experience_level_id\": 2}','2026-03-05 04:18:36'),(57,'Exercises',5,'INSERT',NULL,NULL,'{\"name\": \"Push-Up\", \"category_id\": 1, \"experience_level_id\": 1}','2026-03-05 04:18:36'),(58,'Exercises',6,'INSERT',NULL,NULL,'{\"name\": \"Running\", \"category_id\": 2, \"experience_level_id\": 1}','2026-03-05 04:18:36'),(59,'Exercises',7,'INSERT',NULL,NULL,'{\"name\": \"Cycling\", \"category_id\": 2, \"experience_level_id\": 1}','2026-03-05 04:18:36'),(60,'Exercises',8,'INSERT',NULL,NULL,'{\"name\": \"Jump Rope\", \"category_id\": 2, \"experience_level_id\": 2}','2026-03-05 04:18:36'),(61,'Exercises',9,'INSERT',NULL,NULL,'{\"name\": \"Downward Dog\", \"category_id\": 3, \"experience_level_id\": 1}','2026-03-05 04:18:36'),(62,'Exercises',10,'INSERT',NULL,NULL,'{\"name\": \"Hip Flexor Stretch\", \"category_id\": 3, \"experience_level_id\": 1}','2026-03-05 04:18:36'),(63,'Workouts',1,'INSERT',NULL,NULL,'{\"name\": \"Beginner Fat Burn\", \"status\": \"Scheduled\", \"image_url\": null, \"creator_id\": 11, \"goal_type_id\": 1, \"workout_time_mins\": 30, \"equipment_required\": \"None\", \"experience_level_id\": 1, \"intended_duration_weeks\": 8}','2026-03-05 04:18:37'),(64,'Workouts',2,'INSERT',NULL,NULL,'{\"name\": \"Strength Foundation\", \"status\": \"Scheduled\", \"image_url\": null, \"creator_id\": 11, \"goal_type_id\": 2, \"workout_time_mins\": 60, \"equipment_required\": \"Barbell, Rack\", \"experience_level_id\": 2, \"intended_duration_weeks\": 12}','2026-03-05 04:18:37'),(65,'Workouts',3,'INSERT',NULL,NULL,'{\"name\": \"Endurance Builder\", \"status\": \"Scheduled\", \"image_url\": null, \"creator_id\": 12, \"goal_type_id\": 3, \"workout_time_mins\": 45, \"equipment_required\": \"None\", \"experience_level_id\": 1, \"intended_duration_weeks\": 6}','2026-03-05 04:18:37'),(66,'Workouts',4,'INSERT',NULL,NULL,'{\"name\": \"Muscle Hypertrophy\", \"status\": \"Scheduled\", \"image_url\": null, \"creator_id\": 12, \"goal_type_id\": 2, \"workout_time_mins\": 75, \"equipment_required\": \"Barbell, Dumbbells\", \"experience_level_id\": 3, \"intended_duration_weeks\": 16}','2026-03-05 04:18:37'),(67,'Workouts',5,'INSERT',NULL,NULL,'{\"name\": \"Flexibility & Wellness\", \"status\": \"Scheduled\", \"image_url\": null, \"creator_id\": 13, \"goal_type_id\": 4, \"workout_time_mins\": 40, \"equipment_required\": \"Yoga Mat\", \"experience_level_id\": 1, \"intended_duration_weeks\": 4}','2026-03-05 04:18:37'),(68,'Workouts',6,'INSERT',NULL,NULL,'{\"name\": \"Cardio Conditioning\", \"status\": \"Scheduled\", \"image_url\": null, \"creator_id\": 13, \"goal_type_id\": 3, \"workout_time_mins\": 50, \"equipment_required\": \"Jump Rope\", \"experience_level_id\": 2, \"intended_duration_weeks\": 8}','2026-03-05 04:18:37'),(69,'Workouts',7,'INSERT',NULL,NULL,'{\"name\": \"Core & Stability\", \"status\": \"Not Scheduled\", \"image_url\": null, \"creator_id\": 11, \"goal_type_id\": 4, \"workout_time_mins\": 25, \"equipment_required\": \"None\", \"experience_level_id\": 1, \"intended_duration_weeks\": 6}','2026-03-05 04:18:37'),(70,'Workouts',8,'INSERT',NULL,NULL,'{\"name\": \"Power & Explosiveness\", \"status\": \"Scheduled\", \"image_url\": null, \"creator_id\": 12, \"goal_type_id\": 2, \"workout_time_mins\": 70, \"equipment_required\": \"Barbell, Bumper Plates\", \"experience_level_id\": 3, \"intended_duration_weeks\": 12}','2026-03-05 04:18:37'),(71,'Workouts',9,'INSERT',NULL,NULL,'{\"name\": \"Nutrition & Mobility\", \"status\": \"Scheduled\", \"image_url\": null, \"creator_id\": 13, \"goal_type_id\": 1, \"workout_time_mins\": 35, \"equipment_required\": \"Yoga Mat\", \"experience_level_id\": 1, \"intended_duration_weeks\": 8}','2026-03-05 04:18:37'),(72,'Workouts',10,'INSERT',NULL,NULL,'{\"name\": \"Full Body HIIT\", \"status\": \"Scheduled\", \"image_url\": null, \"creator_id\": 11, \"goal_type_id\": 3, \"workout_time_mins\": 40, \"equipment_required\": \"None\", \"experience_level_id\": 2, \"intended_duration_weeks\": 6}','2026-03-05 04:18:37'),(73,'Workout_Logs',1,'INSERT',NULL,NULL,'{\"client_id\": 1, \"logged_at\": \"2025-02-08 08:00:00.000000\", \"workout_id\": 1}','2026-03-05 04:18:37'),(74,'Workout_Logs',2,'INSERT',NULL,NULL,'{\"client_id\": 1, \"logged_at\": \"2025-02-15 08:00:00.000000\", \"workout_id\": 1}','2026-03-05 04:18:37'),(75,'Workout_Logs',3,'INSERT',NULL,NULL,'{\"client_id\": 2, \"logged_at\": \"2025-02-12 10:00:00.000000\", \"workout_id\": 2}','2026-03-05 04:18:37'),(76,'Workout_Logs',4,'INSERT',NULL,NULL,'{\"client_id\": 3, \"logged_at\": \"2025-02-17 11:00:00.000000\", \"workout_id\": 3}','2026-03-05 04:18:37'),(77,'Workout_Logs',5,'INSERT',NULL,NULL,'{\"client_id\": 4, \"logged_at\": \"2025-02-20 12:00:00.000000\", \"workout_id\": 4}','2026-03-05 04:18:37'),(78,'Workout_Logs',6,'INSERT',NULL,NULL,'{\"client_id\": 5, \"logged_at\": \"2025-03-05 08:00:00.000000\", \"workout_id\": 5}','2026-03-05 04:18:37'),(79,'Workout_Logs',7,'INSERT',NULL,NULL,'{\"client_id\": 6, \"logged_at\": \"2025-03-10 09:00:00.000000\", \"workout_id\": 6}','2026-03-05 04:18:37'),(80,'Workout_Logs',8,'INSERT',NULL,NULL,'{\"client_id\": 8, \"logged_at\": \"2025-03-20 11:00:00.000000\", \"workout_id\": 8}','2026-03-05 04:18:37'),(81,'Workout_Logs',9,'INSERT',NULL,NULL,'{\"client_id\": 9, \"logged_at\": \"2025-04-05 08:00:00.000000\", \"workout_id\": 9}','2026-03-05 04:18:37'),(82,'Workout_Logs',10,'INSERT',NULL,NULL,'{\"client_id\": 10, \"logged_at\": \"2025-04-15 09:00:00.000000\", \"workout_id\": 10}','2026-03-05 04:18:37'),(83,'Set_Results',1,'INSERT',NULL,NULL,'{\"actual_value\": 12.00, \"actual_weight\": null, \"workout_log_id\": 1}','2026-03-05 04:18:37'),(84,'Set_Results',2,'INSERT',NULL,NULL,'{\"actual_value\": 10.00, \"actual_weight\": null, \"workout_log_id\": 1}','2026-03-05 04:18:37'),(85,'Set_Results',3,'INSERT',NULL,NULL,'{\"actual_value\": 11.00, \"actual_weight\": null, \"workout_log_id\": 2}','2026-03-05 04:18:37'),(86,'Set_Results',4,'INSERT',NULL,NULL,'{\"actual_value\": 10.00, \"actual_weight\": 60.00, \"workout_log_id\": 3}','2026-03-05 04:18:37'),(87,'Set_Results',5,'INSERT',NULL,NULL,'{\"actual_value\": 28.00, \"actual_weight\": null, \"workout_log_id\": 4}','2026-03-05 04:18:37'),(88,'Set_Results',6,'INSERT',NULL,NULL,'{\"actual_value\": 5.00, \"actual_weight\": 80.00, \"workout_log_id\": 5}','2026-03-05 04:18:37'),(89,'Set_Results',7,'INSERT',NULL,NULL,'{\"actual_value\": 30.00, \"actual_weight\": null, \"workout_log_id\": 6}','2026-03-05 04:18:37'),(90,'Set_Results',8,'INSERT',NULL,NULL,'{\"actual_value\": 55.00, \"actual_weight\": null, \"workout_log_id\": 7}','2026-03-05 04:18:37'),(91,'Set_Results',9,'INSERT',NULL,NULL,'{\"actual_value\": 3.00, \"actual_weight\": 100.00, \"workout_log_id\": 8}','2026-03-05 04:18:37'),(92,'Set_Results',10,'INSERT',NULL,NULL,'{\"actual_value\": 30.00, \"actual_weight\": null, \"workout_log_id\": 9}','2026-03-05 04:18:37'),(93,'Weight_Logs',1,'INSERT',NULL,NULL,'{\"weight\": 68000, \"user_id\": 1}','2026-03-05 04:18:37'),(94,'Weight_Logs',2,'INSERT',NULL,NULL,'{\"weight\": 90000, \"user_id\": 2}','2026-03-05 04:18:37'),(95,'Weight_Logs',3,'INSERT',NULL,NULL,'{\"weight\": 55000, \"user_id\": 3}','2026-03-05 04:18:37'),(96,'Weight_Logs',4,'INSERT',NULL,NULL,'{\"weight\": 82000, \"user_id\": 4}','2026-03-05 04:18:37'),(97,'Weight_Logs',5,'INSERT',NULL,NULL,'{\"weight\": 63000, \"user_id\": 5}','2026-03-05 04:18:37'),(98,'Weight_Logs',6,'INSERT',NULL,NULL,'{\"weight\": 77000, \"user_id\": 6}','2026-03-05 04:18:37'),(99,'Weight_Logs',7,'INSERT',NULL,NULL,'{\"weight\": 50000, \"user_id\": 7}','2026-03-05 04:18:37'),(100,'Weight_Logs',8,'INSERT',NULL,NULL,'{\"weight\": 95000, \"user_id\": 8}','2026-03-05 04:18:37'),(101,'Weight_Logs',9,'INSERT',NULL,NULL,'{\"weight\": 72000, \"user_id\": 9}','2026-03-05 04:18:37'),(102,'Weight_Logs',10,'INSERT',NULL,NULL,'{\"weight\": 85000, \"user_id\": 10}','2026-03-05 04:18:37'),(103,'Saved_Workouts',1,'INSERT',NULL,NULL,'{\"user_id\": 1, \"workout_id\": 1}','2026-03-05 04:18:37'),(104,'Saved_Workouts',2,'INSERT',NULL,NULL,'{\"user_id\": 2, \"workout_id\": 2}','2026-03-05 04:18:37'),(105,'Saved_Workouts',3,'INSERT',NULL,NULL,'{\"user_id\": 3, \"workout_id\": 3}','2026-03-05 04:18:37'),(106,'Saved_Workouts',4,'INSERT',NULL,NULL,'{\"user_id\": 4, \"workout_id\": 4}','2026-03-05 04:18:37'),(107,'Saved_Workouts',5,'INSERT',NULL,NULL,'{\"user_id\": 5, \"workout_id\": 5}','2026-03-05 04:18:37'),(108,'Saved_Workouts',6,'INSERT',NULL,NULL,'{\"user_id\": 6, \"workout_id\": 6}','2026-03-05 04:18:37'),(109,'Saved_Workouts',7,'INSERT',NULL,NULL,'{\"user_id\": 7, \"workout_id\": 7}','2026-03-05 04:18:37'),(110,'Saved_Workouts',8,'INSERT',NULL,NULL,'{\"user_id\": 8, \"workout_id\": 8}','2026-03-05 04:18:37'),(111,'Saved_Workouts',9,'INSERT',NULL,NULL,'{\"user_id\": 9, \"workout_id\": 9}','2026-03-05 04:18:37'),(112,'Saved_Workouts',10,'INSERT',NULL,NULL,'{\"user_id\": 10, \"workout_id\": 10}','2026-03-05 04:18:37'),(113,'Daily_Surveys',1,'INSERT',NULL,NULL,'{\"user_id\": 1, \"step_count\": 9000, \"sleep_hours\": 7.5, \"survey_date\": \"2025-06-01\", \"energy_level\": 8, \"mood_type_id\": 1, \"water_intake\": 8, \"calories_burned\": 450, \"calories_intake\": 2000}','2026-03-05 04:18:37'),(114,'Daily_Surveys',2,'INSERT',NULL,NULL,'{\"user_id\": 2, \"step_count\": 7500, \"sleep_hours\": 6.0, \"survey_date\": \"2025-06-01\", \"energy_level\": 6, \"mood_type_id\": 2, \"water_intake\": 6, \"calories_burned\": 600, \"calories_intake\": 2500}','2026-03-05 04:18:37'),(115,'Daily_Surveys',3,'INSERT',NULL,NULL,'{\"user_id\": 3, \"step_count\": 11000, \"sleep_hours\": 8.0, \"survey_date\": \"2025-06-01\", \"energy_level\": 9, \"mood_type_id\": 1, \"water_intake\": 9, \"calories_burned\": 300, \"calories_intake\": 1800}','2026-03-05 04:18:37'),(116,'Daily_Surveys',4,'INSERT',NULL,NULL,'{\"user_id\": 4, \"step_count\": 6000, \"sleep_hours\": 5.5, \"survey_date\": \"2025-06-01\", \"energy_level\": 5, \"mood_type_id\": 3, \"water_intake\": 5, \"calories_burned\": 500, \"calories_intake\": 2200}','2026-03-05 04:18:37'),(117,'Daily_Surveys',5,'INSERT',NULL,NULL,'{\"user_id\": 5, \"step_count\": 8000, \"sleep_hours\": 7.0, \"survey_date\": \"2025-06-01\", \"energy_level\": 7, \"mood_type_id\": 2, \"water_intake\": 7, \"calories_burned\": 380, \"calories_intake\": 1700}','2026-03-05 04:18:37'),(118,'Daily_Surveys',6,'INSERT',NULL,NULL,'{\"user_id\": 6, \"step_count\": 4000, \"sleep_hours\": 4.5, \"survey_date\": \"2025-06-01\", \"energy_level\": 3, \"mood_type_id\": 4, \"water_intake\": 4, \"calories_burned\": 400, \"calories_intake\": 2800}','2026-03-05 04:18:37'),(119,'Daily_Surveys',7,'INSERT',NULL,NULL,'{\"user_id\": 7, \"step_count\": 13000, \"sleep_hours\": 9.0, \"survey_date\": \"2025-06-01\", \"energy_level\": 10, \"mood_type_id\": 1, \"water_intake\": 10, \"calories_burned\": 350, \"calories_intake\": 1600}','2026-03-05 04:18:37'),(120,'Daily_Surveys',8,'INSERT',NULL,NULL,'{\"user_id\": 8, \"step_count\": 8500, \"sleep_hours\": 6.5, \"survey_date\": \"2025-06-01\", \"energy_level\": 7, \"mood_type_id\": 2, \"water_intake\": 7, \"calories_burned\": 700, \"calories_intake\": 3000}','2026-03-05 04:18:37'),(121,'Daily_Surveys',9,'INSERT',NULL,NULL,'{\"user_id\": 9, \"step_count\": 7000, \"sleep_hours\": 7.0, \"survey_date\": \"2025-06-01\", \"energy_level\": 6, \"mood_type_id\": 3, \"water_intake\": 6, \"calories_burned\": 420, \"calories_intake\": 1900}','2026-03-05 04:18:37'),(122,'Daily_Surveys',10,'INSERT',NULL,NULL,'{\"user_id\": 10, \"step_count\": 10000, \"sleep_hours\": 8.0, \"survey_date\": \"2025-06-01\", \"energy_level\": 8, \"mood_type_id\": 2, \"water_intake\": 8, \"calories_burned\": 550, \"calories_intake\": 2100}','2026-03-05 04:18:37'),(123,'Cards',1,'INSERT',NULL,NULL,'{\"user_id\": 1, \"is_default\": 1, \"card_type_id\": 1}','2026-03-05 04:18:37'),(124,'Cards',2,'INSERT',NULL,NULL,'{\"user_id\": 2, \"is_default\": 1, \"card_type_id\": 2}','2026-03-05 04:18:37'),(125,'Cards',3,'INSERT',NULL,NULL,'{\"user_id\": 3, \"is_default\": 1, \"card_type_id\": 1}','2026-03-05 04:18:37'),(126,'Cards',4,'INSERT',NULL,NULL,'{\"user_id\": 4, \"is_default\": 1, \"card_type_id\": 3}','2026-03-05 04:18:37'),(127,'Cards',5,'INSERT',NULL,NULL,'{\"user_id\": 5, \"is_default\": 1, \"card_type_id\": 4}','2026-03-05 04:18:37'),(128,'Cards',6,'INSERT',NULL,NULL,'{\"user_id\": 6, \"is_default\": 1, \"card_type_id\": 1}','2026-03-05 04:18:37'),(129,'Cards',7,'INSERT',NULL,NULL,'{\"user_id\": 7, \"is_default\": 1, \"card_type_id\": 2}','2026-03-05 04:18:37'),(130,'Cards',8,'INSERT',NULL,NULL,'{\"user_id\": 8, \"is_default\": 1, \"card_type_id\": 3}','2026-03-05 04:18:37'),(131,'Cards',9,'INSERT',NULL,NULL,'{\"user_id\": 9, \"is_default\": 1, \"card_type_id\": 1}','2026-03-05 04:18:37'),(132,'Cards',10,'INSERT',NULL,NULL,'{\"user_id\": 10, \"is_default\": 1, \"card_type_id\": 4}','2026-03-05 04:18:37'),(133,'Users',17,'INSERT',NULL,NULL,'{\"role\": \"client\", \"email\": \"annabeth6235@gmail.com\", \"auth0_sub\": \"google-oauth2|112736608280708522873\"}','2026-03-27 19:31:10'),(134,'Clients',11,'INSERT',NULL,NULL,'{\"DOB\": null, \"user_id\": 17}','2026-03-27 19:31:10'),(135,'Users',17,'UPDATE',NULL,'{\"role\": \"client\", \"email\": \"annabeth6235@gmail.com\"}','{\"role\": \"client\", \"email\": \"annabeth6235@gmail.com\"}','2026-03-27 19:31:11'),(136,'Users',17,'UPDATE',NULL,'{\"role\": \"client\", \"email\": \"annabeth6235@gmail.com\"}','{\"role\": \"client\", \"email\": \"annabeth6235@gmail.com\"}','2026-03-27 19:34:58'),(137,'Users',17,'UPDATE',NULL,'{\"role\": \"client\", \"email\": \"annabeth6235@gmail.com\"}','{\"role\": \"client\", \"email\": \"annabeth6235@gmail.com\"}','2026-03-28 16:58:19'),(138,'Users',17,'UPDATE',NULL,'{\"role\": \"client\", \"email\": \"annabeth6235@gmail.com\"}','{\"role\": \"client\", \"email\": \"annabeth6235@gmail.com\"}','2026-03-28 16:58:19'),(139,'Users',17,'UPDATE',NULL,'{\"role\": \"client\", \"email\": \"annabeth6235@gmail.com\"}','{\"role\": \"client\", \"email\": \"annabeth6235@gmail.com\"}','2026-03-28 16:58:22'),(140,'Users',17,'UPDATE',NULL,'{\"role\": \"client\", \"email\": \"annabeth6235@gmail.com\"}','{\"role\": \"client\", \"email\": \"annabeth6235@gmail.com\"}','2026-03-28 16:58:23'),(141,'Users',17,'UPDATE',NULL,'{\"role\": \"client\", \"email\": \"annabeth6235@gmail.com\"}','{\"role\": \"client\", \"email\": \"annabeth6235@gmail.com\"}','2026-03-28 16:58:26'),(142,'Users',17,'UPDATE',NULL,'{\"role\": \"client\", \"email\": \"annabeth6235@gmail.com\"}','{\"role\": \"client\", \"email\": \"annabeth6235@gmail.com\"}','2026-03-28 16:58:31'),(143,'Users',17,'UPDATE',NULL,'{\"role\": \"client\", \"email\": \"annabeth6235@gmail.com\"}','{\"role\": \"client\", \"email\": \"annabeth6235@gmail.com\"}','2026-03-28 16:58:49'),(144,'Users',17,'UPDATE',NULL,'{\"role\": \"client\", \"email\": \"annabeth6235@gmail.com\"}','{\"role\": \"client\", \"email\": \"annabeth6235@gmail.com\"}','2026-03-28 16:58:55'),(145,'Users',17,'UPDATE',NULL,'{\"role\": \"client\", \"email\": \"annabeth6235@gmail.com\"}','{\"role\": \"client\", \"email\": \"annabeth6235@gmail.com\"}','2026-03-28 16:58:57'),(146,'Users',17,'UPDATE',NULL,'{\"role\": \"client\", \"email\": \"annabeth6235@gmail.com\"}','{\"role\": \"client\", \"email\": \"annabeth6235@gmail.com\"}','2026-03-28 16:58:58'),(147,'Users',17,'UPDATE',NULL,'{\"role\": \"client\", \"email\": \"annabeth6235@gmail.com\"}','{\"role\": \"client\", \"email\": \"annabeth6235@gmail.com\"}','2026-03-28 17:04:27'),(148,'Users',17,'UPDATE',NULL,'{\"role\": \"client\", \"email\": \"annabeth6235@gmail.com\"}','{\"role\": \"client\", \"email\": \"annabeth6235@gmail.com\"}','2026-03-28 17:04:27'),(149,'Users',17,'UPDATE',NULL,'{\"role\": \"client\", \"email\": \"annabeth6235@gmail.com\"}','{\"role\": \"client\", \"email\": \"annabeth6235@gmail.com\"}','2026-03-28 17:05:23'),(150,'Users',17,'UPDATE',NULL,'{\"role\": \"client\", \"email\": \"annabeth6235@gmail.com\"}','{\"role\": \"client\", \"email\": \"annabeth6235@gmail.com\"}','2026-03-28 17:05:23'),(151,'Users',17,'UPDATE',NULL,'{\"role\": \"client\", \"email\": \"annabeth6235@gmail.com\"}','{\"role\": \"client\", \"email\": \"annabeth6235@gmail.com\"}','2026-03-28 17:05:25'),(152,'Users',17,'UPDATE',NULL,'{\"role\": \"client\", \"email\": \"annabeth6235@gmail.com\"}','{\"role\": \"client\", \"email\": \"annabeth6235@gmail.com\"}','2026-03-28 17:05:26'),(153,'Users',18,'INSERT',NULL,NULL,'{\"role\": \"client\", \"email\": \"alice.johnson@hotmail.com\", \"auth0_sub\": \"auth0|69c858482adfb474a6b2d3f6\"}','2026-03-28 22:38:05'),(154,'Clients',12,'INSERT',NULL,NULL,'{\"DOB\": null, \"user_id\": 18}','2026-03-28 22:38:05'),(155,'Users',18,'UPDATE',NULL,'{\"role\": \"client\", \"email\": \"alice.johnson@hotmail.com\"}','{\"role\": \"client\", \"email\": \"alice.johnson@hotmail.com\"}','2026-03-28 22:38:05'),(156,'Users',18,'DELETE',NULL,'{\"role\": \"client\", \"email\": \"alice.johnson@hotmail.com\", \"auth0_sub\": \"auth0|69c858482adfb474a6b2d3f6\"}',NULL,'2026-03-28 22:40:52'),(157,'Users',19,'INSERT',NULL,NULL,'{\"role\": \"client\", \"email\": \"bob.smith@gmail.com\", \"auth0_sub\": \"auth0|69c859b92adfb474a6b2d4f0\"}','2026-03-28 22:44:14'),(158,'Clients',13,'INSERT',NULL,NULL,'{\"DOB\": null, \"user_id\": 19}','2026-03-28 22:44:14'),(159,'Users',19,'UPDATE',NULL,'{\"role\": \"client\", \"email\": \"bob.smith@gmail.com\"}','{\"role\": \"client\", \"email\": \"bob.smith@gmail.com\"}','2026-03-28 22:44:14'),(160,'Users',19,'DELETE',NULL,'{\"role\": \"client\", \"email\": \"bob.smith@gmail.com\", \"auth0_sub\": \"auth0|69c859b92adfb474a6b2d4f0\"}',NULL,'2026-03-28 22:46:07'),(161,'Users',20,'INSERT',NULL,NULL,'{\"role\": \"client\", \"email\": \"carol.white@yahoo.com\", \"auth0_sub\": \"auth0|69c85aa1e101a5198546d978\"}','2026-03-28 22:48:07'),(162,'Clients',14,'INSERT',NULL,NULL,'{\"DOB\": null, \"user_id\": 20}','2026-03-28 22:48:07'),(163,'Users',20,'UPDATE',NULL,'{\"role\": \"client\", \"email\": \"carol.white@yahoo.com\"}','{\"role\": \"client\", \"email\": \"carol.white@yahoo.com\"}','2026-03-28 22:48:07'),(164,'Users',20,'DELETE',NULL,'{\"role\": \"client\", \"email\": \"carol.white@yahoo.com\", \"auth0_sub\": \"auth0|69c85aa1e101a5198546d978\"}',NULL,'2026-03-28 22:48:28'),(165,'Users',3,'UPDATE',NULL,'{\"role\": \"client\", \"email\": \"carol.white@email.com\"}','{\"role\": \"client\", \"email\": \"carol.white@yahoo.com\"}','2026-03-28 22:48:52'),(166,'Users',21,'INSERT',NULL,NULL,'{\"role\": \"client\", \"email\": \"alice.johnson@hotmail.com\", \"auth0_sub\": \"auth0|69c858482adfb474a6b2d3f6\"}','2026-03-28 22:52:00'),(167,'Clients',15,'INSERT',NULL,NULL,'{\"DOB\": null, \"user_id\": 21}','2026-03-28 22:52:00'),(168,'Users',21,'UPDATE',NULL,'{\"role\": \"client\", \"email\": \"alice.johnson@hotmail.com\"}','{\"role\": \"client\", \"email\": \"alice.johnson@hotmail.com\"}','2026-03-28 22:52:00'),(169,'Users',2,'UPDATE',NULL,'{\"role\": \"client\", \"email\": \"bob.smith@email.com\"}','{\"role\": \"client\", \"email\": \"bob.smith@gmail.com\"}','2026-03-28 23:00:35'),(170,'Users',21,'DELETE',NULL,'{\"role\": \"client\", \"email\": \"alice.johnson@hotmail.com\", \"auth0_sub\": \"auth0|69c858482adfb474a6b2d3f6\"}',NULL,'2026-03-28 23:01:19'),(171,'Users',1,'UPDATE',NULL,'{\"role\": \"client\", \"email\": \"alice.johnson@email.com\"}','{\"role\": \"client\", \"email\": \"alice.johnson@hotmail.com\"}','2026-03-28 23:01:23'),(172,'Users',22,'INSERT',NULL,NULL,'{\"role\": \"client\", \"email\": \"david.brown@yahoo.com\", \"auth0_sub\": \"auth0|69c85df08d65c67e70e9d4ed\"}','2026-03-28 23:02:13'),(173,'Clients',16,'INSERT',NULL,NULL,'{\"DOB\": null, \"user_id\": 22}','2026-03-28 23:02:13'),(174,'Users',22,'UPDATE',NULL,'{\"role\": \"client\", \"email\": \"david.brown@yahoo.com\"}','{\"role\": \"client\", \"email\": \"david.brown@yahoo.com\"}','2026-03-28 23:02:14'),(175,'Users',22,'DELETE',NULL,'{\"role\": \"client\", \"email\": \"david.brown@yahoo.com\", \"auth0_sub\": \"auth0|69c85df08d65c67e70e9d4ed\"}',NULL,'2026-03-28 23:02:48'),(176,'Users',1,'UPDATE',NULL,'{\"role\": \"client\", \"email\": \"alice.johnson@hotmail.com\"}','{\"role\": \"client\", \"email\": \"david.brown@yahoo.com\"}','2026-03-28 23:02:48'),(177,'Users',1,'UPDATE',NULL,'{\"role\": \"client\", \"email\": \"david.brown@yahoo.com\"}','{\"role\": \"client\", \"email\": \"alice.johnson@hotmail.com\"}','2026-03-28 23:04:00'),(178,'Users',4,'UPDATE',NULL,'{\"role\": \"client\", \"email\": \"david.brown@email.com\"}','{\"role\": \"client\", \"email\": \"david.brown@yahoo.com\"}','2026-03-28 23:04:00'),(179,'Users',23,'INSERT',NULL,NULL,'{\"role\": \"client\", \"email\": \"eva.martinez@gmail.com\", \"auth0_sub\": \"auth0|69c85e980f5387a1051ead8c\"}','2026-03-28 23:05:01'),(180,'Clients',17,'INSERT',NULL,NULL,'{\"DOB\": null, \"user_id\": 23}','2026-03-28 23:05:01'),(181,'Users',23,'UPDATE',NULL,'{\"role\": \"client\", \"email\": \"eva.martinez@gmail.com\"}','{\"role\": \"client\", \"email\": \"eva.martinez@gmail.com\"}','2026-03-28 23:05:01'),(182,'Users',23,'DELETE',NULL,'{\"role\": \"client\", \"email\": \"eva.martinez@gmail.com\", \"auth0_sub\": \"auth0|69c85e980f5387a1051ead8c\"}',NULL,'2026-03-28 23:05:22'),(183,'Users',5,'UPDATE',NULL,'{\"role\": \"client\", \"email\": \"eva.martinez@email.com\"}','{\"role\": \"client\", \"email\": \"eva.martinez@gmail.com\"}','2026-03-28 23:05:22'),(184,'Users',24,'INSERT',NULL,NULL,'{\"role\": \"client\", \"email\": \"franklee@outlook.com\", \"auth0_sub\": \"auth0|69c85eeb8d65c67e70e9d57a\"}','2026-03-28 23:06:24'),(185,'Clients',18,'INSERT',NULL,NULL,'{\"DOB\": null, \"user_id\": 24}','2026-03-28 23:06:24'),(186,'Users',24,'UPDATE',NULL,'{\"role\": \"client\", \"email\": \"franklee@outlook.com\"}','{\"role\": \"client\", \"email\": \"franklee@outlook.com\"}','2026-03-28 23:06:24'),(187,'Users',24,'DELETE',NULL,'{\"role\": \"client\", \"email\": \"franklee@outlook.com\", \"auth0_sub\": \"auth0|69c85eeb8d65c67e70e9d57a\"}',NULL,'2026-03-28 23:06:52'),(188,'Users',6,'UPDATE',NULL,'{\"role\": \"client\", \"email\": \"frank.lee@email.com\"}','{\"role\": \"client\", \"email\": \"franklee@outlook.com\"}','2026-03-28 23:06:52'),(189,'Users',25,'INSERT',NULL,NULL,'{\"role\": \"client\", \"email\": \"grace82@gmail.com\", \"auth0_sub\": \"auth0|69c85f452adfb474a6b2d7fd\"}','2026-03-28 23:07:54'),(190,'Clients',19,'INSERT',NULL,NULL,'{\"DOB\": null, \"user_id\": 25}','2026-03-28 23:07:54'),(191,'Users',25,'UPDATE',NULL,'{\"role\": \"client\", \"email\": \"grace82@gmail.com\"}','{\"role\": \"client\", \"email\": \"grace82@gmail.com\"}','2026-03-28 23:07:54'),(192,'Users',25,'DELETE',NULL,'{\"role\": \"client\", \"email\": \"grace82@gmail.com\", \"auth0_sub\": \"auth0|69c85f452adfb474a6b2d7fd\"}',NULL,'2026-03-28 23:08:32'),(193,'Users',7,'UPDATE',NULL,'{\"role\": \"client\", \"email\": \"grace.kim@email.com\"}','{\"role\": \"client\", \"email\": \"grace82@outlook.com\"}','2026-03-28 23:08:32'),(194,'Users',26,'INSERT',NULL,NULL,'{\"role\": \"client\", \"email\": \"henry.nguyen@gmail.com\", \"auth0_sub\": \"auth0|69c868cd8d65c67e70e9da71\"}','2026-03-28 23:48:34'),(195,'Clients',20,'INSERT',NULL,NULL,'{\"DOB\": null, \"user_id\": 26}','2026-03-28 23:48:34'),(196,'Users',26,'UPDATE',NULL,'{\"role\": \"client\", \"email\": \"henry.nguyen@gmail.com\"}','{\"role\": \"client\", \"email\": \"henry.nguyen@gmail.com\"}','2026-03-28 23:48:34'),(197,'Users',26,'DELETE',NULL,'{\"role\": \"client\", \"email\": \"henry.nguyen@gmail.com\", \"auth0_sub\": \"auth0|69c868cd8d65c67e70e9da71\"}',NULL,'2026-03-28 23:49:03'),(198,'Users',8,'UPDATE',NULL,'{\"role\": \"client\", \"email\": \"henry.nguyen@email.com\"}','{\"role\": \"client\", \"email\": \"henry.nguyen@gmail.com\"}','2026-03-28 23:49:03'),(199,'Users',27,'INSERT',NULL,NULL,'{\"role\": \"client\", \"email\": \"isabella.clark@gmail.com\", \"auth0_sub\": \"auth0|69c869320f5387a1051eb328\"}','2026-03-28 23:50:15'),(200,'Clients',21,'INSERT',NULL,NULL,'{\"DOB\": null, \"user_id\": 27}','2026-03-28 23:50:15'),(201,'Users',27,'UPDATE',NULL,'{\"role\": \"client\", \"email\": \"isabella.clark@gmail.com\"}','{\"role\": \"client\", \"email\": \"isabella.clark@gmail.com\"}','2026-03-28 23:50:15'),(202,'Users',27,'UPDATE',NULL,'{\"role\": \"client\", \"email\": \"isabella.clark@gmail.com\"}','{\"role\": \"client\", \"email\": \"isabella.clark@gmail.com\"}','2026-03-28 23:50:17'),(203,'Users',27,'UPDATE',NULL,'{\"role\": \"client\", \"email\": \"isabella.clark@gmail.com\"}','{\"role\": \"client\", \"email\": \"isabella.clark@gmail.com\"}','2026-03-28 23:50:18'),(204,'Users',27,'DELETE',NULL,'{\"role\": \"client\", \"email\": \"isabella.clark@gmail.com\", \"auth0_sub\": \"auth0|69c869320f5387a1051eb328\"}',NULL,'2026-03-28 23:50:52'),(205,'Users',9,'UPDATE',NULL,'{\"role\": \"client\", \"email\": \"isabella.clark@email.com\"}','{\"role\": \"client\", \"email\": \"isabella.clark@gmail.com\"}','2026-03-28 23:50:52'),(206,'Users',28,'INSERT',NULL,NULL,'{\"role\": \"client\", \"email\": \"james.wilson@outlook.com\", \"auth0_sub\": \"auth0|69c869bd0f5387a1051eb372\"}','2026-03-28 23:52:30'),(207,'Clients',22,'INSERT',NULL,NULL,'{\"DOB\": null, \"user_id\": 28}','2026-03-28 23:52:30'),(208,'Users',28,'UPDATE',NULL,'{\"role\": \"client\", \"email\": \"james.wilson@outlook.com\"}','{\"role\": \"client\", \"email\": \"james.wilson@outlook.com\"}','2026-03-28 23:52:30'),(209,'Users',28,'DELETE',NULL,'{\"role\": \"client\", \"email\": \"james.wilson@outlook.com\", \"auth0_sub\": \"auth0|69c869bd0f5387a1051eb372\"}',NULL,'2026-03-28 23:53:15'),(210,'Users',10,'UPDATE',NULL,'{\"role\": \"client\", \"email\": \"james.wilson@email.com\"}','{\"role\": \"client\", \"email\": \"james.wilson@outlook.com\"}','2026-03-28 23:53:15'),(211,'Users',1,'UPDATE',NULL,'{\"role\": \"client\", \"email\": \"alice.johnson@hotmail.com\"}','{\"role\": \"client\", \"email\": \"alice.johnson@hotmail.com\"}','2026-03-30 20:13:51'),(212,'Users',1,'UPDATE',NULL,'{\"role\": \"client\", \"email\": \"alice.johnson@hotmail.com\"}','{\"role\": \"client\", \"email\": \"alice.johnson@hotmail.com\"}','2026-03-30 20:14:30'),(213,'Cards',1,'UPDATE',NULL,'{\"is_default\": 1, \"card_type_id\": 1}','{\"is_default\": 0, \"card_type_id\": 1}','2026-03-30 20:14:39'),(214,'Cards',11,'INSERT',NULL,NULL,'{\"user_id\": 1, \"is_default\": 1, \"card_type_id\": 1}','2026-03-30 20:14:39'),(215,'Users',1,'UPDATE',NULL,'{\"role\": \"client\", \"email\": \"alice.johnson@hotmail.com\"}','{\"role\": \"client\", \"email\": \"alice.johnson@hotmail.com\"}','2026-03-30 22:38:49'),(216,'Users',1,'UPDATE',NULL,'{\"role\": \"client\", \"email\": \"alice.johnson@hotmail.com\"}','{\"role\": \"client\", \"email\": \"alice.johnson@hotmail.com\"}','2026-03-30 23:18:50'),(217,'Users',1,'UPDATE',NULL,'{\"role\": \"client\", \"email\": \"alice.johnson@hotmail.com\"}','{\"role\": \"client\", \"email\": \"alice.johnson@hotmail.com\"}','2026-03-30 23:19:07'),(218,'Users',1,'UPDATE',NULL,'{\"role\": \"client\", \"email\": \"alice.johnson@hotmail.com\"}','{\"role\": \"client\", \"email\": \"alice.johnson@hotmail.com\"}','2026-03-30 23:21:37'),(219,'Users',1,'UPDATE',NULL,'{\"role\": \"client\", \"email\": \"alice.johnson@hotmail.com\"}','{\"role\": \"client\", \"email\": \"alice.johnson@hotmail.com\"}','2026-03-30 23:21:54'),(220,'Users',1,'UPDATE',NULL,'{\"role\": \"client\", \"email\": \"alice.johnson@hotmail.com\"}','{\"role\": \"client\", \"email\": \"alice.johnson@hotmail.com\"}','2026-03-30 23:33:55'),(221,'Users',1,'UPDATE',NULL,'{\"role\": \"client\", \"email\": \"alice.johnson@hotmail.com\"}','{\"role\": \"client\", \"email\": \"alice.johnson@hotmail.com\"}','2026-03-30 23:38:11'),(222,'Users',1,'UPDATE',NULL,'{\"role\": \"client\", \"email\": \"alice.johnson@hotmail.com\"}','{\"role\": \"client\", \"email\": \"alice.johnson@hotmail.com\"}','2026-04-02 22:24:08'),(223,'Users',1,'UPDATE',NULL,'{\"role\": \"client\", \"email\": \"alice.johnson@hotmail.com\"}','{\"role\": \"client\", \"email\": \"alice.johnson@hotmail.com\"}','2026-04-02 22:58:29'),(224,'Users',1,'UPDATE',NULL,'{\"role\": \"client\", \"email\": \"alice.johnson@hotmail.com\"}','{\"role\": \"client\", \"email\": \"alice.johnson@hotmail.com\"}','2026-04-09 00:48:16'),(225,'Users',1,'UPDATE',NULL,'{\"role\": \"client\", \"email\": \"alice.johnson@hotmail.com\"}','{\"role\": \"client\", \"email\": \"alice.johnson@hotmail.com\"}','2026-04-09 00:50:03'),(226,'Users',17,'UPDATE',NULL,'{\"role\": \"client\", \"email\": \"annabeth6235@gmail.com\"}','{\"role\": \"client\", \"email\": \"annabeth6235@gmail.com\"}','2026-04-09 00:50:22'),(227,'Users',17,'UPDATE',NULL,'{\"role\": \"client\", \"email\": \"annabeth6235@gmail.com\"}','{\"role\": \"client\", \"email\": \"annabeth6235@gmail.com\"}','2026-04-09 00:50:23'),(228,'Users',17,'UPDATE',NULL,'{\"role\": \"client\", \"email\": \"annabeth6235@gmail.com\"}','{\"role\": \"client\", \"email\": \"annabeth6235@gmail.com\"}','2026-04-09 00:50:25'),(229,'Users',17,'UPDATE',NULL,'{\"role\": \"client\", \"email\": \"annabeth6235@gmail.com\"}','{\"role\": \"client\", \"email\": \"annabeth6235@gmail.com\"}','2026-04-09 00:50:27'),(230,'Users',17,'UPDATE',NULL,'{\"role\": \"client\", \"email\": \"annabeth6235@gmail.com\"}','{\"role\": \"client\", \"email\": \"annabeth6235@gmail.com\"}','2026-04-09 00:50:29'),(231,'Users',17,'UPDATE',NULL,'{\"role\": \"client\", \"email\": \"annabeth6235@gmail.com\"}','{\"role\": \"client\", \"email\": \"annabeth6235@gmail.com\"}','2026-04-09 00:50:35'),(232,'Users',1,'UPDATE',NULL,'{\"role\": \"client\", \"email\": \"alice.johnson@hotmail.com\"}','{\"role\": \"client\", \"email\": \"alice.johnson@hotmail.com\"}','2026-04-09 18:24:19'),(233,'Users',1,'UPDATE',NULL,'{\"role\": \"client\", \"email\": \"alice.johnson@hotmail.com\"}','{\"role\": \"client\", \"email\": \"alice.johnson@hotmail.com\"}','2026-04-09 18:25:29'),(234,'Users',31,'INSERT',NULL,NULL,'{\"role\": \"coach\", \"email\": \"Percy.Jackson@hotmail.com\", \"auth0_sub\": \"auth0|69d7ef6dd13bd9b5b9bbc96e\"}','2026-04-09 18:26:54'),(235,'Coaches',5,'INSERT',NULL,NULL,'{\"user_id\": 31, \"status_id\": 1, \"is_trainer\": 1, \"hourly_rate\": 0.00, \"max_clients\": null, \"is_nutritionist\": 0, \"years_of_experience\": null}','2026-04-09 18:26:54'),(236,'Users',31,'UPDATE',NULL,'{\"role\": \"coach\", \"email\": \"Percy.Jackson@hotmail.com\"}','{\"role\": \"coach\", \"email\": \"Percy.Jackson@hotmail.com\"}','2026-04-09 18:28:11'),(237,'Users',1,'UPDATE',NULL,'{\"role\": \"client\", \"email\": \"alice.johnson@hotmail.com\"}','{\"role\": \"client\", \"email\": \"alice.johnson@hotmail.com\"}','2026-04-09 18:33:00'),(238,'Users',1,'UPDATE',NULL,'{\"role\": \"client\", \"email\": \"alice.johnson@hotmail.com\"}','{\"role\": \"client\", \"email\": \"alice.johnson@hotmail.com\"}','2026-04-09 18:51:09'),(239,'Users',1,'UPDATE',NULL,'{\"role\": \"client\", \"email\": \"alice.johnson@hotmail.com\"}','{\"role\": \"client\", \"email\": \"alice.johnson@hotmail.com\"}','2026-04-09 18:52:07'),(240,'Users',1,'UPDATE',NULL,'{\"role\": \"client\", \"email\": \"alice.johnson@hotmail.com\"}','{\"role\": \"client\", \"email\": \"alice.johnson@hotmail.com\"}','2026-04-09 18:53:24'),(241,'Users',32,'INSERT',NULL,NULL,'{\"role\": \"client\", \"email\": \"amy.march@outlook.com\", \"auth0_sub\": \"auth0|69d7f5f82415db6d9b67ce71\"}','2026-04-09 18:54:49'),(242,'Clients',23,'INSERT',NULL,NULL,'{\"DOB\": null, \"user_id\": 32}','2026-04-09 18:54:49'),(243,'Users',32,'UPDATE',NULL,'{\"role\": \"client\", \"email\": \"amy.march@outlook.com\"}','{\"role\": \"client\", \"email\": \"amy.march@outlook.com\"}','2026-04-09 19:00:14'),(244,'Users',32,'UPDATE',NULL,'{\"role\": \"client\", \"email\": \"amy.march@outlook.com\"}','{\"role\": \"client\", \"email\": \"amy.march@outlook.com\"}','2026-04-09 19:03:27'),(245,'Users',32,'UPDATE',NULL,'{\"role\": \"client\", \"email\": \"amy.march@outlook.com\"}','{\"role\": \"client\", \"email\": \"amy.march@outlook.com\"}','2026-04-09 19:06:32'),(246,'Users',32,'UPDATE',NULL,'{\"role\": \"client\", \"email\": \"amy.march@outlook.com\"}','{\"role\": \"client\", \"email\": \"amy.march@outlook.com\"}','2026-04-09 19:11:14'),(247,'Users',32,'UPDATE',NULL,'{\"role\": \"client\", \"email\": \"amy.march@outlook.com\"}','{\"role\": \"client\", \"email\": \"amy.march@outlook.com\"}','2026-04-09 19:12:06'),(248,'Users',32,'UPDATE',NULL,'{\"role\": \"client\", \"email\": \"amy.march@outlook.com\"}','{\"role\": \"client\", \"email\": \"amy.march@outlook.com\"}','2026-04-09 19:31:54'),(249,'Users',32,'UPDATE',NULL,'{\"role\": \"client\", \"email\": \"amy.march@outlook.com\"}','{\"role\": \"client\", \"email\": \"amy.march@outlook.com\"}','2026-04-09 21:40:56'),(250,'Users',32,'UPDATE',NULL,'{\"role\": \"client\", \"email\": \"amy.march@outlook.com\"}','{\"role\": \"client\", \"email\": \"amy.march@outlook.com\"}','2026-04-09 21:48:03'),(251,'Users',32,'UPDATE',NULL,'{\"role\": \"client\", \"email\": \"amy.march@outlook.com\"}','{\"role\": \"client\", \"email\": \"amy.march@outlook.com\"}','2026-04-09 21:49:46'),(252,'Users',33,'INSERT',NULL,NULL,'{\"role\": \"client\", \"email\": \"Jo.march@outlook.com\", \"auth0_sub\": \"auth0|69d83995bd96a3b53d2bb522\"}','2026-04-09 23:43:18'),(253,'Clients',24,'INSERT',NULL,NULL,'{\"DOB\": null, \"user_id\": 33}','2026-04-09 23:43:18'),(254,'Users',1,'UPDATE',NULL,'{\"role\": \"client\", \"email\": \"alice.johnson@hotmail.com\"}','{\"role\": \"client\", \"email\": \"alice.johnson@hotmail.com\"}','2026-04-09 23:43:41'),(255,'Users',1,'UPDATE',NULL,'{\"role\": \"client\", \"email\": \"alice.johnson@hotmail.com\"}','{\"role\": \"client\", \"email\": \"alice.johnson@hotmail.com\"}','2026-04-09 23:49:54'),(256,'Users',34,'INSERT',NULL,NULL,'{\"role\": \"client\", \"email\": \"alice.march@hotmail.com\", \"auth0_sub\": \"auth0|69d83b3e7491f5682e15ae41\"}','2026-04-09 23:50:23'),(257,'Clients',25,'INSERT',NULL,NULL,'{\"DOB\": null, \"user_id\": 34}','2026-04-09 23:50:23'),(258,'Users',35,'INSERT',NULL,NULL,'{\"role\": \"client\", \"email\": \"tylerA@gmail.com\", \"auth0_sub\": \"auth0|69d83d71180913421e062387\"}','2026-04-09 23:59:47'),(259,'Clients',26,'INSERT',NULL,NULL,'{\"DOB\": null, \"user_id\": 35}','2026-04-09 23:59:47'),(260,'Users',35,'UPDATE',NULL,'{\"role\": \"client\", \"email\": \"tylerA@gmail.com\"}','{\"role\": \"client\", \"email\": \"tylerA@gmail.com\"}','2026-04-10 00:00:12'),(261,'Users',35,'UPDATE',NULL,'{\"role\": \"client\", \"email\": \"tylerA@gmail.com\"}','{\"role\": \"client\", \"email\": \"tylerA@gmail.com\"}','2026-04-10 00:00:41');
/*!40000 ALTER TABLE `audit_log` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `card_types`
--

DROP TABLE IF EXISTS `card_types`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `card_types` (
  `card_type_id` int NOT NULL AUTO_INCREMENT,
  `card_type_name` varchar(50) NOT NULL,
  PRIMARY KEY (`card_type_id`),
  UNIQUE KEY `card_type_name` (`card_type_name`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `card_types`
--

LOCK TABLES `card_types` WRITE;
/*!40000 ALTER TABLE `card_types` DISABLE KEYS */;
INSERT INTO `card_types` VALUES (3,'Amex'),(4,'Discover'),(2,'Mastercard'),(1,'Visa');
/*!40000 ALTER TABLE `card_types` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `cards`
--

DROP TABLE IF EXISTS `cards`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `cards` (
  `card_id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `card_type_id` int NOT NULL,
  `card_number` char(16) NOT NULL,
  `expiry_month` tinyint NOT NULL,
  `expiry_year` smallint NOT NULL,
  `zip_code` char(10) DEFAULT NULL,
  `is_default` tinyint(1) NOT NULL DEFAULT '0',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `last_updated` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`card_id`),
  KEY `fk_cards_user` (`user_id`),
  KEY `fk_cards_card_type` (`card_type_id`),
  CONSTRAINT `fk_cards_card_type` FOREIGN KEY (`card_type_id`) REFERENCES `card_types` (`card_type_id`),
  CONSTRAINT `fk_cards_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `cards`
--

LOCK TABLES `cards` WRITE;
/*!40000 ALTER TABLE `cards` DISABLE KEYS */;
INSERT INTO `cards` VALUES (1,1,1,'4111111111111111',12,2026,'10001',0,'2025-01-10 13:20:00','2026-03-30 20:14:39'),(2,2,2,'5500005555555559',6,2025,'90210',1,'2025-01-15 14:45:00','2025-01-15 14:45:00'),(3,3,1,'4012888888881881',3,2027,'60601',1,'2025-02-01 15:20:00','2025-02-01 15:20:00'),(4,4,3,'378282246310005',9,2026,'77001',1,'2025-02-10 16:20:00','2025-02-10 16:20:00'),(5,5,4,'6011111111111117',1,2028,'85001',1,'2025-03-05 13:05:00','2025-03-05 13:05:00'),(6,6,1,'4111111111111111',11,2025,'19103',1,'2025-03-20 18:20:00','2025-03-20 18:20:00'),(7,7,2,'5105105105105100',4,2027,'98101',1,'2025-04-01 13:20:00','2025-04-01 13:20:00'),(8,8,3,'371449635398431',8,2026,'30301',1,'2025-04-15 17:45:00','2025-04-15 17:45:00'),(9,9,1,'4222222222222',2,2028,'02101',1,'2025-05-01 12:30:00','2025-05-01 12:30:00'),(10,10,4,'6011000990139424',7,2027,'78201',1,'2025-05-20 15:05:00','2025-05-20 15:05:00'),(11,1,1,'************1111',12,2027,'12345',1,'2026-03-31 00:14:39','2026-03-31 00:14:39');
/*!40000 ALTER TABLE `cards` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_cards_audit_insert` AFTER INSERT ON `cards` FOR EACH ROW BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, new_values)
    VALUES ('Cards', NEW.card_id, 'INSERT', @current_user_id,
        JSON_OBJECT('user_id', NEW.user_id, 'card_type_id', NEW.card_type_id, 'is_default', NEW.is_default));
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_cards_last_updated` BEFORE UPDATE ON `cards` FOR EACH ROW SET NEW.last_updated = NOW() */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_cards_audit_update` AFTER UPDATE ON `cards` FOR EACH ROW BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, old_values, new_values)
    VALUES ('Cards', NEW.card_id, 'UPDATE', @current_user_id,
        JSON_OBJECT('card_type_id', OLD.card_type_id, 'is_default', OLD.is_default),
        JSON_OBJECT('card_type_id', NEW.card_type_id, 'is_default', NEW.is_default));
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_cards_audit_delete` AFTER DELETE ON `cards` FOR EACH ROW BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, old_values)
    VALUES ('Cards', OLD.card_id, 'DELETE', @current_user_id,
        JSON_OBJECT('user_id', OLD.user_id, 'card_type_id', OLD.card_type_id));
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `chat`
--

DROP TABLE IF EXISTS `chat`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `chat` (
  `message_id` int NOT NULL AUTO_INCREMENT,
  `sender_id` int NOT NULL,
  `receiver_id` int NOT NULL,
  `message` text NOT NULL,
  `sent_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `last_updated` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`message_id`),
  KEY `fk_chat_sender` (`sender_id`),
  KEY `fk_chat_receiver` (`receiver_id`),
  CONSTRAINT `fk_chat_receiver` FOREIGN KEY (`receiver_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE,
  CONSTRAINT `fk_chat_sender` FOREIGN KEY (`sender_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `chat`
--

LOCK TABLES `chat` WRITE;
/*!40000 ALTER TABLE `chat` DISABLE KEYS */;
INSERT INTO `chat` VALUES (1,11,1,'Hi Alice! How are you feeling after yesterday\'s workout?','2025-06-01 12:00:00','2025-06-01 12:00:00','2025-06-01 12:00:00'),(2,1,11,'Legs are sore but I feel great! Thanks Coach Karen.','2025-06-01 12:05:00','2025-06-01 12:05:00','2025-06-01 12:05:00'),(3,12,3,'Carol, I updated your endurance plan. Check it out!','2025-06-01 13:00:00','2025-06-01 13:00:00','2025-06-01 13:00:00'),(4,3,12,'Awesome! Looking forward to the new challenges.','2025-06-01 13:10:00','2025-06-01 13:10:00','2025-06-01 13:10:00'),(5,13,5,'Eva, remember to drink water throughout the day!','2025-06-01 14:00:00','2025-06-01 14:00:00','2025-06-01 14:00:00'),(6,5,13,'Will do! I also have a question about my meal plan.','2025-06-01 14:15:00','2025-06-01 14:15:00','2025-06-01 14:15:00'),(7,11,7,'Grace, you have hit a 6-week streak! Incredible work.','2025-06-01 15:00:00','2025-06-01 15:00:00','2025-06-01 15:00:00'),(8,7,11,'Thank you! Cannot believe how far I have come.','2025-06-01 15:05:00','2025-06-01 15:05:00','2025-06-01 15:05:00'),(9,12,8,'Henry, your deadlift numbers are improving fast!','2025-06-01 16:00:00','2025-06-01 16:00:00','2025-06-01 16:00:00'),(10,8,12,'I finally hit 200 lbs. The programming is working perfectly.','2025-06-01 16:10:00','2025-06-01 16:10:00','2025-06-01 16:10:00');
/*!40000 ALTER TABLE `chat` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `client_coach`
--

DROP TABLE IF EXISTS `client_coach`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `client_coach` (
  `client_id` int NOT NULL,
  `coach_id` int NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `last_updated` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `status_name` enum('Pending','Active','Terminated','Declined') NOT NULL DEFAULT 'Pending',
  PRIMARY KEY (`client_id`,`coach_id`),
  KEY `fk_client_coach_coach` (`coach_id`),
  CONSTRAINT `fk_client_coach_client` FOREIGN KEY (`client_id`) REFERENCES `clients` (`client_id`) ON DELETE CASCADE,
  CONSTRAINT `fk_client_coach_coach` FOREIGN KEY (`coach_id`) REFERENCES `coaches` (`coach_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `client_coach`
--

LOCK TABLES `client_coach` WRITE;
/*!40000 ALTER TABLE `client_coach` DISABLE KEYS */;
INSERT INTO `client_coach` VALUES (1,1,'2025-02-01 14:00:00','2025-02-01 14:00:00','Pending'),(1,4,'2024-03-15 13:00:00','2025-04-15 04:00:00','Pending'),(2,1,'2025-02-05 15:00:00','2025-02-05 15:00:00','Pending'),(3,2,'2025-02-10 16:00:00','2025-02-10 16:00:00','Pending'),(4,2,'2025-02-15 17:00:00','2025-02-15 17:00:00','Pending'),(5,3,'2025-03-01 13:00:00','2025-03-01 13:00:00','Pending'),(6,3,'2025-03-05 14:00:00','2025-03-05 14:00:00','Pending'),(6,4,'2024-04-01 13:00:00','2025-04-15 04:00:00','Pending'),(7,1,'2025-03-10 14:00:00','2025-03-10 14:00:00','Pending'),(8,2,'2025-03-15 15:00:00','2025-03-15 15:00:00','Pending'),(9,3,'2025-04-01 12:00:00','2025-04-01 12:00:00','Pending'),(10,1,'2025-04-10 13:00:00','2025-04-10 13:00:00','Pending');
/*!40000 ALTER TABLE `client_coach` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `clients`
--

DROP TABLE IF EXISTS `clients`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `clients` (
  `client_id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `DOB` date DEFAULT NULL,
  `height` int DEFAULT NULL,
  `weight` int DEFAULT NULL,
  `goal_weight` int DEFAULT NULL,
  `sex` varchar(20) DEFAULT NULL,
  `weekly_streak` int NOT NULL DEFAULT '0',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `last_updated` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`client_id`),
  UNIQUE KEY `user_id` (`user_id`),
  CONSTRAINT `fk_clients_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=27 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `clients`
--

LOCK TABLES `clients` WRITE;
/*!40000 ALTER TABLE `clients` DISABLE KEYS */;
INSERT INTO `clients` VALUES (1,1,'1995-03-12',165,68000,60000,'Female',4,'2025-01-10 13:05:00','2025-06-01 14:00:00'),(2,2,'1988-07-25',180,90000,80000,'Male',2,'2025-01-15 14:35:00','2025-06-01 14:00:00'),(3,3,'2000-11-03',158,55000,52000,'Female',7,'2025-02-01 15:05:00','2025-06-01 14:00:00'),(4,4,'1992-04-18',175,82000,75000,'Male',1,'2025-02-10 16:05:00','2025-06-01 14:00:00'),(5,5,'1997-09-30',162,63000,58000,'Female',5,'2025-03-05 12:50:00','2025-06-01 14:00:00'),(6,6,'1985-12-07',170,77000,72000,'Male',3,'2025-03-20 18:05:00','2025-06-01 14:00:00'),(7,7,'2001-06-14',155,50000,48000,'Female',6,'2025-04-01 13:05:00','2025-06-01 14:00:00'),(8,8,'1990-02-22',183,95000,88000,'Male',0,'2025-04-15 17:35:00','2025-06-01 14:00:00'),(9,9,'1998-08-11',167,72000,65000,'Female',8,'2025-05-01 12:20:00','2025-06-01 14:00:00'),(10,10,'1993-01-29',178,85000,78000,'Male',2,'2025-05-20 14:50:00','2025-06-01 14:00:00'),(11,17,NULL,NULL,NULL,NULL,NULL,0,'2026-03-27 23:31:11','2026-03-27 23:31:11'),(23,32,NULL,NULL,NULL,NULL,NULL,0,'2026-04-09 22:54:49','2026-04-09 22:54:49'),(24,33,NULL,NULL,NULL,NULL,NULL,0,'2026-04-10 03:43:19','2026-04-10 03:43:19'),(25,34,NULL,NULL,NULL,NULL,NULL,0,'2026-04-10 03:50:24','2026-04-10 03:50:24'),(26,35,NULL,NULL,NULL,NULL,NULL,0,'2026-04-10 03:59:47','2026-04-10 03:59:47');
/*!40000 ALTER TABLE `clients` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_clients_audit_insert` AFTER INSERT ON `clients` FOR EACH ROW BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, new_values)
    VALUES ('Clients', NEW.client_id, 'INSERT', @current_user_id,
        JSON_OBJECT('user_id', NEW.user_id, 'DOB', NEW.DOB));
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_clients_last_updated` BEFORE UPDATE ON `clients` FOR EACH ROW SET NEW.last_updated = NOW() */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_clients_audit_update` AFTER UPDATE ON `clients` FOR EACH ROW BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, old_values, new_values)
    VALUES ('Clients', NEW.client_id, 'UPDATE', @current_user_id,
        JSON_OBJECT('height', OLD.height, 'weight', OLD.weight, 'goal_weight', OLD.goal_weight, 'weekly_streak', OLD.weekly_streak),
        JSON_OBJECT('height', NEW.height, 'weight', NEW.weight, 'goal_weight', NEW.goal_weight, 'weekly_streak', NEW.weekly_streak));
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_clients_audit_delete` AFTER DELETE ON `clients` FOR EACH ROW BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, old_values)
    VALUES ('Clients', OLD.client_id, 'DELETE', @current_user_id,
        JSON_OBJECT('user_id', OLD.user_id));
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `coach_availability`
--

DROP TABLE IF EXISTS `coach_availability`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `coach_availability` (
  `availability_id` int NOT NULL AUTO_INCREMENT,
  `coach_id` int NOT NULL,
  `day_of_week` enum('MON','TUE','WED','THU','FRI','SAT','SUN') NOT NULL,
  `start_time` time NOT NULL,
  `end_time` time NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `last_updated` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`availability_id`),
  UNIQUE KEY `uq_coach_day` (`coach_id`,`day_of_week`),
  CONSTRAINT `fk_coach_availability_coach` FOREIGN KEY (`coach_id`) REFERENCES `coaches` (`coach_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `coach_availability`
--

LOCK TABLES `coach_availability` WRITE;
/*!40000 ALTER TABLE `coach_availability` DISABLE KEYS */;
INSERT INTO `coach_availability` VALUES (1,1,'MON','07:00:00','12:00:00','2024-06-01 12:00:00','2024-06-01 12:00:00'),(2,1,'WED','07:00:00','12:00:00','2024-06-01 12:00:00','2024-06-01 12:00:00'),(3,1,'FRI','07:00:00','12:00:00','2024-06-01 12:00:00','2024-06-01 12:00:00'),(4,1,'SAT','09:00:00','14:00:00','2024-06-01 12:00:00','2024-06-01 12:00:00'),(5,2,'MON','06:00:00','14:00:00','2024-07-15 13:00:00','2024-07-15 13:00:00'),(6,2,'TUE','06:00:00','14:00:00','2024-07-15 13:00:00','2024-07-15 13:00:00'),(7,2,'THU','06:00:00','14:00:00','2024-07-15 13:00:00','2024-07-15 13:00:00'),(8,3,'TUE','10:00:00','18:00:00','2024-08-01 14:00:00','2024-08-01 14:00:00'),(9,3,'WED','10:00:00','18:00:00','2024-08-01 14:00:00','2024-08-01 14:00:00'),(10,3,'SAT','08:00:00','16:00:00','2024-08-01 14:00:00','2024-08-01 14:00:00');
/*!40000 ALTER TABLE `coach_availability` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_coach_availability_audit_insert` AFTER INSERT ON `coach_availability` FOR EACH ROW BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, new_values)
    VALUES ('Coach_Availability', NEW.availability_id, 'INSERT', @current_user_id,
        JSON_OBJECT('coach_id', NEW.coach_id, 'day_of_week', NEW.day_of_week, 'start_time', NEW.start_time, 'end_time', NEW.end_time));
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_coach_availability_last_updated` BEFORE UPDATE ON `coach_availability` FOR EACH ROW SET NEW.last_updated = NOW() */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_coach_availability_audit_update` AFTER UPDATE ON `coach_availability` FOR EACH ROW BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, old_values, new_values)
    VALUES ('Coach_Availability', NEW.availability_id, 'UPDATE', @current_user_id,
        JSON_OBJECT('day_of_week', OLD.day_of_week, 'start_time', OLD.start_time, 'end_time', OLD.end_time),
        JSON_OBJECT('day_of_week', NEW.day_of_week, 'start_time', NEW.start_time, 'end_time', NEW.end_time));
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_coach_availability_audit_delete` AFTER DELETE ON `coach_availability` FOR EACH ROW BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, old_values)
    VALUES ('Coach_Availability', OLD.availability_id, 'DELETE', @current_user_id,
        JSON_OBJECT('coach_id', OLD.coach_id, 'day_of_week', OLD.day_of_week));
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `coach_certifications`
--

DROP TABLE IF EXISTS `coach_certifications`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `coach_certifications` (
  `certification_id` int NOT NULL AUTO_INCREMENT,
  `coach_id` int NOT NULL,
  `certification_name` varchar(255) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`certification_id`),
  KEY `fk_coach_certifications_coach` (`coach_id`),
  CONSTRAINT `fk_coach_certifications_coach` FOREIGN KEY (`coach_id`) REFERENCES `coaches` (`coach_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `coach_certifications`
--

LOCK TABLES `coach_certifications` WRITE;
/*!40000 ALTER TABLE `coach_certifications` DISABLE KEYS */;
INSERT INTO `coach_certifications` VALUES (1,1,'NASM Certified Personal Trainer (CPT)','2024-06-01 12:10:00'),(2,1,'ACE Group Fitness Instructor','2024-06-01 12:10:00'),(3,1,'TRX Suspension Training Certification','2024-06-01 12:10:00'),(4,1,'CPR/AED Certified','2024-06-01 12:10:00'),(5,2,'CSCS – Certified Strength and Conditioning','2024-07-15 13:10:00'),(6,2,'NSCA Certified Personal Trainer','2024-07-15 13:10:00'),(7,2,'Precision Nutrition Level 1','2024-07-15 13:10:00'),(8,2,'USA Weightlifting Sports Performance Coach','2024-07-15 13:10:00'),(9,3,'RYT-200 Yoga Alliance Certification','2024-08-01 14:10:00'),(10,3,'Precision Nutrition Level 2','2024-08-01 14:10:00'),(11,3,'ACE Certified Personal Trainer','2024-08-01 14:10:00');
/*!40000 ALTER TABLE `coach_certifications` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `coach_payment_history`
--

DROP TABLE IF EXISTS `coach_payment_history`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `coach_payment_history` (
  `payment_id` int NOT NULL AUTO_INCREMENT,
  `client_id` int NOT NULL,
  `coach_id` int NOT NULL,
  `amount` decimal(10,2) NOT NULL,
  `payment_date` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `last_updated` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`payment_id`),
  KEY `fk_payment_client` (`client_id`),
  KEY `fk_payment_coach` (`coach_id`),
  CONSTRAINT `fk_payment_client` FOREIGN KEY (`client_id`) REFERENCES `clients` (`client_id`) ON DELETE CASCADE,
  CONSTRAINT `fk_payment_coach` FOREIGN KEY (`coach_id`) REFERENCES `coaches` (`coach_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `coach_payment_history`
--

LOCK TABLES `coach_payment_history` WRITE;
/*!40000 ALTER TABLE `coach_payment_history` DISABLE KEYS */;
INSERT INTO `coach_payment_history` VALUES (1,1,1,150.00,'2025-02-01 14:30:00','2025-02-01 14:30:00','2025-02-01 14:30:00'),(2,1,1,150.00,'2025-03-01 14:30:00','2025-03-01 14:30:00','2025-03-01 14:30:00'),(3,2,1,150.00,'2025-02-05 15:30:00','2025-02-05 15:30:00','2025-02-05 15:30:00'),(4,3,2,180.00,'2025-02-10 16:30:00','2025-02-10 16:30:00','2025-02-10 16:30:00'),(5,4,2,180.00,'2025-02-15 17:30:00','2025-02-15 17:30:00','2025-02-15 17:30:00'),(6,5,3,130.00,'2025-03-01 13:30:00','2025-03-01 13:30:00','2025-03-01 13:30:00'),(7,6,3,130.00,'2025-03-05 14:30:00','2025-03-05 14:30:00','2025-03-05 14:30:00'),(8,7,1,150.00,'2025-03-10 14:30:00','2025-03-10 14:30:00','2025-03-10 14:30:00'),(9,8,2,180.00,'2025-03-15 15:30:00','2025-03-15 15:30:00','2025-03-15 15:30:00'),(10,9,3,130.00,'2025-04-01 12:30:00','2025-04-01 12:30:00','2025-04-01 12:30:00');
/*!40000 ALTER TABLE `coach_payment_history` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `coach_session_formats`
--

DROP TABLE IF EXISTS `coach_session_formats`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `coach_session_formats` (
  `coach_id` int NOT NULL,
  `session_format_id` int NOT NULL,
  PRIMARY KEY (`coach_id`,`session_format_id`),
  KEY `fk_coach_session_formats_session_format` (`session_format_id`),
  CONSTRAINT `fk_coach_session_formats_coach` FOREIGN KEY (`coach_id`) REFERENCES `coaches` (`coach_id`) ON DELETE CASCADE,
  CONSTRAINT `fk_coach_session_formats_session_format` FOREIGN KEY (`session_format_id`) REFERENCES `session_formats` (`session_format_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `coach_session_formats`
--

LOCK TABLES `coach_session_formats` WRITE;
/*!40000 ALTER TABLE `coach_session_formats` DISABLE KEYS */;
INSERT INTO `coach_session_formats` VALUES (1,1),(3,1),(1,2),(2,3);
/*!40000 ALTER TABLE `coach_session_formats` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `coach_specialities`
--

DROP TABLE IF EXISTS `coach_specialities`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `coach_specialities` (
  `coach_id` int NOT NULL,
  `goal_type_id` int NOT NULL,
  PRIMARY KEY (`coach_id`,`goal_type_id`),
  KEY `fk_coach_specialities_goal_type` (`goal_type_id`),
  CONSTRAINT `fk_coach_specialities_coach` FOREIGN KEY (`coach_id`) REFERENCES `coaches` (`coach_id`) ON DELETE CASCADE,
  CONSTRAINT `fk_coach_specialities_goal_type` FOREIGN KEY (`goal_type_id`) REFERENCES `goal_types` (`goal_type_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `coach_specialities`
--

LOCK TABLES `coach_specialities` WRITE;
/*!40000 ALTER TABLE `coach_specialities` DISABLE KEYS */;
INSERT INTO `coach_specialities` VALUES (1,1),(2,1),(3,1),(1,2),(2,2),(2,3),(3,3),(1,4),(3,4),(2,5);
/*!40000 ALTER TABLE `coach_specialities` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `coach_statuses`
--

DROP TABLE IF EXISTS `coach_statuses`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `coach_statuses` (
  `status_id` int NOT NULL AUTO_INCREMENT,
  `status_name` varchar(50) NOT NULL,
  PRIMARY KEY (`status_id`),
  UNIQUE KEY `status_name` (`status_name`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `coach_statuses`
--

LOCK TABLES `coach_statuses` WRITE;
/*!40000 ALTER TABLE `coach_statuses` DISABLE KEYS */;
INSERT INTO `coach_statuses` VALUES (2,'Active'),(1,'Pending'),(4,'Rejected'),(3,'Suspended');
/*!40000 ALTER TABLE `coach_statuses` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `coaches`
--

DROP TABLE IF EXISTS `coaches`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `coaches` (
  `coach_id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `gender` varchar(20) DEFAULT NULL,
  `hourly_rate` decimal(10,2) DEFAULT NULL,
  `accepting_clients` tinyint(1) NOT NULL DEFAULT '1',
  `bio` text,
  `status_id` int NOT NULL DEFAULT '1',
  `is_trainer` tinyint(1) NOT NULL DEFAULT '1',
  `is_nutritionist` tinyint(1) NOT NULL DEFAULT '0',
  `years_of_experience` int DEFAULT NULL,
  `max_clients` int DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `last_updated` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`coach_id`),
  UNIQUE KEY `user_id` (`user_id`),
  KEY `fk_coaches_coach_status` (`status_id`),
  CONSTRAINT `fk_coaches_coach_status` FOREIGN KEY (`status_id`) REFERENCES `coach_statuses` (`status_id`),
  CONSTRAINT `fk_coaches_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `coaches`
--

LOCK TABLES `coaches` WRITE;
/*!40000 ALTER TABLE `coaches` DISABLE KEYS */;
INSERT INTO `coaches` VALUES (1,11,'Female',75.00,1,'Certified personal trainer specializing in weight loss and strength training.',2,1,0,8,20,'2024-06-01 12:05:00','2025-01-01 05:00:00'),(2,12,'Male',90.00,1,'Strength and conditioning coach with a focus on athletic performance.',2,1,1,12,15,'2024-07-15 13:05:00','2025-01-01 05:00:00'),(3,13,'Female',65.00,1,'Yoga and flexibility specialist with nutrition coaching credentials.',2,0,1,5,25,'2024-08-01 14:05:00','2025-01-01 05:00:00'),(4,16,'Male',70.00,0,'Strength coach — account suspended following client conduct reports.',3,1,0,6,20,'2024-03-01 14:05:00','2025-04-15 04:00:00'),(5,31,NULL,0.00,1,NULL,1,1,0,NULL,NULL,'2026-04-09 22:26:55','2026-04-09 22:26:55');
/*!40000 ALTER TABLE `coaches` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_coaches_audit_insert` AFTER INSERT ON `coaches` FOR EACH ROW BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, new_values)
    VALUES ('Coaches', NEW.coach_id, 'INSERT', @current_user_id,
        JSON_OBJECT(
            'user_id',             NEW.user_id,
            'status_id',           NEW.status_id,
            'hourly_rate',         NEW.hourly_rate,
            'is_trainer',          NEW.is_trainer,
            'is_nutritionist',     NEW.is_nutritionist,
            'years_of_experience', NEW.years_of_experience,
            'max_clients',         NEW.max_clients
        ));
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_coaches_last_updated` BEFORE UPDATE ON `coaches` FOR EACH ROW SET NEW.last_updated = NOW() */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_coaches_audit_update` AFTER UPDATE ON `coaches` FOR EACH ROW BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, old_values, new_values)
    VALUES ('Coaches', NEW.coach_id, 'UPDATE', @current_user_id,
        JSON_OBJECT(
            'status_id',           OLD.status_id,
            'hourly_rate',         OLD.hourly_rate,
            'accepting_clients',   OLD.accepting_clients,
            'is_trainer',          OLD.is_trainer,
            'is_nutritionist',     OLD.is_nutritionist,
            'years_of_experience', OLD.years_of_experience,
            'max_clients',         OLD.max_clients
        ),
        JSON_OBJECT(
            'status_id',           NEW.status_id,
            'hourly_rate',         NEW.hourly_rate,
            'accepting_clients',   NEW.accepting_clients,
            'is_trainer',          NEW.is_trainer,
            'is_nutritionist',     NEW.is_nutritionist,
            'years_of_experience', NEW.years_of_experience,
            'max_clients',         NEW.max_clients
        ));
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_coaches_audit_delete` AFTER DELETE ON `coaches` FOR EACH ROW BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, old_values)
    VALUES ('Coaches', OLD.coach_id, 'DELETE', @current_user_id,
        JSON_OBJECT('user_id', OLD.user_id, 'status_id', OLD.status_id));
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `daily_surveys`
--

DROP TABLE IF EXISTS `daily_surveys`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `daily_surveys` (
  `survey_id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `survey_date` date NOT NULL,
  `mood_type_id` int NOT NULL,
  `energy_level` tinyint DEFAULT NULL,
  `sleep_hours` decimal(4,1) DEFAULT NULL,
  `step_count` int DEFAULT NULL,
  `calories_intake` int DEFAULT NULL,
  `calories_burned` int DEFAULT NULL,
  `water_intake` tinyint DEFAULT NULL,
  `notes` text,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `last_updated` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`survey_id`),
  UNIQUE KEY `uq_survey_user_date` (`user_id`,`survey_date`),
  KEY `fk_daily_surveys_mood_type` (`mood_type_id`),
  CONSTRAINT `fk_daily_surveys_mood_type` FOREIGN KEY (`mood_type_id`) REFERENCES `mood_types` (`mood_type_id`),
  CONSTRAINT `fk_daily_surveys_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `daily_surveys`
--

LOCK TABLES `daily_surveys` WRITE;
/*!40000 ALTER TABLE `daily_surveys` DISABLE KEYS */;
INSERT INTO `daily_surveys` VALUES (1,1,'2025-06-01',1,8,7.5,9000,2000,450,8,'Great run this morning!','2025-06-02 00:00:00','2025-06-02 00:00:00'),(2,2,'2025-06-01',2,6,6.0,7500,2500,600,6,'Legs still sore from squats.','2025-06-02 00:00:00','2025-06-02 00:00:00'),(3,3,'2025-06-01',1,9,8.0,11000,1800,300,9,'Feeling amazing today.','2025-06-02 00:00:00','2025-06-02 00:00:00'),(4,4,'2025-06-01',3,5,5.5,6000,2200,500,5,'Tired but pushed through.','2025-06-02 00:00:00','2025-06-02 00:00:00'),(5,5,'2025-06-01',2,7,7.0,8000,1700,380,7,'Yoga session was relaxing.','2025-06-02 00:00:00','2025-06-02 00:00:00'),(6,6,'2025-06-01',4,3,4.5,4000,2800,400,4,'Rough day, skipped workout.','2025-06-02 00:00:00','2025-06-02 00:00:00'),(7,7,'2025-06-01',1,10,9.0,13000,1600,350,10,'Personal best on 5k today!','2025-06-02 00:00:00','2025-06-02 00:00:00'),(8,8,'2025-06-01',2,7,6.5,8500,3000,700,7,'Heavy deadlift day.','2025-06-02 00:00:00','2025-06-02 00:00:00'),(9,9,'2025-06-01',3,6,7.0,7000,1900,420,6,'Steady progress on nutrition.','2025-06-02 00:00:00','2025-06-02 00:00:00'),(10,10,'2025-06-01',2,8,8.0,10000,2100,550,8,'Good HIIT session.','2025-06-02 00:00:00','2025-06-02 00:00:00');
/*!40000 ALTER TABLE `daily_surveys` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_daily_surveys_audit_insert` AFTER INSERT ON `daily_surveys` FOR EACH ROW BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, new_values)
    VALUES ('Daily_Surveys', NEW.survey_id, 'INSERT', @current_user_id,
        JSON_OBJECT(
            'user_id',         NEW.user_id,
            'survey_date',     NEW.survey_date,
            'mood_type_id',    NEW.mood_type_id,
            'energy_level',    NEW.energy_level,
            'sleep_hours',     NEW.sleep_hours,
            'step_count',      NEW.step_count,
            'calories_intake', NEW.calories_intake,
            'calories_burned', NEW.calories_burned,
            'water_intake',    NEW.water_intake
        ));
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_daily_surveys_last_updated` BEFORE UPDATE ON `daily_surveys` FOR EACH ROW SET NEW.last_updated = NOW() */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_daily_surveys_audit_update` AFTER UPDATE ON `daily_surveys` FOR EACH ROW BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, old_values, new_values)
    VALUES ('Daily_Surveys', NEW.survey_id, 'UPDATE', @current_user_id,
        JSON_OBJECT(
            'mood_type_id',    OLD.mood_type_id,
            'energy_level',    OLD.energy_level,
            'sleep_hours',     OLD.sleep_hours,
            'step_count',      OLD.step_count,
            'calories_intake', OLD.calories_intake,
            'calories_burned', OLD.calories_burned,
            'water_intake',    OLD.water_intake
        ),
        JSON_OBJECT(
            'mood_type_id',    NEW.mood_type_id,
            'energy_level',    NEW.energy_level,
            'sleep_hours',     NEW.sleep_hours,
            'step_count',      NEW.step_count,
            'calories_intake', NEW.calories_intake,
            'calories_burned', NEW.calories_burned,
            'water_intake',    NEW.water_intake
        ));
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_daily_surveys_audit_delete` AFTER DELETE ON `daily_surveys` FOR EACH ROW BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, old_values)
    VALUES ('Daily_Surveys', OLD.survey_id, 'DELETE', @current_user_id,
        JSON_OBJECT('user_id', OLD.user_id, 'survey_date', OLD.survey_date));
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `exercise_categories`
--

DROP TABLE IF EXISTS `exercise_categories`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `exercise_categories` (
  `category_id` int NOT NULL AUTO_INCREMENT,
  `category_name` varchar(50) NOT NULL,
  PRIMARY KEY (`category_id`),
  UNIQUE KEY `category_name` (`category_name`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `exercise_categories`
--

LOCK TABLES `exercise_categories` WRITE;
/*!40000 ALTER TABLE `exercise_categories` DISABLE KEYS */;
INSERT INTO `exercise_categories` VALUES (2,'Cardio'),(3,'Flexibility'),(1,'Strength');
/*!40000 ALTER TABLE `exercise_categories` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `exercise_muscles`
--

DROP TABLE IF EXISTS `exercise_muscles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `exercise_muscles` (
  `exercise_id` int NOT NULL,
  `muscle_group_id` int NOT NULL,
  PRIMARY KEY (`exercise_id`,`muscle_group_id`),
  KEY `fk_exercise_muscles_muscle_group` (`muscle_group_id`),
  CONSTRAINT `fk_exercise_muscles_exercise` FOREIGN KEY (`exercise_id`) REFERENCES `exercises` (`exercise_id`) ON DELETE CASCADE,
  CONSTRAINT `fk_exercise_muscles_muscle_group` FOREIGN KEY (`muscle_group_id`) REFERENCES `muscle_groups` (`muscle_group_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `exercise_muscles`
--

LOCK TABLES `exercise_muscles` WRITE;
/*!40000 ALTER TABLE `exercise_muscles` DISABLE KEYS */;
INSERT INTO `exercise_muscles` VALUES (2,1),(5,1),(3,2),(4,2),(4,4),(2,6),(1,8),(1,9),(6,9),(3,10);
/*!40000 ALTER TABLE `exercise_muscles` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `exercises`
--

DROP TABLE IF EXISTS `exercises`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `exercises` (
  `exercise_id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `category_id` int NOT NULL,
  `experience_level_id` int DEFAULT NULL,
  `equipment` varchar(255) DEFAULT NULL,
  `instructions` text,
  `tips` text,
  `image_url` text,
  `video_url` text,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `last_updated` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`exercise_id`),
  KEY `fk_exercises_category` (`category_id`),
  KEY `fk_exercises_experience_level` (`experience_level_id`),
  CONSTRAINT `fk_exercises_category` FOREIGN KEY (`category_id`) REFERENCES `exercise_categories` (`category_id`),
  CONSTRAINT `fk_exercises_experience_level` FOREIGN KEY (`experience_level_id`) REFERENCES `experience_levels` (`experience_level_id`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `exercises`
--

LOCK TABLES `exercises` WRITE;
/*!40000 ALTER TABLE `exercises` DISABLE KEYS */;
INSERT INTO `exercises` VALUES (1,'Barbell Back Squat',1,2,'Barbell, Squat Rack','Stand with bar across upper back. Squat until thighs are parallel. Drive up through heels.','Keep chest up and knees tracking over toes.',NULL,NULL,'2025-01-01 05:00:00','2025-01-01 05:00:00'),(2,'Bench Press',1,2,'Barbell, Bench','Lie on bench, lower bar to chest, press up fully.','Retract shoulder blades throughout the lift.',NULL,NULL,'2025-01-01 05:00:00','2025-01-01 05:00:00'),(3,'Deadlift',1,3,'Barbell','Hinge at hips, grip bar, drive hips forward to stand.','Keep back flat and bar close to body.',NULL,NULL,'2025-01-01 05:00:00','2025-01-01 05:00:00'),(4,'Pull-Up',1,2,'Pull-Up Bar','Hang from bar, pull chest to bar, lower slowly.','Engage core and avoid swinging.',NULL,NULL,'2025-01-01 05:00:00','2025-01-01 05:00:00'),(5,'Push-Up',1,1,'None','Start in plank. Lower chest to floor, press back up.','Keep body in a straight line.',NULL,NULL,'2025-01-01 05:00:00','2025-01-01 05:00:00'),(6,'Running',2,1,'None','Maintain steady pace. Land midfoot.','Stay hydrated and keep cadence above 160 spm.',NULL,NULL,'2025-01-01 05:00:00','2025-01-01 05:00:00'),(7,'Cycling',2,1,'Bike or Stationary','Pedal at consistent resistance for target duration.','Adjust seat so leg is nearly straight at bottom.',NULL,NULL,'2025-01-01 05:00:00','2025-01-01 05:00:00'),(8,'Jump Rope',2,2,'Jump Rope','Jump with both feet, turning rope with wrists.','Keep jumps low to conserve energy.',NULL,NULL,'2025-01-01 05:00:00','2025-01-01 05:00:00'),(9,'Downward Dog',3,1,'Yoga Mat','From plank, push hips up forming an inverted V.','Press heels toward the ground.',NULL,NULL,'2025-01-01 05:00:00','2025-01-01 05:00:00'),(10,'Hip Flexor Stretch',3,1,'None','Lunge forward, lower back knee to ground, push hips forward.','Hold 30 seconds each side.',NULL,NULL,'2025-01-01 05:00:00','2025-01-01 05:00:00');
/*!40000 ALTER TABLE `exercises` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_exercises_audit_insert` AFTER INSERT ON `exercises` FOR EACH ROW BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, new_values)
    VALUES ('Exercises', NEW.exercise_id, 'INSERT', @current_user_id,
        JSON_OBJECT('name', NEW.name, 'category_id', NEW.category_id, 'experience_level_id', NEW.experience_level_id));
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_exercises_last_updated` BEFORE UPDATE ON `exercises` FOR EACH ROW SET NEW.last_updated = NOW() */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_exercises_audit_update` AFTER UPDATE ON `exercises` FOR EACH ROW BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, old_values, new_values)
    VALUES ('Exercises', NEW.exercise_id, 'UPDATE', @current_user_id,
        JSON_OBJECT('name', OLD.name, 'category_id', OLD.category_id, 'experience_level_id', OLD.experience_level_id),
        JSON_OBJECT('name', NEW.name, 'category_id', NEW.category_id, 'experience_level_id', NEW.experience_level_id));
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_exercises_audit_delete` AFTER DELETE ON `exercises` FOR EACH ROW BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, old_values)
    VALUES ('Exercises', OLD.exercise_id, 'DELETE', @current_user_id,
        JSON_OBJECT('name', OLD.name));
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `experience_levels`
--

DROP TABLE IF EXISTS `experience_levels`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `experience_levels` (
  `experience_level_id` int NOT NULL AUTO_INCREMENT,
  `experience_level_name` varchar(50) NOT NULL,
  PRIMARY KEY (`experience_level_id`),
  UNIQUE KEY `experience_level_name` (`experience_level_name`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `experience_levels`
--

LOCK TABLES `experience_levels` WRITE;
/*!40000 ALTER TABLE `experience_levels` DISABLE KEYS */;
INSERT INTO `experience_levels` VALUES (3,'Advanced'),(1,'Beginner'),(2,'Intermediate');
/*!40000 ALTER TABLE `experience_levels` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `goal_types`
--

DROP TABLE IF EXISTS `goal_types`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `goal_types` (
  `goal_type_id` int NOT NULL AUTO_INCREMENT,
  `goal_type_name` varchar(50) NOT NULL,
  PRIMARY KEY (`goal_type_id`),
  UNIQUE KEY `goal_type_name` (`goal_type_name`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `goal_types`
--

LOCK TABLES `goal_types` WRITE;
/*!40000 ALTER TABLE `goal_types` DISABLE KEYS */;
INSERT INTO `goal_types` VALUES (2,'Build Muscle'),(3,'Improve Endurance'),(1,'Lose Weight'),(5,'Other'),(4,'Stay Healthy');
/*!40000 ALTER TABLE `goal_types` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `goals`
--

DROP TABLE IF EXISTS `goals`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `goals` (
  `goal_id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `goal_type_id` int NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `last_updated` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`goal_id`),
  KEY `fk_goals_user` (`user_id`),
  KEY `fk_goals_goal_type` (`goal_type_id`),
  CONSTRAINT `fk_goals_goal_type` FOREIGN KEY (`goal_type_id`) REFERENCES `goal_types` (`goal_type_id`),
  CONSTRAINT `fk_goals_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `goals`
--

LOCK TABLES `goals` WRITE;
/*!40000 ALTER TABLE `goals` DISABLE KEYS */;
INSERT INTO `goals` VALUES (1,1,1,'2025-01-10 13:10:00','2025-01-10 13:10:00'),(2,2,2,'2025-01-15 14:40:00','2025-01-15 14:40:00'),(3,3,4,'2025-02-01 15:10:00','2025-02-01 15:10:00'),(4,4,2,'2025-02-10 16:10:00','2025-02-10 16:10:00'),(5,5,1,'2025-03-05 12:55:00','2025-03-05 12:55:00'),(6,6,3,'2025-03-20 18:10:00','2025-03-20 18:10:00'),(7,7,4,'2025-04-01 13:10:00','2025-04-01 13:10:00'),(8,8,2,'2025-04-15 17:40:00','2025-04-15 17:40:00'),(9,9,1,'2025-05-01 12:25:00','2025-05-01 12:25:00'),(10,10,3,'2025-05-20 14:55:00','2025-05-20 14:55:00');
/*!40000 ALTER TABLE `goals` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_goals_audit_insert` AFTER INSERT ON `goals` FOR EACH ROW BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, new_values)
    VALUES ('Goals', NEW.goal_id, 'INSERT', @current_user_id,
        JSON_OBJECT('user_id', NEW.user_id, 'goal_type_id', NEW.goal_type_id));
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_goals_last_updated` BEFORE UPDATE ON `goals` FOR EACH ROW SET NEW.last_updated = NOW() */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_goals_audit_delete` AFTER DELETE ON `goals` FOR EACH ROW BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, old_values)
    VALUES ('Goals', OLD.goal_id, 'DELETE', @current_user_id,
        JSON_OBJECT('user_id', OLD.user_id, 'goal_type_id', OLD.goal_type_id));
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `mood_types`
--

DROP TABLE IF EXISTS `mood_types`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `mood_types` (
  `mood_type_id` int NOT NULL AUTO_INCREMENT,
  `mood_type_name` varchar(20) NOT NULL,
  PRIMARY KEY (`mood_type_id`),
  UNIQUE KEY `mood_type_name` (`mood_type_name`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `mood_types`
--

LOCK TABLES `mood_types` WRITE;
/*!40000 ALTER TABLE `mood_types` DISABLE KEYS */;
INSERT INTO `mood_types` VALUES (2,'Good'),(1,'Great'),(4,'Low'),(3,'Okay');
/*!40000 ALTER TABLE `mood_types` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `muscle_groups`
--

DROP TABLE IF EXISTS `muscle_groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `muscle_groups` (
  `muscle_group_id` int NOT NULL AUTO_INCREMENT,
  `muscle_group_name` varchar(100) NOT NULL,
  PRIMARY KEY (`muscle_group_id`),
  UNIQUE KEY `muscle_group_name` (`muscle_group_name`)
) ENGINE=InnoDB AUTO_INCREMENT=14 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `muscle_groups`
--

LOCK TABLES `muscle_groups` WRITE;
/*!40000 ALTER TABLE `muscle_groups` DISABLE KEYS */;
INSERT INTO `muscle_groups` VALUES (2,'Back'),(4,'Biceps'),(11,'Calves'),(1,'Chest'),(7,'Core'),(6,'Forearms'),(13,'Full Body'),(8,'Glutes'),(10,'Hamstrings'),(12,'Hip Flexors'),(9,'Quads'),(3,'Shoulders'),(5,'Triceps');
/*!40000 ALTER TABLE `muscle_groups` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `notebook`
--

DROP TABLE IF EXISTS `notebook`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `notebook` (
  `note_id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `content` text,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `last_updated` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`note_id`),
  KEY `fk_notebook_user` (`user_id`),
  CONSTRAINT `fk_notebook_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `notebook`
--

LOCK TABLES `notebook` WRITE;
/*!40000 ALTER TABLE `notebook` DISABLE KEYS */;
INSERT INTO `notebook` VALUES (1,1,'Today I completed my first 5k run without stopping. Big milestone!','2025-06-02 01:00:00','2025-06-02 01:00:00'),(2,2,'New squat PR: 225 lbs. Next goal is 250.','2025-06-02 01:00:00','2025-06-02 01:00:00'),(3,3,'Tried meal prepping for the first time. Makes tracking calories so easy.','2025-06-02 01:00:00','2025-06-02 01:00:00'),(4,4,'Rest day today. Stretched for 30 minutes. Body needed it.','2025-06-02 01:00:00','2025-06-02 01:00:00'),(5,5,'Down 3 lbs this month. Slow and steady.','2025-06-02 01:00:00','2025-06-02 01:00:00'),(6,6,'Struggled today but finished the workout. Proud of not quitting.','2025-06-02 01:00:00','2025-06-02 01:00:00'),(7,7,'Week 6 done! Feeling stronger and more confident.','2025-06-02 01:00:00','2025-06-02 01:00:00'),(8,8,'Coach increased my volume today. My back is pumped.','2025-06-02 01:00:00','2025-06-02 01:00:00'),(9,9,'Focused on breathing during yoga today. Felt very centered.','2025-06-02 01:00:00','2025-06-02 01:00:00'),(10,10,'HIIT session was brutal but the endorphins after are unmatched.','2025-06-02 01:00:00','2025-06-02 01:00:00');
/*!40000 ALTER TABLE `notebook` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `notifications`
--

DROP TABLE IF EXISTS `notifications`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `notifications` (
  `notification_id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `message` text NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `last_updated` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`notification_id`),
  KEY `fk_notifications_user` (`user_id`),
  CONSTRAINT `fk_notifications_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `notifications`
--

LOCK TABLES `notifications` WRITE;
/*!40000 ALTER TABLE `notifications` DISABLE KEYS */;
INSERT INTO `notifications` VALUES (1,1,'Your workout for today has been scheduled.','2025-06-01 11:00:00','2025-06-01 11:00:00'),(2,2,'Karen left feedback on your last session.','2025-06-01 11:05:00','2025-06-01 11:05:00'),(3,3,'Great job hitting your weekly streak!','2025-06-01 11:10:00','2025-06-01 11:10:00'),(4,4,'New workout assigned by your coach.','2025-06-01 11:15:00','2025-06-01 11:15:00'),(5,5,'Reminder: log your meals today.','2025-06-01 11:20:00','2025-06-01 11:20:00'),(6,6,'Your coach has updated your workout plan.','2025-06-01 11:25:00','2025-06-01 11:25:00'),(7,7,'New message from Coach Karen.','2025-06-01 11:30:00','2025-06-01 11:30:00'),(8,8,'Payment of $180 processed successfully.','2025-06-01 11:35:00','2025-06-01 11:35:00'),(9,9,'Do not forget to complete your daily survey!','2025-06-01 11:40:00','2025-06-01 11:40:00'),(10,10,'You have a session scheduled for tomorrow at 9 AM.','2025-06-01 11:45:00','2025-06-01 11:45:00');
/*!40000 ALTER TABLE `notifications` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `reports`
--

DROP TABLE IF EXISTS `reports`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `reports` (
  `report_id` int NOT NULL AUTO_INCREMENT,
  `reporter_id` int NOT NULL,
  `coach_id` int NOT NULL,
  `reason` text,
  `status` varchar(50) DEFAULT 'Pending',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `last_updated` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`report_id`),
  KEY `fk_reports_reporter` (`reporter_id`),
  KEY `fk_reports_coach` (`coach_id`),
  CONSTRAINT `fk_reports_coach` FOREIGN KEY (`coach_id`) REFERENCES `coaches` (`coach_id`) ON DELETE CASCADE,
  CONSTRAINT `fk_reports_reporter` FOREIGN KEY (`reporter_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `reports`
--

LOCK TABLES `reports` WRITE;
/*!40000 ALTER TABLE `reports` DISABLE KEYS */;
INSERT INTO `reports` VALUES (1,1,4,'Coach was frequently late to scheduled sessions.','Resolved','2025-05-01 14:00:00','2025-05-01 14:00:00'),(2,4,2,'Coach shared my personal progress data without consent.','Pending','2025-05-10 15:00:00','2025-05-10 15:00:00'),(3,6,4,'Session was cancelled last minute with no notice.','Resolved','2025-04-20 13:00:00','2025-05-01 16:00:00');
/*!40000 ALTER TABLE `reports` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `reviews`
--

DROP TABLE IF EXISTS `reviews`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `reviews` (
  `review_id` int NOT NULL AUTO_INCREMENT,
  `client_id` int NOT NULL,
  `coach_id` int NOT NULL,
  `description` text,
  `rating` tinyint NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `last_updated` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`review_id`),
  KEY `fk_reviews_client` (`client_id`),
  KEY `fk_reviews_coach` (`coach_id`),
  CONSTRAINT `fk_reviews_client` FOREIGN KEY (`client_id`) REFERENCES `clients` (`client_id`) ON DELETE CASCADE,
  CONSTRAINT `fk_reviews_coach` FOREIGN KEY (`coach_id`) REFERENCES `coaches` (`coach_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `reviews`
--

LOCK TABLES `reviews` WRITE;
/*!40000 ALTER TABLE `reviews` DISABLE KEYS */;
INSERT INTO `reviews` VALUES (1,1,1,'Karen is fantastic! Lost 8 lbs in 6 weeks.',5,'2025-04-01 14:00:00','2025-04-01 14:00:00'),(2,2,1,'Great programming. Could communicate more proactively.',4,'2025-04-05 15:00:00','2025-04-05 15:00:00'),(3,3,2,'Liam pushes you to your limits in the best way.',5,'2025-04-10 16:00:00','2025-04-10 16:00:00'),(4,4,2,'Good coach but sessions run long sometimes.',4,'2025-04-15 17:00:00','2025-04-15 17:00:00'),(5,5,3,'Mia completely changed my relationship with fitness.',5,'2025-05-01 13:00:00','2025-05-01 13:00:00'),(6,6,3,'Very knowledgeable on nutrition. Highly recommend.',5,'2025-05-05 14:00:00','2025-05-05 14:00:00'),(7,7,1,'Workouts are fun and effective.',5,'2025-05-10 15:00:00','2025-05-10 15:00:00'),(8,8,2,'Excellent strength programming. PRs every month!',5,'2025-05-15 16:00:00','2025-05-15 16:00:00'),(9,9,3,'Mia helped me recover from a plateau. Very supportive.',4,'2025-06-01 13:00:00','2025-06-01 13:00:00'),(10,10,1,'Solid coach. Would love more flexibility options.',4,'2025-06-05 14:00:00','2025-06-05 14:00:00');
/*!40000 ALTER TABLE `reviews` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `saved_workouts`
--

DROP TABLE IF EXISTS `saved_workouts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `saved_workouts` (
  `user_id` int NOT NULL,
  `workout_id` int NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`user_id`,`workout_id`),
  KEY `fk_saved_workouts_workout` (`workout_id`),
  CONSTRAINT `fk_saved_workouts_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE,
  CONSTRAINT `fk_saved_workouts_workout` FOREIGN KEY (`workout_id`) REFERENCES `workouts` (`workout_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `saved_workouts`
--

LOCK TABLES `saved_workouts` WRITE;
/*!40000 ALTER TABLE `saved_workouts` DISABLE KEYS */;
INSERT INTO `saved_workouts` VALUES (1,1,'2025-02-01 14:20:00'),(2,2,'2025-02-05 15:20:00'),(3,3,'2025-02-10 16:20:00'),(4,4,'2025-02-15 17:20:00'),(5,5,'2025-03-01 13:20:00'),(6,6,'2025-03-05 14:20:00'),(7,7,'2025-03-10 14:20:00'),(8,8,'2025-03-15 15:20:00'),(9,9,'2025-04-01 12:20:00'),(10,10,'2025-04-10 13:20:00');
/*!40000 ALTER TABLE `saved_workouts` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_saved_workouts_audit_insert` AFTER INSERT ON `saved_workouts` FOR EACH ROW BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, new_values)
    VALUES ('Saved_Workouts', NEW.workout_id, 'INSERT', @current_user_id,
        JSON_OBJECT('user_id', NEW.user_id, 'workout_id', NEW.workout_id));
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_saved_workouts_audit_delete` AFTER DELETE ON `saved_workouts` FOR EACH ROW BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, old_values)
    VALUES ('Saved_Workouts', OLD.workout_id, 'DELETE', @current_user_id,
        JSON_OBJECT('user_id', OLD.user_id, 'workout_id', OLD.workout_id));
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `scheduled_workout`
--

DROP TABLE IF EXISTS `scheduled_workout`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `scheduled_workout` (
  `user_id` int NOT NULL,
  `workout_id` int NOT NULL,
  `scheduled_date` date NOT NULL,
  `status` varchar(50) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `last_updated` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`user_id`,`workout_id`,`scheduled_date`),
  KEY `fk_scheduled_workout` (`workout_id`),
  CONSTRAINT `fk_scheduled_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE,
  CONSTRAINT `fk_scheduled_workout` FOREIGN KEY (`workout_id`) REFERENCES `workouts` (`workout_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `scheduled_workout`
--

LOCK TABLES `scheduled_workout` WRITE;
/*!40000 ALTER TABLE `scheduled_workout` DISABLE KEYS */;
INSERT INTO `scheduled_workout` VALUES (1,1,'2025-06-03','Upcoming','2025-06-01 13:00:00','2025-06-01 13:00:00'),(2,2,'2025-06-04','Upcoming','2025-06-01 13:00:00','2025-06-01 13:00:00'),(3,3,'2025-06-05','Upcoming','2025-06-01 13:00:00','2025-06-01 13:00:00'),(4,4,'2025-06-06','Upcoming','2025-06-01 13:00:00','2025-06-01 13:00:00'),(5,5,'2025-06-07','Upcoming','2025-06-01 13:00:00','2025-06-01 13:00:00'),(6,6,'2025-06-03','Upcoming','2025-06-01 13:00:00','2025-06-01 13:00:00'),(7,7,'2025-06-04','Upcoming','2025-06-01 13:00:00','2025-06-01 13:00:00'),(8,8,'2025-06-05','Upcoming','2025-06-01 13:00:00','2025-06-01 13:00:00'),(9,9,'2025-06-06','Upcoming','2025-06-01 13:00:00','2025-06-01 13:00:00'),(10,10,'2025-06-07','Upcoming','2025-06-01 13:00:00','2025-06-01 13:00:00');
/*!40000 ALTER TABLE `scheduled_workout` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `session_formats`
--

DROP TABLE IF EXISTS `session_formats`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `session_formats` (
  `session_format_id` int NOT NULL AUTO_INCREMENT,
  `session_format_name` varchar(50) NOT NULL,
  PRIMARY KEY (`session_format_id`),
  UNIQUE KEY `session_format_name` (`session_format_name`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `session_formats`
--

LOCK TABLES `session_formats` WRITE;
/*!40000 ALTER TABLE `session_formats` DISABLE KEYS */;
INSERT INTO `session_formats` VALUES (3,'Both'),(2,'In-Person'),(1,'Virtual');
/*!40000 ALTER TABLE `session_formats` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `set_results`
--

DROP TABLE IF EXISTS `set_results`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `set_results` (
  `set_results_id` int NOT NULL AUTO_INCREMENT,
  `workout_log_id` int NOT NULL,
  `actual_weight` decimal(8,2) DEFAULT NULL,
  `actual_value` decimal(8,2) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `last_updated` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`set_results_id`),
  KEY `fk_set_results_workout_log` (`workout_log_id`),
  CONSTRAINT `fk_set_results_workout_log` FOREIGN KEY (`workout_log_id`) REFERENCES `workout_logs` (`workout_log_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `set_results`
--

LOCK TABLES `set_results` WRITE;
/*!40000 ALTER TABLE `set_results` DISABLE KEYS */;
INSERT INTO `set_results` VALUES (1,1,NULL,12.00,'2025-02-08 13:10:00','2025-02-08 13:10:00'),(2,1,NULL,10.00,'2025-02-08 13:15:00','2025-02-08 13:15:00'),(3,2,NULL,11.00,'2025-02-15 13:10:00','2025-02-15 13:10:00'),(4,3,60.00,10.00,'2025-02-12 15:10:00','2025-02-12 15:10:00'),(5,4,NULL,28.00,'2025-02-17 16:10:00','2025-02-17 16:10:00'),(6,5,80.00,5.00,'2025-02-20 17:10:00','2025-02-20 17:10:00'),(7,6,NULL,30.00,'2025-03-05 13:10:00','2025-03-05 13:10:00'),(8,7,NULL,55.00,'2025-03-10 13:10:00','2025-03-10 13:10:00'),(9,8,100.00,3.00,'2025-03-20 15:10:00','2025-03-20 15:10:00'),(10,9,NULL,30.00,'2025-04-05 12:10:00','2025-04-05 12:10:00');
/*!40000 ALTER TABLE `set_results` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_set_results_audit_insert` AFTER INSERT ON `set_results` FOR EACH ROW BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, new_values)
    VALUES ('Set_Results', NEW.set_results_id, 'INSERT', @current_user_id,
        JSON_OBJECT('workout_log_id', NEW.workout_log_id, 'actual_weight', NEW.actual_weight, 'actual_value', NEW.actual_value));
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_set_results_last_updated` BEFORE UPDATE ON `set_results` FOR EACH ROW SET NEW.last_updated = NOW() */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_set_results_audit_update` AFTER UPDATE ON `set_results` FOR EACH ROW BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, old_values, new_values)
    VALUES ('Set_Results', NEW.set_results_id, 'UPDATE', @current_user_id,
        JSON_OBJECT('actual_weight', OLD.actual_weight, 'actual_value', OLD.actual_value),
        JSON_OBJECT('actual_weight', NEW.actual_weight, 'actual_value', NEW.actual_value));
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `units`
--

DROP TABLE IF EXISTS `units`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `units` (
  `unit_id` int NOT NULL AUTO_INCREMENT,
  `unit_name` varchar(50) NOT NULL,
  PRIMARY KEY (`unit_id`),
  UNIQUE KEY `unit_name` (`unit_name`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `units`
--

LOCK TABLES `units` WRITE;
/*!40000 ALTER TABLE `units` DISABLE KEYS */;
INSERT INTO `units` VALUES (2,'hrs'),(6,'km'),(7,'lb'),(5,'m'),(4,'mi'),(3,'mins'),(1,'reps');
/*!40000 ALTER TABLE `units` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `user_id` int NOT NULL AUTO_INCREMENT,
  `auth0_sub` varchar(128) NOT NULL,
  `email` varchar(255) NOT NULL,
  `first_name` varchar(100) DEFAULT NULL,
  `last_name` varchar(100) DEFAULT NULL,
  `profile_picture` text,
  `role` varchar(50) NOT NULL DEFAULT 'client',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `last_updated` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`user_id`),
  UNIQUE KEY `auth0_sub` (`auth0_sub`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=36 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES (1,'auth0|69c858482adfb474a6b2d3f6','alice.johnson@hotmail.com','Alice','Johnson','https://s.gravatar.com/avatar/fa725a68b7a7285a36f6918e956b02b2?s=480&r=pg&d=https%3A%2F%2Fcdn.auth0.com%2Favatars%2Fal.png','client','2025-01-10 13:00:00','2026-04-09 23:49:54'),(2,'auth0|69c859b92adfb474a6b2d4f0','bob.smith@gmail.com','Bob','Smith',NULL,'client','2025-01-15 14:30:00','2026-03-28 23:00:35'),(3,'auth0|69c85aa1e101a5198546d978','carol.white@yahoo.com','Carol','White',NULL,'client','2025-02-01 15:00:00','2026-03-28 22:48:52'),(4,'auth0|69c85df08d65c67e70e9d4ed','david.brown@yahoo.com','David','Brown',NULL,'client','2025-02-10 16:00:00','2026-03-28 23:04:00'),(5,'auth0|69c85e980f5387a1051ead8c','eva.martinez@gmail.com','Eva','Martinez',NULL,'client','2025-03-05 12:45:00','2026-03-28 23:05:22'),(6,'auth0|69c85eeb8d65c67e70e9d57a','franklee@outlook.com','Frank','Lee',NULL,'client','2025-03-20 18:00:00','2026-03-28 23:06:52'),(7,'auth0|69c85f452adfb474a6b2d7fd','grace82@outlook.com','Grace','Kim',NULL,'client','2025-04-01 13:00:00','2026-03-28 23:08:32'),(8,'auth0|69c868cd8d65c67e70e9da71','henry.nguyen@gmail.com','Henry','Nguyen',NULL,'client','2025-04-15 17:30:00','2026-03-28 23:49:03'),(9,'auth0|69c869320f5387a1051eb328','isabella.clark@gmail.com','Isabella','Clark',NULL,'client','2025-05-01 12:15:00','2026-03-28 23:50:52'),(10,'auth0|69c869bd0f5387a1051eb372','james.wilson@outlook.com','James','Wilson',NULL,'client','2025-05-20 14:45:00','2026-03-28 23:53:15'),(11,'auth0|user011','karen.taylor@email.com','Karen','Taylor',NULL,'coach','2024-06-01 12:00:00','2024-06-01 12:00:00'),(12,'auth0|user012','liam.anderson@email.com','Liam','Anderson',NULL,'coach','2024-07-15 13:00:00','2024-07-15 13:00:00'),(13,'auth0|user013','mia.thompson@email.com','Mia','Thompson',NULL,'coach','2024-08-01 14:00:00','2024-08-01 14:00:00'),(14,'auth0|user014','noah.harris@email.com','Noah','Harris',NULL,'admin','2024-01-01 13:00:00','2024-01-01 13:00:00'),(15,'auth0|user015','olivia.martin@email.com','Olivia','Martin',NULL,'admin','2024-01-02 13:00:00','2024-01-02 13:00:00'),(16,'auth0|user016','derek.ross@email.com','Derek','Ross',NULL,'coach','2024-03-01 14:00:00','2025-04-15 04:00:00'),(17,'google-oauth2|112736608280708522873','annabeth6235@gmail.com','Cat','Morland','https://lh3.googleusercontent.com/a/ACg8ocJoa4xfHUwm5Taa9iDino2RKEhbcg8bOGvfiL9YzgkY3LWsHzg=s96-c','client','2026-03-27 23:31:11','2026-04-09 00:50:35'),(31,'auth0|69d7ef6dd13bd9b5b9bbc96e','Percy.Jackson@hotmail.com','Percy','Jackson',NULL,'coach','2026-04-09 22:26:55','2026-04-09 18:28:11'),(32,'auth0|69d7f5f82415db6d9b67ce71','amy.march@outlook.com','amy','march',NULL,'client','2026-04-09 22:54:49','2026-04-09 21:49:46'),(33,'auth0|69d83995bd96a3b53d2bb522','Jo.march@outlook.com','jo','march',NULL,'client','2026-04-10 03:43:19','2026-04-10 03:43:19'),(34,'auth0|69d83b3e7491f5682e15ae41','alice.march@hotmail.com','alice','march',NULL,'client','2026-04-10 03:50:24','2026-04-10 03:50:24'),(35,'auth0|69d83d71180913421e062387','tylerA@gmail.com','Tyler','Ambrozy',NULL,'client','2026-04-10 03:59:47','2026-04-10 00:00:41');
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_users_audit_insert` AFTER INSERT ON `users` FOR EACH ROW BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, new_values)
    VALUES ('Users', NEW.user_id, 'INSERT', @current_user_id,
        JSON_OBJECT('email', NEW.email, 'role', NEW.role, 'auth0_sub', NEW.auth0_sub));
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_users_last_updated` BEFORE UPDATE ON `users` FOR EACH ROW SET NEW.last_updated = NOW() */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_users_audit_update` AFTER UPDATE ON `users` FOR EACH ROW BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, old_values, new_values)
    VALUES ('Users', NEW.user_id, 'UPDATE', @current_user_id,
        JSON_OBJECT('email', OLD.email, 'role', OLD.role),
        JSON_OBJECT('email', NEW.email, 'role', NEW.role));
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_users_audit_delete` AFTER DELETE ON `users` FOR EACH ROW BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, old_values)
    VALUES ('Users', OLD.user_id, 'DELETE', @current_user_id,
        JSON_OBJECT('email', OLD.email, 'role', OLD.role, 'auth0_sub', OLD.auth0_sub));
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `weight_logs`
--

DROP TABLE IF EXISTS `weight_logs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `weight_logs` (
  `weight_log_id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `weight` int NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `last_updated` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`weight_log_id`),
  KEY `fk_weight_logs_user` (`user_id`),
  CONSTRAINT `fk_weight_logs_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `weight_logs`
--

LOCK TABLES `weight_logs` WRITE;
/*!40000 ALTER TABLE `weight_logs` DISABLE KEYS */;
INSERT INTO `weight_logs` VALUES (1,1,68000,'2025-01-10 13:00:00','2025-01-10 13:00:00'),(2,2,90000,'2025-01-15 14:00:00','2025-01-15 14:00:00'),(3,3,55000,'2025-02-01 15:00:00','2025-02-01 15:00:00'),(4,4,82000,'2025-02-10 16:00:00','2025-02-10 16:00:00'),(5,5,63000,'2025-03-05 13:00:00','2025-03-05 13:00:00'),(6,6,77000,'2025-03-20 18:00:00','2025-03-20 18:00:00'),(7,7,50000,'2025-04-01 13:00:00','2025-04-01 13:00:00'),(8,8,95000,'2025-04-15 17:00:00','2025-04-15 17:00:00'),(9,9,72000,'2025-05-01 12:00:00','2025-05-01 12:00:00'),(10,10,85000,'2025-05-20 14:00:00','2025-05-20 14:00:00');
/*!40000 ALTER TABLE `weight_logs` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_weight_logs_audit_insert` AFTER INSERT ON `weight_logs` FOR EACH ROW BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, new_values)
    VALUES ('Weight_Logs', NEW.weight_log_id, 'INSERT', @current_user_id,
        JSON_OBJECT('user_id', NEW.user_id, 'weight', NEW.weight));
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_weight_logs_last_updated` BEFORE UPDATE ON `weight_logs` FOR EACH ROW SET NEW.last_updated = NOW() */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_weight_logs_audit_delete` AFTER DELETE ON `weight_logs` FOR EACH ROW BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, old_values)
    VALUES ('Weight_Logs', OLD.weight_log_id, 'DELETE', @current_user_id,
        JSON_OBJECT('user_id', OLD.user_id, 'weight', OLD.weight));
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `workout_logs`
--

DROP TABLE IF EXISTS `workout_logs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `workout_logs` (
  `workout_log_id` int NOT NULL AUTO_INCREMENT,
  `workout_id` int NOT NULL,
  `client_id` int NOT NULL,
  `logged_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `last_updated` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`workout_log_id`),
  KEY `fk_workout_logs_workout` (`workout_id`),
  KEY `fk_workout_logs_client` (`client_id`),
  CONSTRAINT `fk_workout_logs_client` FOREIGN KEY (`client_id`) REFERENCES `clients` (`client_id`) ON DELETE CASCADE,
  CONSTRAINT `fk_workout_logs_workout` FOREIGN KEY (`workout_id`) REFERENCES `workouts` (`workout_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `workout_logs`
--

LOCK TABLES `workout_logs` WRITE;
/*!40000 ALTER TABLE `workout_logs` DISABLE KEYS */;
INSERT INTO `workout_logs` VALUES (1,1,1,'2025-02-08 13:00:00','2025-02-08 13:01:00','2025-02-08 13:01:00'),(2,1,1,'2025-02-15 13:00:00','2025-02-15 13:01:00','2025-02-15 13:01:00'),(3,2,2,'2025-02-12 15:00:00','2025-02-12 15:01:00','2025-02-12 15:01:00'),(4,3,3,'2025-02-17 16:00:00','2025-02-17 16:01:00','2025-02-17 16:01:00'),(5,4,4,'2025-02-20 17:00:00','2025-02-20 17:01:00','2025-02-20 17:01:00'),(6,5,5,'2025-03-05 13:00:00','2025-03-05 13:01:00','2025-03-05 13:01:00'),(7,6,6,'2025-03-10 13:00:00','2025-03-10 13:01:00','2025-03-10 13:01:00'),(8,8,8,'2025-03-20 15:00:00','2025-03-20 15:01:00','2025-03-20 15:01:00'),(9,9,9,'2025-04-05 12:00:00','2025-04-05 12:01:00','2025-04-05 12:01:00'),(10,10,10,'2025-04-15 13:00:00','2025-04-15 13:01:00','2025-04-15 13:01:00');
/*!40000 ALTER TABLE `workout_logs` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_workout_logs_audit_insert` AFTER INSERT ON `workout_logs` FOR EACH ROW BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, new_values)
    VALUES ('Workout_Logs', NEW.workout_log_id, 'INSERT', @current_user_id,
        JSON_OBJECT('workout_id', NEW.workout_id, 'client_id', NEW.client_id, 'logged_at', NEW.logged_at));
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_workout_logs_last_updated` BEFORE UPDATE ON `workout_logs` FOR EACH ROW SET NEW.last_updated = NOW() */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_workout_logs_audit_delete` AFTER DELETE ON `workout_logs` FOR EACH ROW BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, old_values)
    VALUES ('Workout_Logs', OLD.workout_log_id, 'DELETE', @current_user_id,
        JSON_OBJECT('workout_id', OLD.workout_id, 'client_id', OLD.client_id));
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `workout_plans`
--

DROP TABLE IF EXISTS `workout_plans`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `workout_plans` (
  `workout_id` int NOT NULL,
  `exercise_id` int NOT NULL,
  `sets` int DEFAULT NULL,
  `target_value` decimal(8,2) DEFAULT NULL,
  `unit_id` int NOT NULL,
  `order_in_workout` int DEFAULT NULL,
  `rest` int DEFAULT NULL,
  `weeks_completed` int NOT NULL DEFAULT '0',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `last_updated` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`workout_id`,`exercise_id`),
  KEY `fk_workout_plans_exercise` (`exercise_id`),
  KEY `fk_workout_plans_unit` (`unit_id`),
  CONSTRAINT `fk_workout_plans_exercise` FOREIGN KEY (`exercise_id`) REFERENCES `exercises` (`exercise_id`) ON DELETE CASCADE,
  CONSTRAINT `fk_workout_plans_unit` FOREIGN KEY (`unit_id`) REFERENCES `units` (`unit_id`),
  CONSTRAINT `fk_workout_plans_workout` FOREIGN KEY (`workout_id`) REFERENCES `workouts` (`workout_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `workout_plans`
--

LOCK TABLES `workout_plans` WRITE;
/*!40000 ALTER TABLE `workout_plans` DISABLE KEYS */;
INSERT INTO `workout_plans` VALUES (1,5,3,12.00,1,1,60,0,'2025-02-01 14:15:00','2025-02-01 14:15:00'),(1,6,1,20.00,3,2,90,0,'2025-02-01 14:15:00','2025-02-01 14:15:00'),(2,1,4,10.00,1,1,120,0,'2025-02-05 15:15:00','2025-02-05 15:15:00'),(2,2,4,10.00,1,2,120,0,'2025-02-05 15:15:00','2025-02-05 15:15:00'),(3,6,1,30.00,3,1,60,0,'2025-02-10 16:15:00','2025-02-10 16:15:00'),(4,3,5,5.00,1,1,180,0,'2025-02-15 17:15:00','2025-02-15 17:15:00'),(5,9,1,30.00,3,1,30,0,'2025-03-01 13:15:00','2025-03-01 13:15:00'),(6,8,5,60.00,3,1,90,0,'2025-03-05 14:15:00','2025-03-05 14:15:00'),(7,5,3,20.00,1,1,45,0,'2025-03-10 14:15:00','2025-03-10 14:15:00'),(8,3,6,3.00,1,1,240,0,'2025-03-15 15:15:00','2025-03-15 15:15:00');
/*!40000 ALTER TABLE `workout_plans` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_workout_plans_last_updated` BEFORE UPDATE ON `workout_plans` FOR EACH ROW SET NEW.last_updated = NOW() */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_workout_plans_audit_update` AFTER UPDATE ON `workout_plans` FOR EACH ROW BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, old_values, new_values)
    VALUES ('Workout_Plans', NEW.workout_id, 'UPDATE', @current_user_id,
        JSON_OBJECT('exercise_id', OLD.exercise_id, 'sets', OLD.sets, 'target_value', OLD.target_value, 'unit_id', OLD.unit_id, 'weeks_completed', OLD.weeks_completed),
        JSON_OBJECT('exercise_id', NEW.exercise_id, 'sets', NEW.sets, 'target_value', NEW.target_value, 'unit_id', NEW.unit_id, 'weeks_completed', NEW.weeks_completed));
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `workouts`
--

DROP TABLE IF EXISTS `workouts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `workouts` (
  `workout_id` int NOT NULL AUTO_INCREMENT,
  `creator_id` int NOT NULL,
  `assigned_to` int DEFAULT NULL,
  `name` varchar(255) NOT NULL,
  `status` varchar(20) DEFAULT 'Not Scheduled',
  `goal_type_id` int DEFAULT NULL,
  `experience_level_id` int DEFAULT NULL,
  `equipment_required` varchar(255) DEFAULT NULL,
  `workout_time_mins` int DEFAULT NULL,
  `intended_duration_weeks` int DEFAULT NULL,
  `image_url` text,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `last_updated` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`workout_id`),
  KEY `fk_workouts_creator` (`creator_id`),
  KEY `fk_workouts_assigned` (`assigned_to`),
  KEY `fk_workouts_goal_type` (`goal_type_id`),
  KEY `fk_workouts_experience_level` (`experience_level_id`),
  CONSTRAINT `fk_workouts_assigned` FOREIGN KEY (`assigned_to`) REFERENCES `users` (`user_id`),
  CONSTRAINT `fk_workouts_creator` FOREIGN KEY (`creator_id`) REFERENCES `users` (`user_id`),
  CONSTRAINT `fk_workouts_experience_level` FOREIGN KEY (`experience_level_id`) REFERENCES `experience_levels` (`experience_level_id`),
  CONSTRAINT `fk_workouts_goal_type` FOREIGN KEY (`goal_type_id`) REFERENCES `goal_types` (`goal_type_id`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `workouts`
--

LOCK TABLES `workouts` WRITE;
/*!40000 ALTER TABLE `workouts` DISABLE KEYS */;
INSERT INTO `workouts` VALUES (1,11,1,'Beginner Fat Burn','Scheduled',1,1,'None',30,8,NULL,'2025-02-01 14:10:00','2025-02-01 14:10:00'),(2,11,2,'Strength Foundation','Scheduled',2,2,'Barbell, Rack',60,12,NULL,'2025-02-05 15:10:00','2025-02-05 15:10:00'),(3,12,3,'Endurance Builder','Scheduled',3,1,'None',45,6,NULL,'2025-02-10 16:10:00','2025-02-10 16:10:00'),(4,12,4,'Muscle Hypertrophy','Scheduled',2,3,'Barbell, Dumbbells',75,16,NULL,'2025-02-15 17:10:00','2025-02-15 17:10:00'),(5,13,5,'Flexibility & Wellness','Scheduled',4,1,'Yoga Mat',40,4,NULL,'2025-03-01 13:10:00','2025-03-01 13:10:00'),(6,13,6,'Cardio Conditioning','Scheduled',3,2,'Jump Rope',50,8,NULL,'2025-03-05 14:10:00','2025-03-05 14:10:00'),(7,11,7,'Core & Stability','Not Scheduled',4,1,'None',25,6,NULL,'2025-03-10 14:10:00','2025-03-10 14:10:00'),(8,12,8,'Power & Explosiveness','Scheduled',2,3,'Barbell, Bumper Plates',70,12,NULL,'2025-03-15 15:10:00','2025-03-15 15:10:00'),(9,13,9,'Nutrition & Mobility','Scheduled',1,1,'Yoga Mat',35,8,NULL,'2025-04-01 12:10:00','2025-04-01 12:10:00'),(10,11,10,'Full Body HIIT','Scheduled',3,2,'None',40,6,NULL,'2025-04-10 13:10:00','2025-04-10 13:10:00');
/*!40000 ALTER TABLE `workouts` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_workouts_audit_insert` AFTER INSERT ON `workouts` FOR EACH ROW BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, new_values)
    VALUES ('Workouts', NEW.workout_id, 'INSERT', @current_user_id,
        JSON_OBJECT(
            'name',                    NEW.name,
            'status',                  NEW.status,
            'creator_id',              NEW.creator_id,
            'goal_type_id',            NEW.goal_type_id,
            'experience_level_id',     NEW.experience_level_id,
            'equipment_required',      NEW.equipment_required,
            'workout_time_mins',       NEW.workout_time_mins,
            'intended_duration_weeks', NEW.intended_duration_weeks,
            'image_url',               NEW.image_url
        ));
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_workouts_last_updated` BEFORE UPDATE ON `workouts` FOR EACH ROW SET NEW.last_updated = NOW() */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_workouts_audit_update` AFTER UPDATE ON `workouts` FOR EACH ROW BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, old_values, new_values)
    VALUES ('Workouts', NEW.workout_id, 'UPDATE', @current_user_id,
        JSON_OBJECT(
            'name',                    OLD.name,
            'status',                  OLD.status,
            'goal_type_id',            OLD.goal_type_id,
            'experience_level_id',     OLD.experience_level_id,
            'equipment_required',      OLD.equipment_required,
            'workout_time_mins',       OLD.workout_time_mins,
            'intended_duration_weeks', OLD.intended_duration_weeks,
            'image_url',               OLD.image_url
        ),
        JSON_OBJECT(
            'name',                    NEW.name,
            'status',                  NEW.status,
            'goal_type_id',            NEW.goal_type_id,
            'experience_level_id',     NEW.experience_level_id,
            'equipment_required',      NEW.equipment_required,
            'workout_time_mins',       NEW.workout_time_mins,
            'intended_duration_weeks', NEW.intended_duration_weeks,
            'image_url',               NEW.image_url
        ));
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_workouts_audit_delete` AFTER DELETE ON `workouts` FOR EACH ROW BEGIN
    INSERT INTO Audit_Log (table_name, record_id, action, changed_by, old_values)
    VALUES ('Workouts', OLD.workout_id, 'DELETE', @current_user_id,
        JSON_OBJECT('name', OLD.name, 'creator_id', OLD.creator_id));
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-04-10 14:53:08
