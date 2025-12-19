"""
地方文书管理系统 - 核心路由与功能实现
覆盖：用户认证、文书CRUD、笔记/收藏/阅读记录功能
"""
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# 导入model.py的核心模型与函数（适配db.sql）
from model import (
    get_session, User, Document, Resource, Note, Favorite, AccessRecord, ResourceInfo,
    get_resources_by_document, get_document_by_id, create_document, update_document, delete_document,
    create_note, get_notes_by_user, get_notes_by_resource, update_note, delete_note,
    toggle_favorite, is_resource_favorited,
    create_access_record, get_access_records_by_user,
    get_favorite_documents_by_user, fulltext_search_resources, count_resources_by_document
)

from sqlalchemy import or_


# ============================================================
# 1. Flask应用初始化
# ============================================================
app = Flask(__name__)
app.secret_key = "dev"  # 生产环境需改为随机秘钥
app.config['PERMANENT_SESSION_LIFETIME'] = 3600 * 24  # 会话有效期1天

# 配置Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # 未登录跳转页
login_manager.login_message = "请先登录后再操作"
login_manager.login_message_category = "warning"

# ============================================================
# 2. Flask-Login核心函数
# ============================================================
@login_manager.user_loader
def load_user(user_id):
    """加载用户（Flask-Login必需）"""
    session = get_session()
    try:
        return session.query(User).get(int(user_id))
    finally:
        session.close()

# ============================================================
# 3. 全局上下文处理器
# ============================================================
@app.context_processor
def inject_globals():
    """全局模板变量"""
    return {
        "current_user": current_user,
        "current_year": datetime.now().year,
        "app_name": "地方文书管理系统"
    }


