from flask import (Flask, render_template, make_response, url_for, request,
                   redirect, flash, session, send_from_directory, jsonify)
app = Flask(__name__)

import secrets
import cs304dbi as dbi

# we need a secret_key to use flash() and sessions
app.secret_key = secrets.token_hex()

@app.route('/')
def dashboard():
    return render_template('customer-dash.html', page_title='Dashboard')

@app.route('/search/')
def search():
    bname = request.args['search-bname']
    with dbi.connect() as conn:
        with dbi.dict_cursor(conn) as curs:
            curs.execute('use szab304_db')
            curs.execute('''select business_name from business where business_name like %s''', ('%' + bname + '%'))
            businesses = curs.fetchall()
            #If there is no business with that in it's name, then flash a message and redirect user to their dashboard.
            if not businesses:
                flash(f'There is no business with {bname} in the name')
                return render_template('customer-dash.html', page_title='Dashboard')
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
