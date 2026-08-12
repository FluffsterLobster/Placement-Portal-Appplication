from flask import render_template, request, flash, redirect, url_for, send_file, jsonify, abort, session
from flask_login import login_user, logout_user, login_required, current_user
from flask import Blueprint
from sqlalchemy import select, func
from werkzeug.utils import secure_filename
import os
cp = Blueprint("cp", __name__, url_prefix='/company')
sd = Blueprint("sd", __name__, url_prefix='/student')
ad = Blueprint("ad", __name__, url_prefix='/admin')

import base.formdata as fd
from models import Student, Admin, Company, Placement_drive, Application, Resume, db
from commons import not_logged_in_required, nullish_string, nullish_int, admin_required, company_required, allowed_file
from datetime import datetime
from io import BytesIO

@ad.route("/users")
@login_required
@admin_required
def list_users():
    companies = Company.query.all()
    students = Student.query.all()
    for c in companies:
        c.created_at_ = c.created_at.strftime("%d-%m-%Y %H:%M")
    return render_template("admin/user_list.html", companies=companies, students=students, role="Admin")

@ad.route("/placement_drives")
@login_required
@admin_required
def list_drives():
    Placement_drive.close_expired()
    drives = Placement_drive.query.all()
    for drive in drives:
        drive.app_deadline_ = drive.app_deadline.strftime("%d-%m-%Y %H:%M")
        drive.created_at_ =drive.created_at.strftime("%d-%m-%Y %H:%M")
    return render_template("admin/placement_list.html", drives=drives, role="Admin")

@ad.route("/company/<int:comp_id>/approve", methods=["POST"])
@admin_required
def approve_company(comp_id):
    company = Company.query.get(comp_id)
    if not company:
        return flash("Company not found", "error")
    company.approve()
    flash("Status Updated", "success")
    return redirect(url_for("ad.list_users"))

@ad.route("/company/<int:comp_id>/blacklist", methods=["POST"])
@admin_required
def blacklist_company(comp_id):
    company = Company.query.get(comp_id)
    if not company:
        return flash("Company not found", "error")
    company.reject()
    company.blacklist()

    flash("Company has been blacklisted", "success")
    return redirect(url_for("ad.list_users"))

@ad.route("/company/<int:comp_id>/unblacklist", methods=["POST"])
@admin_required
def un_blacklist_company(comp_id):
    company = Company.query.get(comp_id)
    if not company:
        return flash("Company not found", "error")
    company.un_blacklist()

    flash("Company has been unblacklisted", "success")
    return redirect(url_for("ad.list_users"))

@ad.route("/student/<int:std_id>/blacklist", methods=["POST"])
@admin_required
def blacklist_student(std_id):
    student = Student.query.get(std_id)
    if not student:
        return flash("Student not found", "error")
    
    student.blacklist()
    app = Application.query.filter_by(std_username= student.username).all()
    for a in app:
        a.reject()

    flash("Student has been blacklisted", "success")
    return redirect(url_for("ad.list_users"))

@ad.route("/student/<int:std_id>/unblacklist", methods=["POST"])
@admin_required
def un_blacklist_student(std_id):
    student = Student.query.get(std_id)
    if not student:
        return flash("Student not found", "error")
    
    student.un_blacklist()

    flash("Student has been unblacklisted", "success")
    return redirect(url_for("ad.list_users"))

    
@cp.route("/drives/<int:drive_id>/delete", methods=["POST"])
@company_required
def delete_drive(drive_id):
    drive = Placement_drive.query.get(drive_id)
    if not drive:
        return flash("Company not found", "error")
    drive.delete()
    flash("Status Updated", "success")
    return redirect(url_for("cp.c_placement_drives"))

    
@ad.route("/company/<int:comp_id>/reject", methods=["POST"])
@admin_required
def reject_company(comp_id):
    company = Company.query.get(comp_id)
    if not company:
        return flash("Company not found", "error")

    company.reject()
    db.session.commit()
    flash("Status Updated", "success")
    return redirect(url_for("ad.list_users"))

