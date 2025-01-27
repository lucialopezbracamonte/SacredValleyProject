from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Initialize Flask app and configure database
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'  # Database location
db = SQLAlchemy(app)  # Initialize SQLAlchemy ORM

# Define the Reports model to represent report entries in the database
class Reports(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Unique ID for each report
    tutor = db.Column(db.String(200), nullable=False)  # Name of the tutor
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)  # Date of the report
    entry = db.Column(db.Time, nullable=False)  # Entry time
    exit = db.Column(db.Time, nullable=False)  # Exit time
    notes = db.Column(db.String(200), nullable=False)  # Additional notes for the report

# Define the Users model to represent users in the database
class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Unique ID for each user
    name = db.Column(db.String(200), nullable=False)  # User's name
    password = db.Column(db.String(200), nullable=True)  # User's password (optional)

# Route for the login page
@app.route('/')
def login():
    # Retrieve all users except the first one
    users = Users.query.order_by(Users.id).offset(1).all()
    return render_template('login.html', users=users)

# Route for the main dashboard page for a specific user
@app.route('/index/<int:id>', methods=['POST', 'GET'])
def index(id):
    if id == 0:  # Redirect admin user to the admin page
        return redirect("/admin")
    # Fetch user name and ID based on the provided ID
    user = Users.query.filter_by(id=id).first().name
    user_id = Users.query.filter_by(id=id).first().id
    # Retrieve all reports for the user, ordered by date (newest first)
    reports = Reports.query.filter_by(tutor=user).order_by(Reports.date.desc()).all()
    return render_template('index.html', reports=reports, user=user, user_id=user_id)

# Route for password verification (admin access)
@app.route('/password', methods=['POST', 'GET'])
def password():
    if request.method == 'GET':
        return render_template('password.html', text="")
    else:
        # Check if the entered password matches the admin's password
        input = request.form['password']
        if input == Users.query.filter_by(name="Gaby").first().password:
            return redirect('/admin')  # Redirect to admin page if valid
        else:
            text = "Contraseña incorrecta"  # Display error message if invalid
            return render_template('password.html', text=text)

# Route for the admin page
@app.route('/admin', methods=['POST', 'GET'])
def admin():
    filters = ['tutor', 'fecha']  # Filtering options
    if request.method == 'GET':
        # Retrieve all reports ordered by date (newest first)
        reports = Reports.query.order_by(Reports.date.desc()).all()
    else:
        # Apply filtering based on the selected option
        filter = request.form['filters']
        if filter == "fecha":
            reports = Reports.query.order_by(Reports.date.desc())
            filters.remove('fecha')
            filters.append('fecha')
        elif filter == "tutor":
            reports = Reports.query.order_by(Reports.tutor.desc())
            filters.remove('tutor')
            filters.append('tutor')
    return render_template('admin.html', filters=filters, reports=reports)

# Route to create a new report
@app.route('/create/<int:id>', methods=['POST', 'GET'])
def create(id):
    user = Users.query.filter_by(id=id).first().name  # Retrieve user name by ID
    if request.method == 'POST':
        # Extract form data for the new report
        date_str = request.form['date']
        entry_str = request.form['entry']
        exit_str = request.form['exit']
        notes = request.form['notes']
        tutor = user

        # Parse date and time strings
        date = datetime.strptime(date_str, '%Y-%m-%d')
        entry = datetime.strptime(entry_str, '%H:%M').time()
        exit_time = datetime.strptime(exit_str, '%H:%M').time()

        # Create and save the new report
        report = Reports(date=date, entry=entry, exit=exit_time, notes=notes, tutor=tutor)
        db.session.add(report)
        db.session.commit()

        return redirect(f"/index/{id}")
    else:
        # Render the create page with current date prefilled
        date = datetime.now()
        user_id = id
        return render_template('create.html', user_id=user_id, date=date)

# Route to view details of a specific report
@app.route('/detail/<int:user_id>/<int:report_id>', methods=['POST', 'GET'])
def detail(user_id, report_id):
    report = Reports.query.filter_by(id=report_id).first()  # Fetch the specific report
    user = Users.query.filter_by(id=user_id).first()  # Fetch the user
    return render_template('detail.html', user=user, report=report)

# Route to delete a specific report
@app.route('/delete/<int:user_id>/<int:report_id>', methods=['POST', 'GET'])
def delete(user_id, report_id):
    report = Reports.query.filter_by(id=report_id).first()  # Fetch the specific report
    if request.method == 'GET':
        return render_template('delete.html', user_id=user_id, report_id=report_id)
    else:
        try:
            # Delete the report from the database
            db.session.delete(report)
            db.session.commit()
            return redirect(f'/index/{user_id}')
        except:
            return 'There was a problem deleting that task'

# Route to edit an existing report
@app.route('/edit/<int:user_id>/<int:report_id>', methods=['POST', 'GET'])
def edit(report_id, user_id):
    report = Reports.query.filter_by(id=report_id).first()  # Fetch the specific report
    if request.method == 'POST':
        # Update report details based on form data
        date_str = request.form['date']
        entry_str = request.form['entry']
        exit_str = request.form['exit']

        report.date = datetime.strptime(date_str, '%Y-%m-%d')
        report.entry = datetime.strptime(entry_str, '%H:%M').time()
        report.exit = datetime.strptime(exit_str, '%H:%M').time()
        report.notes = request.form['notes']

        db.session.commit()  # Save changes to the database
        return redirect(f'/detail/{user_id}/{report_id}')
    else:
        # Render the edit page with prefilled report data
        exit_time = report.exit.strftime('%H:%M')
        entry = report.entry.strftime('%H:%M')
        return render_template("edit.html", user_id=user_id, report=report, entry=entry, exit=exit_time)
