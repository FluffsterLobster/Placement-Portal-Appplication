from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, DateTimeLocalField, SubmitField, IntegerField, TextAreaField, FileField
from flask_wtf.file import FileRequired, FileAllowed
from wtforms.validators import (
    DataRequired,
    Email,
    Length,
    Regexp,
    Optional,
)
from models import Student, Admin, Company, Placement_drive, Application
from datetime import datetime
current_year = datetime.now().year

class Student_Profile(FlaskForm):
    username = StringField("Username", [DataRequired()],  render_kw={"readonly": True})
    email = StringField("Email ID", [DataRequired(), Email(), Length(max=40)])
    name = StringField("Full Name", [DataRequired()])
    grad_yr = SelectField("Graduation Year",[DataRequired()], choices= [(current_year, current_year), (current_year+1, current_year+1), (current_year+2, current_year+2)])
    dept_id = StringField("Department", [DataRequired()])
    submit = SubmitField("Submit")

    def prepopulate_on_edit(self, data: Student):
        self.email.data = data.email
        self.username.data = data.username
        self.name.data = data.name
        self.grad_yr.data = data.grad_yr
        self.dept_id.data = data.dept_id

class Company_Profile(FlaskForm):
    username = StringField("Username", [DataRequired()],  render_kw={"readonly": True})
    cntct_mail = StringField("HR Mail", [DataRequired(), Email(), Length(max=40)])
    name = StringField("Company Name", [DataRequired()])
    website = StringField("Website", [DataRequired()] )
    submit = SubmitField("Submit")

    def prepopulate_on_edit(self, data: Company):
        self.cntct_mail.data = data.cntct_mail
        self.username.data = data.username
        self.name.data = data.name
        self.website.data = data.website


class Admin_Profile(FlaskForm):
    username = StringField("Username", [DataRequired()],  render_kw={"readonly": True})
    email = StringField("Email ID", [DataRequired(), Email(), Length(max=40)])
    name = StringField("Full Name", [DataRequired()])
    submit = SubmitField("Submit")

    def prepopulate_on_edit(self, data: Admin):
        self.email.data = data.email
        self.username.data = data.username
        self.name.data = data.name


class C_Placement_Drive(FlaskForm):
        username = StringField("Username", [DataRequired()],  render_kw={"readonly": True})
        job_title = StringField("Job Title", [DataRequired()])
        job_description = TextAreaField("Job Description", [DataRequired()])
        el_criteria = StringField("Eligibility Criteria", [DataRequired()])
        location = StringField("Location")
        salary = IntegerField("Expected Salary (per annum)", [DataRequired()], default="00")
        app_deadline = DateTimeLocalField("Application Deadline",[DataRequired()], format='%Y-%m-%dT%H:%M')
        submit = SubmitField("Submit for Admin Approval")
        

        def prepopulate(self, data: Placement_drive):
            self.username.data = data.username
         
class C_Application(FlaskForm):
    submit = SubmitField("Apply Now")

class E_Placement_Drive(FlaskForm):
    username = StringField("Username", [DataRequired()],  render_kw={"readonly": True})
    job_title = StringField("Job Title", [DataRequired()])
    job_description = TextAreaField("Job Description", [DataRequired()])
    el_criteria = StringField("Eligibility Criteria", [DataRequired()])
    location = StringField("Location")
    salary = IntegerField("Expected Salary (per annum)", [DataRequired()])
    app_deadline = DateTimeLocalField("Application Deadline",[DataRequired()], format='%Y-%m-%dT%H:%M')
    submit = SubmitField("Submit")

    def prepopulate_on_edit(self, data: Placement_drive):
        self.username.data = data.username
        self.job_title.data = data.job_title
        self.job_description.data = data.job_description
        self.el_criteria.data = data.el_criteria
        self.location.data = data.location
        self.salary.data = data.salary
        self.app_deadline.data = data.app_deadline

class Resume(FlaskForm):
    resume = FileField('Select Resume')
    submit = SubmitField('Upload')
    