
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    content = db.Column(db.Text)
    tags = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    author = db.Column(db.String(100))

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    content = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    posts = Post.query.order_by(Post.created_at.desc()).all()
    return render_template('index.html', posts=posts)

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        user = User(
            username=request.form['username'],
            email=request.form['email'],
            password=generate_password_hash(request.form['password'])
        )
        db.session.add(user)
        db.session.commit()
        flash('Registered successfully')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email']).first()

        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect(url_for('dashboard'))

        flash('Invalid credentials')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')

@app.route('/dashboard')
@login_required
def dashboard():
    posts = Post.query.filter_by(author=current_user.username).all()
    return render_template('dashboard.html', posts=posts)

@app.route('/create', methods=['GET','POST'])
@login_required
def create():
    if request.method == 'POST':
        post = Post(
            title=request.form['title'],
            content=request.form['content'],
            tags=request.form['tags'],
            author=current_user.username
        )
        db.session.add(post)
        db.session.commit()
        return redirect('/')
    return render_template('create_post.html')

@app.route('/post/<int:id>', methods=['GET','POST'])
def post(id):
    post = Post.query.get_or_404(id)

    comments = Comment.query.filter_by(post_id=id).all()

    if request.method == 'POST':
        comment = Comment(
            title=request.form['title'],
            content=request.form['content'],
            post_id=id
        )
        db.session.add(comment)
        db.session.commit()
        flash('Comment added')
        return redirect(url_for('post', id=id))

    return render_template('post.html', post=post, comments=comments)

@app.route('/edit/<int:id>', methods=['GET','POST'])
@login_required
def edit(id):
    post = Post.query.get_or_404(id)

    if request.method == 'POST':
        post.title = request.form['title']
        post.content = request.form['content']
        post.tags = request.form['tags']
        db.session.commit()
        return redirect('/dashboard')

    return render_template('edit_post.html', post=post)

@app.route('/delete/<int:id>')
@login_required
def delete(id):
    post = Post.query.get_or_404(id)
    db.session.delete(post)
    db.session.commit()
    return redirect('/dashboard')

@app.route('/tag/<tag>')
def tag(tag):
    posts = Post.query.filter(Post.tags.contains(tag)).all()
    return render_template('tag.html', posts=posts, tag=tag)

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

def seed_posts():
    if Post.query.count() == 0:
        for i in range(1,11):
            post = Post(
                title=f"Sample Blog Post {i}",
                content="This is a generated sample blog post for assignment requirements. " * 8,
                tags="python,flask,tech",
                author="Admin"
            )
            db.session.add(post)
        db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        seed_posts()

    app.run(host='0.0.0.0', port=81, debug=True)
