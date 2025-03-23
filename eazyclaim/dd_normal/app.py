from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from forms import ClaimForm
from models import db, Claim
import hashlib
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mysecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/claims/submit-claim/', methods=['GET', 'POST'])
def submit_claim():
    form = ClaimForm()
    if form.validate_on_submit():
        data_string = form.pan_card.data + form.aadhar_card.data + form.hospital_bill_number.data
        claim_hash = hashlib.sha512(data_string.encode()).hexdigest()

        # Check if claim already exists in the database
        existing_claim = Claim.query.filter_by(claim_hash=claim_hash).first()
        if existing_claim:
            flash('Duplicate claim detected! This claim has already been submitted.', 'danger')
            return redirect(url_for('submit_claim'))  # Redirect back to form

        approved_amount = min(form.claimed_amount.data, form.total_bill_amount.data)

        claim = Claim(
            patient_name=form.patient_name.data,
            patient_age=form.patient_age.data,
            patient_sex=form.patient_sex.data,
            hospital_name=form.hospital_name.data,
            pan_card=form.pan_card.data,
            aadhar_card=form.aadhar_card.data,
            hospital_bill_number=form.hospital_bill_number.data,
            total_bill_amount=form.total_bill_amount.data,
            claimed_amount=form.claimed_amount.data,
            approved_amount=approved_amount,
            date_of_submission=form.date_of_submission.data,
            date_of_discharge=form.date_of_discharge.data,
            claim_hash=claim_hash
        )
        db.session.add(claim)
        db.session.commit()
        flash('Claim submitted successfully!', 'success')
        return redirect(url_for('claim_list'))

    return render_template('submit_claim.html', form=form)


@app.route('/claims/')
def claim_list():
    claims = Claim.query.all()
    return render_template('claim_list.html', claims=claims)

if __name__ == '__main__':
    app.run(debug=True, port=5001)
