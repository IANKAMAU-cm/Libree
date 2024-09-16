from flask import Flask, render_template, redirect, url_for, flash, request, session
from flask_sqlalchemy import SQLAlchemy
from models import Admin, Book, Member, Loan
from forms import LoginForm, RegisterForm, BookForm, EditBookForm, MLoginForm, MRegisterForm
from flask_login import LoginManager, login_user, logout_user
from database import db
import os
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from flask_wtf.csrf import CSRFProtect
from flask_wtf import FlaskForm
from wtforms import SubmitField


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///library.db'
app.config['SECRET_KEY'] = 'your_secret_key'  # Add a secret key for security

app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
csrf = CSRFProtect(app)
# Load configurations
app.config.from_object('config.Config')

# Initialize database with the app
db.init_app(app)

# Initialize Flask-Login
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return Admin.query.get(int(user_id))

# Routes
@app.route('/')
def home():
    return redirect(url_for('mlogin'))

@app.route('/manage_members')
def manage_members():
    members = Member.query.all()  # Retrieve all members
    return render_template('manage_members.html', members=members)

@app.route('/librarian/member/<int:member_id>/loans')
def librarian_member_loans(member_id):
    # Retrieve the member by their ID
    member = Member.query.get_or_404(member_id)
    
    # Retrieve the loans for the member
    loans = Loan.query.filter_by(member_id=member_id).all()
    
    # Render the admin-specific template
    return render_template('librarian_member_loans.html', loans=loans, member=member)



#Route for admin registration and login
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        admin = Admin.query.filter_by(username=form.username.data).first()
        if admin and admin.check_password(form.password.data):
            login_user(admin)
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))  # Redirect to dashboard after login
        else:
            flash('Invalid username or password.')
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        # Create new admin user
        new_admin = Admin(username=form.username.data)
        new_admin.set_password(form.password.data)  # Hash the password
        db.session.add(new_admin)
        db.session.commit()
        flash('Account created successfully! You can now log in.', 'success')
        return redirect(url_for('login'))  # Redirect to login after registration

    return render_template('register.html', form=form)

@app.route('/logout')
def logout():
    logout_user()  # Use Flask-Login's logout function
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))  # Redirect to login page

#Member Registration and login routes
@app.route('/memberregister', methods=['GET', 'POST'])
def mregister():
    form = MRegisterForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256')
        new_member = Member(username=form.username.data, password=hashed_password)
        db.session.add(new_member)
        db.session.commit()
        flash('Account created successfully!', 'success')
        return redirect(url_for('login'))
    if Member.query.filter_by(username=form.username.data).first():
        flash('Username already exists.', 'danger')
        return redirect(url_for('memberregister'))
    
    return render_template('memberregister.html', form=form)

@app.route('/memberlogin', methods=['GET', 'POST'])
def mlogin():
    form = MLoginForm()
    if form.validate_on_submit():
        member = Member.query.filter_by(username=form.username.data).first()
        if member and check_password_hash(member.password, form.password.data):
            session['member_id'] = member.id
            flash('Login successful!', 'success')
            return redirect(url_for('view_books'))
        else:
            flash('Login unsuccessful. Check your username and password.', 'danger')
    return render_template('memberlogin.html', form=form)

@app.route('/mlogout')
def mlogout():
    session.pop('member_id', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('mlogin'))


#route to the dashboard
@app.route('/dashboard')
def dashboard():
    # You can add logic to fetch data about books, loans, members, etc.
    selected_member_id = None  # Define or retrieve the selected member ID
    return render_template('dashboard.html', selected_member_id=selected_member_id)

# Route to list books
@app.route('/books')
def list_books():
    books = Book.query.all()
    return render_template('list_books.html', books=books)

@app.route('/view_books')
def view_books():
    books = Book.query.all()  # Query to fetch all books

    if 'member_id' not in session:
        flash('Please log in to access this page.', 'warning')
        return redirect(url_for('mlogin'))
    return render_template('view_books.html', books=books)

@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    form = BookForm()
    if form.validate_on_submit():
        # Handle the picture upload
        picture_file = None
        if form.picture.data:
            picture_file = secure_filename(form.picture.data.filename)
            form.picture.data.save(os.path.join(app.config['UPLOAD_FOLDER'], picture_file))

        # Create a new book
        new_book = Book(
            picture=picture_file,
            title=form.title.data,
            author=form.author.data,
            isbn=form.isbn.data,
            genre=form.genre.data,
            description=form.description.data,
            publication_year=form.publication_year.data,
            available_quantity=form.available_quantity.data,
            total_quantity=form.total_quantity.data,
            shelf=form.shelf.data
        )

        db.session.add(new_book)
        db.session.commit()
        flash('Book added successfully!', 'success')
        return redirect(url_for('list_books'))

    return render_template('add_book.html', form=form)

