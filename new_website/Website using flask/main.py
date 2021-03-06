from flask import Flask,render_template,request,session,redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_mail import Mail
from werkzeug.utils import secure_filename
import json
import os
import math

with open('config.json','r') as c:
    params=json.load(c)["params"]
app=Flask(__name__)
local_server=True
app.config['SECRET_KEY'] = 'secret_key'
app.config['UPLOAD_FOLDER']=params['upload_location']
app.config['my_folder']=params['my_folder']
app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = '465',
    MAIL_USE_SSL = True,
    MAIL_USERNAME = params['gmail-user'],
    MAIL_PASSWORD=  params['gmail-password']
)
mail = Mail(app)

if(local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']


db = SQLAlchemy(app)


class Contects(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80),nullable=False)
    email = db.Column(db.String(20),nullable=False)
    phone_num = db.Column(db.String(12),nullable=False)
    date = db.Column(db.String(12),nullable=True)
    mes = db.Column(db.String(120), nullable=False)


class Post(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80),nullable=False)
    content = db.Column(db.String(200),nullable=False)
    tagline = db.Column(db.String(200),nullable=False)
    date = db.Column(db.String(12),nullable=False)
    slug = db.Column(db.String(20),nullable=True)
    img_name = db.Column(db.String(30),nullable=True)

@app.route("/")
def home():
    posts=Post.query.filter_by().all()
    last=math.ceil(len(posts)/int(params['no_of_posts']))
    page=(request.args.get('page'))
    if(not str(page).isnumeric()):
        page=1
    page=int(page)
    posts=posts[(page-1)*int(params['no_of_posts']):(page)*int(params['no_of_posts'])]
    if page==1:
        prev="#"
        next="/?page="+str(page+1)

    elif page==last:
        prev="/?page="+str(page-1)
        next = '#'
    else:
        prev="/?page="+str(page-1)
        next="/?page="+str(page+1)


    return render_template("index.html",params=params,post=posts,prev=prev,next=next)

@app.route("/about")
def about():
    return render_template("about.html",params=params)

@app.route("/gallery")
def gallery():
    post = Post.query.all()
    return render_template("gallery.html",params=params,post=post)


@app.route("/contact",methods=['GET','POST'])
def contact():
    if (request.method=="POST"):
        name=request.form.get('name')
        email=request.form.get('email')
        phone=request.form.get('phone')
        message=request.form.get('message')
        entry=Contects(name=name,email=email,phone_num=phone,date=datetime.now(),mes=message)
        db.session.add(entry)
        db.session.commit()
        mail.send_message('New message from user-' + name,
                          sender=email,
                          recipients=[params['gmail-user']],
                          body="Message="+message + "\nPhone=" + phone+"\nEmail="+email
                          )
    return render_template("contact.html",params=params)

@app.route("/post")
def post():
    return render_template("post.html",params=params)

@app.route("/dashboard", methods=['GET','POST'])
def dashboard():

    if 'user' in session and session['user']==params['admin_user']:
        post = Post.query.all()
        return render_template("dashboard.html", params=params, post=post)
    if request.method=='POST':
        username=request.form.get('uname')
        password=request.form.get('pass')
        if username==params['admin_user'] and password==params['admin_password']:
            session['user']=username
            post=Post.query.all()
            return render_template("dashboard.html", params=params,post=post)

    return render_template("signin.html",params=params)


@app.route("/edit/<string:sno>", methods=['GET','POST'])
def edit(sno):
    if ('user' in session and session['user'] == params['admin_user']):
        if request.method == 'POST':
            box_title=request.form.get('title')
            tagline=request.form.get('tline')
            slug=request.form.get('slug')
            content=request.form.get('content')

            post=Post.query.filter_by(sno=sno).first()
            post.title=box_title
            post.tagline=tagline
            post.slug=slug
            post.content=content
            db.session.commit()
            return redirect('/edit/'+sno)

        post = Post.query.filter_by(sno=sno).first()
        return render_template('edit.html',params=params,post=post)



@app.route("/show/<string:sno>", methods=['GET','POST'])
def show(sno):
    post = Post.query.filter_by(sno=sno).first()
    return render_template('show_image.html', params=params, post=post)



@app.route("/add/<string:sno>", methods=['GET','POST'])
def add(sno):
    if ('user' in session and session['user'] == params['admin_user']):
        if request.method == 'POST':
            box_title=request.form.get('title')
            tagline=request.form.get('tline')
            slug=request.form.get('slug')
            content=request.form.get('content')
            f = request.files['file']

            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
            post=Post(title=box_title,tagline=tagline,content=content,date=datetime.now(),slug=slug,img_name=f.filename)
            db.session.add(post)
            db.session.commit()
        post = Post.query.filter_by(sno=sno).first()

        return render_template('add.html',params=params,sno=sno,post=post)


@app.route("/delete/<string:sno>", methods=['GET','POST'])
def delete(sno):
    if 'user' in session and session['user'] == params['admin_user']:
        p = Post.query.filter_by(sno=sno).first()
        db.session.delete(p)
        db.session.commit()
    return redirect('/dashboard')





@app.route("/post/<string:post_slug>", methods=['get'])
def post_route(post_slug):
    post=Post.query.filter_by(slug=post_slug).first()
    return render_template("post.html",params=params,post=post)

@app.route("/uploader",methods=['GET','POST'])
def upload():
    if 'user' in session and session['user'] == params['admin_user']:
        if request.method == 'POST':
            f=request.files['file']
            f.save(os.path.join(app.config['my_folder'],secure_filename(f.filename)))
            return redirect('/dashboard')


@app.route("/logout")
def logout():
    session.pop('user')
    return redirect('/dashboard')



app.run(debug=True)

