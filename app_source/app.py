from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from model import get_session, User

# 先创建 app（最重要的一行）
app = Flask(__name__)
app.secret_key = "dev"

# 配置 Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# 用户加载器函数
@login_manager.user_loader
def load_user(user_id):
    session = get_session()
    try:
        return session.query(User).get(int(user_id))
    finally:
        session.close()

# 上下文处理器
@app.context_processor
def inject_globals():
    return {
        "current_user": current_user,
        "current_year": datetime.now().year
    }

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
@app.route("/")
def index():
    return redirect(url_for("documents"))

@app.route('/home')
def home():
    return render_template('home.html')

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        
        session = get_session()
        try:
            # 尝试通过用户名或邮箱查找用户
            user = session.query(User).filter((User.username == username) | (User.user_email == username)).first()
            
            if user and check_password_hash(user.password, password):
                login_user(user)
                flash("登录成功！", "success")
                return redirect(url_for("documents"))
            else:
                flash("用户名/邮箱或密码错误", "error")
        finally:
            session.close()
    
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        password2 = request.form["password2"]
        
        if password != password2:
            flash("两次输入的密码不一致", "error")
            return redirect(url_for("register"))
        
        session = get_session()
        try:
            # 检查用户名是否已存在
            existing_user = session.query(User).filter(User.username == username).first()
            if existing_user:
                flash("用户名已存在", "error")
                return redirect(url_for("register"))
            
            # 检查邮箱是否已存在
            existing_email = session.query(User).filter(User.user_email == email).first()
            if existing_email:
                flash("邮箱已被注册", "error")
                return redirect(url_for("register"))
            
            # 创建新用户
            hashed_password = generate_password_hash(password)
            new_user = User(username=username, user_email=email, password=hashed_password)
            session.add(new_user)
            session.commit()
            
            flash("注册成功！请登录", "success")
            return redirect(url_for("login"))
        finally:
            session.close()
    
    return render_template("register.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("已成功登出", "success")
    return redirect(url_for("login"))

# 基本路由 - 保持原有结构但不实现具体功能
@app.route("/documents")
def documents():
    return render_template("documents.html", documents=FAKE_DOCS)

@app.route("/documents/<int:doc_id>")
def document_detail(doc_id):
    doc = next((d for d in FAKE_DOCS if d["id"] == doc_id), None)
    return render_template("document_detail.html", doc=doc, notes=[])

@app.route("/search")
def search():
    return render_template("search_results.html", results=FAKE_DOCS)

# 保留路由但不实现具体功能（由其他同学实现）
@app.route("/favorites")
def favorites():
    return render_template("favorite_documents.html", favorites=[])

@app.route("/favorites/toggle/<int:doc_id>", methods=["POST"])
def toggle_favorite(doc_id):
    return {"ok": True, "favorited": False}

@app.route("/notes")
def notes():
    return render_template("notes.html", notes=[])

@app.route("/history")
def history():
    return render_template("reading_history.html", history=[])

# 5️⃣ 最后才 run
if __name__ == "__main__":
    app.run(debug=True)