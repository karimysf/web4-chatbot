-- MySQL dump 10.13  Distrib 8.0.42, for Linux (x86_64)
--
-- Host: localhost    Database: PlateformeFormation
-- ------------------------------------------------------
-- Server version	8.0.42-0ubuntu0.24.04.1

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
-- Table structure for table `Administrateur`
--

DROP TABLE IF EXISTS `Administrateur`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `Administrateur` (
  `id` int NOT NULL AUTO_INCREMENT,
  `Nom` varchar(100) DEFAULT NULL,
  `Prenom` varchar(100) DEFAULT NULL,
  `AdresseEmail` varchar(150) DEFAULT NULL,
  `MotDePasse` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `AdresseEmail` (`AdresseEmail`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Administrateur`
--

LOCK TABLES `Administrateur` WRITE;
/*!40000 ALTER TABLE `Administrateur` DISABLE KEYS */;
INSERT INTO `Administrateur` VALUES (1,'Karim','Admin','admin@example.com','adminpass');
/*!40000 ALTER TABLE `Administrateur` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `Apprenants`
--

DROP TABLE IF EXISTS `Apprenants`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `Apprenants` (
  `id` int NOT NULL AUTO_INCREMENT,
  `Nom` varchar(100) DEFAULT NULL,
  `Prenom` varchar(100) DEFAULT NULL,
  `AdresseEmail` varchar(150) DEFAULT NULL,
  `MotDePasse` varchar(255) DEFAULT NULL,
  `Phone` varchar(20) DEFAULT NULL,
  `Ville` varchar(100) DEFAULT NULL,
  `TypeDeFormation` varchar(100) DEFAULT NULL,
  `CodeCoupon` varchar(50) DEFAULT NULL,
  `DateDebutFormation` date DEFAULT NULL,
  `DateFinFormation` date DEFAULT NULL,
  `Centre` varchar(100) DEFAULT NULL,
  `NiveauDeConnaissance` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `AdresseEmail` (`AdresseEmail`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Apprenants`
--

LOCK TABLES `Apprenants` WRITE;
/*!40000 ALTER TABLE `Apprenants` DISABLE KEYS */;
INSERT INTO `Apprenants` VALUES (1,'Doe','John','john.apprenant@example.com','pass123','0600000001','Rabat','IA','CODE123','2025-07-01','2025-12-31','Centre A','Débutant'),(3,'Doe','John','john2.apprenant@example.com','pass123','0600000001','Rabat','IA','CODE123','2025-07-01','2025-12-31','Centre A','Débutant'),(4,'Doe','John','john3.apprenant@example.com','pass123','0600000001','Rabat','IA','CODE123','2025-07-01','2025-12-31','Centre A','Débutant');
/*!40000 ALTER TABLE `Apprenants` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `BaseConnaissances`
--

DROP TABLE IF EXISTS `BaseConnaissances`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `BaseConnaissances` (
  `id` int NOT NULL AUTO_INCREMENT,
  `titre` varchar(255) NOT NULL,
  `description` text NOT NULL,
  `fichier` longblob,
  `type_fichier` varchar(50) DEFAULT NULL,
  `lien_web` varchar(500) DEFAULT NULL,
  `date_ajout` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `BaseConnaissances`
--

LOCK TABLES `BaseConnaissances` WRITE;
/*!40000 ALTER TABLE `BaseConnaissances` DISABLE KEYS */;
INSERT INTO `BaseConnaissances` VALUES (1,'Test','Test',_binary '~/Desktop/mdp.txt.save','txt',NULL,'2025-07-15 12:22:07'),(2,'Test','Test',_binary '~/Desktop/mdp.txt.save','txt',NULL,'2025-07-15 12:57:35'),(3,'Test','Test',_binary '/home/karim/Desktop/web4-projet/script.js','js',NULL,'2025-07-15 13:02:55'),(4,'pwned','<script>alert(1)</script>','','none',NULL,'2025-07-15 15:26:02');
/*!40000 ALTER TABLE `BaseConnaissances` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `Karim`
--

DROP TABLE IF EXISTS `Karim`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `Karim` (
  `id` int DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Karim`
--

LOCK TABLES `Karim` WRITE;
/*!40000 ALTER TABLE `Karim` DISABLE KEYS */;
/*!40000 ALTER TABLE `Karim` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `Messages`
--

DROP TABLE IF EXISTS `Messages`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `Messages` (
  `id` int NOT NULL AUTO_INCREMENT,
  `expediteur_email` varchar(150) DEFAULT NULL,
  `expediteur_role` varchar(50) DEFAULT NULL,
  `destinataire_email` varchar(150) DEFAULT NULL,
  `destinataire_role` varchar(50) DEFAULT NULL,
  `sujet` text,
  `contenu` text,
  `lu` tinyint(1) DEFAULT '0',
  `date_envoi` datetime DEFAULT CURRENT_TIMESTAMP,
  `expediteur_supprime` tinyint(1) DEFAULT '0',
  `destinataire_supprime` tinyint(1) DEFAULT '0',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Messages`
--

LOCK TABLES `Messages` WRITE;
/*!40000 ALTER TABLE `Messages` DISABLE KEYS */;
INSERT INTO `Messages` VALUES (1,'john.apprenant@example.com','Apprenant','john.apprenant@example.com','Apprenant','sujet','lol',1,'2025-07-15 11:50:14',0,0),(2,'john.apprenant@example.com','Apprenant','john.apprenant@example.com','Apprenant','<script>alert(1)</script>','<script>alert(1)</script>',1,'2025-07-15 12:27:12',0,0),(3,'john.apprenant@example.com','Apprenant','john.apprenant@example.com','Apprenant','<script>alert(\"Test XSS\")</script>','<script>alert(\"Test XSS\")</script>',1,'2025-07-15 12:31:22',0,0);
/*!40000 ALTER TABLE `Messages` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `Parcours`
--

DROP TABLE IF EXISTS `Parcours`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `Parcours` (
  `id` int NOT NULL AUTO_INCREMENT,
  `email_apprenant` varchar(150) DEFAULT NULL,
  `titre` varchar(255) DEFAULT NULL,
  `description` text,
  `niveau` varchar(50) DEFAULT NULL,
  `duree` varchar(50) DEFAULT NULL,
  `date_debut` date DEFAULT NULL,
  `date_fin` date DEFAULT NULL,
  `etat` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Parcours`
--

LOCK TABLES `Parcours` WRITE;
/*!40000 ALTER TABLE `Parcours` DISABLE KEYS */;
/*!40000 ALTER TABLE `Parcours` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `Presence`
--

DROP TABLE IF EXISTS `Presence`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `Presence` (
  `id` int NOT NULL AUTO_INCREMENT,
  `apprenant_id` int DEFAULT NULL,
  `Nom` varchar(100) DEFAULT NULL,
  `Prenom` varchar(100) DEFAULT NULL,
  `AdresseEmail` varchar(150) DEFAULT NULL,
  `Centre` varchar(100) DEFAULT NULL,
  `date_connexion` date DEFAULT NULL,
  `heure_connexion` datetime DEFAULT NULL,
  `heure_deconnexion` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Presence`
--

LOCK TABLES `Presence` WRITE;
/*!40000 ALTER TABLE `Presence` DISABLE KEYS */;
INSERT INTO `Presence` VALUES (1,1,'Doe','John','john.apprenant@example.com','Centre A','2025-07-15','2025-07-15 11:11:29',NULL),(2,1,'Doe','John','john.apprenant@example.com','Centre A','2025-07-15','2025-07-15 11:19:45',NULL),(3,1,'Doe','John','john.apprenant@example.com','Centre A','2025-07-15','2025-07-15 11:48:10','2025-07-15 11:55:12'),(4,1,'Doe','John','john.apprenant@example.com','Centre A','2025-07-15','2025-07-15 12:11:41',NULL),(5,1,'Doe','John','john.apprenant@example.com','Centre A','2025-07-15','2025-07-15 14:37:46',NULL),(6,1,'Doe','John','john.apprenant@example.com','Centre A','2025-07-15','2025-07-15 16:00:29',NULL);
/*!40000 ALTER TABLE `Presence` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `PresenceCentre`
--

DROP TABLE IF EXISTS `PresenceCentre`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `PresenceCentre` (
  `id` int NOT NULL AUTO_INCREMENT,
  `apprenant_id` int DEFAULT NULL,
  `Nom` varchar(100) DEFAULT NULL,
  `Prenom` varchar(100) DEFAULT NULL,
  `AdresseEmail` varchar(150) DEFAULT NULL,
  `Centre` varchar(100) DEFAULT NULL,
  `date_connexion` date DEFAULT NULL,
  `heure_connexion` datetime DEFAULT NULL,
  `heure_deconnexion` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `PresenceCentre`
--

LOCK TABLES `PresenceCentre` WRITE;
/*!40000 ALTER TABLE `PresenceCentre` DISABLE KEYS */;
INSERT INTO `PresenceCentre` VALUES (1,1,'Doe','John','john.apprenant@example.com','Centre A','2025-07-15','2025-07-15 11:11:29',NULL),(2,1,'Doe','John','john.apprenant@example.com','Centre A','2025-07-15','2025-07-15 11:19:45',NULL),(3,1,'Doe','John','john.apprenant@example.com','Centre A','2025-07-15','2025-07-15 11:48:10','2025-07-15 11:55:12'),(4,1,'Doe','John','john.apprenant@example.com','Centre A','2025-07-15','2025-07-15 12:11:41',NULL),(5,1,'Doe','John','john.apprenant@example.com','Centre A','2025-07-15','2025-07-15 14:37:46',NULL),(6,1,'Doe','John','john.apprenant@example.com','Centre A','2025-07-15','2025-07-15 16:00:29',NULL);
/*!40000 ALTER TABLE `PresenceCentre` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ResponsablePedagogique`
--

DROP TABLE IF EXISTS `ResponsablePedagogique`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ResponsablePedagogique` (
  `id` int NOT NULL AUTO_INCREMENT,
  `Nom` varchar(100) DEFAULT NULL,
  `Prenom` varchar(100) DEFAULT NULL,
  `AdresseEmail` varchar(150) DEFAULT NULL,
  `MotDePasse` varchar(255) DEFAULT NULL,
  `Phone` varchar(20) DEFAULT NULL,
  `Ville` varchar(100) DEFAULT NULL,
  `CodeCoupon` varchar(50) DEFAULT NULL,
  `Centre` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `AdresseEmail` (`AdresseEmail`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ResponsablePedagogique`
--

LOCK TABLES `ResponsablePedagogique` WRITE;
/*!40000 ALTER TABLE `ResponsablePedagogique` DISABLE KEYS */;
INSERT INTO `ResponsablePedagogique` VALUES (1,'Smith','Anna','anna.pedago@example.com','pass456','0600000002','Casablanca','PEDA456','Centre A');
/*!40000 ALTER TABLE `ResponsablePedagogique` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `Responsable_de_centre_de_coding`
--

DROP TABLE IF EXISTS `Responsable_de_centre_de_coding`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `Responsable_de_centre_de_coding` (
  `id` int NOT NULL AUTO_INCREMENT,
  `Nom` varchar(100) DEFAULT NULL,
  `Prenom` varchar(100) DEFAULT NULL,
  `AdresseEmail` varchar(150) DEFAULT NULL,
  `MotDePasse` varchar(255) DEFAULT NULL,
  `Phone` varchar(20) DEFAULT NULL,
  `Ville` varchar(100) DEFAULT NULL,
  `CodeCoupon` varchar(50) DEFAULT NULL,
  `Centre` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `AdresseEmail` (`AdresseEmail`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Responsable_de_centre_de_coding`
--

LOCK TABLES `Responsable_de_centre_de_coding` WRITE;
/*!40000 ALTER TABLE `Responsable_de_centre_de_coding` DISABLE KEYS */;
INSERT INTO `Responsable_de_centre_de_coding` VALUES (1,'Ben','Ali','ali.coding@example.com','pass789','0600000003','Fès','CODE789','Centre A');
/*!40000 ALTER TABLE `Responsable_de_centre_de_coding` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `Tutoriels`
--

DROP TABLE IF EXISTS `Tutoriels`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `Tutoriels` (
  `id` int NOT NULL AUTO_INCREMENT,
  `categorie` varchar(100) DEFAULT NULL,
  `video_url` text NOT NULL,
  `description` text,
  `objectifs` text,
  `date_creation` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Tutoriels`
--

LOCK TABLES `Tutoriels` WRITE;
/*!40000 ALTER TABLE `Tutoriels` DISABLE KEYS */;
/*!40000 ALTER TABLE `Tutoriels` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `historique`
--

DROP TABLE IF EXISTS `historique`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `historique` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `message` text NOT NULL,
  `response` text,
  `session_id` varchar(100) NOT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `historique`
--

LOCK TABLES `historique` WRITE;
/*!40000 ALTER TABLE `historique` DISABLE KEYS */;
/*!40000 ALTER TABLE `historique` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-07-17 11:52:02
