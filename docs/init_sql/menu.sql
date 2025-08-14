/*
 Navicat Premium Dump SQL

 Source Server         : 123456
 Source Server Type    : MySQL
 Source Server Version : 80404 (8.4.4)
 Source Host           : localhost:3306
 Source Schema         : multi_tenant_db_dev

 Target Server Type    : MySQL
 Target Server Version : 80404 (8.4.4)
 File Encoding         : 65001

 Date: 14/08/2025 15:57:08
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for menu
-- ----------------------------
DROP TABLE IF EXISTS `menu`;
CREATE TABLE `menu`  (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `code` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `path` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `component` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `redirect` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `title` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `icon` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `extra_icon` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `rank` int NOT NULL,
  `show_link` tinyint(1) NOT NULL,
  `show_parent` tinyint(1) NOT NULL,
  `roles` json NULL,
  `auths` json NULL,
  `keep_alive` tinyint(1) NOT NULL,
  `frame_src` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `frame_loading` tinyint(1) NOT NULL,
  `hidden_tag` tinyint(1) NOT NULL,
  `dynamic_level` int NULL DEFAULT NULL,
  `active_path` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `transition_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `enter_transition` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `leave_transition` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL,
  `remarks` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `parent_id` bigint NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `name`(`name` ASC) USING BTREE,
  UNIQUE INDEX `code`(`code` ASC) USING BTREE,
  INDEX `menu_parent_id_7f4b2723_fk_menu_id`(`parent_id` ASC) USING BTREE,
  CONSTRAINT `menu_parent_id_7f4b2723_fk_menu_id` FOREIGN KEY (`parent_id`) REFERENCES `menu` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 58 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of menu
-- ----------------------------
INSERT INTO `menu` VALUES (22, 'CMS', 'cms', '/cms', NULL, '/cms/article', 'cms.menu.cmsManagement', 'ri:article-line', NULL, 5, 1, 1, '[]', '[]', 0, NULL, 1, 0, NULL, NULL, NULL, NULL, NULL, 1, '由load_provided_cms_menus命令导入', '2025-06-24 14:19:04.705059', '2025-06-24 14:19:04.705076', NULL);
INSERT INTO `menu` VALUES (23, 'ArticleManagement', 'articleManagement', '/cms/article', '', '', 'cms.menu.articleManagement', 'ri:file-list-line', NULL, 0, 1, 1, '[]', '[]', 1, NULL, 0, 0, NULL, NULL, NULL, NULL, NULL, 1, NULL, '2025-06-24 14:19:04.706365', '2025-06-26 10:57:20.980793', 22);
INSERT INTO `menu` VALUES (24, 'ArticleCreate', 'articlecreate', '/cms/article/create', '/src/views/cms/article/create.vue', NULL, 'cms.menu.articleCreate', '', NULL, 5, 0, 1, '[]', '[]', 0, NULL, 1, 0, NULL, '', NULL, NULL, NULL, 1, '由load_provided_cms_menus命令导入', '2025-06-24 14:19:04.707275', '2025-06-24 14:21:38.297683', 23);
INSERT INTO `menu` VALUES (25, 'ArticleEdit', 'articleedit', '/cms/article/edit/:id', '/src/views/cms/article/edit.vue', NULL, 'cms.menu.articleEdit', '', NULL, 6, 0, 1, '[]', '[]', 0, NULL, 1, 0, NULL, '', NULL, NULL, NULL, 1, '由load_provided_cms_menus命令导入', '2025-06-24 14:19:04.708226', '2025-06-24 14:21:38.300148', 23);
INSERT INTO `menu` VALUES (26, 'ArticleDetail', 'articledetail', '/cms/article/detail/:id', '/src/views/cms/article/detail.vue', NULL, 'cms.menu.articleDetail', '', NULL, 7, 0, 1, '[]', '[]', 0, NULL, 1, 0, NULL, '', NULL, NULL, NULL, 1, '由load_provided_cms_menus命令导入', '2025-06-24 14:19:04.709037', '2025-06-24 14:21:38.303153', 23);
INSERT INTO `menu` VALUES (27, 'CommentManagement', 'commentManagement', '/cms/comment', '', '', 'cms.menu.commentManagement', 'ri:chat-1-line', NULL, 3, 1, 1, '[]', '[]', 1, NULL, 0, 0, NULL, NULL, NULL, NULL, NULL, 1, NULL, '2025-06-24 14:19:04.709812', '2025-06-27 14:46:09.788886', 22);
INSERT INTO `menu` VALUES (28, 'CommentDetail', 'commentdetail', '/cms/comment/detail/:id', '/src/views/cms/comment/detail.vue', '', 'cms.menu.commentDetail', 'ep:menu', NULL, 0, 0, 0, '[]', '[]', 0, NULL, 0, 0, NULL, NULL, NULL, NULL, NULL, 1, NULL, '2025-06-24 14:19:04.710621', '2025-07-15 02:22:44.320285', 27);
INSERT INTO `menu` VALUES (29, 'CategoryManagement', 'categorymanagement', '/cms/category', '', '', 'cms.menu.categoryManagement', 'ri:folder-2-line', NULL, 0, 1, 1, '[]', '[]', 1, NULL, 1, 0, NULL, NULL, NULL, NULL, NULL, 1, NULL, '2025-06-24 14:19:04.711752', '2025-06-27 13:48:03.279385', 22);
INSERT INTO `menu` VALUES (30, 'TagManagement', 'tagManagement', '/cms/tag', '', '', 'cms.menu.tagManagement', 'ep:refrigerator', NULL, 0, 1, 1, '[]', '[]', 1, NULL, 0, 0, NULL, NULL, NULL, NULL, NULL, 1, NULL, '2025-06-24 14:19:04.713053', '2025-06-27 06:00:54.320478', 22);
INSERT INTO `menu` VALUES (31, 'ArticleList', 'ArticleList', '/cms/article/index', '/src/views/cms/article/index.vue', '', 'cms.menu.articleList', 'ri:user-line', NULL, 0, 1, 0, '[]', '[]', 0, NULL, 0, 0, NULL, NULL, NULL, NULL, NULL, 1, NULL, '2025-06-26 11:00:07.557936', '2025-06-27 05:46:20.791510', 23);
INSERT INTO `menu` VALUES (32, 'CategoryList', 'categoryList', '/cms/category/index', '/src/views/cms/category/index.vue', '', 'cms.menu.categoryList', '', NULL, 0, 1, 0, '[]', '[]', 0, NULL, 0, 0, NULL, NULL, NULL, NULL, NULL, 1, NULL, '2025-06-27 02:51:10.943586', '2025-06-27 14:35:51.318841', 29);
INSERT INTO `menu` VALUES (33, 'CategoryEdit', 'menus.categoryEdit', '/cms/category/edit/:id', '/src/views/cms/category/edit.vue', '', 'cms.menu.categoryEdit', '', NULL, 0, 0, 0, '[]', '[]', 0, NULL, 0, 0, NULL, NULL, NULL, NULL, NULL, 1, NULL, '2025-06-27 03:08:56.383211', '2025-06-27 03:08:56.383224', 29);
INSERT INTO `menu` VALUES (34, 'CategroyDetail', 'categoryDetail', '/cms/category/:id', '/src/views/cms/category/detail.vue', '', 'cms.menu.categoryDetail', '', NULL, 0, 0, 0, '[]', '[]', 0, NULL, 0, 0, NULL, NULL, NULL, NULL, NULL, 1, NULL, '2025-06-27 03:10:48.883712', '2025-06-27 13:01:53.276230', 29);
INSERT INTO `menu` VALUES (35, 'TagList', 'tagList', '/cms/tag/index', '/src/views/cms/tag/index.vue', '', 'cms.menu.tagList', '', NULL, 0, 1, 0, '[]', '[]', 0, NULL, 0, 0, NULL, NULL, NULL, NULL, NULL, 1, NULL, '2025-06-27 03:20:11.572864', '2025-06-27 03:20:11.572874', 30);
INSERT INTO `menu` VALUES (36, 'TagCreate', 'tagCreate', '/cms/tag/create', '/src/views/cms/tag/create.vue', '', 'cms.menu.tagCreate', '', NULL, 0, 0, 0, '[]', '[]', 0, NULL, 0, 0, NULL, NULL, NULL, NULL, NULL, 1, NULL, '2025-06-27 03:29:18.994262', '2025-06-27 03:29:18.994273', 30);
INSERT INTO `menu` VALUES (37, 'TagEdit', 'tagEdit', '/cms/tag/edit/:id', '/src/views/cms/tag/edit.vue', '', 'cms.menu.tagEdit', '', NULL, 0, 0, 0, '[]', '[]', 0, NULL, 0, 0, NULL, NULL, NULL, NULL, NULL, 1, NULL, '2025-06-27 03:32:15.977529', '2025-06-27 03:32:15.977541', 30);
INSERT INTO `menu` VALUES (38, 'CommentList', 'commentList', '/cms/comment/index', '/src/views/cms/comment/index.vue', '', 'cms.menu.commentList', '', NULL, 0, 1, 0, '[]', '[]', 0, NULL, 0, 0, NULL, NULL, NULL, NULL, NULL, 1, NULL, '2025-06-27 03:48:02.925170', '2025-06-27 14:45:10.287827', 27);
INSERT INTO `menu` VALUES (39, 'CommentCreate', 'commentCreate', '/cms/comment/create', '/src/views/cms/comment/create.vue', '', 'cms.menu.commentCreate', '', NULL, 0, 0, 0, '[]', '[]', 0, NULL, 0, 0, NULL, NULL, NULL, NULL, NULL, 1, NULL, '2025-06-27 03:54:34.630680', '2025-06-27 03:54:34.630690', 27);
INSERT INTO `menu` VALUES (40, 'CommentEdit', 'commentEdit', '/cms/comment/edit/:id', '/src/views/cms/comment/edit.vue', '', 'cms.menu.commentEdit', '', NULL, 0, 0, 0, '[]', '[]', 0, NULL, 0, 0, NULL, NULL, NULL, NULL, NULL, 1, NULL, '2025-06-27 03:55:51.176913', '2025-06-27 03:55:51.176924', 27);
INSERT INTO `menu` VALUES (41, 'menus.articleVersion', 'articleVersion', '/cms/article/version/:id', '/src/views/cms/article/version', '', 'cms.menu.articleVersion', 'ep:cellphone', NULL, 0, 0, 0, '[]', '[]', 0, NULL, 0, 0, NULL, NULL, NULL, NULL, NULL, 1, NULL, '2025-06-27 13:42:14.524045', '2025-06-27 13:42:14.524055', 23);
INSERT INTO `menu` VALUES (42, 'Customer', 'customer', '/customer', '', '/customer/index', 'customer.menu.customerManagement', 'ep:dessert', NULL, 0, 1, 1, '[]', '[]', 1, NULL, 0, 0, NULL, NULL, NULL, NULL, NULL, 1, NULL, '2025-07-05 09:50:05.681624', '2025-07-06 06:37:39.236869', NULL);
INSERT INTO `menu` VALUES (43, 'CustomerList', 'customerList', '/customer/index', '/src/views/customer/index.vue', '', 'customer.menu.customerList', 'ri:menu-line', NULL, 0, 1, 1, '[]', '[]', 0, NULL, 0, 0, NULL, NULL, NULL, NULL, NULL, 1, NULL, '2025-07-05 09:52:18.214324', '2025-07-05 09:52:18.214333', 42);
INSERT INTO `menu` VALUES (44, 'CustomerCreate', 'customerCreate', '/customer/create', '/src/views/customer/create.vue', '', 'customer.menu.customerCreate', '', NULL, 0, 0, 0, '[]', '[]', 0, NULL, 0, 0, NULL, NULL, NULL, NULL, NULL, 1, NULL, '2025-07-05 09:53:00.334894', '2025-07-05 09:53:00.334907', 42);
INSERT INTO `menu` VALUES (45, 'CustomerEdit', 'customerEdit', '/customer/edit/:id', '/src/views/customer/edit.vue', '', 'customer.menu.customerEdit', '', NULL, 0, 0, 0, '[]', '[]', 0, NULL, 0, 0, NULL, NULL, NULL, NULL, NULL, 1, NULL, '2025-07-05 09:54:05.860122', '2025-07-05 09:54:05.860133', 42);
INSERT INTO `menu` VALUES (46, 'CustomerDetail', 'customerDetail', '/customer/detail/:id', '/src/views/customer/detail.vue', '', 'customer.menu.customerDetail', '', NULL, 0, 0, 0, '[]', '[]', 0, NULL, 0, 0, NULL, NULL, NULL, NULL, NULL, 1, NULL, '2025-07-05 09:54:58.216792', '2025-07-05 09:54:58.216805', 42);
INSERT INTO `menu` VALUES (47, 'Member', 'member', '/member', '', '/member/index', 'member.memberManagement', 'ep:avatar', NULL, 0, 1, 1, '[]', '[]', 0, NULL, 0, 0, NULL, NULL, NULL, NULL, NULL, 1, NULL, '2025-07-06 06:12:52.289264', '2025-07-06 06:12:52.289274', NULL);
INSERT INTO `menu` VALUES (48, 'MemberList', 'memberList', '/member/index', '/src/views/member/index.vue', '', 'member.memberList', 'ri:menu-line', NULL, 0, 1, 1, '[]', '[]', 0, NULL, 0, 0, NULL, NULL, NULL, NULL, NULL, 1, NULL, '2025-07-06 06:19:07.639763', '2025-07-21 02:55:16.035050', 42);
INSERT INTO `menu` VALUES (49, 'MemberCreate', 'memberCreate', '/member/create', '/src/views/member/create.vue', '', 'member.createMember', '', NULL, 0, 0, 0, '[]', '[]', 0, NULL, 0, 0, NULL, NULL, NULL, NULL, NULL, 1, NULL, '2025-07-06 06:20:10.360060', '2025-07-21 02:55:50.847692', 42);
INSERT INTO `menu` VALUES (50, 'MemberEdit', 'memberEdit', '/member/edit/:id', '/src/views/member/edit.vue', '', 'member.editMember', '', NULL, 0, 0, 0, '[]', '[]', 0, NULL, 0, 0, NULL, NULL, NULL, NULL, NULL, 1, NULL, '2025-07-06 06:20:55.105634', '2025-07-21 02:55:54.043743', 42);
INSERT INTO `menu` VALUES (51, 'MemberDetail', 'memberDetail', '/member/detail/:id', '/src/views/member/detail.vue', '', 'member.memberDetail', '', NULL, 0, 0, 0, '[]', '[]', 0, NULL, 0, 0, NULL, NULL, NULL, NULL, NULL, 1, NULL, '2025-07-06 06:21:39.530833', '2025-07-21 02:56:36.004060', 42);
INSERT INTO `menu` VALUES (52, 'Order', 'order', '/order', '', '/order/index', 'order.menu.pureOrde', 'ep:list', NULL, 0, 1, 1, '[]', '[]', 1, NULL, 0, 0, NULL, NULL, NULL, NULL, NULL, 1, NULL, '2025-07-14 10:16:22.730724', '2025-07-14 14:27:07.419268', NULL);
INSERT INTO `menu` VALUES (53, 'OrderIndex', 'orderIndex', '/order/index', '/src/views/order/index.vue', '', 'order.menu.orderList', 'ep:sunny', NULL, 0, 1, 1, '[]', '[]', 0, NULL, 0, 0, NULL, NULL, NULL, NULL, NULL, 1, NULL, '2025-07-14 10:20:39.799711', '2025-07-15 02:14:29.336320', 52);
INSERT INTO `menu` VALUES (54, 'OrderStatistics', 'orderStatistics', '/order/statistics', '/src/views/order/statistics.vue', '', 'order.menu.statisticsTitle', 'ep:box', NULL, 0, 1, 1, '[]', '[]', 0, NULL, 0, 0, NULL, NULL, NULL, NULL, NULL, 1, NULL, '2025-07-14 10:21:51.449676', '2025-07-14 14:28:36.369650', 52);
INSERT INTO `menu` VALUES (55, 'orderCreate', 'orderCreate', '/order/create', '/src/views/order/create.vue', '', 'order.menu.createOrder', '', NULL, 0, 0, 0, '[]', '[]', 0, NULL, 0, 0, NULL, NULL, NULL, NULL, NULL, 1, NULL, '2025-07-14 10:23:06.313294', '2025-07-14 10:23:06.313304', 52);
INSERT INTO `menu` VALUES (56, 'OrderEdit', 'orderEdit', '/order/edit/:id', '/src/views/order/edit.vue', '', 'order.menu.editOrder', '', NULL, 0, 0, 0, '[]', '[]', 0, NULL, 0, 0, NULL, NULL, NULL, NULL, NULL, 1, NULL, '2025-07-14 10:24:39.847378', '2025-07-14 12:07:57.120735', 52);
INSERT INTO `menu` VALUES (57, 'OrderDetail', 'orderDetail', '/order/detail/:id', '/src/views/order/detail.vue', '', 'order.menu.orderDetail', '', NULL, 0, 0, 0, '[]', '[]', 0, NULL, 0, 0, NULL, NULL, NULL, NULL, NULL, 1, NULL, '2025-07-14 10:26:01.051263', '2025-07-14 12:08:03.199974', 52);

SET FOREIGN_KEY_CHECKS = 1;