@ad.route("/drives/<int:drive_id>/approve", methods=["POST"])
@admin_required
def approve_drive(drive_id):
    drive = Placement_drive.query.get(drive_id)
    if not drive:
        return flash("Placement Drive not found", "error")
    
    drive.approve()
    db.session.commit()
    flash("Status Updated", "success")
    return redirect(url_for("ad.list_drives"))




@cp.route("applications/shortlist/<int:app_id>", methods=["POST"])
@company_required
def shortlist_applications(app_id):
    
    app = Application.query.get(app_id)
    if not app:
        return flash("Application not found", "error")
    
    app.shortlist()
    db.session.commit()
    flash("Status Updated", "success")
    return redirect(url_for("cp.c_applications"))

@cp.route("applications/reject/<int:app_id>", methods=["POST"])
@company_required
def reject_applications(app_id):
    
    app = Application.query.get(app_id)
    if not app:
        return flash("Application not found", "error")
    
    app.reject()
    db.session.commit()
    flash("Status Updated", "success")
    return redirect(url_for("cp.c_applications"))

@cp.route("applications/select/<int:app_id>", methods=["POST"])
@company_required
def select_applications(app_id):
    
    app = Application.query.get(app_id)
    if not app:
        return flash("Application not found", "error")
    
    if app.sts != "Shortlisted":
        flash("Application has not been shortlisted yet", "error")
    
    app.select()
    
    flash("Status Updated", "success")
    return redirect(url_for("cp.c_applications"))
    
@ad.route("/drives/<int:drive_id>/reject", methods=["POST"])
@admin_required
def reject_drive(drive_id):
    drive = Placement_drive.query.get(drive_id)
    if not drive:
        return flash("Placement Drive not found", "error")

    drive.reject()
    db.session.commit()
    flash("Status Updated", "success")
    return redirect(url_for("ad.list_drives"))

@cp.route("/drives/<int:drive_id>/close", methods=["POST"])
@login_required
@company_required
def close_drive(drive_id):
    drive = Placement_drive.query.filter_by(id=drive_id, username=current_user.username).first_or_404()
    if drive.is_closed:
        flash("Drive already closed.", "error")
        return redirect(url_for("cp.c_placement_drives"))
    drive.close()
    flash("Drive closed successfully.", "success")
    return redirect(url_for("cp.c_placement_drives"))

@sd.route("/edit-profile", methods=["GET", "POST"])
@login_required
def edit_profile_student():
    form = fd.Student_Profile()
    form_= fd.Resume()
    if request.method == "GET":
        form.prepopulate_on_edit(current_user)  
    
    if request.method == "POST" and form.validate_on_submit(): 
        student = Student.find_std(current_user.username)
        if form.name.data is not None:
            student.name = form.name.data
        if form.email.data is not None:
            student.email = form.email.data
        if form.dept_id.data is not None:
            student.dept_id = form.dept_id.data
        if form.grad_yr.data is not None:
            student.grad_yr = form.grad_yr.data
        '''if form.password.data is not None:
            student.set_password(form.password.data)'''
        
        db.session.commit()
        flash("Your details were successfully updated.", "success")
        return redirect(url_for("index"))
    
    res = Resume.query.get(current_user.username)
    #if  res is None:
    if request.method == "POST" and form_.validate_on_submit():
        upload_resume(current_user.username)
    
    return render_template("student/edit_profile_student.html", form=form, role='Student', form_=form_,  s = current_user, res=res)


@cp.route("/edit-profile", methods=["GET", "POST"])
@login_required
def edit_profile_company():
    form = fd.Company_Profile()
    if request.method == "GET":
        form.prepopulate_on_edit(current_user)  # type: ignore
    
    if request.method == "POST" and form.validate_on_submit():
        company = Company.find_comp(current_user.username)
        if form.name.data is not None:
            company.name = form.name.data
        if form.website.data is not None:
            company.website = form.website.data
        if form.cntct_mail.data is not None:
            company.cntct_mail = form.cntct_mail.data
        
        db.session.commit()  
        flash("Your details were successfully updated.", "success")
        return redirect(url_for("cp.company_dashboard"))
        
    else: 
       
        return render_template("company/edit_profile_company.html", form=form, role='Company')
    
