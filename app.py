"""
Author: Sophia Zhang
"""
from flask import (Flask, render_template, make_response, url_for, request,
                   redirect, flash, session, send_from_directory, jsonify)
from werkzeug.utils import secure_filename
app = Flask(__name__)

import os
import secrets
import pymysql
import cs304dbi as dbi
import posting_db
import auth_db
import customer_db

# we need a secret_key to use flash() and sessions
app.secret_key = secrets.token_hex()

# configure DBI
print(dbi.conf('szab304_db'))

# This gets us better error messages for certain common request errors
app.config['TRAP_BAD_REQUEST_ERRORS'] = True

# Uploaded images go in this folder; reject files over 2 MB
app.config['UPLOADS'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024


@app.route('/')
def index():
    return render_template('main.html', page_title='Main Page')


@app.route('/about/')
def about():
    return render_template('about.html', page_title='About Us')


@app.route('/join/', methods=['GET', 'POST'])
def join():
    """Create a business or customer account and log it in."""
    if request.method == 'GET':
        return render_template('join.html', page_title='Join')
    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip() or None
    passwd1 = request.form.get('password1', '')
    passwd2 = request.form.get('password2', '')
    account_type = request.form.get('account_type')
    business_name = request.form.get('business_name', '').strip() or None
    if username == '':
        flash('username is required')
        return render_template('join.html', page_title='Join')
    if passwd1 == '':
        flash('password is required')
        return render_template('join.html', page_title='Join')
    if passwd1 != passwd2:
        flash('passwords do not match')
        return render_template('join.html', page_title='Join')
    if account_type not in ('business', 'customer'):
        flash('choose business or customer')
        return render_template('join.html', page_title='Join')
    if account_type == 'business' and business_name is None:
        flash('businesses need a business name')
        return render_template('join.html', page_title='Join')
    hashed = auth_db.hash_password(passwd1)
    with dbi.connect() as conn:
        try:
            account_id = auth_db.create_account(conn, username, email, hashed,
                                                account_type, business_name)
        except pymysql.IntegrityError:
            conn.rollback()   # end transaction
            flash('That username is taken')
            return render_template('join.html', page_title='Join')
    session['account_id'] = account_id
    session['username'] = username
    session['account_type'] = account_type
    session['logged_in'] = True
    flash('Welcome, {}!'.format(username))
    if account_type == 'business':
        return redirect(url_for('new_post'))
    return redirect(url_for('index'))


@app.route('/login/', methods=['GET', 'POST'])
def login():
    """Check username and password, remembers the account in the
    session"""
    if request.method == 'GET':
        return render_template('login.html', page_title='Log In')
    username = request.form.get('username', '').strip()
    passwd = request.form.get('password', '')
    with dbi.connect() as conn:
        row = auth_db.get_login_info(conn, username)
        if row is None:
            # Same message as a wrong password
            flash('login incorrect. Try again or join')
            return render_template('login.html', page_title='Log In')
        okay, new_hash = auth_db.verify_password(passwd, row['password_hash'])
        if not okay:
            flash('login incorrect. Try again or join')
            return render_template('login.html', page_title='Log In')
        if new_hash is not None:
            auth_db.update_hash(conn, row['account_id'], new_hash)
    session['account_id'] = row['account_id']
    session['username'] = username
    session['account_type'] = row['account_type']
    session['logged_in'] = True
    flash('successfully logged in as ' + username)
    if row['account_type'] == 'business':
        return redirect(url_for('new_post'))
    return redirect(url_for('index'))


# log in as any account without a password for testing
# Delete this route later 
@app.route('/test-login/<int:account_id>')
def test_login(account_id):
    with dbi.connect() as conn:
        row = auth_db.get_account(conn, account_id)
    if row is None:
        flash('No account with id {}'.format(account_id))
        return redirect(url_for('index'))
    session['account_id'] = row['account_id']
    session['username'] = row['username']
    session['account_type'] = row['account_type']
    session['logged_in'] = True
    flash('TEST LOGIN as {} ({})'.format(row['username'], row['account_type']))
    if row['account_type'] == 'business':
        return redirect(url_for('new_post'))
    return redirect(url_for('index'))


@app.route('/logout/', methods=['POST'])
def logout():
    if 'account_id' in session:
        session.clear()
        flash('You are logged out')
    else:
        flash('you are not logged in. Please log in or join')
    return redirect(url_for('index'))


@app.route('/post/new/', methods=['GET', 'POST'])
def new_post():
    """Business accounts upload an item (image + price) or a service
    (image + optional price + hours)"""
    account_id = session.get('account_id')
    if account_id is None:
        flash('Please log in first')
        return redirect(url_for('login'))
    with dbi.connect() as conn:
        business = posting_db.is_business(conn, account_id)
    if not business:
        flash('Only business accounts can create postings')
        return redirect(url_for('index'))
    if request.method == 'GET':
        return render_template('new_post.html', page_title='New Posting')
    # POST: read and check the form
    post_type = request.form.get('post_type')
    title = request.form.get('title', '').strip()
    price = request.form.get('price', '').strip() or None
    description = request.form.get('description', '').strip() or None
    f = request.files.get('pic')
    if post_type not in ('item', 'scheduling'):
        flash('Choose item or scheduling')
        return render_template('new_post.html', page_title='New Posting')
    if not title:
        flash('Please give your posting a title')
        return render_template('new_post.html', page_title='New Posting')
    if post_type == 'item' and price is None:
        flash('Items need a price')
        return render_template('new_post.html', page_title='New Posting')
    # The image is optional; only check it if one was chosen
    has_image = f is not None and f.filename != ''
    if has_image:
        ext = f.filename.rsplit('.', 1)[-1].lower()
        if ext not in ('jpg', 'jpeg', 'png', 'gif'):
            flash('Image must be a jpg, png or gif')
            return render_template('new_post.html', page_title='New Posting')
    # datetime-local inputs send '2026-11-23T09:00'
    start_time = request.form.get('start_time', '').replace('T', ' ')
    end_time = request.form.get('end_time', '').replace('T', ' ')
    if post_type == 'scheduling':
        if not (start_time and end_time):
            flash('Services need a start and end time')
            return render_template('new_post.html', page_title='New Posting')
        if start_time >= end_time:
            flash('End time must be after start time')
            return render_template('new_post.html', page_title='New Posting')
    with dbi.connect() as conn:
        # Insert the row first so we can name the file after its post_id
        post_id = posting_db.insert_posting(conn, account_id, post_type,
                                            title, price, description)
        if has_image:
            filename = secure_filename('{}.{}'.format(post_id, ext))
            pathname = os.path.join(app.config['UPLOADS'], filename)
            f.save(pathname)
            os.chmod(pathname, 0o444)
            posting_db.set_image(conn, post_id, filename)
        if post_type == 'scheduling':
            posting_db.insert_time_slot(conn, post_id, start_time, end_time)
        conn.commit()

    flash('Posting created')
    return redirect(url_for('show_post', post_id=post_id))


@app.route('/my-postings/')
def my_postings():
    """List every posting the logged-in business has made"""
    account_id = session.get('account_id')
    if account_id is None:
        flash('Please log in first')
        return redirect(url_for('login'))
    with dbi.connect() as conn:
        if not posting_db.is_business(conn, account_id):
            flash('Only business accounts have postings')
            return redirect(url_for('index'))
        posts = posting_db.get_postings_by_account(conn, account_id)
    return render_template('my_postings.html', page_title='My Postings',
                           posts=posts)


@app.route('/customer/<int:customer_id>')
def customer_profile(customer_id):
    """What a business sees about a customer: name, email, contact info,
    and any slots the customer has booked with this business."""
    account_id = session.get('account_id')
    if account_id is None:
        flash('Please log in first')
        return redirect(url_for('login'))
    with dbi.connect() as conn:
        if not posting_db.is_business(conn, account_id):
            flash('Only business accounts can view customer profiles')
            return redirect(url_for('index'))
        customer = customer_db.get_customer(conn, customer_id)
        bookings = customer_db.get_bookings_with_business(conn, customer_id,
                                                          account_id)
        inquiries = customer_db.get_inquiries_with_business(conn, customer_id,
                                                            account_id)
    # Only show people who are this business's customers: they booked a slot or sent an inquiry. Same message whether or not the customer exists.
    if customer is None or not (bookings or inquiries):
        flash('You can only view your own customers')
        return redirect(url_for('index'))
    return render_template('customer.html', page_title=customer['username'],
                           customer=customer, bookings=bookings,
                           inquiries=inquiries)


@app.route('/post/<int:post_id>')
def show_post(post_id):
    """Show one posting with its image, price and hours."""
    with dbi.connect() as conn:
        post = posting_db.get_posting(conn, post_id)
        if post is None:
            flash('No such posting')
            return redirect(url_for('index'))
        slots = posting_db.get_time_slots(conn, post_id)
    return render_template('post.html', page_title=post['title'],
                           post=post, slots=slots)


@app.route('/post-image/<int:post_id>')
def post_image(post_id):
    """Send the image file for a posting"""
    with dbi.connect() as conn:
        post = posting_db.get_posting(conn, post_id)
    if post is None or post['image_link'] is None:
        flash('No image for that posting')
        return redirect(url_for('index'))
    return send_from_directory(app.config['UPLOADS'], post['image_link'])

# @app.route('/')
# def dashboard():
#     return render_template('customer-dash.html', page_title='Dashboard')

@app.route('/search/')
def search():
    bname = request.args.get('search-bname')

    # If the user has not submitted a search, show the search form
    if not bname:
        return render_template('search.html', page_title="Search")   

    with dbi.connect() as conn:     
        with dbi.dict_cursor(conn) as curs:
            curs.execute('use szab304_db')
            curs.execute('''select business_name from business where business_name like %s''', ('%' + bname + '%'))
            businesses = curs.fetchall()
            #If there is no business with that in it's name, then flash a message and redirect user to their dashboard.
            if not businesses:
                flash(f'There is no business with {bname} in the name')
                return render_template('search.html', page_title='Search')
            return render_template('search.html', page_title = "Search", businesses=businesses)

@app.route('/getProfile/<business_name>')
def getProfile(business_name):
    with dbi.connect() as conn:
        with dbi.dict_cursor(conn) as curs:
            curs.execute('use szab304_db')
            curs.execute('''select contact_info, description from business where business_name = %s''', business_name)
            business = curs.fetchone()
            try:
                contact_info = business['contact_info']
            except:
                contact_info = "None"
            try:
                description = business['description']
            except:
                description = "None"
            return render_template('business-profile.html', page_title=business_name, business_name=business_name, contact_info=contact_info, description=description)

if __name__ == '__main__':
    import sys, os
    if len(sys.argv) > 1:
        # arg, if any, is the desired port number
        port = int(sys.argv[1])
        assert(port>1024)
    else:
        port = os.getuid()
    app.debug = True
    app.run('0.0.0.0',port)