# ============================================================
# 4. 错误处理
# ============================================================
@app.errorhandler(404)
def page_not_found(e):
    """404页面"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    """500页面"""
    return render_template('500.html'), 500

# 3️⃣ 假数据（用于临时展示，后续可替换为数据库查询）
FAKE_DOCS = [
    {
        "id": 1,
        "title": "出师表",
        "author": "诸葛亮",
        "period": "三国",
        "year": "建兴五年",
        "tags": "奏表,政治",
        "content": "臣亮言：先帝创业未半而中道崩殂……\n愿陛下托臣以讨贼兴复之效……"
    },
    {
        "id": 2,
        "title": "岳阳楼记",
        "author": "范仲淹",
        "period": "北宋",
        "year": "庆历六年",
        "tags": "散文,山水",
        "content": "庆历四年春，滕子京谪守巴陵郡……\n不以物喜，不以己悲……"
    },
]

# 4️⃣ 路由 - 只保留用户认证相关和基本路由
@app.route('/home')
def home():
    return render_template('home.html')


# ============================================================
# 5. 用户认证路由（登录/注册/登出）
# ============================================================
@app.route("/login", methods=["GET", "POST"])
def login():
    """用户登录"""
    # 已登录用户直接跳转
    if current_user.is_authenticated:
        return redirect(url_for("documents"))
    
    if request.method == "POST":
        # 获取表单数据
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        
        # 基础校验
        if not username or not password:
            flash("用户名/邮箱和密码不能为空", "error")
            return render_template("login.html")
        
        # 数据库查询
        session = get_session()
        try:
            # 支持用户名/邮箱登录
            user = session.query(User).filter(
                (User.username == username) | (User.user_email == username)
            ).first()
            
            # 验证密码
            if user and check_password_hash(user.password, password):
                login_user(user)  # 登录用户
                flash("登录成功！", "success")
                # 跳转到之前的页面（如果有）
                next_page = request.args.get('next')
                return redirect(next_page or url_for("documents"))
            else:
                flash("用户名/邮箱或密码错误", "error")
        except Exception as e:
            flash(f"登录失败：{str(e)}", "error")
        finally:
            session.close()
    
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    """用户注册"""
    # 已登录用户直接跳转
    if current_user.is_authenticated:
        return redirect(url_for("documents"))
    
    if request.method == "POST":
        # 获取表单数据
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()
        password2 = request.form.get("password2", "").strip()
        pr_question = request.form.get("pr_question", "").strip()
        pr_answer = request.form.get("pr_answer", "").strip()
        
        # 基础校验
        if not username or not email or not password:
            flash("用户名、邮箱、密码不能为空", "error")
            return render_template("register.html")
        if password != password2:
            flash("两次输入的密码不一致", "error")
            return render_template("register.html")
        if len(password) < 6:
            flash("密码长度不能少于6位", "error")
            return render_template("register.html")
        
        # 数据库操作
        session = get_session()
        try:
            # 检查用户名/邮箱是否已存在
            if session.query(User).filter(User.username == username).first():
                flash("用户名已存在", "error")
                return render_template("register.html")
            if session.query(User).filter(User.user_email == email).first():
                flash("邮箱已被注册", "error")
                return render_template("register.html")
            
            # 创建新用户（密码加密）
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
            new_user = User(
                username=username,
                user_email=email,
                password=hashed_password,
                pr_question=pr_question,
                pr_answer=pr_answer
            )
            session.add(new_user)
            session.commit()
            
            flash("注册成功！请登录", "success")
            return redirect(url_for("login"))
        except Exception as e:
            flash(f"注册失败：{str(e)}", "error")
        finally:
            session.close()
    
    return render_template("register.html")

@app.route("/logout")
@login_required
def logout():
    """用户登出"""
    logout_user()
    flash("已成功登出", "success")
    return redirect(url_for("login"))

# ============================================================
# 6. 核心路由（首页/主页）
# ============================================================
@app.route("/")
def index():
    """首页（重定向到文书列表）"""
    return redirect(url_for("documents"))

@app.route('/home')
def home():
    """系统主页（展示统计信息）"""
    session = get_session()
    try:
        from model import get_document_stats
        stats = get_document_stats(session)
        total_docs = len(stats)
        total_resources = sum([stat.resource_count for stat in stats])
        total_collections = sum([stat.collection_count for stat in stats])
        total_notes = sum([stat.annotation_count for stat in stats])
        
        return render_template(
            'home.html',
            total_docs=total_docs,
            total_resources=total_resources,
            total_collections=total_collections,
            total_notes=total_notes
        )
    except Exception as e:
        flash(f"加载主页失败：{str(e)}", "error")
        return render_template('home.html')
    finally:
        session.close()

# ============================================================
# 7. 文书管理路由（CRUD）
# ============================================================
@app.route("/documents")
def documents():
    """文书列表页"""
    session = get_session()
    try:
        # 查询所有文书
        docs = session.query(Document).order_by(Document.document_id).all()
        docs_list = []
        
        for doc in docs:
            # 统计资源数
            resource_count = count_resources_by_document(session, doc.document_id)
            # 获取第一个资源的作者（示例）
            author = "未知"
            first_resource = session.query(Resource).filter(Resource.document_id == doc.document_id).first()
            if first_resource:
                res_info = session.query(ResourceInfo).filter(ResourceInfo.resource_id == first_resource.resource_id).first()
                if res_info and res_info.author:
                    author = res_info.author
            
            docs_list.append({
                "id": doc.document_id,
                "title": doc.document_name,
                "author": author,
                "region": doc.document_region,
                "intro": doc.document_intro[:100] + "..." if doc.document_intro else "",
                "resource_count": resource_count
            })
        
        return render_template("documents.html", documents=docs_list)
    except Exception as e:
        flash(f"加载文书列表失败：{str(e)}", "error")
        return render_template("documents.html", documents=[])
    finally:
        session.close()

@app.route("/documents/<int:doc_id>")
def document_detail(doc_id):
    """文书详情页"""
    session = get_session()
    try:
        # 查询文书基本信息
        doc = get_document_by_id(session, doc_id)
        if not doc:
            flash("文书不存在", "error")
            return redirect(url_for("documents"))
        
        # 查询文书下的所有资源
        resources = get_resources_by_document(session, doc_id)
        resource_list = []
        
        # 组装资源数据（含收藏状态、笔记）
        current_user_id = current_user.user_id if current_user.is_authenticated else 0
        for res in resources:
            # 收藏状态
            is_favorited = is_resource_favorited(session, current_user_id, res.resource_id) if current_user_id else False
            # 资源笔记
            notes = get_notes_by_resource(session, res.resource_id)
            note_list = [{
                "id": n.annotation_id,
                "content": n.annotation_content,
                "tags": n.annotation_tags,
                "time": n.update_time.strftime("%Y-%m-%d %H:%M"),
                "is_owner": n.user_id == current_user_id if current_user.is_authenticated else False
            } for n in notes]
            # 资源信息（作者/年代）
            res_info = session.query(ResourceInfo).filter(ResourceInfo.resource_id == res.resource_id).first()
            author = res_info.author if res_info else "未知"
            dynasty = res_info.dynasty_period if res_info else "未知"
            
            resource_list.append({
                "id": res.resource_id,
                "name": res.resource_name,
                "type": res.resource_type,
                "author": author,
                "dynasty": dynasty,
                "original_text": res.original_text,
                "simplified_text": res.simplified_text,
                "vernacular_translation": res.vernacular_translation,
                "is_favorited": is_favorited,
                "notes": note_list
            })
        
        # 文书基本信息
        doc_detail = {
            "id": doc.document_id,
            "title": doc.document_name,
            "region": doc.document_region,
            "intro": doc.document_intro,
            "resource_count": len(resources)
        }
        
        return render_template(
            "document_detail.html",
            doc=doc_detail,
            resources=resource_list,
            current_user_id=current_user_id
        )
    except Exception as e:
        flash(f"加载文书详情失败：{str(e)}", "error")
        return redirect(url_for("documents"))
    finally:
        session.close()

@app.route("/documents/add", methods=["GET", "POST"])
@login_required
def add_document():
    """添加文书"""
    if request.method == "POST":
        # 获取表单数据
        name = request.form.get("name", "").strip()
        region = request.form.get("region", "").strip()
        intro = request.form.get("intro", "").strip()
        
        # 基础校验
        if not name:
            flash("文书名称不能为空", "error")
            return render_template("add_document.html")
        
        # 数据库操作
        session = get_session()
        try:
            # 检查名称是否重复
            if session.query(Document).filter(Document.document_name == name).first():
                flash("文书名称已存在", "error")
                return render_template("add_document.html")
            
            # 创建文书
            create_document(session, name=name, region=region, intro=intro)
            flash("文书添加成功！", "success")
            return redirect(url_for("documents"))
        except Exception as e:
            flash(f"添加文书失败：{str(e)}", "error")
        finally:
            session.close()
    
    return render_template("add_document.html")

@app.route("/documents/edit/<int:doc_id>", methods=["GET", "POST"])
@login_required
def edit_document(doc_id):
    """编辑文书"""
    session = get_session()
    try:
        # 查询文书
        doc = get_document_by_id(session, doc_id)
        if not doc:
            flash("文书不存在", "error")
            return redirect(url_for("documents"))
        
        if request.method == "POST":
            # 获取表单数据
            name = request.form.get("name", "").strip()
            region = request.form.get("region", "").strip()
            intro = request.form.get("intro", "").strip()
            
            # 基础校验
            if not name:
                flash("文书名称不能为空", "error")
                return render_template("edit_document.html", doc=doc)
            
            # 检查名称重复（排除自身）
            if session.query(Document).filter(
                Document.document_name == name,
                Document.document_id != doc_id
            ).first():
                flash("文书名称已存在", "error")
                return render_template("edit_document.html", doc=doc)
            
            # 更新文书
            update_document(session, doc_id, name=name, region=region, intro=intro)
            flash("文书编辑成功！", "success")
            return redirect(url_for("document_detail", doc_id=doc_id))
        
        return render_template("edit_document.html", doc=doc)
    except Exception as e:
        flash(f"编辑文书失败：{str(e)}", "error")
        return redirect(url_for("documents"))
    finally:
        session.close()

@app.route("/documents/delete/<int:doc_id>", methods=["POST"])
@login_required
def delete_document_route(doc_id):
    """删除文书（POST请求）"""
    session = get_session()
    try:
        # 删除文书
        if delete_document(session, doc_id):
            flash("文书删除成功！", "success")
        else:
            flash("文书不存在", "error")
    except Exception as e:
        flash(f"删除文书失败：{str(e)}", "error")
    finally:
        session.close()
    
    return redirect(url_for("documents"))

# ============================================================
# 8. 搜索路由
# ============================================================
@app.route("/search")
def search():
    """全文搜索"""
    keyword = request.args.get("keyword", "").strip()
    results = []
    
    if keyword:
        session = get_session()
        try:
            # 全文检索资源
            resources = fulltext_search_resources(session, keyword)
            current_user_id = current_user.user_id if current_user.is_authenticated else 0
            
            for res in resources:
                # 收藏状态
                is_favorited = is_resource_favorited(session, current_user_id, res.resource_id) if current_user_id else False
                # 文书信息
                doc = get_document_by_id(session, res.document_id)
                
                results.append({
                    "id": res.resource_id,
                    "title": res.resource_name,
                    "document_title": doc.document_name if doc else "未知",
                    "content": res.simplified_text[:200] + "..." if res.simplified_text else "",
                    "is_favorited": is_favorited
                })
        except Exception as e:
            flash(f"搜索失败：{str(e)}", "error")
        finally:
            session.close()
    
    return render_template("search_results.html", results=results, keyword=keyword)

# ============================================================
# 9. 收藏功能路由
# ============================================================
@app.route("/favorites")
@login_required
def favorites():
    """我的收藏"""
    session = get_session()
    try:
        # 查询用户收藏的文书
        favorite_docs = get_favorite_documents_by_user(session, current_user.user_id)
        favorites_list = []
        
        for doc in favorite_docs:
            # 查询文书下的收藏资源
            resources = get_resources_by_document(session, doc.document_id)
            fav_resources = []
            
            for res in resources:
                if is_resource_favorited(session, current_user.user_id, res.resource_id):
                    # 查询收藏信息
                    fav = session.query(Favorite).filter(
                        Favorite.user_id == current_user.user_id,
                        Favorite.resource_id == res.resource_id
                    ).first()
                    
                    fav_resources.append({
                        "id": res.resource_id,
                        "name": res.resource_name,
                        "tags": fav.collection_tags if fav else "",
                        "time": fav.collection_time.strftime("%Y-%m-%d %H:%M") if fav else ""
                    })
            
            if fav_resources:  # 只展示有收藏资源的文书
                favorites_list.append({
                    "id": doc.document_id,
                    "title": doc.document_name,
                    "intro": doc.document_intro[:100] + "..." if doc.document_intro else "",
                    "resources": fav_resources
                })
        
        return render_template("favorite_documents.html", favorites=favorites_list)
    except Exception as e:
        flash(f"加载收藏列表失败：{str(e)}", "error")
        return render_template("favorite_documents.html", favorites=[])
    finally:
        session.close()

@app.route("/favorites/toggle/<int:resource_id>", methods=["POST"])
@login_required
def toggle_favorite_route(resource_id):
    """切换收藏状态（AJAX接口）"""
    tags = request.form.get("tags", "").strip()
    session = get_session()
    
    try:
        # 切换收藏
        success, favorited = toggle_favorite(session, current_user.user_id, resource_id, tags)
        
        if success:
            msg = "收藏成功" if favorited else "取消收藏成功"
            return jsonify({"ok": True, "favorited": favorited, "msg": msg})
        else:
            return jsonify({"ok": False, "msg": "操作失败"}), 500
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)}), 500
    finally:
        session.close()

# ============================================================
# 10. 笔记功能路由
# ============================================================
@app.route("/notes")
@login_required
def notes():
    """我的笔记"""
    session = get_session()
    try:
        # 查询用户所有笔记
        user_notes = get_notes_by_user(session, current_user.user_id)
        notes_list = []
        
        for note in user_notes:
            # 关联资源和文书
            res = get_document_by_id(session, note.resource_id)  # 此处应为Resource，修正：
            res = session.query(Resource).get(note.resource_id)
            doc = get_document_by_id(session, res.document_id) if res else None
            
            notes_list.append({
                "id": note.annotation_id,
                "content": note.annotation_content,
                "tags": note.annotation_tags,
                "resource_name": res.resource_name if res else "未知",
                "document_name": doc.document_name if doc else "未知",
                "update_time": note.update_time.strftime("%Y-%m-%d %H:%M")
            })
        
        return render_template("notes.html", notes=notes_list)
    except Exception as e:
        flash(f"加载笔记列表失败：{str(e)}", "error")
        return render_template("notes.html", notes=[])
    finally:
        session.close()

@app.route("/notes/add", methods=["POST"])
@login_required
def add_note():
    """添加笔记（AJAX接口）"""
    resource_id = request.form.get("resource_id")
    content = request.form.get("content", "").strip()
    tags = request.form.get("tags", "").strip()
    
    # 基础校验
    if not resource_id or not content:
        return jsonify({"ok": False, "msg": "资源ID和笔记内容不能为空"}), 400
    
    session = get_session()
    try:
        # 创建笔记
        create_note(session, current_user.user_id, int(resource_id), content, tags)
        return jsonify({"ok": True, "msg": "笔记添加成功"})
    except Exception as e:
        return jsonify({"ok": False, "msg": f"添加笔记失败：{str(e)}"}), 500
    finally:
        session.close()

@app.route("/notes/edit/<int:note_id>", methods=["POST"])
@login_required
def edit_note(note_id):
    """编辑笔记（AJAX接口）"""
    content = request.form.get("content", "").strip()
    tags = request.form.get("tags", "").strip()
    
    # 基础校验
    if not content:
        return jsonify({"ok": False, "msg": "笔记内容不能为空"}), 400
    
    session = get_session()
    try:
        # 验证笔记归属
        note = session.query(Note).get(note_id)
        if not note or note.user_id != current_user.user_id:
            return jsonify({"ok": False, "msg": "笔记不存在或无操作权限"}), 403
        
        # 更新笔记
        update_note(session, note_id, content, tags)
        return jsonify({"ok": True, "msg": "笔记编辑成功"})
    except Exception as e:
        return jsonify({"ok": False, "msg": f"编辑笔记失败：{str(e)}"}), 500
    finally:
        session.close()

@app.route("/notes/delete/<int:note_id>", methods=["POST"])
@login_required
def remove_note(note_id):
    """删除笔记（AJAX接口）"""
    session = get_session()
    try:
        # 验证笔记归属
        note = session.query(Note).get(note_id)
        if not note or note.user_id != current_user.user_id:
            return jsonify({"ok": False, "msg": "笔记不存在或无操作权限"}), 403
        
        # 删除笔记
        delete_note(session, note_id)
        return jsonify({"ok": True, "msg": "笔记删除成功"})
    except Exception as e:
        return jsonify({"ok": False, "msg": f"删除笔记失败：{str(e)}"}), 500
    finally:
        session.close()

# ============================================================
# 11. 阅读记录功能路由
# ============================================================
@app.route("/history")
@login_required
def history():
    """我的阅读记录"""
    session = get_session()
    try:
        # 查询用户阅读记录
        access_records = get_access_records_by_user(session, current_user.user_id)
        history_list = []
        
        for record in access_records:
            # 关联资源和文书
            res = session.query(Resource).get(record.resource_id)
            doc = get_document_by_id(session, res.document_id) if res else None
            
            history_list.append({
                "id": record.access_id,
                "resource_name": res.resource_name if res else "未知",
                "document_name": doc.document_name if doc else "未知",
                "read_time": record.access_time.strftime("%Y-%m-%d %H:%M"),
                "progress": record.read_progress
            })
        
        return render_template("reading_history.html", history=history_list)
    except Exception as e:
        flash(f"加载阅读记录失败：{str(e)}", "error")
        return render_template("reading_history.html", history=[])
    finally:
        session.close()

@app.route("/history/record/<int:resource_id>", methods=["POST"])
@login_required
def record_read_progress(resource_id):
    """记录阅读进度（AJAX接口）"""
    try:
        progress = int(request.form.get("progress", 0))
        # 限制进度范围
        progress = max(0, min(100, progress))
    except ValueError:
        return jsonify({"ok": False, "msg": "进度必须是数字"}), 400
    
    session = get_session()
    try:
        # 创建/更新阅读记录
        create_access_record(session, current_user.user_id, resource_id, progress)
        return jsonify({"ok": True, "msg": "阅读进度已记录"})
    except Exception as e:
        return jsonify({"ok": False, "msg": f"记录进度失败：{str(e)}"}), 500
    finally:
        session.close()

# ============================================================
# 12. 应用启动
# ============================================================
if __name__ == "__main__":
    # 开发环境：debug=True，生产环境需关闭
    app.run(host="0.0.0.0", port=5000, debug=True)