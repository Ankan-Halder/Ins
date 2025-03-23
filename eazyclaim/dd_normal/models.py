from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Claim(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_name = db.Column(db.String(100), nullable=False)
    patient_age = db.Column(db.Integer, nullable=False)
    patient_sex = db.Column(db.String(10), nullable=False)
    hospital_name = db.Column(db.String(255), nullable=False)
    pan_card = db.Column(db.String(20), nullable=False)
    aadhar_card = db.Column(db.String(20), nullable=False)
    hospital_bill_number = db.Column(db.String(50), nullable=False)
    total_bill_amount = db.Column(db.Float, nullable=False)
    claimed_amount = db.Column(db.Float, nullable=False)
    approved_amount = db.Column(db.Float, nullable=False)
    date_of_submission = db.Column(db.Date, nullable=False)
    date_of_discharge = db.Column(db.Date, nullable=False)
    claim_hash = db.Column(db.String(128), unique=True, nullable=False)
