from flask import Flask, request, session, redirect, url_for, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = "your_secret_key"

# 使用環境變數 DATABASE_URL 設定 SQLAlchemy 的資料庫 URI
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# 定義使用者資料庫模型
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    score = db.Column(db.Integer, default=0)
    history = db.Column(db.String(500), default="")  # 儲存已回答題目的 ID，逗號分隔

# 定義題目資料庫模型
class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(500), nullable=False)
    answer = db.Column(db.String(100), nullable=False)

# 初始化資料庫
def init_app():
    with app.app_context():
        # 創建資料庫表格
        db.create_all()

        # 檢查題目資料是否已存在
        if Question.query.count() == 0:  # 只有在題目表格為空時才插入題目
            # 插入新題目
            questions = [
                Question(description="CMD-1", answer="Pomeloflag{01_HAHAHA_you_find_it}"),
                Question(description="CMD-2", answer="Pomeloflag{02_Base64_is_too_easy_to_you}"),
                Question(description="CMD-3", answer="Pomeloflag{03_LOL_is_a_good_game}"),
                Question(description="CMD-4", answer="Pomeloflag{04_Caesar_cipher_is_so_cool}"),
                Question(description="CMD-5", answer="Pomeloflag{05_VIP666}"),
                Question(description="CMD-6", answer="Pomeloflag{06_Heartbreak}"),
                Question(description="CMD-7", answer="Pomeloflag{07_ASCII_fun}"),
                Question(description="CMD-8", answer="Pomeloflag{08_Base_32_Skill_get}"),
                Question(description="CMD-9", answer="Pomeloflag{09_STORY_IS_ONGOING_AND_NEVER_DIED}"),
                Question(description="CMD-10", answer="Pomeloflag{10_OHTHEPASSWORDISTHISSTRING}"),
                Question(description="Web-1", answer="Pomeloflag{YoU_FOund_tHe_FLag_1}"),
                Question(description="Web-2", answer="Pomeloflag{You_FoUnd_THe_flAg_2}"),
                Question(description="Web-3", answer="Pomeloflag{yOu_foUNd_thE_flaG_3}"),
                Question(description="Web-4", answer="Pomeloflag{yOU_FOunD_THe_fLaG_4}"),
            ]
            db.session.add_all(questions)
            db.session.commit()
            print("題目資料已重新插入！")
        else:
            print("題目資料已經存在，不需要重新插入。")


# 啟動應用時執行初始化
init_app()

# 註冊頁面
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return "帳號已存在！<br><a href='/register'>重新註冊</a>"
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        return "註冊成功！<br><a href='/login'>登入</a>"
    return render_template('register.html')

# 登入頁面
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            session['username'] = username
            return redirect(url_for('home'))
        return "帳號或密碼錯誤！<br><a href='/login'>重新登入</a>"
    return render_template('login.html')

# 首頁（顯示題目列表）
@app.route('/')
def home():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    # 從資料庫獲取所有題目
    questions = Question.query.all()
    return render_template('home.html', questions=questions)

# 答題頁面
@app.route('/question/<int:question_id>')
def question_page(question_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    question = Question.query.get(question_id)
    if not question:
        return "找不到這個題目！", 404
    return render_template('question_page.html', question=question, question_id=question_id)

# 提交答案
@app.route('/submit/<int:question_id>', methods=['POST'])
def submit(question_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    user = User.query.filter_by(username=username).first()

    if not user:
        return redirect(url_for('login'))
    
    question = Question.query.get(question_id)
    if not question:
        return "找不到這個題目！", 404

    # 檢查使用者是否已經回答過該題目且答案是正確的
    answered_questions = user.history.split(",")[:-1]  # 去掉最後的空字符
    for q in answered_questions:
        parts = q.split("|")
        if len(parts) == 3:  # 確保格式正確：question_id|answered_time|result
            answered_question_id, answered_time, result = parts
            if answered_question_id == str(question_id) and result == "正確":
                return f"你已經正確回答過這個問題！<br><a href='/'>返回題目列表</a>"

    user_answer = request.form.get('answer')
    answered_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    if user_answer == question.answer:
        user.score += 10  # 答對加分
        result = "正確"
    else:
        result = "錯誤"
    
    # 在history中記錄回答結果，避免重複紀錄
    if user.history:
        user.history += f"{question_id}|{answered_time}|{result},"  # 記錄新回答
    else:
        user.history = f"{question_id}|{answered_time}|{result},"
    
    db.session.commit()
    
    if result == "正確":
        return f"答對了！<br><a href='/'>返回題目列表</a>"
    else:
        return f"答錯了，請再試一次！<br><a href='/question/{question_id}'>重新回答</a>"

# 登出
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

# 排行榜
@app.route('/ranking')
def ranking():
    if 'username' not in session:
        return redirect(url_for('login'))

    users = User.query.order_by(User.score.desc(), User.history).all()

    users_with_history = []
    for user in users:
        answered_questions = user.history.split(",")[:-1]  # 去掉最後的空字符
        answered_info = {}

        for q in answered_questions:
            parts = q.split("|")
            if len(parts) == 3:
                question_id, answered_time, result = parts
                question = Question.query.get(int(question_id))
                if question:
                    answered_info[question.description] = {"time": answered_time, "result": result}

        users_with_history.append({
            "username": user.username,
            "score": user.score,
            "answered_info": answered_info
        })

    return render_template('ranking.html', users=users_with_history, questions=Question.query.all())

# 刪除使用者
@app.route('/delete_user/<username>', methods=['POST'])
def delete_user(username):
    print(f"刪除使用者: {username}")  # 確認路由是否觸發
    if 'username' not in session:
        return redirect(url_for('login'))

    # 查找使用者資料
    user = User.query.filter_by(username=username).first()
    if not user:
        return f"找不到使用者 {username}！", 404

    # 刪除該使用者
    db.session.delete(user)
    db.session.commit()

    return redirect(url_for('ranking'))  # 刪除後重新導向排行榜頁面

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
