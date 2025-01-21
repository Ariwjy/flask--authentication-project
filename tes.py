import os
from flask import Flask, flash, redirect, request, session, url_for, render_template
from datetime import datetime, time, timedelta
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

import psycopg2
import bcrypt

UPLOAD_FOLDER = 'static/image/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:admin@localhost/postgres'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key ="hello"
app.permanent_session_lifetime = timedelta(minutes=5)



db =SQLAlchemy(app)

conn = psycopg2.connect(
    host="localhost",
    database="postgres",
    user="postgres",
    password="admin"
)
    
class User(db.Model):
    __tablename__="user"
    id = db.Column(db.Integer, primary_key=True, unique = True, autoincrement=True)
    username = db.Column(db.String(100), unique = True, nullable = False)
    email = db.Column(db.String(100), unique = True, nullable = False)
    password = db.Column(db.String(100), nullable = False)
    name = db.Column(db.String(255), nullable = False, default = "John Doe")
    company = db.Column(db.String(255), nullable = False, default = "Ltd")
    phone = db.Column(db.Integer, nullable =False, default = 62)
    role_id = db.Column(db.Integer, db.ForeignKey('role.role_id'), nullable =False, default = 3)
    photo = db.Column(db.String(255), nullable = False, default = "logo.png")

    
    
role = db.relationship('Role', backref='users') 
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    
class Role(db.Model):
    __tablename__="role"
    role_id = db.Column(db.Integer, primary_key=True, nullable =False)
    isRole = db.Column(db.String(100), nullable = False)
    action = db.Column(db.String(100), nullable = False)


#route ke halaman home
@app.route("/")
def home():
    return render_template("index.html", user=user)

#sign in
@app.route("/signin", methods=["GET", "POST"])
def signin():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        
        user=User.query.filter_by(email=email).first()
        
        
        if not user:
            flash("Email is not registered!", "danger")
            return render_template("signin.html", email=email, password=password)
        
        if bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):            
            session.permanent = True        
            session["user"] = user.username
            session["email"] = user.email
            session["password"] = user.password
            session["id"] = user.id
            session["role_id"] = user.role_id
            flash ("Login succcesful!")
            return redirect(url_for("user"))
        
        else:
            flash("password is incorrect!")
            return render_template("signin.html", email=email, password=password)
        
    else:
        if "user" in session:
            flash ("Already logged in!")
            return redirect(url_for("user"))
            
        return render_template("signin.html")
    
#sign up
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]
        
        existing_username=User.query.filter_by(username=username).first()
        if existing_username:
            flash("Username is already taken!")
            return render_template("signup.html", email=email, password=password, confirm_password=confirm_password)
        
        existing_email=User.query.filter_by(email=email).first()
        if existing_email:
            flash("Email is already taken!")
            return render_template("signup.html", username=username, password=password, confirm_password=confirm_password)

        if password != confirm_password:
                flash("Passwords do not match!", "danger")
                return render_template("signup.html", username=username, email=email, password=password, confirm_password=confirm_password)
        try:
            hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            new_user = User(username=username, email=email, password=hashed.decode('utf-8'))
            db.session.add(new_user)
            db.session.commit()
            flash("Sign up successful!", "success")
            
            session.permanent = True        
            session["user"] = new_user.username
            session["email"] = new_user.email
            session["password"] = new_user.password
            session["id"] = new_user.id
            
            return redirect("/user")
        except Exception as e:
            flash(f"Error: {str(e)}", "danger")
            return redirect("/signup")
    
    else:
        if "user" in session:
            flash ("Already logged in!")
            return redirect(url_for("user"))
            
        return render_template("signup.html")

#user profile    
@app.route("/user", methods=["POST", "GET"])
def user():
    if "user" in session:
        username = session["user"]
        user = User.query.filter_by(username=username).first()                  
        return render_template("user.html", user=user)
    else:
        flash("You are not logged in!")
        return redirect(url_for("signin"))
    
#db connection    
@app.route("/user/database")
def userdatabase():
    cur = conn.cursor()
    cur.execute('SELECT * FROM public.user')
    data = cur.fetchall()
    print(data)
    return str(data)

