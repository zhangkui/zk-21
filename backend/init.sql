-- 海岛养殖网箱病害巡检与死鱼异常上报平台 数据库初始化脚本
CREATE DATABASE IF NOT EXISTS aqua_platform DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE aqua_platform;

-- 创建用户并授权
CREATE USER IF NOT EXISTS 'aqua_user'@'%' IDENTIFIED BY 'aqua123456';
GRANT ALL PRIVILEGES ON aqua_platform.* TO 'aqua_user'@'%';
FLUSH PRIVILEGES;

-- 设置时区
SET time_zone = '+8:00';
