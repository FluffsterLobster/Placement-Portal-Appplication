from flask import render_template, request, flash, redirect, url_for, session
from flask_login import login_user, logout_user, login_required, current_user
from flask import Blueprint
auth = Blueprint("auth", __name__, url_prefix='/auth')

import auth.formdata as fd
import base.formdata as fd_
from base.routes import upload_resume
from models import Student, Admin, Company,Resume, db
from commons import not_logged_in_required, nullish_string, admin_required, allowed_file

@auth.route("/student_login", methods=["GET", "POST"])
@not_logged_in_required
def student_login():
    form = fd.StudentLogin()
        
    if request.method == "POST" and form.validate_on_submit():
        user = Student.find_std(form.username.data)
        password_attempt = nullish_string(form.password)

        if user is None or not user.match_password(password_attempt):
            flash(f"Invalid Email or Password input - try again!", "error")
            return redirect(url_for("auth.student_login"))
        
        if user.is_blacklisted == True:    
            flash(f"You are blacklisted, please contact the admin", "error")
            return redirect(url_for("auth.student_login"))
        
        login_user(user)
        session["user_type"] = "student"
        flash(f"You are successfully logged in, {user.name}", "success")
        return redirect(url_for("sd.student_dashboard"))         
    

    return render_template("auth/login.html", role="a Student", title="Log In (as a Student)", form=form, a = "Enter Institue Roll number")      

    


@auth.route("/student_register", methods=["GET", "POST"])
@not_logged_in_required
def student_register():
    form = fd.StudentRegister()
    form_ = fd_.Resume()
    

    if request.method == "POST" and form.validate_on_submit():
        new_student = Student.create(
            email=nullish_string(form.email),
            name=nullish_string(form.name),
            password=nullish_string(form.password),
            username = nullish_string(form.username),
            dept_id = nullish_string(form.dept_id),
            grad_yr = nullish_string(form.grad_yr), 
            current_cgpa= form.current_cgpa.data           
        )
       
        if Student.query.filter_by(username=form.username.data).first():
            flash('Username taken.', 'error')
            return redirect(url_for("auth.student_register"))
        
        db.session.add(new_student)
        db.session.commit()  

        

        flash("You are registered as a student. Please login.", "success")
        return redirect(url_for("auth.student_login"))
    return render_template("auth/student_register.html", role="a Student", title="Register", form=form)
        
    

        
    
    
    



@auth.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.student_login"))


@auth.route("/create_admin", methods=["GET", "POST"])
@admin_required
def create_admin():
    form = fd.CreateAdmin()

    if request.method == "POST" and form.validate_on_submit():
        new_admin = Admin.create(
            email=nullish_string(form.email),
            name=nullish_string(form.name),
            password=nullish_string(form.password),
            username = nullish_string(form.username),
                    
        )

        if Admin.query.filter_by(username=form.username.data).first():
            flash('Admin already exists.', 'error')
            return redirect(url_for("auth.create_admin"))
        
        db.session.add(new_admin)
        db.session.commit() 
        flash("Admin has been added. Please login.", "success")
        return redirect(url_for("ad.admin_dashboard"))
    return render_template("auth/add_admin.html", role="Admin", title="Add Admin", form=form )


@auth.route("/admin_login", methods=["GET", "POST"])
@not_logged_in_required
def admin_login():
    form = fd.AdminLogin()

    if request.method == "POST" and form.validate_on_submit():
        admin = Admin.find_ad(form.username.data)
        password_attempt = nullish_string(form.password)
        if admin is None:
            flash("You are not an admin.", "error")
            return redirect(url_for("auth.student_login"))
        

        if admin is None or not admin.match_password(password_attempt):
            flash("Invalid Email or Password input - try again!", "error")
            return redirect(url_for("auth.admin_login"))
        
        login_user(admin)
        session["user_type"] = "admin"
        flash(f"You are successfully logged in, {admin.name}", "success")
        return redirect(url_for("ad.admin_dashboard"))
        
    return render_template("auth/login.html", role = "an Admin", title="Admin Log In", adminpage=True, form=form, a = "Enter Username")
     
    
    

@auth.route("/company_login", methods=["GET", "POST"])
@not_logged_in_required
def company_login():
    form = fd.CompanyLogin()
    
    if request.method == "POST" and form.validate_on_submit():
        comp = Company.find_comp(form.username.data)
        password_attempt = nullish_string(form.password)
            
        if comp is None or not comp.match_password(password_attempt):
            flash("Invalid Email or Password input - try again!", "error")
            return redirect(url_for("auth.company_login"))
        
        if comp.is_active == False:    
            flash(f"You are blacklisted, please contact the admin", "error")
            return redirect(url_for("auth.company_login"))

        if comp.approval_sts == "Pending":
            flash("Admin approval is pending, try later", "error")
            return redirect(url_for("auth.company_login"))  

        login_user(comp)
        session["user_type"] = "company"
        flash(f"You are successfully logged in, {comp.username}", "success")
        return redirect(url_for("cp.company_dashboard"))  
    return render_template("auth/login.html", role = "a Company", title="Log In (as a Company)", form=form, a = "Enter Username")
    


@auth.route("/company_register", methods=["GET", "POST"])
@not_logged_in_required
def company_register():
    form = fd.CompanyRegister()
    if request.method == "POST" and form.validate_on_submit():
        new_company = Company.create(
            cntct_mail=nullish_string(form.cntct_mail),
            password=nullish_string(form.password),
            username = nullish_string(form.username),
            website = nullish_string(form.website),
        )

        if Company.query.filter_by(username=form.username.data).first():
            flash(f'Username already taken.', 'error')
            return redirect(url_for("auth.company_register"))
        
        if Company.query.filter_by(cntct_mail=form.cntct_mail.data).first():
            flash(f'Email already taken.', 'error')
            return redirect(url_for("auth.company_register"))
        
        db.session.add(new_company)
        db.session.commit()
        flash(f"You are registered as a company. Awaiting Admin approval", "success")
        return redirect(url_for("auth.company_login"))
    
    return render_template("auth/company_register.html", title="Register", form=form, role="a Company")