#logout    
@app.route("/logout")
def logout():
    if "user" not in session:
            return redirect(url_for("signin"))   
    user = session["user"]
    flash(f"You have been logged out {user}", "info")
    session.pop("user", None)
    session.pop("email", None)
    session.pop("id", None)
    return redirect(url_for("home"))   

@app.route("/update", methods=['POST'])
def update():
    if "user" in session:
        id = session["id"]
        user = User.query.get(id)
        
        if user:
            username = request.form.get("username")
            name = request.form.get("name")
            email = request.form.get("email")
            company = request.form.get("company")
            phone = request.form.get("phone")
            file = request.files.get("photo")
            
            if username and username != user.username:
                existing_username = User.query.filter_by(username=username).first()
                if existing_username and existing_username.id != user.id:  
                    flash("Username is already taken!", "danger")
                    return render_template("user.html", user=user, temp_data={
                        "username": username,
                        "name": name,
                        "email": email,
                        "company": company,
                        "phone": phone,
                    })
                user.username = username  
            if name and name != user.name:
                user.name = name  

            if email and email != user.email:
    
                existing_email = User.query.filter_by(email=email).first()
                if existing_email and existing_email.id != user.id:  
                    flash("Email is already taken!", "danger")
                    return render_template("user.html", user=user, temp_data={
                        "username": username,
                        "name": name,
                        "email": email,
                        "company": company,
                        "phone": phone,
                    })
                user.email = email 


            
            if company and company != user.company:
                user.company = company  
          

        
            if phone is not None and str(phone) != str(user.phone):                
                existing_phone = User.query.filter_by(phone=phone).first()
                if existing_phone and existing_phone.id != user.id:  
                    flash("Phone number is already taken!", "danger")
                    return render_template("user.html", user=user, temp_data={
                        "username": username,
                        "name": name,
                        "email": email,
                        "company": company,
                        "phone": phone,
                    })
                user.phone = phone

            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                user.photo = filename

            try:
                if not db.session.is_modified(user):
                    flash("Nothing has changed", "info")
                
                else:
                    db.session.commit()
                    flash("Update Successfully", "success")
                
                return render_template("user.html", user=user)  
            
            except Exception as e:
                db.session.rollback()
                flash(f"An error occurred: {str(e)}", "danger")
                return render_template("user.html", user=user, temp_data={
                    "username": username,
                    "name": name,
                    "email": email,
                    "company": company,
                    "phone": phone,
                })

    flash("You need to log in first!", "danger")
    return redirect(url_for("signin"))

@app.route("/change", methods=['POST'])
def change():
    if "user" in session:
        id = session["id"]
        user = User.query.get(id)
        
        if user:
            Cupassword = request.form["Cuusername"]
            newpassword1 = request.form["newusername1"]
            newpassword2 = request.form["newusername2"] 
            if bcrypt.checkpw(Cupassword.encode('utf-8'), user.password.encode('utf-8')):            
                if newpassword1 != newpassword2:
                    flash("new passwords do not match!", "danger")
                else:
                    hashed = bcrypt.hashpw(newpassword1.encode('utf-8'), bcrypt.gensalt())
                    user.password = hashed.decode('utf-8')
                    try:
                        db.session.commit()
                        flash("Update Successfully", "success")
                        return redirect(url_for("user"))    

                    except Exception as e:
                        db.session.rollback()
                        flash(f"An error occurred: {str(e)}", "danger")
            else:
                flash("Current password is incorrect", "danger")
                return redirect(url_for("user") + "#account-change-password")

    return redirect(url_for("user"))

                    

@app.route("/userdata", methods=["POST", "GET"])
def userdata():
    if "user" in session: 
        username = session["user"]
        user = User.query.filter_by(username=username).first()
        if not user:
            flash("User not found!", "danger")
            return redirect(url_for("user"))

        if user.role_id != 1:
            flash("You are not authorized to view this page.", "danger")
            return redirect(url_for("user"))
        
        cur = conn.cursor()
        cur.execute('SELECT * FROM public."user" INNER JOIN public."role" ON public."role".role_id = public."user".role_id ORDER BY public."role".role_id DESC ;')
        # cur.execute('SELECT * FROM public.user ORDER BY id ASC ')
        data = cur.fetchall()
        return render_template("userdata.html", user=user, data=data)
    flash("You need to log in first!", "danger")
    return redirect(url_for("signin"))
    
