from flask import render_template, flash, redirect, url_for, request, abort
from app import app, db
from app.forms import LoginForm, RegistrationForm
from flask_login import current_user, login_user, logout_user, login_required
import sqlalchemy as sa
from app.models import User, Role, Prints
from urllib.parse import urlsplit
# import cups
import tempfile
import os
from flask_admin.contrib.sqla import ModelView
from flask_admin import BaseView, Admin
from flask_security import Security, SQLAlchemyUserDatastore
import uuid
import PyPDF2


@app.route('/')
@app.route('/index')
@login_required
def index():
    user = {'username': 'Akshit'}
    posts = [
        {
            'author': {'username': 'John'},
            'body': 'Beautiful day in Portland!'
        },
        {
            'author': {'username': 'Susan'},
            'body': 'The Avengers movie was so cool!'
        }
    ]
    return render_template('index.html', title='Home', user=current_user, posts=posts)

###################################################################################################
#Login and user registration
###################################################################################################

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.scalar(sa.select(User).where(User.username == form.username.data))
        if user is None or not user.check_password(form.password.data):
            flash('incorrect username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or urlsplit(next_page).netloc != '':
            next_page = url_for('index')                  
        return redirect(next_page)
    return render_template('login.html', title = 'Sign In', form = form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods = ['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data)
        user.set_password(form.password.data)
        user.weekly_limit = 10
        user.balance = 0
        user.pages_printed = 0 
        user.weekly_print_number = 10
        user.room_number = 9999
        user.role_id=1
        user.fs_uniquifier = uuid.uuid4().hex
        db.session.add(user)
        db.session.commit()
        flash('Registatration Complete!!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


###################################################################################################
#Admin and Roles
###################################################################################################

class AdminPage(BaseView):
    def is_accessible(self):
        return current_user.is_authenticated
        # current_user.role.name == 'Admin'

class AdminModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated
        # current_user.role.name == 'Admin'

    def _handle_view(self, name, **kwargs):
        if not self.is_accessible():
            return redirect(url_for('login', next=request.url))
        
    form_excluded_columns=('prints')


class UserAdmin(AdminModelView):
    column_list = ('username', 'role.name','role_id' ,'balance')
    column_labels = {'username': 'Username', 'role.name': 'Role','role_id':'ROLE_ID', 'balance': 'Balance_Left'}
    column_filters = ('username', 'role.name')


class RoleAdmin(AdminModelView):
    column_list = ('id', 'name',)
    column_labels = {'id':'id','name': 'Role Name'}
    column_filters = ('name',)

class PrintAdmin(AdminModelView):
    column_list = ('id','number_of_pages', 'printed_by_name' )
    column_labels = {'id': 'ID', 'number_of_pages': 'Pages', 'printed_by_name.username': 'Printed By'}
admin = Admin(app, name = 'Admin Panel', base_template='my_master.html', template_mode = 'bootstrap4')
# admin.add_view(ModelView(models.User, db.session))
# admin.add_view(ModelView(models.Role, db.session))

admin.add_view(UserAdmin(User, db.session))
admin.add_view(RoleAdmin(Role, db.session))
admin.add_view(PrintAdmin(Prints, db.session))


####################################################################################################
# Printer Print and upload page
#####################################################################################################

def get_number_of_pages(file_path):
    # try:
    with open(file_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        number_of_pages = len(pdf_reader.pages)
    return (number_of_pages)
    # except Exception as e:
    #     print(f"Error: {e}")
    #     return None




@app.route("/print")
@login_required
def print():
    return render_template("print.html")

    
@app.route("/upload", methods=["POST"])
def upload():
    if 'file' not in request.files:
        return "No file part"

    file = request.files['file']
    if file.filename == '':
        return "No selected file"

    start_page = request.form.get("start_page", type=int)
    end_page = request.form.get("end_page", type=int)
    copies = request.form.get("copies", type=int)
    if copies is None:
        copies = 1
    copies = request.form.get("copies", type=int)
    double_sided = request.form.get("double_sided", type=int)
    user_name = current_user.username

    if file:
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        file.save(temp_file.name)
# checking page number
        number_of_pages = get_number_of_pages(temp_file.name)
        temp_file.close()


        #TODO add start page and end page validation
        
        if start_page is None or end_page is None:
            options = {
                'copies': f"{copies}",
                'sides': 'two-sided-long-edge' if double_sided else 'one-sided'
            }
        else:
            options = {
                'page-ranges': f"{start_page}-{end_page}",
                'copies': f"{copies}",
                'sides': 'two-sided-long-edge' if double_sided else 'one-sided'
            }
            number_of_pages = end_page-start_page

        printer_name = "TvK-Printer-AG-BW"  # Replace with your printer name
        
        
        if current_user.can_print(number_of_pages):
            # Printing the file
            # cups.setUser (user_name)
            # conn.printFile(printer_name, temp_file.name, temp_file.name, options) # add functionality to change Print Job to the AG member responsible
            current_user.post_printing(number_of_pages)
            print= Prints()
            print.number_of_pages = number_of_pages
            print.printed_by_id = current_user.id
            db.session.add(print)
            db.session.commit()

        else:
            return('low balance')

        os.remove(temp_file.name)

        return render_template("upload.html")
    
@app.route('/cups_server')
def cups_server():
    # Redirect to an external website
    cups_server_url = 'http://[2a00:8a60:e004:1339:7a0a:3bc6:b904:af01]:631/printers/TvK-Printer-AG-BW'
    return redirect(cups_server_url)

