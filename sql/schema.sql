CREATE TABLE `users` (
  `user_id` int PRIMARY KEY AUTO_INCREMENT,
  `vorname` varchar(100) NOT NULL,
  `nachname` varchar(100) NOT NULL,
  `email` varchar(255) UNIQUE NOT NULL,
  `passwort_hash` varchar(255) NOT NULL,
  `rolle` varchar(50) NOT NULL,
  `created_at` datetime NOT NULL DEFAULT (CURRENT_TIMESTAMP)
);

CREATE TABLE `ads` (
  `ad_id` int PRIMARY KEY AUTO_INCREMENT,
  `owner_id` int NOT NULL,
  `titel` varchar(255) NOT NULL,
  `text` text NOT NULL,
  `datum` datetime NOT NULL DEFAULT (CURRENT_TIMESTAMP),
  `status` varchar(50) NOT NULL DEFAULT 'aktiv',
  `preis` decimal(10,2),
  `bilder_path` varchar(255)
);

CREATE TABLE `categories` (
  `category_id` int PRIMARY KEY AUTO_INCREMENT,
  `name` varchar(100) UNIQUE NOT NULL
);

CREATE TABLE `ads_categories` (
  `ad_id` int NOT NULL,
  `category_id` int NOT NULL,
  PRIMARY KEY (`ad_id`, `category_id`)
);

CREATE TABLE `messages` (
  `message_id` int PRIMARY KEY AUTO_INCREMENT,
  `from_user_id` int NOT NULL,
  `to_user_id` int NOT NULL,
  `subject` varchar(255),
  `body` text NOT NULL,
  `sent_at` datetime NOT NULL DEFAULT (CURRENT_TIMESTAMP),
  `read_at` datetime
);

CREATE TABLE `ad_images` (
  `image_id` int PRIMARY KEY AUTO_INCREMENT,
  `ad_id` int NOT NULL,
  `file_path` varchar(255) NOT NULL,
  `sort_order` int NOT NULL DEFAULT 1,
  `uploaded_at` datetime NOT NULL DEFAULT (CURRENT_TIMESTAMP)
);

-- Beziehung: Anzeige gehört einem User
ALTER TABLE `ads`
  ADD FOREIGN KEY (`owner_id`)
  REFERENCES `users` (`user_id`);

-- Beziehung: Zuordnung Anzeige <-> Kategorie
-- Wenn eine Anzeige gelöscht wird, sollen auch ihre Kategoriezurodnungen verschwinden.
ALTER TABLE `ads_categories`
  ADD FOREIGN KEY (`ad_id`)
  REFERENCES `ads` (`ad_id`)
  ON DELETE CASCADE;

ALTER TABLE `ads_categories`
  ADD FOREIGN KEY (`category_id`)
  REFERENCES `categories` (`category_id`);

-- Beziehung: Nachrichten zwischen Usern
ALTER TABLE `messages`
  ADD FOREIGN KEY (`from_user_id`)
  REFERENCES `users` (`user_id`);

ALTER TABLE `messages`
  ADD FOREIGN KEY (`to_user_id`)
  REFERENCES `users` (`user_id`);

-- Beziehung: Bilder zu Anzeigen
-- Wenn eine Anzeige gelöscht wird, sollen auch alle Bildpfade/Datensätze verschwinden.
ALTER TABLE `ad_images`
  ADD FOREIGN KEY (`ad_id`)
  REFERENCES `ads` (`ad_id`)
  ON DELETE CASCADE;
