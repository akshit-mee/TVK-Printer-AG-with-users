from flask import render_template, flash, redirect, url_for, request, abort
from app import app, db
from app.forms import LoginForm, RegistrationForm, ChangePasswordForm, AddUserForm, AddBalanceForm, BanUserForm
from flask_login import current_user, login_user, logout_user, login_required
import sqlalchemy as sa
from app.models import User, Role, Prints, BalanceTransaction
from urllib.parse import urlsplit
# import cups
import tempfile
import os
from flask_admin.contrib.sqla import ModelView
from flask_admin import BaseView, Admin
from flask_security import Security, SQLAlchemyUserDatastore
import uuid
import PyPDF2
from datetime import datetime, timezone
from config import user_default


@app.route('/')
@app.route('/index')
@login_required
def index():
    if current_user.weekly_print_number == None:
        current_user.weekly_print_number = 0

    sum_pages = current_user.sum_pages_last_week(current_user.id)
    current_user.weekly_print_number = sum_pages
    total_pages = db.session.query(db.func.sum(Prints.number_of_pages)).scalar()
    if current_user.banned == True:
        flash('You have been banned from printing. Please contact the Printer AG for more information')
    if current_user.registered == False:
        flash('Please register your account with the Printer AG')
    return render_template('index.html', total_pages=total_pages)

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
        user.weekly_limit = user_default.weekly_limit
        user.balance = user_default.balance
        user.pages_printed = user_default.pages_printed
        user.weekly_print_number = user_default.weekly_print_number
        user.room_number = form.room_number.data
        user.role_id= user_default.role_id
        user.banned = user_default.banned
        user.registered= user_default.registered
        user.fs_uniquifier = uuid.uuid4().hex
        db.session.add(user)
        db.session.commit()
        flash('Registatration Complete!!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

###################################################################################################
# PrinterAG role: add user, add balance, ban user
###################################################################################################

@app.route('/add_user', methods=['GET', 'POST'])
@login_required
def add_user():
    if not(current_user.role.name == 'Admin' or current_user.role.name == 'Printer_AG'):
        abort(403)
    form = AddUserForm()
    if form.validate_on_submit():
        user = User(username=form.username.data)
        user.set_password(form.password.data)
        user.balance = form.balance.data
        user.weekly_limit = 10
        user.pages_printed = 0 
        user.weekly_print_number = 0
        user.room_number = User(room_number=form.room_number.data)
        user.role_id=1
        user.banned = False
        user.registered = True
        user.fs_uniquifier = uuid.uuid4().hex
        log = BalanceTransaction(user_id=user.id, amount=form.balance.data, description='Initial Balance During Registration')
        db.session.add(log)
        db.session.add(user)
        db.session.commit()
        flash('User Added Successfully')
        return redirect(url_for('add_user'))
    return render_template('add_user.html', title='Add User', form=form)

@app.route('/add_balance', methods=['GET', 'POST'])
@login_required
def add_balance():
    if not(current_user.role.name == 'Admin' or current_user.role.name == 'Printer_AG'):
        abort(403)
    form = AddBalanceForm()
    if form.validate_on_submit():
        user = db.session.scalar(sa.select(User).where(User.username == form.username.data))
        if user is None:
            flash('User Not Found')
            return redirect(url_for('add_balance'))
        user.add_balance(form.balance.data)
        user.registered = True
        log = BalanceTransaction(user_id=user.id, amount=form.balance.data, description='Added Balance')
        db.session.add(log)
        db.session.commit()
        flash('Balance Added Successfully. Total Balance: ' + str(round(user.balance, 3)) + '€')
        return redirect(url_for('add_balance'))
    return render_template('add_balance.html', title='Add Balance', form=form)

@app.route('/ban_user', methods=['GET', 'POST'])
@login_required
def ban_user():
    if not(current_user.role.name == 'Admin' or current_user.role.name == 'Printer_AG'):
        abort(403)
    form = BanUserForm()
    if form.validate_on_submit():
        user = db.session.scalar(sa.select(User).where(User.username == form.username.data))
        if user is None:
            flash('User Not Found')
            return redirect(url_for('ban_user'))
        if user.role.name == 'Admin':
            flash('Cannot Ban Admin')
            return redirect(url_for('ban_user'))
        if user.role.name == 'Printer_AG' and current_user.role.name != 'Admin':
            flash('Cannot Ban Printer AG if not a Admin')
            return redirect(url_for('ban_user'))
        if form.ban.data:
            user.banned = True
            db.session.commit()
            flash('User Banned Successfully')
            return redirect(url_for('ban_user'))
        elif form.unban.data:
            user.banned = False
            db.session.commit()
            flash('User Unbanned Successfully')
            return redirect(url_for('ban_user'))
    return render_template('ban_user.html', title='Ban User', form=form)

###################################################################################################
# User Profile and Change Password
###################################################################################################
@app.route('/edit_user', methods=['GET', 'POST'])
@login_required
def edit_user():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.check_password(form.current_password.data):
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash('Password Changed Successfully')
            return redirect(url_for('index'))
        else:
            flash('Incorrect Password')
            return redirect(url_for('edit_user'))
    return render_template('edit_user.html', title='Change Password', form=form)

@app.route('/balance_log')
@login_required
def balance_log():
    balance_log = db.session.query(BalanceTransaction).filter(BalanceTransaction.user_id == current_user.id).all()
    return render_template('balance_log.html', transactions=balance_log)



###################################################################################################
#Admin and Roles
###################################################################################################

class AdminPage(BaseView):
    def is_accessible(self):
        return current_user.is_authenticated and (current_user.role.name == 'Admin' or current_user.role.name == 'Printer_AG')

class AdminModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and (current_user.role.name == 'Admin' or current_user.role.name == 'Printer_AG')

    def _handle_view(self, name, **kwargs):
        if not self.is_accessible():
            return redirect(url_for('login', next=request.url))
        
    form_excluded_columns=('prints', 'balance_log', 'password_hash')


class UserAdmin(AdminModelView):
    column_list = ('username', 'role.name','role_id' ,'balance')
    column_labels = {'username': 'Username', 'role.name': 'Role','role_id':'ROLE_ID', 'balance': 'Balance_Left'}
    column_filters = ('username', 'role.name')


class RoleAdmin(AdminModelView):
    column_list = ('id', 'name',)
    column_labels = {'id':'id','name': 'Role Name'}
    column_filters = ('name',)

class PrintAdmin(AdminModelView):
    column_list = ('id','number_of_pages', 'printed_by_name.username', 'time_stamp')
    column_labels = {'id': 'ID', 'number_of_pages': 'Pages', 'printed_by_name.username': 'Printed By', 'time_stamp': 'Time'}

class BalanceTransactionAdmin(AdminModelView):
    column_list = ('id', 'user.username', 'amount', 'timestamp')
    column_labels = {'id': 'ID', 'user.username': 'User', 'amount': 'Amount', 'timestamp': 'Time'}

admin = Admin(app, name = 'Admin Panel', base_template='my_master.html', template_mode = 'bootstrap4')


# admin.add_view(ModelView(models.User, db.session))
# admin.add_view(ModelView(models.Role, db.session))

admin.add_view(UserAdmin(User, db.session))
admin.add_view(RoleAdmin(Role, db.session))
admin.add_view(PrintAdmin(Prints, db.session))
admin.add_view(BalanceTransactionAdmin(BalanceTransaction, db.session))


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
        number_of_pages = number_of_pages * copies


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
            log = BalanceTransaction(user_id=current_user.id, amount= -number_of_pages*user_default.print_cost, description='Printed Document of %d pages' % number_of_pages)
            db.session.add(log)
            print= Prints(number_of_pages=number_of_pages, printed_by_id=current_user.id, time_stamp=datetime.now(timezone.utc) )
            print.number_of_pages = number_of_pages
            print.printed_by_id = current_user.id
            db.session.add(print)
            db.session.commit()

        elif current_user.banned:
            return render_template("error.html", error_header="Banned", error_message="You have been banned from printing. Please contact the Printer AG for more information")
        elif current_user.balance_check(number_of_pages):
            return render_template("error.html", error_header="Weekly Limit Exceeded", error_message="You have exceeded your weekly limit of 10 pages")
        elif current_user.weekly_limit_check(number_of_pages):
            return render_template("error.html", error_header="Low Balance", error_message="You have insufficient balance to print this document. Kindly add balance to your account to continue printing")
        else:
            return render_template("error.html", error_header="Error", error_message="An error occured while printing. Please try again later or contack the Printer AG for assistance.")

        os.remove(temp_file.name)

        return render_template("upload.html")
    
@app.route('/cups_server')
def cups_server():
    # Redirect to an external website
    cups_server_url = 'http://[2a00:8a60:e004:1339:7a0a:3bc6:b904:af01]:631/printers/TvK-Printer-AG-BW'
    return redirect(cups_server_url)

