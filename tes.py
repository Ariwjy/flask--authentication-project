import random
from flask import Flask, flash, redirect, request, session, url_for, render_template
from datetime import timedelta
from flask_sqlalchemy import SQLAlchemy
import psycopg2
import bcrypt

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:admin@localhost/postgres'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key ="hello"
app.permanent_session_lifetime = timedelta(hours=1)

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
    name = db.Column(db.String(255))
    company = db.Column(db.String(255))
    phone = db.Column(db.Integer)


#route ke halaman home
@app.route("/")
def home():
    return render_template("index.html")

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
def userdata():
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
    flash(f"You have been logged out ,{user}", "info")
    session.pop("user", None)
    session.pop("email", None)
    session.pop("id", None)
    return redirect(url_for("home"))

#uploads
@app.route("/uploads")
def uploads():
        return render_template("upload.html")

@app.route("/upload", methods = ['POST'])
def upload():

    if 'file' not in request.files:
        return 'No file part'
    
    file = request.files['file']
    
    if file.filename == '':
        return 'No selected file'

    file.save('uploads/' + file.filename)
    return 'File uploaded successfully'

#update
@app.route("/update", methods=['POST'])
def update():
    if "user" in session:
        id = session["id"]
        user = User.query.get(id)
        
        if user:
            user.username = request.form.get("username")
            user.name = request.form.get("name")
            user.email = request.form.get("email")
            user.company = request.form.get("company")
            user.phone = request.form.get("phone")
            
            try:
                db.session.commit()
                flash("Update Successfully", "success")
                return redirect(url_for("user"))

            except Exception as e:
                db.session.rollback()
                flash(f"An error occurred: {str(e)}", "danger")
                
    return redirect(url_for("user"))


#change password
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

                    

        
        

if __name__ == "__main__":
    app. run (debug=True)