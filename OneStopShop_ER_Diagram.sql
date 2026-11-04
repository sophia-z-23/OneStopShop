CREATE TABLE `business` (
  `id` integer PRIMARY KEY,
  `business_name` varchar(100),
  `contact_info` varchar(250),
  `description` varchar(500)
);

CREATE TABLE `customers` (
  `id` integer PRIMARY KEY,
  `contact_info` varchar(250)
);

CREATE TABLE `account` (
  `userId` integer,
  `account_type` enum,
  `email` varchar(250)
);

ALTER TABLE `account` ADD FOREIGN KEY (`userId`) REFERENCES `business` (`id`);

ALTER TABLE `account` ADD FOREIGN KEY (`userId`) REFERENCES `customers` (`id`);