@ad.route("/edit-profile", methods=["GET", "POST"])
@login_required
@admin_required
def edit_profile_admin():
    form = fd.Admin_Profile()
    if request.method == "GET":
        form.prepopulate_on_edit(current_user)  
    
    if request.method == "POST" and form.validate_on_submit():
        admin = Admin.find_ad(current_user.username)
        if form.name.data is not None:
            admin.name = form.name.data
        if form.email.data is not None:
            admin.email = form.email.data
        
        
        db.session.commit()  # can remain uncaught as it is checked by the form.
        flash("Your details were successfully updated.", "success")
        return redirect(url_for("ad.admin_dashboard"))
    return render_template("admin/edit_profile_admin.html", form=form, role='Admin')

@cp.route("/edit-drive/<int:id>", methods=["GET", "POST"])
@login_required
def edit_drives(id):
    form = fd.E_Placement_Drive()
    if request.method == "GET":
        form.prepopulate_on_edit(Placement_drive.query.get(id))  
    
    if request.method == "POST" and form.validate_on_submit():
        drive = Placement_drive.query.filter_by(id = id).first()
        if form.job_title.data is not None:
            drive.job_title = form.job_title.data
        if form.job_description.data is not None:
            drive.job_description = form.job_description.data
        if form.el_criteria.data is not None:
            drive.el_criteria = form.el_criteria.data
        if form.location.data is not None:
            drive.location = form.location.data
        if form.app_deadline.data is not None:
            drive.app_deadline = form.app_deadline.data
        if form.salary.data is not None:
            drive.salary = form.salary.data

        
        db.session.commit() 
        flash("Your details were successfully updated.", "success")
        return redirect(url_for("cp.c_placement_drives"))
    else:
        return render_template("company/edit_drives.html", form=form, role='Student')
    

@cp.route("/placement_drives", methods=["GET"])
@login_required
@company_required
def c_placement_drives():
    Placement_drive.close_expired()
    drives = Placement_drive.query.filter_by(username = current_user.username)
    return render_template("company/company_placement_drive.html", title="Placement Drives", role="Company", drives=drives)

@sd.route("/placement_drives", methods=["GET", "POST"])
@login_required
def s_placement_drives():
    Placement_drive.close_expired()
    drives = Placement_drive.query.all()
    std=Student.find_std(current_user.username)
    form = fd.C_Application()

    for drive in drives:
        drive.app_deadline_ = drive.app_deadline.strftime("%d-%m-%Y %H:%M")
    
    
    
    
    return render_template("student/s_placement_drives.html", title="Placement Drives", role="Student", form=form, drives=drives, s=std)
    
@cp.route("/applications", methods=["GET", "POST"])
@login_required
def c_applications():
    Placement_drive.close_expired()   
    drives = Placement_drive.query.filter_by(username= current_user.username)
    
    rows__ = []
    for d in drives:
        rows = []
        apps= Application.query.filter_by(drive_id= d.id).all()
        #rows hochhe dictionary of std app ar prottekta row ekta drive er modhye
        for a in apps:
            s = Student.query.filter_by(username = a.std_username).first()
            if s:
                rows.append({ 
                    "student": s, 
                    "application": a
                })
        rows__.append({"drive": d, "rows":rows})

    now = datetime.now()
    
    return render_template("company/c_applications.html", title="Applications", role="Company", rows__=rows__, now=now)    
    

@sd.route("/aplications", methods=["GET"])
@login_required
def s_applications():
    Placement_drive.close_expired()
    apps= Application.query.filter_by(std_username = current_user.username)  

    drives=[]
    for a in apps:
        drive = Placement_drive.query.filter_by(id = a.drive_id).first()
        if drive:
            drive.app_deadline_ = drive.app_deadline.strftime("%d-%m-%Y %H:%M")
            drives.append(drive)
    now = datetime.now()
    return render_template("student/s_applications.html", title="Applications", role="Student", applications=apps, drives=drives)


