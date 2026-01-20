import os
import re
import time
import smtplib
import subprocess
from email.message import EmailMessage

from flask import Flask, render_template, request

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


# ---------------- HOME PAGE ----------------
@app.route("/")
def index():
    return render_template("index.html")


# ---------------- FORM SUBMISSION ----------------
@app.route("/submit", methods=["POST"])
def submit():
    file = request.files.get("file")
    weights = request.form.get("weights")
    impacts = request.form.get("impacts")
    email = request.form.get("email")

    # -------- BASIC VALIDATION --------
    if not file or not weights or not impacts or not email:
        return "Error: All fields are required"

    # Email validation
    email_regex = r"^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$"
    if not re.match(email_regex, email):
        return "Error: Invalid email format"

    weights_list = weights.split(",")
    impacts_list = impacts.split(",")

    if len(weights_list) != len(impacts_list):
        return "Error: Number of weights must be equal to number of impacts"

    for i in impacts_list:
        if i not in ["+", "-"]:
            return "Error: Impacts must be either + or -"

    # -------- SAVE INPUT FILE --------
    timestamp = int(time.time())
    input_path = os.path.join(UPLOAD_FOLDER, f"input_{timestamp}.csv")
    output_path = os.path.join(OUTPUT_FOLDER, f"result_{timestamp}.csv")

    file.save(input_path)

    # -------- CALL TOPSIS PACKAGE VIA CLI --------
    try:
        command = [
            "topsis",
            input_path,
            weights,
            impacts
        ]
        subprocess.run(command, check=True)

        # Rename generated output file
        if os.path.exists("output.csv"):
            os.rename("output.csv", output_path)
        else:
            return "Error: Output file not generated"

    except Exception as e:
        return f"Error while processing TOPSIS: {str(e)}"

    # -------- SEND EMAIL --------
    try:
        send_email(email, output_path)
    except Exception as e:
        return f"Error while sending email: {str(e)}"

    return "Success! Result file has been sent to your email."


# ---------------- EMAIL FUNCTION ----------------
def send_email(receiver_email, attachment_path):
    sender_email = "vansgarg55@gmail.com"
    sender_password = "yqjnzlgyrnacpbnr"    

    msg = EmailMessage()
    msg["Subject"] = "TOPSIS Result"
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg.set_content("Please find attached the TOPSIS result file.")

    with open(attachment_path, "rb") as f:
        file_data = f.read()
        file_name = os.path.basename(attachment_path)

    msg.add_attachment(
        file_data,
        maintype="application",
        subtype="octet-stream",
        filename=file_name
    )

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)


# ---------------- RUN APP ----------------
if __name__ == "__main__":
    app.run(debug=True)