@app.route('/book/<int:book_id>/edit', methods=['GET', 'POST'])
def edit_book(book_id):
    book = Book.query.get_or_404(book_id)
    form = EditBookForm()

    if form.validate_on_submit():
        book.title = form.title.data
        book.author = form.author.data
        book.isbn = form.isbn.data
        book.genre = form.genre.data
        book.description = form.description.data
        book.publication_year = form.publication_year.data
        book.available_quantity = form.available_quantity.data
        book.total_quantity = form.total_quantity.data
        book.shelf = form.shelf.data

        if form.picture.data:
            picture_file = secure_filename(form.picture.data.filename)
            picture_path = os.path.join(app.config['UPLOAD_FOLDER'], picture_file)
            form.picture.data.save(picture_path)
            book.picture = picture_file

        db.session.commit()
        flash(f'Book {book.title} has been updated!', 'success')
        return redirect(url_for('list_books'))

    elif request.method == 'GET':
        # Pre-populate the form with existing book data
        form.title.data = book.title
        form.author.data = book.author
        form.isbn.data = book.isbn
        form.genre.data = book.genre
        form.description.data = book.description
        form.publication_year.data = book.publication_year
        form.available_quantity.data = book.available_quantity
        form.total_quantity.data = book.total_quantity
        form.shelf.data = book.shelf

    return render_template('edit_book.html', form=form, book=book)

@app.route('/borrow/<int:book_id>', methods=['POST'])
def borrow_book(book_id):
    if 'member_id' not in session:
        flash('Please log in to borrow a book', 'danger')
        return redirect(url_for('login'))
    
    book = Book.query.get_or_404(book_id)
    if book.available_quantity > 0:
        due_date = datetime.utcnow() + timedelta(days=14)  # Set due date to 14 days from now
        loan = Loan(book_id=book.id, member_id=session['member_id'], status='borrowed', due_date=due_date)
        book.available_quantity -= 1
        db.session.add(loan)
        db.session.commit()
        flash(f'You have successfully borrowed {book.title}', 'success')
    else:
        flash('This book is currently unavailable', 'danger')
    return redirect(url_for('view_books'))


# Define a simple form with CSRF protection
class ReturnBookForm(FlaskForm):
    submit = SubmitField('Mark as Returned')

@app.route('/return/<int:loan_id>', methods=['POST'])
def return_book(loan_id):
    form = ReturnBookForm()

    if form.validate_on_submit():  # Ensures CSRF token is valid
        loan = Loan.query.get_or_404(loan_id)
        book = Book.query.get(loan.book_id)
        
        # Check if the book is overdue
        if datetime.utcnow() > loan.due_date and loan.status == 'borrowed':
            loan.status = 'overdue'
            flash(f'The book {book.title} is overdue! Please return it as soon as possible.', 'warning')

        if loan.status == 'borrowed':
            loan.status = 'returned'
            loan.return_date = datetime.utcnow()
            book.available_quantity += 1
            db.session.commit()
            flash(f'Book {book.title} has been returned successfully.', 'success')

        # Redirect to different pages based on the role
        if 'librarian_id' in session:
            return redirect(url_for('dashboard', member_id=loan.member_id))
        elif 'member_id' in session and session['member_id'] == loan.member_id:
            return redirect(url_for('dashboard', member_id=loan.member_id))
        else:
            return redirect(url_for('dashboard'))  # Redirect to a default page if neither role is detected

    # Handle case where form validation fails
    flash('Invalid submission or CSRF token.', 'danger')
    return redirect(url_for('book_loans'))


@app.route('/member/<int:member_id>/loans')
def member_loans(member_id):
    if 'member_id' not in session or session['member_id'] != member_id:
        flash('You are not authorized to view this page.', 'danger')
        return redirect(url_for('mlogin'))
    member = Member.query.get_or_404(member_id)
    loans = Loan.query.filter_by(member_id=member_id).all()
    return render_template('member_loans.html', loans=loans, member=member, member_id=member_id)

@app.route('/book_loans')
def book_loans():
    loans = Loan.query.filter(Loan.status != 'returned').all()  # Show only active loans
    form = ReturnBookForm()  # Create an instance of the form
    return render_template('book_loans.html', loans=loans, form=form)

#search route
@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query')
    
    if query:
        # Searching across multiple models, adjust depending on your schema
        book_results = Book.query.filter(
            (Book.title.ilike(f'%{query}%')) | 
            (Book.author.ilike(f'%{query}%')) |
            (Book.isbn.ilike(f'%{query}%'))
        ).all()

        member_results = Member.query.filter(
            (Member.username.ilike(f'%{query}%')) |
            (Member.borrow_history.ilike(f'%{query}%'))
        ).all()

        loan_results = Loan.query.filter(
            (Loan.book.ilike(f'%{query}%')) |
            (Loan.status.ilike(f'%{query}%')) | 
            (Loan.borrow_date.ilike(f'%{query}%')) |
            (Loan.return_date.ilike(f'%{query}%')) |
            (Loan.due_date.ilike(f'%{query}%'))
        ).all()

        return render_template('search_results.html', 
                               query=query, 
                               book_results=book_results, 
                               member_results=member_results,
                               loan_results=loan_results)
    else:
        # No query, just redirect to the dashboard or show an error message
        return redirect(url_for('dashboard'))


# Create the database tables if they don't exist
if __name__ == '__main__':
    with app.app_context():
        #db.drop_all()
        db.create_all()
    app.run(debug=True)