@cp.route("/create_drives", methods=["GET", "POST"])
@login_required
@company_required
def create_drives():
    form=fd.C_Placement_Drive()
    comp_id = Company.find_comp(current_user.username)
    form.prepopulate(current_user)
    if request.method == "POST" and form.validate_on_submit():
        
        new_drive = Placement_drive.create(
            job_title = nullish_string(form.job_title),
            job_description =  nullish_string(form.job_description),
            el_criteria= nullish_string(form.el_criteria),
            app_deadline= form.app_deadline.data,
            location = nullish_string(form.location), 
            username = comp_id.username,
            salary = nullish_int(form.salary) 
        )
        
        if Placement_drive.query.filter_by(
            username       = form.username.data,
            job_title      = form.job_title.data,
            app_deadline   = form.app_deadline.data
        ).first():
            flash(f'Drive already exists.', 'error')
            return redirect(url_for("cp.c_placement_drives"))
        
        if Company.find_comp(current_user.username) is None:
            flash(f'Not logged in as a company', 'error')
            return redirect(url_for("cp.c_placement_drives"))
        
        db.session.add(new_drive)
        db.session.commit()  
        flash(f"Placement drive had been created. Awaiting Admin approval", "success")
        return redirect(url_for('cp.c_placement_drives'))
    
    else:
        print(form.errors)
        return render_template("company/create_drives.html", title="Placement Drives", form=form, role="Company")



@sd.route("/create_applications/<int:drive_id>", methods=["POST"])
@login_required
def create_application(drive_id):
    Placement_drive.close_expired()
    std_id = Student.find_std(current_user.username)
    form = fd.C_Application()
    if request.method == "POST" and form.validate_on_submit():
        
        new_app = Application.create(
            drive_id = drive_id,
            std_username = std_id.username
        )

        if Resume.query.filter_by(std_username = current_user.username).count() == 0:
            flash(f'Please upload resume before applying', 'error')
            return redirect(url_for("sd.s_placement_drives"))

        
        if Application.query.filter_by(
            drive_id = drive_id,
            std_username = current_user.username
        ).first():
            flash(f'You have already applied', 'error')
            return redirect(url_for("sd.s_placement_drives"))
        
        if not std_id:
            flash("Student not found", "error")
            return redirect(url_for('auth.student_login'))
                
        if Placement_drive.query.get(drive_id).is_closed == True:
            flash(f'Drive has been closed', 'error')
            return redirect(url_for("sd.student_dashboard"))

        db.session.add(new_app)
        db.session.commit()  
        flash(f"Application has been submitted", "success")
        return redirect(url_for('sd.s_applications'))
    flash(f"Application has not been submitted", "error")
    return redirect(url_for('sd.s_placement_drives'))
   

@sd.route("/upload_resume/<int:std_id>", methods=["POST"])
@login_required
def upload_resume(std_id):
    form = fd.Resume()
    std = Student.query.filter_by(id = std_id).first()

    file = form.resume.data
    file_st = request.files['resume']
    
    if current_user.is_authenticated == True:
        if form.validate_on_submit(): 

            if Resume.query.filter_by(std_username=std.username).first() is not None:
                flash(f"Resume already exists, editing the file", "success")
                return edit_resume(file, file_st)
            
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join('uploads/resumes', filename)
                file.save(filepath)
                resume = Resume.create(filename=filename, resume_data=file_st.read(), std_username=std.username)
                
                db.session.add(resume)
                db.session.commit()
                
                flash(f"Resume has been uploaded {std.username}", "success")     
                return redirect(url_for('sd.s_placement_drives'))
                
            flash (f"Invalid file type", "error")
            return redirect(url_for('sd.s_placement_drives'))
       
        flash (f"Some error has occurred, try uploading again", "error")
        return redirect(url_for('sd.s_placement_drives'))
    
    if current_user.is_authenticated == False:
        if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                resume = Resume.create(filename=filename, resume_data=file_st.read(), std_username=std.username)
                
                db.session.add(resume)
                db.session.commit()
                     
                return flash(f"Resume has been uploaded ", "success")
                
        flash (f"Invalid file type", "error")
        return redirect(url_for('auth.student_register'))
        
    flash (f"Some error has occurred, try uploading again", "error")
    return redirect(url_for('auth.student_register'))
    

