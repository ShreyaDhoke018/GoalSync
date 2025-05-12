from extensions import db
from sqlalchemy.dialects.mysql import TINYINT

class Users(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.VARCHAR(50))
    email = db.Column(db.VARCHAR(100))
    password = db.Column(db.VARCHAR(255))
    created_at = db.Column(db.TIMESTAMP)
    last_login = db.Column(db.TIMESTAMP)
    is_active = db.Column(TINYINT(1))

class User_marks(db.Model):
    __tablename__ = 'user_marks'
    id = db.Column(db.Integer, primary_key=True)
    sid = db.Column(db.Integer, db.ForeignKey('users.id'))
    grade = db.Column(db.VARCHAR(150), unique=True)
    marks = db.Column(db.FLOAT)
    hours = db.Column(db.FLOAT)
    capable_cgpa = db.Column(db.FLOAT)
    capable_hours = db.Column(db.FLOAT)

class CourseDetails(db.Model):
    __tablename__ = "course"
    id = db.Column(db.Integer, primary_key=True)
    course_name = db.Column(db.VARCHAR(100))
    subj_names = db.Column(db.Text)