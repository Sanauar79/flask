from flask import Flask, request,render_template,flash, redirect,session,url_for
from flask import send_file
from flask_migrate import Migrate
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Mail, Message
from sqlalchemy import String, Integer, DateTime
import csv
import io
from flask_sqlalchemy import SQLAlchemy
from forms import ContactForm
import bcrypt
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os


app = Flask(__name__)

uri = os.environ.get('DATABASE_URL')
if uri and uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = uri

app.config['SQLALCHEMY_DATABASE_URI'] =  os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)
app.secret_key = 'secret_key'


app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'sanauarh@gmail.com'
app.config['MAIL_PASSWORD'] = 'kftpwzpgeymcwutj'  
app.config['MAIL_DEFAULT_SENDER'] = 'sanauarh@gmail.com'
mail = Mail(app)

serializer = URLSafeTimedSerializer(app.secret_key)

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    is_verified = db.Column(db.Boolean, default=False)
    verification_token = db.Column(db.String(64), unique=True, nullable=True)
    role = db.Column(db.String(10), default='user') 

    contacts = db.relationship('Contact', backref='user', lazy=True)

    def __init__(self,name,email,password,role='user'):
        self.name = name
        self.email = email
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        self.role = role
    
    def check_password(self,password):
        return bcrypt.checkpw(password.encode('utf-8'),self.password.encode('utf-8'))

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self,name,email,phone,description,user_id):
        self.name = name
        self.email = email
        self.phone=phone
        self.description=description
        self.user_id=user_id
        
        

   

# with app.app_context():
#     db.create_all()
#     print("Database tables created.")


@app.route('/')
def index():
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    errors = {}

    if request.method == 'POST':
        name = request.form['name'].strip()
        email = request.form['email'].strip()
        password = request.form['password'].strip()

        if not name:
            errors['name'] = 'Name is required.'
        if not email:
            errors['email'] = 'Email is required.'
        elif User.query.filter_by(email=email).first():
            errors['email'] = 'Email already exists.'
        if not password:
            errors['password'] = 'Password is required.'
        elif len(password) < 6:
            errors['password'] = 'Password must be at least 6 characters.'

        if not errors:
            new_user = User(name=name, email=email, password=password,role='user')
            db.session.add(new_user)
            db.session.commit()

            token = serializer.dumps(email, salt='email-confirm')

            confirm_url = url_for('confirm_email', token=token, _external=True)

            msg = Message('Please confirm your email', recipients=[email])
            msg.body = f'Hi {name},\n\nPlease confirm your email by clicking the link:\n{confirm_url}\n\nThank you!'
            mail.send(msg)

            flash('Registration successful. Please check your email to confirm.', 'info')
            return redirect('/login')

    return render_template('register.html', errors=errors)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        if not email or not password:
            flash('Please fill in all fields.', 'danger')
            return render_template('login.html')

        user = User.query.filter_by(email=email).first()

        if user:
           
            if not user.is_verified:
                flash('Please verify your email before logging in.', 'warning')
                return render_template('login.html')

           
            if user.check_password(password):
                session['email'] = user.email
                session['role'] = user.role  

            flash(f'Welcome {user.name}!', 'success')

         
            if user.role == 'admin':
                return redirect('/admin_dashboard')
            else:
                return redirect('/user_dashboard')
        else:
            flash('Invalid email or password.', 'danger')
   
    return render_template('login.html')

@app.route('/admin_dashboard')
def admin_dashboard():
    if 'email' not in session or session.get('role') != 'admin':
        flash('Access denied.', 'danger')
        return redirect('/login')
    
    user = User.query.filter_by(email=session['email']).first()
    users = User.query.all()
    return render_template('admin_dashboard.html', user=user , users=users)

