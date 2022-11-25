from flask import Flask,render_template,flash,redirect,url_for,session,request,logging
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators,IntegerField
from passlib.hash import sha256_crypt
from passlib.hash import sha256_crypt
from functools import wraps
import matplotlib.pyplot as plt
import numpy as np

app = Flask(__name__)
app.secret_key="cüzdan"

class RegisterForm(Form):
    name=StringField("İsim Soyisim",validators=[validators.Length(min=6, max=30)])
    username = StringField("Kullanıcı adı",validators=[validators.Length(min=6, max=30)])
    email = StringField("E posta",validators=[validators.email(message="Geçerli bir email adresi giriniz")])
    password = PasswordField("Parola",validators=[
        validators.DataRequired("Lütfen bir parola belileyin"),
        validators.length(min=8),
        validators.EqualTo(fieldname="confirm",message="Parolanız Uyuşmuyor")        
    ])
    confirm=PasswordField("Parola Doğrula")

class LoginForm(Form):
    username=StringField("Kullanıcı adı")
    password=PasswordField("Parola")

class HesapForm(Form):
    gelir=IntegerField("Gelir",validators=[validators.Length(min=6, max=75)])
    gider=IntegerField("Gider",validators=[validators.Length(min=8)])

def login_required(f):
    @wraps(f)
    def decorator_function(*args,**kwargs):
        if "logged_in" in session:
            return f(*args,**kwargs)
        else:
            flash("Bu sayfayı görüntülemek için giriş yapmanız lazım...","danger")
            return redirect(url_for("login"))
    return decorator_function


app.config["MYSQL_HOST"] ="localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "cüzdan"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

mysql = MySQL(app)


@app.route("/")
def index():

    return render_template("index.html")


@app.route("/hesap/<string:username>")
def hesap(username):
    cursor=mysql.connection.cursor()
    result = cursor.execute("Select * from hesap where username = %s",(username,))
    
    if result > 0:
        hesap = cursor.fetchone()
        cursor.close()
        return render_template("hesap.html",hesap=hesap)
    else:
        return render_template("hesap.html")
    
@app.route("/register",methods=["GET","POST"])
def register():
    form = RegisterForm(request.form)
    if(request.method=="POST" and form.validate()):
        name=form.name.data
        username=form.username.data
        email=form.email.data
        password = sha256_crypt.encrypt(form.password.data)

        cursor = mysql.connection.cursor()
        cursor.execute("Insert into user(name,email,username,password) VALUES(%s,%s,%s,%s) ",(name,email,username,password))
        mysql.connection.commit()
        cursor.close()
        flash("Başarıyla kayıt oldunuz...","success")
        return redirect(url_for("login"))

    else:
        return render_template("register.html",form=form)

@app.route("/login",methods=["GET","POST"])
def login():
    form = LoginForm(request.form)
    if(request.method=="POST"):
        username=form.username.data
        password = form.password.data

        cursor = mysql.connection.cursor()
        result=cursor.execute("Select * from user where username = %s",(username,))
       
        
        if result>0:
            data=cursor.fetchone()
        
            real_passw=data["password"]
            if sha256_crypt.verify(password,real_passw):
                flash("Başarılı giriş yaptınız..","success")
                session["logged_in"] = True
                session["username"] = username
                
                return redirect(url_for("index"))     
            else:
                flash("Parolanızı yanlış girdiniz","danger")
                return redirect(url_for("login"))
        else:
            flash("Böyle bir kullanıcı bulunmuyor...","danger")
            return redirect(url_for("login"))

    return render_template("login.html",form=form)

@app.route("/dashboard")
@login_required
def dashboard():
    cursor=mysql.connection.cursor()
    result=cursor.execute("Select * from hesap where username = %s",(session["username"],))
    

    if result>0:
        hesap = cursor.fetchall()
        cursor.close()
        return render_template("dashboard.html",hesap=hesap)
    else:
        return render_template("dashboard.html")

@app.route("/addhesap",methods=["GET","POST"])
@login_required
def addhesap():
    form=HesapForm(request.form)
    if request.method=="POST" and form.validate:
        gelir = form.gelir.data
        gider = form.gider.data
        cursor = mysql.connection.cursor()
        result=cursor.execute("Select * from hesap where username=%s",[session["username"]],)
       
        if result==0:

           cursor.execute("Insert into  hesap (gelir,username,gider) VALUES(%s,%s,%s)",(gelir,session["username"],gider,))
           
           mysql.connection.commit()
           cursor.close()
           flash("Hesap kaydedildi...","success")
           return redirect(url_for("dashboard"))
        else:
            flash("Zaten bir hesap var","danger")
            return redirect(url_for("dashboard"))  
    return render_template("addhesap.html",form=form)

@app.route("/delete/<string:username>")
@login_required
def delete(username):
    cursor=mysql.connection.cursor()
    result = cursor.execute("Select * from hesap where username= %s",(session["username"],))
  
    
    if result > 0:
         cursor.execute("Delete from hesap where username = %s",([session["username"]]))
         mysql.connection.commit()
         cursor.close()
         return redirect(url_for("dashboard"))
    else:
        flash("Böyle bir hesap yok veya bu işlem için yetkiniz yok","danger")
        return redirect(url_for("dashboard"))

@app.route("/edit/<string:username>",methods=["GET","POST"])
@login_required
def edit(username):
    if request.method == "GET":
        cursor = mysql.connection.cursor()
        result = cursor.execute("Select * from hesap where  username= %s ",([session["username"]]))
        
        
        if result == 0:
            flash("Böyle bir hesap yok veya bu işlem için yetkiniz yok","danger")
            session.clear()
            return redirect(url_for("index"))
        else:
            hesap=cursor.fetchone()
            
            form =HesapForm()
            form.gelir.data = hesap["gelir"]
            form.gider.data = hesap["gider"]
            return render_template("update.html", form=form)
    else:
        form = HesapForm(request.form)
        gelir=form.gelir.data
        gider = form.gider.data
        cursor = mysql.connection.cursor()
       

        cursor.execute("Select gelir from hesap where username = %s",([session["username"]],))
        eskigelir=cursor.fetchall()
        
        for i in eskigelir:
             eskigelir=i["gelir"]

        eskigider=cursor.execute("Select gider  from hesap where username = %s",([session["username"]],))
        eskigider=cursor.fetchall()
        
        for i in eskigider:
             eskigider=i["gider"]
        
        yenigelir=int(eskigelir)+int(gelir)
        yenigider=int(eskigider)+int(gider)
        cursor.execute("Update hesap set gelir=%s , gider=%s where username=%s",(yenigelir,yenigider,[session["username"]],))
        mysql.connection.commit()
        cursor.close()
        flash("Hesap Başarılı bir şekilde eklendi","success")
        return redirect(url_for("dashboard"))
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

if __name__ =="__main__":
    app.run(debug = True)

  