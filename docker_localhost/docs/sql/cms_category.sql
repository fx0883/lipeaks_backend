/*
 Navicat Premium Dump SQL

 Source Server         : 123456
 Source Server Type    : MySQL
 Source Server Version : 80404 (8.4.4)
 Source Host           : localhost:3306
 Source Schema         : multi_tenant_db

 Target Server Type    : MySQL
 Target Server Version : 80404 (8.4.4)
 File Encoding         : 65001

 Date: 16/07/2025 11:40:19
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for cms_category
-- ----------------------------
DROP TABLE IF EXISTS `cms_category`;
CREATE TABLE `cms_category`  (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `slug` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL,
  `cover_image` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `sort_order` int NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `seo_title` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL,
  `seo_description` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL,
  `parent_id` bigint NULL DEFAULT NULL,
  `tenant_id` bigint NOT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `slug`(`slug` ASC) USING BTREE,
  INDEX `cms_categor_parent__a5b368_idx`(`parent_id` ASC) USING BTREE,
  INDEX `cms_categor_is_acti_d7f522_idx`(`is_active` ASC) USING BTREE,
  INDEX `cms_categor_tenant__cbc12e_idx`(`tenant_id` ASC, `parent_id` ASC) USING BTREE,
  INDEX `cms_categor_tenant__945ea6_idx`(`tenant_id` ASC, `is_active` ASC) USING BTREE,
  CONSTRAINT `cms_category_parent_id_c0bcb26a_fk_cms_category_id` FOREIGN KEY (`parent_id`) REFERENCES `cms_category` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `cms_category_tenant_id_06c25778_fk_tenant_id` FOREIGN KEY (`tenant_id`) REFERENCES `tenant` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 13 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of cms_category
-- ----------------------------
INSERT INTO `cms_category` VALUES (1, 'Product', 'product-655', '', NULL, '2025-07-08 14:01:50.263836', '2025-07-11 05:14:39.291316', 0, 1, NULL, NULL, NULL, 17);
INSERT INTO `cms_category` VALUES (3, 'Features', 'features-699', '', NULL, '2025-07-09 03:33:45.838924', '2025-07-09 03:33:45.838924', 0, 1, NULL, NULL, 1, 17);
INSERT INTO `cms_category` VALUES (4, 'Use Cases', 'use-cases-434', '', NULL, '2025-07-09 03:36:55.467487', '2025-07-09 03:36:55.467487', 0, 1, NULL, NULL, 1, 17);
INSERT INTO `cms_category` VALUES (5, 'Documentation', 'documentation-643', '', NULL, '2025-07-09 03:37:52.100238', '2025-07-09 03:37:52.100238', 0, 1, NULL, NULL, 1, 17);
INSERT INTO `cms_category` VALUES (6, 'Blog', 'blog-803', '', NULL, '2025-07-09 03:39:46.142216', '2025-07-11 05:14:14.030654', 1, 1, NULL, NULL, NULL, 17);
INSERT INTO `cms_category` VALUES (7, 'Case Studies', 'case-studies-792', '', NULL, '2025-07-09 03:40:49.601310', '2025-07-11 05:14:48.062699', 3, 1, NULL, NULL, NULL, 17);
INSERT INTO `cms_category` VALUES (8, 'Changelog', 'changelog-753', '', NULL, '2025-07-09 03:42:30.531495', '2025-07-11 05:14:20.390646', 2, 1, NULL, NULL, NULL, 17);

SET FOREIGN_KEY_CHECKS = 1;
