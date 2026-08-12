from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, SubmitField, FloatField
from wtforms.validators import (
    DataRequired,
    Email,
    Length,
    Optional,
    NumberRange,
    Regexp,
    ValidationError,
)
from models import Student, Admin, Company
from datetime import datetime
current_year = datetime.now().year

class StudentLogin(FlaskForm):
    username = StringField("Username", [DataRequired()])
    password = PasswordField("Password", [DataRequired()])
    submit = SubmitField("Log In")

    def validate_email(self, username):
        if Student.find_std(username.data) is None: #(.data???)
            raise ValidationError("Unknown user! Please create a new account!")


class StudentRegister(FlaskForm):
    email = StringField("Email ID", [DataRequired(), Email(message="Enter valid Email address")])
    password = PasswordField("Password", [DataRequired(), Length(min=8, message="Password must be at least 8 characters"), Regexp(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$', message="Password must contain atleast 1 lowercase,  uppercase character, digit and special character")])
    username = StringField("Username", [DataRequired()])
    name = StringField("Full Name", [DataRequired()])
    dept_id = StringField("Department", [DataRequired()])
    grad_yr = SelectField("Graduation Year", [DataRequired()], choices=[(current_year, current_year), (current_year+1, current_year+1), (current_year+2, current_year+2)])
    current_cgpa = FloatField("Current CGPA", [DataRequired(), NumberRange(min=0, max=10.0, message="Enter valid CGPA")])
    submit = SubmitField("Register")

class CreateAdmin(FlaskForm):
    email = StringField("Email ID", [DataRequired(), Email(message="Enter valid Email address"), Length(max=40)])
    password = PasswordField("Password", [DataRequired(), Length(min=8, message="Password must be at least 8 characters"), Regexp(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$', message="Password must contain atleast 1 lowercase,  uppercase character, digit and special character")])
    username = StringField("Username", [DataRequired()])
    name = StringField("Full Name", [DataRequired()])
    submit = SubmitField("Add Amin")    


class AdminLogin(FlaskForm):
    username = StringField("Username", [DataRequired()])
    password = PasswordField("Password", [DataRequired()])
    submit = SubmitField("Log In")

    def validate_user(self, username):
        if Admin.find_ad(username.data) is None:
            raise ValidationError("Unknown user, not an admin!")
        
class CompanyLogin(FlaskForm):
    username = StringField("Username", [DataRequired()])
    password = PasswordField("Password", [DataRequired()])
    submit = SubmitField("Log In")

    def validate_email(self, username):
        if Company.find_comp(username.data) is None: #(.data???)
            raise ValidationError("Unknown user! Please create a new account!")
        
class CompanyRegister(FlaskForm):
    password = PasswordField("Password", [DataRequired(), Length(min=8, message="Password must be at least 8 characters"), Regexp(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$', message="Password must contain atleast 1 lowercase,  uppercase character, digit and special character")])
    username = StringField("Company Name", [DataRequired()])
    cntct_mail = StringField("HR email", [DataRequired(), Email(message="Enter valid Email address"), Length(max=40)])
    website = StringField("Website", [DataRequired(), Length(max=100)])
    submit = SubmitField("Register")


