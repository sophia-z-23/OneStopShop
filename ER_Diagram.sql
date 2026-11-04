CREATE TABLE `business` (
  `account_id` integer PRIMARY KEY,
  `business_name` varchar(100),
  `contact_info` varchar(250),
  `description` varchar(500)
);

CREATE TABLE `customers` (
  `account_id` integer PRIMARY KEY,
  `contact_info` varchar(250)
);

CREATE TABLE `account` (
  `account_id` integer PRIMARY KEY AUTO_INCREMENT,
  `account_type` ENUM ('business', 'customer'),
  `email` varchar(250)
);

CREATE TABLE `posting` (
  `post_id` integer PRIMARY KEY,
  `account_id` integer,
  `post_type` ENUM ('scheduling', 'item'),
  `image_link` varchar(500),
  `created_at` timestamp
);

CREATE TABLE `time_slot` (
  `slot_id` integer PRIMARY KEY,
  `post_id` integer,
  `start_time` datetime,
  `end_time` datetime,
  `customer_id` integer
);

ALTER TABLE `account` ADD FOREIGN KEY (`account_id`) REFERENCES `business` (`account_id`);

ALTER TABLE `account` ADD FOREIGN KEY (`account_id`) REFERENCES `customers` (`account_id`);

ALTER TABLE `posting` ADD FOREIGN KEY (`account_id`) REFERENCES `account` (`account_id`);

ALTER TABLE `time_slot` ADD FOREIGN KEY (`post_id`) REFERENCES `posting` (`post_id`);

ALTER TABLE `time_slot` ADD FOREIGN KEY (`customer_id`) REFERENCES `customers` (`account_id`);
