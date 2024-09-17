from flask import Flask, render_template, redirect, url_for, flash, request, session, send_file
from flask_sqlalchemy import SQLAlchemy
from models import Admin, Book, Member, Loan, Ebook
from forms import LoginForm, RegisterForm, BookForm, EditBookForm, MLoginForm, MRegisterForm, EbookUploadForm
from flask_login import LoginManager, login_user, logout_user
from database import db
import os
import pandas as pd
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from flask_wtf.csrf import CSRFProtect
from flask_wtf import FlaskForm
from wtforms import SubmitField
from io import BytesIO


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
        new_admin.set_password(form.password.data, method='pbkdf2:sha256')  # Hash the password
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
    # Card 1: Most Recent Borrowed Books
    recent_borrowed_books = Loan.query.order_by(Loan.borrow_date.desc()).limit(5).all()

    # Card 2: Total Books and E-books
    total_books = Book.query.count()
    total_ebooks = Ebook.query.count()

    # Graph 1: Members with Most Borrowed Books
    members = Member.query.all()
    member_names = [member.username for member in members]
    member_borrow_count = [Loan.query.filter_by(member_id=member.id).count() for member in members]

    # Graph 2: Most Borrowed Books
    books = Book.query.all()
    book_titles = [book.title for book in books]
    book_borrow_count = [Loan.query.filter_by(book_id=book.id).count() for book in books]


    selected_member_id = None  # Define or retrieve the selected member ID
    return render_template('dashboard.html', selected_member_id=selected_member_id, recent_borrowed_books=recent_borrowed_books,
        total_books=total_books,
        total_ebooks=total_ebooks,
        member_names=member_names,
        member_borrow_count=member_borrow_count,
        book_titles=book_titles,
        book_borrow_count=book_borrow_count)

# Route to list books
@app.route('/books')
def list_books():
    books = Book.query.all()
    return render_template('list_books.html', books=books)

@app.route('/view_books', methods=['GET'])
def view_books():
    # Get the current page number, defaulting to 1 if not provided
    page = request.args.get('page', 1, type=int)
    
    # Define how many books per page
    per_page = 10

    books = Book.query.paginate(page=page, per_page=per_page)
    #books = Book.query.all()  # Query to fetch all books

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

        member_results = Member.query.join(Loan).filter(
            (Member.username.ilike(f'%{query}%'))
        ).all()

        # Search in the Loan model and join with Book and Member to search related fields
        loan_results = Loan.query.join(Member).join(Book).filter(
            (Book.title.ilike(f'%{query}%')) |   # Search for the book title in loans
            (Loan.status.ilike(f'%{query}%')) | 
            (Loan.due_date.ilike(f'%{query}%')) |
            (Member.username.ilike(f'%{query}%'))  # Search for member username in loans
        ).all()

        return render_template('search_results.html', 
                               query=query, 
                               book_results=book_results, 
                               member_results=member_results,
                               loan_results=loan_results)
    else:
        # No query, just redirect to the dashboard or show an error message
        return redirect(url_for('dashboard'))


# Route for searching books
@app.route('/search_books', methods=['GET'])
def search_books():
    query = request.args.get('query')
    page = request.args.get('page', 1, type=int)
    per_page = 10

    if query:
        # Search for books by title, author, or ISBN
        book_results = Book.query.filter(
            (Book.title.ilike(f'%{query}%')) | 
            (Book.author.ilike(f'%{query}%')) | 
            (Book.isbn.ilike(f'%{query}%'))
        ).paginate(page=page, per_page=per_page)

        return render_template('view_books.html', books=book_results, query=query)
    else:
        # If no query, return all books or redirect to the view_books page
        all_books = Book.query.all()
        return render_template('view_books.html', books=all_books)


@app.route('/upload_ebook', methods=['GET', 'POST'])
def upload_ebook():
    form = EbookUploadForm()
    if request.method == 'POST' and form.validate_on_submit():
        title = form.title.data
        file = form.file.data

        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            # Store the path relative to 'static' for URLs
            file_url = f'uploads/{filename}'
            # Debugging print statements
            print(f"File saved at: {file_path}")  # File path on disk
            print(f"File URL: {file_url}")        # URL path


            new_ebook = Ebook(title=title, file_path=file_url)
            db.session.add(new_ebook)
            db.session.commit()

            flash('E-book uploaded successfully!', 'success')
            return redirect(url_for('upload_ebook'))

    return render_template('upload_ebook.html', form=form)

@app.route('/view_ebooks')
def view_ebooks():
    ebooks = Ebook.query.all()
    return render_template('view_ebooks.html', ebooks=ebooks)

@app.route('/read_ebook/<int:ebook_id>')
def read_ebook(ebook_id):
    ebook = Ebook.query.get_or_404(ebook_id)
    return render_template('read_ebook.html', ebook=ebook)


@app.route('/report/borrowed_books', methods=['GET'])
def borrowed_books_report():
    # Query borrowed books
    borrowed_books = Loan.query.filter_by(status='borrowed').all()

    # Create data for the report
    data = []
    for loan in borrowed_books:
        data.append({
            "Book Title": loan.book.title,
            "Author": loan.book.author,
            "ISBN": loan.book.isbn,
            "Borrower Name": loan.member.username,
            "Borrow Date": loan.borrow_date,
            "Due Date": loan.due_date
        })

    # Create a DataFrame and export it as a CSV
    df = pd.DataFrame(data)
    
    # Save to a BytesIO buffer to send as a file
    buffer = BytesIO()
    df.to_csv(buffer, index=False)
    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name="borrowed_books_report.csv", mimetype='text/csv')

@app.route('/reports')
def reports_page():
    return render_template('reports.html')

@app.route('/report/all_books', methods=['GET'])
def all_books_report():
    # Query all books and e-books
    books = Book.query.all()
    ebooks = Ebook.query.all()

    # Create data for the report
    data = []
    # Add physical books
    for book in books:
        data.append({
            "Title": book.title,
            "Author": book.author,
            "ISBN": book.isbn,
            "Publication Year": book.publication_year
        })
    
    # Add e-books
    for ebook in ebooks:
        data.append({
            "Title": ebook.title,
            "Author": 'N/A',  # Assuming e-books don't have an author field
            "ISBN": 'N/A',    # Assuming e-books don't have an ISBN field
            "Publication Year": 'N/A'  # Assuming e-books don't have a publication year
        })

    # Create a DataFrame and export as a CSV
    df = pd.DataFrame(data)
    
    buffer = BytesIO()
    df.to_csv(buffer, index=False)
    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name="all_books_report.csv", mimetype='text/csv')



@app.route('/report/returned_books', methods=['GET'])
def returned_books_report():
    # Query returned books
    returned_books = Loan.query.filter_by(status='returned').all()

    # Create data for the report
    data = []
    for loan in returned_books:
        data.append({
            "Book Title": loan.book.title,
            "Author": loan.book.author,
            "ISBN": loan.book.isbn,
            "Borrower Name": loan.member.username,
            "Borrow Date": loan.borrow_date,
            "Return Date": loan.return_date
        })

    # Create a DataFrame and export as a CSV
    df = pd.DataFrame(data)

    buffer = BytesIO()
    df.to_csv(buffer, index=False)
    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name="returned_books_report.csv", mimetype='text/csv')



# Create the database tables if they don't exist
if __name__ == '__main__':
    with app.app_context():
        db.drop_all()
        #db.create_all()
    app.run(debug=True)