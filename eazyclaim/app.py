from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import random
import os
import re
import PyPDF2
from PIL import Image
import pytesseract

app = Flask(__name__)

# Database configuration
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(BASE_DIR, 'easyclaim.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')  # Or specify a custom path
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

db = SQLAlchemy(app)

# Models
class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    dob = db.Column(db.String(20), nullable=False)
    sex = db.Column(db.String(10), nullable=False)
    mobile = db.Column(db.String(10), nullable=False, unique=True)
    email = db.Column(db.String(100), nullable=False, unique=True)
    aadhar = db.Column(db.String(12), nullable=False, unique=True)
    pan = db.Column(db.String(10), nullable=False, unique=True)
    card_number = db.Column(db.String(19), nullable=False)
    expiry_date = db.Column(db.String(10), nullable=False)
    cvv = db.Column(db.String(3), nullable=False)
    credit_amount = db.Column(db.Float, nullable=False)  # New field for total cover amount

class InsurancePolicy(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('application.id'), nullable=False)
    insurance_name = db.Column(db.String(100), nullable=False)
    policy_number = db.Column(db.String(50), nullable=False)
    cover_amount = db.Column(db.Float, nullable=False)

class Claim(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    card_number = db.Column(db.String(20), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    aadhar = db.Column(db.String(20), nullable=False)
    pan = db.Column(db.String(20), nullable=False)
    hospital_name = db.Column(db.String(255), nullable=False)
    bill_number = db.Column(db.String(50), nullable=False)
    bill_amount = db.Column(db.Float, nullable=False)


# Create tables
with app.app_context():
    db.create_all()

# Routes
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/apply', methods=['GET', 'POST'])
def apply_card():
    if request.method == 'POST':
        # Collect form data
        name = request.form['name']
        age = request.form['age']
        dob = request.form['dob']
        sex = request.form['sex']
        mobile = request.form['mobile']
        email = request.form['email']
        aadhar = request.form['aadhar']
        pan = request.form['pan']

        # Generate credit card details
        card_number = generate_card_number()
        expiry_date = "12/30"  # Example expiry date
        cvv = str(random.randint(100, 999))

        # Collect insurance details
        insurance_names = request.form.getlist('insurance_name[]')
        policy_numbers = request.form.getlist('policy_number[]')
        covers = request.form.getlist('cover[]')

        # Calculate total credit amount (sum of all cover amounts)
        total_cover_amount = sum(float(cover) for cover in covers)

        # Save application details in the database
        application = Application(
            name=name, age=age, dob=dob, sex=sex, mobile=mobile,
            email=email, aadhar=aadhar, pan=pan,
            card_number=card_number, expiry_date=expiry_date, cvv=cvv,
            credit_amount=total_cover_amount  # Store total cover as credit amount
        )
        db.session.add(application)
        db.session.commit()

        # Save insurance details in the database
        for insurance_name, policy_number, cover in zip(insurance_names, policy_numbers, covers):
            policy = InsurancePolicy(
                application_id=application.id,
                insurance_name=insurance_name,
                policy_number=policy_number,
                cover_amount=float(cover)
            )
            db.session.add(policy)

        db.session.commit()

        # Redirect to the success page with generated details
        return render_template(
            'success.html',
            name=name,
            card_number=card_number,
            expiry_date=expiry_date,
            cvv=cvv,
            credit_amount=total_cover_amount
        )

    return render_template('apply.html')


    

@app.route('/submit_claim', methods=['GET', 'POST'])
def submit_claim():
    if request.method == 'POST':
        # Check if it's a card search request
        if 'card_number' in request.form:
            card_number = request.form.get('card_number')  # Safely get the card number from the form

            if card_number:
                # Search for the card details in the database
                card = Application.query.filter_by(card_number=card_number).first()

                if card:
                    # Fetch all insurance policies related to the card
                    insurances = InsurancePolicy.query.filter_by(application_id=card.id).all()

                    # Calculate the total insurance cover
                    total_cover = sum(policy.cover_amount for policy in insurances)

                    # Render the template with card and insurance details
                    return render_template(
                        'submit_claim.html',
                        card={
                            "id": card.id,
                            "name": card.name,
                            "card_number": card.card_number,
                            "insurance_cover": total_cover  # Total insurance cover
                        },
                        insurances=insurances,  # List of associated policies
                        error=None  # No error
                    )
                else:
                    # Card not found
                    return render_template('submit_claim.html', card=None, insurances=None, error="Card not found.")
            else:
                # No card number provided
                return render_template('submit_claim.html', card=None, insurances=None, error="Please provide a card number.")

        # Check if it's a file upload request
        elif 'file' in request.files:
            file = request.files['file']
            card_id = request.form.get('card_id')

            if file and card_id:
                try:
                    # Save uploaded file
                    upload_folder = app.config.get('UPLOAD_FOLDER', './uploads')  # Default to './uploads' if not configured
                    os.makedirs(upload_folder, exist_ok=True)  # Ensure the folder exists

                    file_path = os.path.join(upload_folder, file.filename)
                    file.save(file_path)

                    # Extract data from the uploaded file
                    extracted_data = extract_data_from_file(file_path)

                    

                    if not extracted_data:
                        return render_template(
                            'submit_claim.html',
                            card=None,
                            extracted_data=None,
                            error="Failed to extract data from the file."
                        )

                    # Fetch card details for display
                    card = Application.query.get(card_id)
                    if card:
                        insurances = InsurancePolicy.query.filter_by(application_id=card.id).all()  # Fetch related policies
                        total_cover = sum(policy.cover_amount for policy in insurances)
                        return render_template(
                        'submit_claim.html',
                        card={
                            "id": card.id,
                            "name": card.name,
                            "card_number": card.card_number,
                            "insurance_cover": total_cover
                            
                        },
                        insurances=insurances, 
                        extracted_data=extracted_data,
                        error=None
                        )
                    else:
                        return render_template('submit_claim.html', card=None, extracted_data=None, error="Card not found.")

                except Exception as e:
                    # Handle any exceptions during file processing
                    return render_template('submit_claim.html', card=None, extracted_data=None, error=f"An error occurred: {e}")
            else:
                # File or card_id missing
                return render_template('submit_claim.html', card=None, extracted_data=None, error="File or card ID is missing.")

        # Check if it's a claim submission request
        elif 'confirm_claim' in request.form:
            card_id = request.form.get('card_id')
            bill_number = request.form.get('bill_number')
            bill_amount = request.form.get('bill_amount')
            hospital_name = request.form.get('hospital_name')

            if card_id and bill_number and bill_amount and hospital_name:
                try:
                    # Save the claim to the database
                    card = Application.query.get(card_id)
                    claim = Claim(
                        card_number=card.card_number,
                        name=card.name,
                        aadhar=card.aadhar,
                        pan=card.pan,
                        hospital_name=hospital_name,
                        bill_number=bill_number,
                        bill_amount=bill_amount
                    )
                    db.session.add(claim)
                    db.session.commit()

                    return render_template(
                        'submit_claim.html',
                        card={
                            "id": card.id,
                            "name": card.name,
                            "card_number": card.card_number,
                            "aadhar": card.aadhar,
                            "pan": card.pan,
                        },
                        claim=claim,
                        extracted_data=None,
                        error=None
                    )
                except Exception as e:
                    # Handle database errors
                    return render_template('submit_claim.html', card=None, extracted_data=None, error=f"An error occurred: {e}")
            else:
                # Missing required fields
                return render_template('submit_claim.html', card=None, extracted_data=None, error="All fields are required.")

    # Default response for GET requests
    return render_template('submit_claim.html', card=None, extracted_data=None, error=None)



def preprocess_text(text):
    """Clean and preprocess extracted text."""
    # Normalize line breaks and spaces
    text = text.replace("\n", " ").strip()
    text = re.sub(r"\s+", " ", text)

    # Standardize currency symbols
    text = text.replace("Rs.", "₹").replace("INR", "₹")
    
    return text


def parse_text(text):
    """Parse text to extract hospital name, bill amount, and bill number."""
    # Initialize the dictionary to store extracted data
    extracted_data = {}

    # Preprocess the text for consistency
    text = preprocess_text(text)

    # Define regex patterns for extracting information
    hospital_name_pattern = r"(Hospital Name|Facility):\s*([^\n]+)"
    bill_number_pattern = r"(Bill Number|Invoice No\.|Invoice Number):\s*(\w+)"
    bill_amount_pattern = r"(Total Amount|Bill Amount|Amount Paid):?\s*₹?\s*([\d,]+\.\d{1,2}|\d+)"

    # Extract hospital name
    hospital_match = re.search(hospital_name_pattern, text, re.IGNORECASE)
    if hospital_match:
        extracted_data["hospital_name"] = hospital_match.group(2).strip()

    # Extract bill number
    bill_number_match = re.search(bill_number_pattern, text, re.IGNORECASE)
    if bill_number_match:
        extracted_data["bill_number"] = bill_number_match.group(2).strip()

    # Extract bill amount
    bill_amount_match = re.search(bill_amount_pattern, text, re.IGNORECASE)
    if bill_amount_match:
        extracted_data["bill_amount"] = bill_amount_match.group(2).replace(",", "").strip()

    return extracted_data


def extract_data_from_file(file_path):
    """Extract data from a PDF or image file."""
    extracted_data = {}

    # Handle PDF files
    if file_path.lower().endswith(".pdf"):
        try:
            with open(file_path, "rb") as pdf_file:
                reader = PyPDF2.PdfReader(pdf_file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() or ""  # Ensure no None type is appended
                print("Extracted Text from PDF:", text)  # Debugging print
                extracted_data = parse_text(text)  # Parse the extracted text
        except Exception as e:
            print(f"Error extracting text from PDF: {e}")

    # Handle image files
    elif file_path.lower().endswith((".jpg", ".jpeg", ".png")):
        try:
            image = Image.open(file_path).convert("L")  # Convert to grayscale for better OCR accuracy
            text = pytesseract.image_to_string(image)  # Perform OCR
            print("Extracted Text from Image:", text)  # Debugging print
            extracted_data = parse_text(text)  # Parse the extracted text
        except Exception as e:
            print(f"Error extracting text from image: {e}")

    return extracted_data

# Utility Functions
def generate_card_number():
    """Generate a random 16-digit credit card number."""
    return " ".join(str(random.randint(1000, 9999)) for _ in range(4))

# Main Entry
if __name__ == '__main__':
    app.run(debug=True,port=5002)