@sd.route("/edit_resume", methods=["POST"])
@login_required
def edit_resume(file, file_st):
    std_id = Student.find_std(current_user.username)
    if not std_id:
        flash("Not logged in as a Student", "error")
        return redirect(url_for('sd.student_dashboard'))
    
    #file = request.files['resume']
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        existing_resume = Resume.query.filter_by(std_username=std_id.username).first()
        
        if existing_resume:
            existing_resume.filename = filename
            existing_resume.resume_data=file_st.read()
            
        db.session.commit()
        flash(f"Resume updated successfully for {std_id.username}", "success")
        return redirect(url_for('sd.edit_profile_student'))
    
    flash("Invalid file. Try again.", "error")
    return redirect(url_for('sd.edit_resume'))  

@cp.route("/download_resume/<int:std_id>", methods=["GET"])
@login_required
def c_download_resume(std_id):

    std = Student.query.filter_by(id = std_id).first()

    if Resume.query.filter_by(std_username = std.username) is None:
        flash(f'No resume uploaded', 'error')
        return redirect(url_for('cp.c_applications'))  
    resume = Resume.query.filter_by(std_username = std.username).first()
    
    response = send_file(
        BytesIO(resume.resume_data), download_name=resume.filename, as_attachment=True, mimetype='application/pdf')
    flash(f"Resume of {std_id} has been downloaded" , "success")
    return response

@ad.route("/download_resume/<int:std_id>", methods=["GET"])
@login_required
def a_download_resume(std_id):

    std = Student.query.filter_by(id = std_id).first()
    if Resume.query.filter_by(std_username = std.username).count() == 0:
        flash(f'No resume uploaded', 'error')
        return redirect(url_for('ad.list_applications'))
    
    resume = Resume.query.filter_by(std_username = std.username).first()
    response = send_file(
        BytesIO(resume.resume_data), download_name=resume.filename, as_attachment=True, mimetype='application/pdf')
    flash(f"Resume of {std_id} has been downloaded" , "success")
    return response

@sd.route("/download_resume/<int:std_id>", methods=["GET"])
@login_required
def s_download_resume(std_id):
    

    if Resume.query.filter_by(std_username = current_user.username).count() == 0:
        flash(f'No resume uploaded', 'error')
        return redirect(url_for('sd.s_placement_drives'))
    
    std = Student.query.filter_by(id = std_id).first()
    resume = Resume.query.filter_by(std_username=std.username).first()
    
    response = send_file(
        BytesIO(resume.resume_data), download_name=resume.filename, as_attachment=True, mimetype='application/pdf')
    flash(f"Resume of {std_id} has been downloaded" , "success")
    return response


@ad.route("/student_applications", methods=["GET"])
@login_required
@admin_required
def list_applications():
    students = Student.query.all()
      

    drives = {d.id: d for d in Placement_drive.query.all()}

    rows = []
    for s in students:
        apps = Application.query.filter_by(std_username=s.username).all()
        for a in apps:
            a.created_at_ = a.created_at.strftime("%d-%m-%Y %H:%M")
            d = drives.get(a.drive_id)
            if d:
                rows.append({
                    "drive": d,
                    "student": s,
                    "application": a
                })

    return render_template("admin/application_list.html",title="Student Applications", role="Admin", rows=rows)


