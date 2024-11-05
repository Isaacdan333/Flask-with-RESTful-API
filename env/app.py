from flask import Flask, render_template, request, jsonify, session, abort
from werkzeug.utils import secure_filename
from flask_mysqldb import MySQL
import MySQLdb.cursors
import jwt
import os

app = Flask(__name__)
app.secret_key = 'private_isaac'
app.config['SECRET_KEY'] = 'private_key'
app.config['extensions'] = ['.jpg','jpeg','.pdf','.png','.JPG','.JPEG','.PDF','.PNG']
app.config['UPLOADS'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024 # 2MB or 2000 kb

#SQL setup
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root' 
app.config['MYSQL_PASSWORD'] = 'Csdegree2002!' 
app.config['MYSQL_DB'] = 'temp_table'
mysql = MySQL(app)

@app.route('/')
def home():
    return render_template('index.html')

# JWT Authorization
@app.route('/login', methods=['GET', 'POST'])
def login():
    username = request.form.get('username')
    passw = request.form.get('password')
    if username == 'admin' and passw == 'password': # Checks admin login
        token = jwt.encode({'username': username}, app.config['SECRET_KEY'], algorithm='HS256')
        return f'token: {token}'
    elif username and passw and request.method == 'POST':
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM user_list WHERE username = % s', (username, ))
        account = cursor.fetchone()
        if account: # checks if account is already in database
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            return f'Welcome back {username}, Click here to see public information. <a href="/public">See public information</a>"'
        else: # adds account to the sql database
            cursor.execute('INSERT INTO user_list VALUES \
		    	(NULL, % s, % s)',(username, passw ))
            mysql.connection.commit()
            return f'Welcome {username}, Click here to see public information. <a href="/public">See public information</a>"'
    else:
        return app.aborter(400)

@app.route('/protected', methods=['GET'])
def protected():
    token = request.headers.get('Authorization')
    if not token:
        return app.aborter(403)
    try:
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        return jsonify({'Message': f'Hello and welcome, {data["username"]}'})
    except:
        return app.aborter(401)

# Non authorized public route
@app.route('/public', methods=['GET'])
def public_info():
    if 'id' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('DELETE FROM user_list WHERE id = % s',
                       (session['id'], ))
        cursor.close()
        session.pop('loggedin', None)
        session.pop('id', None)
        session.pop('username', None)
    image_files = [f for f in os.listdir(app.config['UPLOADS'])]
    image_paths = [os.path.join(app.config['UPLOADS'], image) for image in image_files]
    return render_template('images.html', images=zip(image_paths, image_files))

# File Upload
@app.route('/upload')
def upload():
    return '''
    <html>
    <form action="/sendFile" method="POST" enctype="multipart/form-data">
        <input type="file" name="file"/><br>
        <input type="submit"/>
    </form>
    </html>
    '''

@app.route('/sendFile',methods=['POST','GET'])
def sendFile():
    uploaded_file = request.files['file']
    if uploaded_file.filename != '':
        filename = secure_filename(uploaded_file.filename)
        if os.path.splitext(filename)[1] in app.config['extensions']:
            uploaded_file.save(os.path.join(app.config['UPLOADS'],filename))
            return f'{uploaded_file.filename} has been succesfully sent.'
    return 'File type is not supported. File Types supported are .jpg, .jpeg, .pdf, and .png'

# Error Handlers
@app.errorhandler(400)
def bad_request(e):
    return jsonify({"error": "Invalid information required."}), 400

@app.errorhandler(401)
def unauthroized(e):
    return jsonify({"error": "Unauthorized access"}), 401

@app.errorhandler(403)
def token_missing(e):
    return jsonify({"error": "token is missing."}), 403

@app.errorhandler(404)
def page_not_found(e):
    return jsonify({"error": "Page Not Found"}), 404

@app.errorhandler(413)
def file_too_large(error):
    return jsonify({"error": "File is too large. Maximum file size allowed is 2MB."}), 413

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Error from server"}), 500

if __name__ == '__main__':
    app.run(debug=True)
