-- ============================================
-- 数据库：地方文书管理系统
-- 数据库名：our_document
-- ============================================

-- 创建数据库
CREATE DATABASE our_document 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

-- 使用数据库
USE our_document;

-- ============================================
-- 1. 文书信息表 (document_info)
-- ============================================
CREATE TABLE document_info (
    document_id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '文书ID（主键、自增）',
    document_name VARCHAR(255) NOT NULL UNIQUE COMMENT '文书名称（唯一性）',
    document_region VARCHAR(255) COMMENT '文书区域',
    document_intro TEXT COMMENT '文书简介',
    document_cover BLOB COMMENT '文书封面（二进制存储）',
    INDEX idx_document_region (document_region),
    INDEX idx_document_name (document_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用于存储集成文书的基本信息，供用户查询和管理员统一管理';

-- ============================================
-- 2. 资源内容表 (resource_content)
-- ============================================
CREATE TABLE resource_content (
    resource_id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '资源ID（主键、自增）',
    document_id BIGINT NOT NULL COMMENT '文书ID（外键）',
    resource_name VARCHAR(255) NOT NULL UNIQUE COMMENT '资源名称（唯一性）',
    resource_type VARCHAR(255) COMMENT '资源类型',
    original_text TEXT COMMENT '原文',
    simplified_text TEXT COMMENT '简体版全文',
    vernacular_translation TEXT COMMENT '白话文翻译',
    INDEX idx_document_id (document_id),
    INDEX idx_resource_name (resource_name),
    INDEX idx_resource_type (resource_type),
    FOREIGN KEY (document_id) REFERENCES document_info(document_id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='存储具体资源的内容，供查询和查看';

-- ============================================
-- 3. 资源信息表 (resource_info)
-- ============================================
CREATE TABLE resource_info (
    resource_id BIGINT PRIMARY KEY COMMENT '资源ID（主键）',
    document_id BIGINT NOT NULL COMMENT '文书ID（外键）',
    dynasty_period VARCHAR(255) COMMENT '年代',
    reign_title VARCHAR(255) COMMENT '年号',
    resource_region VARCHAR(255) COMMENT '资源区域（属地）',
    household_registry VARCHAR(255) COMMENT '归户',
    author VARCHAR(100) COMMENT '作者',
    INDEX idx_document_id (document_id),
    INDEX idx_dynasty_period (dynasty_period),
    INDEX idx_reign_title (reign_title),
    INDEX idx_resource_region (resource_region),
    INDEX idx_author (author),
    FOREIGN KEY (document_id) REFERENCES document_info(document_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (resource_id) REFERENCES resource_content(resource_id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='存储资源信息，主要供查询';

-- ============================================
-- 4. 资源图片表 (resource_image)
-- ============================================
CREATE TABLE resource_image (
    image_id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '图片ID（主键）',
    document_id BIGINT NOT NULL COMMENT '文书ID（外键）',
    resource_id BIGINT NOT NULL COMMENT '资源ID（外键）',
    page BIGINT COMMENT '页码',
    INDEX idx_document_id (document_id),
    INDEX idx_resource_id (resource_id),
    INDEX idx_page (page),
    INDEX idx_document_resource (document_id, resource_id),
    FOREIGN KEY (document_id) REFERENCES document_info(document_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (resource_id) REFERENCES resource_content(resource_id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用于存储文书对应的图片资源';

-- ============================================
-- 5. 资源载体表 (resource_carrier)
-- ============================================
CREATE TABLE resource_carrier (
    resource_id BIGINT PRIMARY KEY COMMENT '资源ID（主键）',
    document_id BIGINT NOT NULL COMMENT '文书ID（外键）',
    resource_material VARCHAR(255) COMMENT '文献材质',
    resource_dimensions VARCHAR(255) COMMENT '文献尺寸',
    INDEX idx_document_id (document_id),
    FOREIGN KEY (document_id) REFERENCES document_info(document_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (resource_id) REFERENCES resource_content(resource_id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='存储资源其他信息，一般情况下使用频率较低';

-- ============================================
-- 6. 用户信息表 (user_info)
-- ============================================
CREATE TABLE user_info (
    user_id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '用户ID（主键、自增）',
    username VARCHAR(30) NOT NULL UNIQUE COMMENT '用户名（唯一性）',
    user_email VARCHAR(30) NOT NULL UNIQUE COMMENT '用户邮箱（唯一性）',
    password VARCHAR(255) NOT NULL COMMENT '密码',
    pr_question TEXT COMMENT '问题（用户自定义，用于找回密码）',
    pr_answer TEXT COMMENT '答案（用户自定义，用于找回密码时匹配问题）',
    INDEX idx_username (username),
    INDEX idx_user_email (user_email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='存储用户信息，便于用户注册/登录';

-- ============================================
-- 7. 阅读记录表 (access_record)
-- ============================================
CREATE TABLE access_record (
    access_id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '阅读ID（主键、自增）',
    user_id BIGINT NOT NULL COMMENT '用户ID（外键，复合唯一约束的一部分）',
    document_id BIGINT NOT NULL COMMENT '文书ID（外键）',
    resource_id BIGINT NOT NULL COMMENT '资源ID（外键，复合唯一约束的一部分）',
    access_time DATETIME NOT NULL COMMENT '访问时间（记录最后访问时间，用于排序）',
    INDEX idx_user_id (user_id),
    INDEX idx_document_id (document_id),
    INDEX idx_resource_id (resource_id),
    INDEX idx_access_time (access_time),
    INDEX idx_user_resource (user_id, resource_id),
    UNIQUE KEY uk_user_resource (user_id, resource_id),
    FOREIGN KEY (user_id) REFERENCES user_info(user_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (document_id) REFERENCES document_info(document_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (resource_id) REFERENCES resource_content(resource_id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='存储用户访问信息，便于快速访问收藏的资源';

-- ============================================
-- 8. 收藏信息表 (collection_info)
-- ============================================
CREATE TABLE collection_info (
    collection_id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '收藏ID（主键、自增）',
    user_id BIGINT NOT NULL COMMENT '用户ID（外键，复合唯一约束的一部分）',
    document_id BIGINT NOT NULL COMMENT '文书ID（外键）',
    resource_id BIGINT NOT NULL COMMENT '资源ID（外键，复合唯一约束的一部分）',
    collection_tags VARCHAR(20) COMMENT '收藏标签',
    collection_time DATETIME NOT NULL COMMENT '收藏时间',
    INDEX idx_user_id (user_id),
    INDEX idx_document_id (document_id),
    INDEX idx_resource_id (resource_id),
    INDEX idx_collection_time (collection_time),
    INDEX idx_collection_tags (collection_tags),
    INDEX idx_user_resource (user_id, resource_id),
    UNIQUE KEY uk_user_resource (user_id, resource_id),
    FOREIGN KEY (user_id) REFERENCES user_info(user_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (document_id) REFERENCES document_info(document_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (resource_id) REFERENCES resource_content(resource_id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='存储用户收藏信息，便于快速访问收藏的资源';

-- ============================================
-- 9. 笔记表 (annotation)
-- ============================================
CREATE TABLE annotation (
    annotation_id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '注释ID（主键、自增）',
    user_id BIGINT NOT NULL COMMENT '用户ID（外键）',
    document_id BIGINT NOT NULL COMMENT '文书ID（外键）',
    resource_id BIGINT NOT NULL COMMENT '资源ID（外键）',
    annotation_content TEXT COMMENT '注释内容',
    annotation_tags VARCHAR(20) COMMENT '注释标签',
    annotation_time DATETIME NOT NULL COMMENT '注释时间',
    update_time DATETIME NOT NULL COMMENT '更新时间（初始为创建时间，同步为修改时间）',
    INDEX idx_user_id (user_id),
    INDEX idx_document_id (document_id),
    INDEX idx_resource_id (resource_id),
    INDEX idx_annotation_time (annotation_time),
    INDEX idx_update_time (update_time),
    INDEX idx_annotation_tags (annotation_tags),
    INDEX idx_user_resource (user_id, resource_id),
    FOREIGN KEY (user_id) REFERENCES user_info(user_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (document_id) REFERENCES document_info(document_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (resource_id) REFERENCES resource_content(resource_id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='存储用户注释信息，便于用户查看和访问注释对应的资源';

-- ============================================
-- 视图创建
-- ============================================

-- 视图1：完整的资源信息视图（包含文书、资源内容、资源信息）
CREATE VIEW v_resource_full AS
SELECT 
    d.document_id,
    d.document_name,
    d.document_region AS document_region,
    d.document_intro,
    rc.resource_id,
    rc.resource_name,
    rc.resource_type,
    rc.original_text,
    rc.simplified_text,
    rc.vernacular_translation,
    ri.dynasty_period,
    ri.reign_title,
    ri.resource_region,
    ri.household_registry,
    ri.author,
    rc_material.resource_material,
    rc_material.resource_dimensions
FROM document_info d
INNER JOIN resource_content rc ON d.document_id = rc.document_id
LEFT JOIN resource_info ri ON rc.resource_id = ri.resource_id
LEFT JOIN resource_carrier rc_material ON rc.resource_id = rc_material.resource_id;

-- 视图2：用户收藏详情视图
CREATE VIEW v_user_collections AS
SELECT 
    ci.collection_id,
    ci.user_id,
    u.username,
    ci.document_id,
    d.document_name,
    ci.resource_id,
    rc.resource_name,
    ci.collection_tags,
    ci.collection_time
FROM collection_info ci
INNER JOIN user_info u ON ci.user_id = u.user_id
INNER JOIN document_info d ON ci.document_id = d.document_id
INNER JOIN resource_content rc ON ci.resource_id = rc.resource_id;

-- 视图3：用户阅读记录详情视图
CREATE VIEW v_user_access_records AS
SELECT 
    ar.access_id,
    ar.user_id,
    u.username,
    ar.document_id,
    d.document_name,
    ar.resource_id,
    rc.resource_name,
    ar.access_time
FROM access_record ar
INNER JOIN user_info u ON ar.user_id = u.user_id
INNER JOIN document_info d ON ar.document_id = d.document_id
INNER JOIN resource_content rc ON ar.resource_id = rc.resource_id;

-- 视图4：用户笔记详情视图
CREATE VIEW v_user_annotations AS
SELECT 
    a.annotation_id,
    a.user_id,
    u.username,
    a.document_id,
    d.document_name,
    a.resource_id,
    rc.resource_name,
    a.annotation_content,
    a.annotation_tags,
    a.annotation_time,
    a.update_time
FROM annotation a
INNER JOIN user_info u ON a.user_id = u.user_id
INNER JOIN document_info d ON a.document_id = d.document_id
INNER JOIN resource_content rc ON a.resource_id = rc.resource_id;

-- 视图5：资源统计视图（每个资源的图片数量）
CREATE VIEW v_resource_image_count AS
SELECT 
    ri.resource_id,
    ri.document_id,
    rc.resource_name,
    COUNT(rimg.image_id) AS image_count,
    MAX(rimg.page) AS max_page
FROM resource_content rc
LEFT JOIN resource_image rimg ON rc.resource_id = rimg.resource_id
LEFT JOIN resource_info ri ON rc.resource_id = ri.resource_id
GROUP BY ri.resource_id, ri.document_id, rc.resource_name;

-- 视图6：文书资源统计视图
CREATE VIEW v_document_resource_stats AS
SELECT 
    d.document_id,
    d.document_name,
    d.document_region,
    COUNT(DISTINCT rc.resource_id) AS resource_count,
    COUNT(DISTINCT rimg.image_id) AS image_count,
    COUNT(DISTINCT ci.collection_id) AS collection_count,
    COUNT(DISTINCT a.annotation_id) AS annotation_count
FROM document_info d
LEFT JOIN resource_content rc ON d.document_id = rc.document_id
LEFT JOIN resource_image rimg ON rc.resource_id = rimg.resource_id
LEFT JOIN collection_info ci ON rc.resource_id = ci.resource_id
LEFT JOIN annotation a ON rc.resource_id = a.resource_id
GROUP BY d.document_id, d.document_name, d.document_region;

-- ============================================
-- 额外索引（优化查询性能）
-- ============================================

-- 为resource_content表的全文搜索创建索引（如果需要全文搜索）
-- ALTER TABLE resource_content ADD FULLTEXT INDEX ft_original_text (original_text);
-- ALTER TABLE resource_content ADD FULLTEXT INDEX ft_simplified_text (simplified_text);
-- ALTER TABLE resource_content ADD FULLTEXT INDEX ft_vernacular_translation (vernacular_translation);

-- 为document_info表的全文搜索创建索引
-- ALTER TABLE document_info ADD FULLTEXT INDEX ft_document_intro (document_intro);

-- 为annotation表的全文搜索创建索引
-- ALTER TABLE annotation ADD FULLTEXT INDEX ft_annotation_content (annotation_content);

-- ============================================
-- 完成
-- ============================================