@app.route("/edit",  methods=["POST", "GET"])
def edit():
    id = request.form.get("id")
    username =  request.form.get("username")
    name = request.form.get("name")
    email = request.form.get("email")
    company = request.form.get("company")
    phone = request.form.get("phone")
    password = request.form.get("password")
    isRole = request.form.get("role").lower()
    file = request.files.get("photo")
    
    user = User.query.filter_by(id=id).first()
    if not user:
        flash("User not found!", "danger")
        return redirect(url_for("userdata"))
  
    if username and username != user.username:
        existing_username = User.query.filter_by(username=username).first()
        if existing_username and existing_username.id != user.id:  
            flash("Username is already taken!", "danger")
            return redirect(url_for("userdata"))
        user.username = username
        
    if email and email != user.email:
        existing_email = User.query.filter_by(email=email).first()
        if existing_email and existing_email.id != user.id:  
            flash("Email is already taken!", "danger")
            return redirect(url_for("userdata"))
        user.email = email

    if phone and str(phone) != str(user.phone):
        existing_phone = User.query.filter_by(phone=phone).first()
        if existing_phone and existing_phone.id != user.id:  
            flash("Phone number is already taken!", "danger")
            return redirect(url_for("userdata"))
        user.phone = phone
        
    if name and name != user.name:
        user.name = name

    if company and company != user.company:
        user.company = company

    if password and password != user.password:
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        user.password = hashed.decode('utf-8')
        
    if isRole:
        role = Role.query.filter_by(isRole=isRole).first()
        if not role:
            flash("The specified role does not exist!", "danger")
            return redirect(url_for("userdata"))
        
        if isRole and isRole != role.role_id:
            if isRole.lower() == "admin":
                user.role_id = 2
            elif isRole.lower() == "user":
                user.role_id = 3
            else:
                flash("There is no name for that role", "danger")
                return redirect(url_for("userdata"))

            

    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        user.photo = filename
        if filename != user.photo:
            user.photo = filename
    try:
        if not db.session.is_modified(user):
            flash("Nothing has changed", "info")
                
        else:
            db.session.commit()
            flash("Update Successfully", "success")
                
        return redirect(url_for("userdata"))
            
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred: {str(e)}", "danger")
        return redirect(url_for("userdata"))

    
@app.route("/delete", methods = ["POST", "GET"] )
def delete():
    id = request.form.get("id2")    
    user = User.query.filter_by(id=id).first()
    
    if not user:
        flash("User not found!", "danger")
        return redirect(url_for("userdata"))
    try:
        db.session.delete(user) 
        db.session.commit()  
        flash("User has been deleted successfully", "success")
    
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred: {str(e)}", "danger")
        return redirect(url_for("userdata"))
    
    return redirect(url_for("userdata"))

@app.route("/add", methods = ["POST", "GET"] )
def add():
    username = request.form["username3"]
    name = request.form["name3"]
    email = request.form["email3"]
    phone = request.form["phone3"]
    password = request.form["password3"]
        
    existing_username=User.query.filter_by(username=username).first()
    if existing_username:
        flash("Username is already taken!")
        return redirect("/userdata")
        
    existing_email=User.query.filter_by(email=email).first()
    if existing_email:
        flash("Email is already taken!")
        return redirect("/userdata")
    
    existing_phone=User.query.filter_by(phone=phone).first()
    if existing_phone:
        flash("Phone number is already taken!")
        return redirect("/userdata")

    try:
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        new_user = User(username=username, name=name, email=email, phone=phone, password=hashed.decode('utf-8'))
        db.session.add(new_user)
        db.session.commit()
        flash("Sign up successful!", "success")
            
        return redirect("/userdata")
    except Exception as e:
        flash(f"Error: {str(e)}", "danger")
        return redirect("/userdata")
    
    
if __name__ == "__main__":
    app. run (debug=True)