@app.route('/user_dashboard')
def user_dashboard():
    if 'email' not in session or session.get('role') != 'user':
        flash('Access denied.', 'danger')
        return redirect('/login')
    
    user = User.query.filter_by(email=session['email']).first()
    messages = Contact.query.filter_by(user_id=user.id).all()
    message_count = len(messages)
    return render_template('user_dashboard.html' , user=user,message_count=message_count,messages=messages)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if 'email' not in session:
        flash("Please log in first.", "danger")
        return redirect('/login')
    user = User.query.filter_by(email=session['email']).first()
    form = ContactForm()
    if form.validate_on_submit():
        message = Contact(
            name=form.name.data,
            email=form.email.data,
            phone=form.phone.data,
            description=form.description.data,
            user_id=user.id if user else None  
        )

        db.session.add(message)
        db.session.commit()

        send_email_to_user(
            name=form.name.data,
            to_email=form.email.data
        )

        send_email_to_admin(
            name=form.name.data,
            email=form.email.data,
            phone=form.phone.data,
            description=form.description.data
        )

        flash('Message sent and saved successfully!', 'success')
        return redirect(url_for('user_dashboard'))

    return render_template('contact.html', form=form)


@app.route('/admin/messages')
def admin_messages():
    if 'email' not in session:
        flash("Please log in first.", "danger")
        return redirect('/login')
    messages = Contact.query.order_by(Contact.id.desc()).all()
    return render_template('admin_messages.html', messages=messages)

@app.route('/delete_message/<int:message_id>', methods=['GET'])
def delete_message(message_id):
    message = Contact.query.get_or_404(message_id)
    db.session.delete(message)
    db.session.commit()
    flash('Message deleted successfully.', 'success')
    return redirect(url_for('admin_messages')) 

@app.route('/update_message/<int:message_id>', methods=['GET', 'POST'])
def update_message(message_id):
    message = Contact.query.get_or_404(message_id)

    form = ContactForm(obj=message)  

    if form.validate_on_submit():
        message.name = form.name.data
        message.email = form.email.data
        message.phone = form.phone.data
        message.description = form.description.data  
        db.session.commit()
        flash('Message updated successfully.', 'success')
        return redirect(url_for('admin_messages'))

    return render_template('update_message.html', form=form, message=message)



@app.route('/logout')
def logout():
    session.pop('email',None)
    return redirect('/login')

@app.route('/admin/export')
def export_messages():
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(['ID', 'Name', 'Email', 'Message'])
    messages = Contact.query.all()
    for msg in messages:
        writer.writerow([msg.id, msg.name, msg.email,msg.phone, msg.description])

    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype='text/csv',
        download_name='contact_messages.csv',
        as_attachment=True
    )

@app.route('/confirm/<token>')
def confirm_email(token):
    try:
        email = serializer.loads(token, salt='email-confirm', max_age=3600)  
    except:
        flash('The confirmation link is invalid or has expired.', 'danger')
        return redirect('/login')

    user = User.query.filter_by(email=email).first_or_404()
    if user.is_verified:
        flash('Account already confirmed. Please login.', 'success')
    else:
        user.is_verified = True
        db.session.commit()
        flash('Email confirmed. You can now login.', 'success')

    return redirect('/login')


def send_email_to_user(name, to_email):
    subject = "Thank you for contacting us"
    body = f"""
    Hi {name},

    Thanks for reaching out to us. We have received your message and will get back to you soon.

    Best regards,
    CRUD Team
    """
    send_email(to_email, subject, body)


def send_email_to_admin(name, email, phone, description):
    subject = "New Contact Form Submission"
    body = f"""
    A new contact form has been submitted:

    Name: {name}
    Email: {email}
    Phone: {phone}
    Message:
    {description}
    """
    admin_email = "sanauarh@gmail.com" 
    send_email(admin_email, subject, body)


def send_email(to_email, subject, body):
    sender_email = "sanauarh@gmail.com"
    sender_password = "kftpwzpgeymcwutj" 

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
            smtp.starttls()
            smtp.login(sender_email, sender_password)
            smtp.send_message(msg)
    except Exception as e:
        print(f"Failed to send email: {e}")


if __name__ == '__main__':
    app.run(debug=True)