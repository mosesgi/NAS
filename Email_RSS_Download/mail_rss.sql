CREATE TABLE `mail_rss` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `mail_mid` varchar(256) DEFAULT NULL,
  `mail_time` varchar(50) DEFAULT NULL,
  `sender_name` varchar(200) DEFAULT NULL,
  `sender_addr` varchar(200) DEFAULT NULL,
  `subject` varchar(300) DEFAULT NULL,
  `content` mediumtext DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;