from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, IntegerField, DateField, SubmitField, SelectField
from wtforms.validators import DataRequired, NumberRange

class ClaimForm(FlaskForm):
    patient_name = StringField('Patient Name', validators=[DataRequired()])
    patient_age = IntegerField('Patient Age', validators=[DataRequired(), NumberRange(min=0, max=120)])
    patient_sex = SelectField('Patient Sex', choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')], validators=[DataRequired()])
    hospital_name = StringField('Hospital Name', validators=[DataRequired()])
    pan_card = StringField('PAN Card', validators=[DataRequired()])
    aadhar_card = StringField('Aadhar Card', validators=[DataRequired()])
    hospital_bill_number = StringField('Hospital Bill No.', validators=[DataRequired()])
    total_bill_amount = FloatField('Total Bill Amount', validators=[DataRequired(), NumberRange(min=0)])
    claimed_amount = FloatField('Claimed Amount', validators=[DataRequired(), NumberRange(min=0)])
    date_of_submission = DateField('Date of Submission', format='%Y-%m-%d', validators=[DataRequired()])
    date_of_discharge = DateField('Date of Discharge', format='%Y-%m-%d', validators=[DataRequired()])
    submit = SubmitField('Submit')
