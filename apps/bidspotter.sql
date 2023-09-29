DROP TABLE IF EXISTS `flask_dance_oauth`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `flas  k_dance_oauth` (
  `id` varchar(0) DEFAULT NULL,
  `provider` varchar(0) DEFAULT NULL,
  `created_at` varchar(0) DEFAULT NULL,
  `token` varchar(0) DEFAULT NULL,
  `user_id` varchar(0) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `flask_dance_oauth`
--

LOCK TABLES `flask_dance_oauth` WRITE;
/*!40000 ALTER TABLE `flask_dance_oauth` DISABLE KEYS */;
/*!40000 ALTER TABLE `flask_dance_oauth` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `users` (
  `id` varchar(0) DEFAULT NULL,
  `username` varchar(0) DEFAULT NULL,
  `email` varchar(0) DEFAULT NULL,
  `password` varchar(0) DEFAULT NULL,
  `oauth_github` varchar(0) DEFAULT NULL
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;

UNLOCK TABLES;