from flask import Flask, render_template, request, redirect, session, flash, url_for
from models import User, Post, Comment, Like, init_db, SessionLocal
import base64
from sqlalchemy.orm import joinedload
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'secret_key'
init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    db = SessionLocal()
    if request.method == 'POST':
        uname = request.form['name']
        email = request.form['email']
        passw = request.form['password']
        profile = request.files['profile']

        if profile:
            image_data = base64.b64encode(profile.read()).decode('utf-8')
            new_user = User(name=uname, email=email, password=passw, profile_photo=image_data)
            db.add(new_user)
            db.commit()
            flash('Account created successfully.')
            return redirect('/login')
        else:
            flash('Image upload failed.')
            return redirect('/register')

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    db = SessionLocal()
    if request.method == 'POST':
        email = request.form['email']
        passw = request.form['password']
        user = db.query(User).filter_by(email=email, password=passw).first()
        if user:
            session['user_id'] = user.id
            session['name'] = user.name
            flash('You have been Logged In')
            return redirect('/dashboard')
        else:
            flash('Invalid email or password')
            return redirect('/login')
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    db = SessionLocal()
    if 'name' not in session:
        flash('Please log in to access your dashboard.')
        return redirect('/login')

    posts = db.query(Post).options(joinedload(Post.comments), joinedload(Post.likes)).order_by(Post.created_at.desc()).all()
    return render_template('dashboard.html', posts=posts, user_id=session.get('user_id'))

@app.route('/post', methods=['GET', 'POST'])
def post():
    db = SessionLocal()
    if 'user_id' not in session:
        flash('You must be logged in to post.')
        return redirect('/login')

    if request.method == 'POST':
        content = request.form['content']
        photo = request.files['image']
        user_id = session['user_id']
        image_data = base64.b64encode(photo.read()).decode('utf-8') if photo else None
        new_post = Post(content=content, user_id=user_id, photo=image_data)
        db.add(new_post)
        db.commit()
        flash(f'Post added successfully.')
        return redirect('/dashboard')

    return render_template('post.html')

@app.route('/comment/<int:post_id>', methods=['POST'])
def comment(post_id):
    db = SessionLocal()
    if 'name' not in session:
        flash('You must be logged in to comment.')
        return redirect('/login')

    content = request.form['comment']
    username = session['name']
    new_comment = Comment(username=username, content=content, post_id=post_id, user_id=session['user_id'])
    db.add(new_comment)
    db.commit()
    flash('Comment added.')
    return redirect('/dashboard')


@app.route('/like/<int:post_id>')
def like(post_id):
    db = SessionLocal()
    user_id = session.get('user_id')
    if not user_id:
        flash('Login required to like posts.')
        return redirect('/login')

    existing_like = db.query(Like).filter_by(user_id=user_id, post_id=post_id).first()
    if existing_like:
        db.delete(existing_like)
        flash('Unliked the post.')
    else:
        new_like = Like(user_id=user_id, post_id=post_id)
        db.add(new_like)
        flash('Liked the post.')
    db.commit()
    return redirect('/dashboard')

@app.route('/delete/<int:id>')
def delete(id):
    db = SessionLocal()
    post = db.query(Post).get(id)
    if post:
        db.delete(post)
        db.commit()
        flash('Post deleted.')
    return redirect('/dashboard')

@app.route('/profile')
def profile():
  db = SessionLocal()
  user =db.query(User).filter_by(name=session['name']).first()
  return render_template('profile.html', user=user)

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.')
    return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True)
