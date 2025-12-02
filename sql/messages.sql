ALTER TABLE `messages`
  ADD COLUMN `ad_id` int NOT NULL AFTER `message_id`;

ALTER TABLE `messages`
  ADD CONSTRAINT `fk_messages_ad`
  FOREIGN KEY (`ad_id`) REFERENCES `ads` (`ad_id`) ON DELETE CASCADE;
