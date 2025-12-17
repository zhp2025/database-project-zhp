"""
地方文书管理系统 - 数据模型与常用数据库操作

说明：
- 使用 SQLAlchemy 连接 MySQL，并通过 ORM 定义核心数据表模型：
  User（用户）、Document（文书）、Resource（资源）、Note（笔记）、Favorite（收藏）
- 提供若干函数完成实验/课程要求的“数据库基本功能 + 高级功能”示例。

在使用前，请先确保已经在 MySQL 中执行过 `db.sql` 中的建库和建表语句。
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy import (
    Column,
    BigInteger,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    create_engine,
    func,
    text,
)
from sqlalchemy.orm import declarative_base, relationship, Session, sessionmaker

# ============================================================
# 1. 数据库连接配置
# ============================================================

DB_HOST = "localhost"
DB_PORT = 3306
DB_USER = "root"
DB_PASSWORD = "M17382930994c@"
DB_NAME = "our_document"

DATABASE_URL = (
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    "?charset=utf8mb4"
)

# 创建 SQLAlchemy Engine 和 Session 工厂
engine = create_engine(
    DATABASE_URL,
    echo=False,  # 调试时可设为 True 观察 SQL
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

Base = declarative_base()


def get_session() -> Session:
    """获取一个新的数据库会话。调用方用完后需要手动关闭。"""

    return SessionLocal()


# ============================================================
# 2. ORM 模型定义
#    对应 db.sql 中的各个表
# ============================================================


class User(Base):
    """用户信息，对应表 user_info"""

    __tablename__ = "user_info"

    user_id = Column(BigInteger, primary_key=True, autoincrement=True)
    username = Column(String(30), unique=True, nullable=False)
    user_email = Column(String(30), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    pr_question = Column(Text)
    pr_answer = Column(Text)

    # 关系
    notes = relationship("Note", back_populates="user")
    favorites = relationship("Favorite", back_populates="user")


class Document(Base):
    """文书信息，对应表 document_info"""

    __tablename__ = "document_info"

    document_id = Column(BigInteger, primary_key=True, autoincrement=True)
    document_name = Column(String(255), unique=True, nullable=False)
    document_region = Column(String(255))
    document_intro = Column(Text)
    document_cover = Column(
        # 实际存储为 BLOB，ORM 中可以按 bytes 类型映射
        # 这里不直接操作封面图片，仅保留字段
        # MySQL BLOB 默认映射为 LargeBinary
        # 为简洁起见此处使用 Text/bytes 皆可，不影响查询示例
        Text
    )

    # 关系
    resources = relationship("Resource", back_populates="document")
    # Note: notes和favorites现在通过resource间接访问（符合第三范式）


class Resource(Base):
    """资源内容，对应表 resource_content"""

    __tablename__ = "resource_content"

    resource_id = Column(BigInteger, primary_key=True, autoincrement=True)
    document_id = Column(BigInteger, ForeignKey("document_info.document_id"), nullable=False)
    resource_name = Column(String(255), unique=True, nullable=False)
    resource_type = Column(String(255))
    original_text = Column(Text)
    simplified_text = Column(Text)
    vernacular_translation = Column(Text)

    document = relationship("Document", back_populates="resources")
    notes = relationship("Note", back_populates="resource")
    favorites = relationship("Favorite", back_populates="resource")


class Note(Base):
    """用户笔记，对应表 annotation"""

    __tablename__ = "annotation"

    annotation_id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("user_info.user_id"), nullable=False)
    resource_id = Column(BigInteger, ForeignKey("resource_content.resource_id"), nullable=False)
    annotation_content = Column(Text)
    annotation_tags = Column(String(20))
    annotation_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    update_time = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="notes")
    resource = relationship("Resource", back_populates="notes")
    
    # 通过resource访问document（消除传递依赖）
    @property
    def document(self):
        """通过resource访问document"""
        return self.resource.document if self.resource else None


class Favorite(Base):
    """收藏信息，对应表 collection_info"""

    __tablename__ = "collection_info"

    collection_id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("user_info.user_id"), nullable=False)
    resource_id = Column(BigInteger, ForeignKey("resource_content.resource_id"), nullable=False)
    collection_tags = Column(String(20))
    collection_time = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="favorites")
    resource = relationship("Resource", back_populates="favorites")
    
    # 通过resource访问document（消除传递依赖）
    @property
    def document(self):
        """通过resource访问document"""
        return self.resource.document if self.resource else None


# 视图模型（只读），以文书资源统计视图为例
class DocumentStats(Base):
    """文书统计视图，对应视图 v_document_resource_stats（只读）"""

    __tablename__ = "v_document_resource_stats"
    __table_args__ = {"info": {"is_view": True}}

    document_id = Column(BigInteger, primary_key=True)
    document_name = Column(String(255))
    document_region = Column(String(255))
    resource_count = Column(Integer)
    image_count = Column(Integer)
    collection_count = Column(Integer)
    annotation_count = Column(Integer)


# ============================================================
# 3. 基本查询功能（对应题目 b.i ~ b.vi）
# ============================================================


def get_resources_by_document(session: Session, document_id: int) -> List[Resource]:
    """b.i 查询某一文书的所有资源列表"""

    return (
        session.query(Resource)
        .filter(Resource.document_id == document_id)
        .order_by(Resource.resource_id)
        .all()
    )


def get_documents_by_author(session: Session, author: str) -> List[Document]:
    """
    b.ii 查询特定作者的所有文书

    说明：作者字段在 resource_info（资源信息表）中，这里通过原生 SQL 进行一次简单关联查询：
    document_info ← resource_content ← resource_info
    """

    sql = text(
        """
        SELECT DISTINCT d.*
        FROM document_info d
        JOIN resource_content rc ON d.document_id = rc.document_id
        JOIN resource_info ri ON rc.resource_id = ri.resource_id
        WHERE ri.author = :author
        """
    )
    result = session.execute(sql, {"author": author})
    # 使用 ORM 的映射加载 Document
    document_ids = [row.document_id for row in result]
    if not document_ids:
        return []
    return (
        session.query(Document)
        .filter(Document.document_id.in_(document_ids))
        .order_by(Document.document_id)
        .all()
    )


def search_transcription_by_keyword(session: Session, keyword: str) -> List[Resource]:
    """
    b.iii 查询包含特定关键词的转录文本

    这里使用 LIKE 方式在 simplified_text / vernacular_translation 中模糊匹配。
    （如果已建立全文索引，可使用 fulltext_search_resources 函数）
    """

    pattern = f"%{keyword}%"
    return (
        session.query(Resource)
        .filter(
            (Resource.simplified_text.ilike(pattern))
            | (Resource.vernacular_translation.ilike(pattern))
        )
        .all()
    )


def get_favorite_documents_by_user(session: Session, user_id: int) -> List[Document]:
    """b.iv 查询某个用户收藏的文书"""

    return (
        session.query(Document)
        .join(Resource, Resource.document_id == Document.document_id)
        .join(Favorite, Favorite.resource_id == Resource.resource_id)
        .filter(Favorite.user_id == user_id)
        .distinct()
        .order_by(Document.document_id)
        .all()
    )


def count_resources_by_document(session: Session, document_id: int) -> int:
    """b.v 统计某个文书的资源数量"""

    return (
        session.query(func.count(Resource.resource_id))
        .filter(Resource.document_id == document_id)
        .scalar()
        or 0
    )


def count_resources_by_document_and_type(
    session: Session, document_id: int, resource_type: str
) -> int:
    """b.vi 统计某个文书中某种类型文书资源数量"""

    return (
        session.query(func.count(Resource.resource_id))
        .filter(
            Resource.document_id == document_id,
            Resource.resource_type == resource_type,
        )
        .scalar()
        or 0
    )


# ============================================================
# 4. 高级功能：存储过程 / 触发器 / 视图 / 全文检索
# ============================================================


def init_advanced_db_features(session: Session) -> None:
    """
    在数据库中初始化高级特性：
    - 存储过程：批量插入新的文书及其资源
    - 触发器：自动维护 annotation 表的时间字段
    - 全文索引：为资源转录文本建立 FULLTEXT 索引

    注意：该函数设计为幂等，多次执行不会报错（利用 IF NOT EXISTS 判断）。
    """

    # 1) 存储过程：批量导入新文书记录（示例）
    # 作用：接收文书名称和简介，插入 document_info，并返回新 ID
    session.execute(
        text(
            """
        DROP PROCEDURE IF EXISTS sp_insert_document;
        """
        )
    )

    session.execute(
        text(
            """
        CREATE PROCEDURE sp_insert_document(
            IN p_name VARCHAR(255),
            IN p_region VARCHAR(255),
            IN p_intro TEXT
        )
        BEGIN
            INSERT INTO document_info(document_name, document_region, document_intro)
            VALUES(p_name, p_region, p_intro);
            SELECT LAST_INSERT_ID() AS document_id;
        END;
        """
        )
    )

    # 2) 触发器：自动维护 annotation 的时间字段
    session.execute(text("DROP TRIGGER IF EXISTS trg_annotation_before_insert;"))
    session.execute(text("DROP TRIGGER IF EXISTS trg_annotation_before_update;"))

    session.execute(
        text(
            """
        CREATE TRIGGER trg_annotation_before_insert
        BEFORE INSERT ON annotation
        FOR EACH ROW
        BEGIN
            IF NEW.annotation_time IS NULL THEN
                SET NEW.annotation_time = NOW();
            END IF;
            SET NEW.update_time = NEW.annotation_time;
        END;
        """
        )
    )

    session.execute(
        text(
            """
        CREATE TRIGGER trg_annotation_before_update
        BEFORE UPDATE ON annotation
        FOR EACH ROW
        BEGIN
            SET NEW.update_time = NOW();
        END;
        """
        )
    )

    # 3) 全文索引：在资源转录文本上建立 FULLTEXT 索引
    # MySQL 5.6+ InnoDB 支持 FULLTEXT，注意只在文本字段上建立。
    session.execute(
        text(
            """
        ALTER TABLE resource_content
        ADD FULLTEXT INDEX IF NOT EXISTS ft_resource_text
        (original_text, simplified_text, vernacular_translation);
        """
        )
    )

    session.commit()


def call_insert_document_procedure(
    session: Session, name: str, region: Optional[str], intro: Optional[str]
) -> int:
    """
    调用存储过程 sp_insert_document，插入一条文书记录并返回新 document_id。
    （对应高级功能 c.i 存储）
    """

    result = session.execute(
        text("CALL sp_insert_document(:name, :region, :intro);"),
        {"name": name, "region": region, "intro": intro},
    )
    row = result.fetchone()
    # 存储过程中 SELECT LAST_INSERT_ID() AS document_id
    return int(row.document_id) if row and hasattr(row, "document_id") else 0


def fulltext_search_resources(session: Session, keyword: str) -> List[Resource]:
    """
    使用 MySQL FULLTEXT 进行全文检索（对应高级功能 c.iv 全文检索）。

    依赖：已经通过 init_advanced_db_features 建立 FULLTEXT 索引。
    """

    # MATCH AGAINST 只能通过 text() 写原生 SQL
    sql = text(
        """
        SELECT *
        FROM resource_content
        WHERE MATCH(original_text, simplified_text, vernacular_translation)
              AGAINST (:kw IN NATURAL LANGUAGE MODE)
        """
    )
    result = session.execute(sql, {"kw": keyword})
    resource_ids = [row.resource_id for row in result]
    if not resource_ids:
        return []
    return (
        session.query(Resource)
        .filter(Resource.resource_id.in_(resource_ids))
        .all()
    )


def get_document_stats(session: Session) -> List[DocumentStats]:
    """
    示例：通过视图 v_document_resource_stats 查询文书的资源/收藏/笔记统计信息。
    （对应高级功能 c.iii 视图）
    """

    return session.query(DocumentStats).order_by(DocumentStats.document_id).all()


# ============================================================
# 5. 文书的增删改查封装（示例）
# ============================================================


def create_document(
    session: Session,
    name: str,
    region: Optional[str] = None,
    intro: Optional[str] = None,
) -> Document:
    """创建（新增）文书记录"""

    doc = Document(document_name=name, document_region=region, document_intro=intro)
    session.add(doc)
    session.commit()
    session.refresh(doc)
    return doc


def get_document_by_id(session: Session, document_id: int) -> Optional[Document]:
    """按主键查询单个文书"""

    return session.get(Document, document_id)


def update_document(
    session: Session,
    document_id: int,
    name: Optional[str] = None,
    region: Optional[str] = None,
    intro: Optional[str] = None,
) -> Optional[Document]:
    """编辑（更新）文书信息"""

    doc = session.get(Document, document_id)
    if not doc:
        return None

    if name is not None:
        doc.document_name = name
    if region is not None:
        doc.document_region = region
    if intro is not None:
        doc.document_intro = intro

    session.commit()
    session.refresh(doc)
    return doc


def delete_document(session: Session, document_id: int) -> bool:
    """删除文书（级联删除其资源、收藏、笔记等，依赖外键的 ON DELETE CASCADE 设置）"""

    doc = session.get(Document, document_id)
    if not doc:
        return False
    session.delete(doc)
    session.commit()
    return True


# ============================================================
# 6. 简单演示（可选）
#    直接运行本文件时，可做一次连通性与功能测试
# ============================================================

if __name__ == "__main__":
    # 简单自测：仅在命令行执行 python model.py 时运行
    with get_session() as s:
        # 初始化高级特性（若已在数据库中创建过，可注释掉）
        try:
            init_advanced_db_features(s)
        except Exception as exc:  # pragma: no cover - 仅用于调试输出
            print("初始化高级特性时出错：", exc)

        # 打印当前文书统计信息（来自视图）
        stats: List[Tuple[int, str, int]] = [
            (st.document_id, st.document_name, st.resource_count)
            for st in get_document_stats(s)
        ]
        print("当前文书统计（document_id, document_name, resource_count）:", stats)


