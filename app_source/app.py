from flask import Flask, render_template, request, redirect, url_for
from types import SimpleNamespace
from datetime import datetime

# 先创建 app（最重要的一行）
app = Flask(__name__)
app.secret_key = "dev"

# 再写 context_processor（此时 app 已存在）
@app.context_processor
def inject_globals():
    fake_user = SimpleNamespace(
        is_authenticated=False,
        username="访客"
    )
    return {
        "current_user": fake_user,
        "current_year": datetime.now().year
    }

# 3️⃣ 假数据
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

# 4️⃣ 路由
@app.route("/")
def index():
    return redirect(url_for("documents"))
@app.route('/home')
def home():
    return render_template('home.html')

@app.route("/login", methods=["GET", "POST"])
def login():
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    return render_template("register.html")

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

@app.route("/favorites")
def favorites():
    return render_template("favorite_documents.html", favorites=[FAKE_DOCS[0]])

@app.route("/favorites/toggle/<int:doc_id>", methods=["POST"])
def toggle_favorite(doc_id):
    return {"ok": True, "favorited": True}

@app.route("/notes")
def notes():
    return render_template("notes.html", notes=[])

@app.route("/history")
def history():
    return render_template("reading_history.html", history=[])

# 5️⃣ 最后才 run
if __name__ == "__main__":
    app.run(debug=True)