@ad.route("/dashboard", methods=["GET"])
@login_required
@admin_required
def admin_dashboard():
    students = Student.query.all()
    s = Student.get_total()
    c = Company.get_total()
    p = Placement_drive.get_total()
    a = Application.get_total()

    sts_app = Application.query.filter_by(sts='Applied').count()
    sts_sh = Application.query.filter_by(sts='Shortlisted').count()
    sts_se = Application.query.filter_by(sts='Selected').count()
    sts_re = Application.query.filter_by(sts='Rejected').count()
    drv_app = Placement_drive.query.filter_by(sts="Approved").count()
    drv_rej = Placement_drive.query.filter_by(sts="Rejected").count()
    drv_pen = Placement_drive.query.filter_by(sts="Pending").count()

    info={"sts_app":sts_app, "sts_re":sts_re, "sts_se":sts_se, "sts_sh":sts_sh, "drv_app":drv_app, "drv_pen":drv_pen, "drv_rej":drv_rej, "s":s, "c":c, "p":p, "a":a}

    chart_data = {
        'labels': ['No Response', 'Shortlisted', 'Selected', 'Rejected'],
        'datasets': [{
            'data': [sts_app, sts_sh, sts_se, sts_re],
            'backgroundColor': ['#AA6384', '#36A2EB', '#AACE56', '#4BC0C0'],
            'hoverOffset': 4
        }]
    }

    return render_template("admin/admin_dashboard.html", title="Admin Dashboard",role="Admin", info=info, chart_data=chart_data)

@cp.route("/dashboard", methods=["GET"])
@login_required
@company_required
def company_dashboard():
    pd = Placement_drive.get_my_drives(current_user.username)
    d_active = Placement_drive.active_get_drives_comp(current_user.username)
    drives = Placement_drive.query.filter_by(username=current_user.username).all()
    total_ap = select(func.count()).select_from(Application).join(Placement_drive,Application.drive_id == Placement_drive.id).filter_by(username=current_user.username)
    ap = db.session.execute(total_ap).scalar()
    rows = []
    
    for d in drives:
        a = Application.comp_app(d.id)
        if a:
            rows.append({
                "d": d,
                "n_app": a
            })    

    return render_template("company/company_dashboard.html", title="Company Dashboard",role="Company", rows=rows, d_active=d_active, ap = ap, pd = pd)

@sd.route("/dashboard", methods=["GET"])
@login_required
def student_dashboard():
    Placement_drive.close_expired()    
    
    d_active = Placement_drive.active_get_drives()
    a_t = Application.get_my_application(current_user.username)
    a_sh = Application.get_shortlisted_application(current_user.username)
    a_se = Application.get_selected_application(current_user.username)
    drives = Placement_drive.query.filter_by(sts = "Approved").all()
    

    for d in drives:
        d.app_deadline_ = d.app_deadline.strftime("%d-%m-%Y %H:%M")
        
    rows = []
    for d in drives:
        a = Application.query.filter_by(drive_id = d.id, std_username = current_user.username).first()
        if a:
            rows.append({
                "d": d,
                "n_app": a.sts
            })
        else:rows.append({
                "d": d,
                "n_app": "Not Applied"
            })


    return render_template("student/student_dashboard.html", title="Student Dashboard",role="Student", d_active=d_active, a_se=a_se, a_sh=a_sh, a_t=a_t, rows=rows)

@ad.route("/search_users/", methods=["GET"])
def search_users():
    query = request.args.get('q').strip()
    students = Student.search_std(query).all() if query else ""
    companies = Company.search_comp(query).all() if query else ""

    for c in companies:
        c.created_at_ = c.created_at.strftime("%d-%m-%Y %H:%M")

    return render_template("admin/search_users.html", students=students, companies=companies, role="Admin", title="Seach Users")

@ad.route("/search_drives/", methods=["GET"])
def search_drives():
    query = request.args.get('q').strip()
    drives = Placement_drive.search_drive(query).all() if query else ""

    for d in drives:
        d.created_at_ = d.created_at.strftime("%d-%m-%Y %H:%M")
        d.app_deadline_ = d.app_deadline.strftime("%d-%m-%Y %H:%M")

    return render_template("admin/placement_list.html", drives=drives, role="Admin", title="Seach Users")
