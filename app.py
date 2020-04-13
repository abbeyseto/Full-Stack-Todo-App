"""
All the APIs for this todos application Currently we support the following 3 controllers:

1. **index** - The main view for Todos
2. **create_todo** - called to add a new todo
3. **delete_todo** - called to delete todo
4. **set_completed_todo** - called to set a todo as completed
"""
from functools import wraps
import json
from os import environ as env
from werkzeug.exceptions import HTTPException
from dotenv import load_dotenv, find_dotenv
from flask import Flask, jsonify, redirect, render_template, session, url_for, request, abort, _request_ctx_stack, session
from authlib.integrations.flask_client import OAuth
from six.moves.urllib.parse import urlencode
from six.moves.urllib.request import urlopen
from datetime import datetime
import sys
import pytest
import http.client
import requests
from jose import jwt
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS, cross_origin

AUTH0_DOMAIN = 'setoapps.auth0.com'
API_AUDIENCE = 'todo'
ALGORITHMS = ["RS256"]
list_location = 1

app = Flask(__name__)
app.secret_key = "iloveflask"
CORS(app)
# CORS(app, resources={r"*/api/*": {"origins":"*"}})
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://AshNelson:ologinahtti1@localhost:5432/todoapp'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
oauth = OAuth(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)


class Todo(db.Model):
    __tablename__ = 'todos'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(), nullable=False)
    completed = db.Column(db.Boolean, nullable=False, default=False)
    list_id = db.Column(db.Integer, db.ForeignKey(
        'todolists.id'), nullable=False)

    def __repr__(self):
        return f'<Todo {self.id} {self.description}>'


class TodoList(db.Model):
    __tablename__ = 'todolists'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    completed = db.Column(db.Boolean, nullable=False, default=False)

    def __repr__(self):
        return f'<TodoList {self.id} {self.name}>'


class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    auth_id = db.Column(db.String(), nullable=False)
    name = db.Column(db.String())
    first_name = db.Column(db.String())
    last_name = db.Column(db.String())
    email = db.Column(db.String(), nullable=False, unique=True)
    email_Verified = db.Column(db.Boolean, nullable=False, default=False)
    image = db.Column(db.String())
    created_at = db.Column(db.DateTime(), default=datetime.now())
    updated_at = db.Column(db.DateTime(), default=datetime.now())

    def __repr__(self):
        return f'<User ID: {self.id}, name: {self.first_name}>'


auth0 = oauth.register(
    'auth0',
    client_id='nO4zPv9ENUFZlmOf2jHuaNB8FwVIMqYh',
    client_secret='gLQUML4j199NYO0sDxE58Svp4-lvwoOrM9LKnrWva1Z0nCR0r7l-BgPsJI96hiuC',
    api_base_url='https://setoapps.auth0.com',
    access_token_url='https://setoapps.auth0.com/oauth/token',
    authorize_url='https://setoapps.auth0.com/authorize',
    client_kwargs={
        'scope': 'openid profile email',
    },
)


@app.after_request
def after_request(response):
    response.headers.add('Access-Control_Allow-Headers',
                         'Content-Type, Authorization')
    response.headers.add('Access-Control_Allow-Methods',
                         'GET, POST, PATCH, DELETE, OPTIONS')
    return response


@app.route('/')
# @requires_auth
@cross_origin()
def index():
    return redirect(url_for('get_list_todos', list_id=list_location))


# Here we're using the /callback route.
# @app.route('/callback')
def token_handling(token):
    # Handles response from token endpoint
    url = "https://setoapps.auth0.com/userinfo"
    headers = {"Authorization": "Bearer " + token + " "}
    response = requests.post(url, headers=headers)
    userinfo = response.json()
    print(userinfo)
    # Store the user information in flask session.
    session['jwt_payload'] = userinfo
    session['profile'] = {
        'auth_id': userinfo['sub'],
        'name': userinfo['name'],
        'first_name': userinfo['given_name'],
        'last_name': userinfo['family_name'],
        'picture': userinfo['picture'],
        'email': userinfo['email'],
        'updated_at': userinfo['updated_at']
    }
    session['SECRET_KEY'] = userinfo['sub']
    user = User.query.filter_by(email=session['profile']['email']).all()
    if not user:
        userProfile = session['profile']
        newUser = User(auth_id=userProfile['auth_id'],
                       name=userProfile['name'],
                       first_name=userProfile['first_name'],
                       last_name=userProfile['last_name'],
                       email=userProfile['email'],
                       image=userProfile['picture'],
                       updated_at=userProfile['updated_at']
                       )
        db.session.add(newUser)
        db.session.commit()
    print(userinfo, session)
    return redirect(url_for('get_list_todos', list_id=list_location))


@app.route('/login')
def login():
    return redirect("https://setoapps.auth0.com/authorize?response_type=code&client_id=nO4zPv9ENUFZlmOf2jHuaNB8FwVIMqYh&redirect_uri=https://127.0.0.1:5000/authenticate&scope=openid%20profile%20email&state=xyzABC123")


@app.route('/authenticate')
def authenticate():
    code = request.args.get('code')
    url = "https://setoapps.auth0.com/oauth/token"
    payload = "grant_type=authorization_code&client_id=nO4zPv9ENUFZlmOf2jHuaNB8FwVIMqYh&client_secret=gLQUML4j199NYO0sDxE58Svp4-lvwoOrM9LKnrWva1Z0nCR0r7l-BgPsJI96hiuC&code=" + \
        code+"&redirect_uri=https://127.0.0.1:5000/lists/1&audience=todo"
    headers = {"Content-type": "application/x-www-form-urlencoded"}
    response = requests.post(url, data=payload, headers=headers)
    data = response.json()
    print(data)
    print('TOKEN HERE', data.get('access_token'))
    token = data.get('access_token')
    token_handling(token)
    return redirect(url_for('get_list_todos', list_id=list_location))


@app.route('/welcome')
def home():
    return render_template('home.html')


@app.route('/logout')
def logout():
    # Clear session stored data
    session.clear()
    # Redirect user to logout endpoint
    params = {'returnTo': url_for(
        'home', _external=True), 'client_id': 'nO4zPv9ENUFZlmOf2jHuaNB8FwVIMqYh'}
    return redirect('https://' + AUTH0_DOMAIN + '/v2/logout?' + urlencode(params))


@app.route('/todos/<int:todo_id>', methods=['DELETE'])
def delete_todo(todo_id):
    try:
        Todo.query.filter_by(id=todo_id).delete()
        db.session.commit()
    except:
        db.session.rollback()
    finally:
        db.session.close()
    return jsonify({'success': True})


@app.route('/lists/<int:list_id>', methods=['DELETE'])
def delete_list(list_id):
    global list_location
    list_location = 1
    try:
        Todo.query.filter_by(list_id=list_id).delete()
        TodoList.query.filter_by(id=list_id).delete()
        db.session.commit()
    except:
        db.session.rollback()
    finally:
        db.session.close()
    return redirect(url_for('get_list_todos', list_id=list_location))
# note: more conventionally, we would write a
# POST endpoint to /todos for the create endpoint:
# @app.route('/todos', method=['POST'])
@app.route('/todos/create', methods=['POST'])
def create_todo():
    error = False
    body = {}
    try:
        description = request.get_json()['description']
        list_id = request.get_json()['list_id']
        todo = Todo(description=description, list_id=list_id, completed=False)
        db.session.add(todo)
        db.session.commit()
        body['id'] = todo.id
        body['completed'] = todo.completed
        body['description'] = todo.description
        body['list_id'] = todo.list_id
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
    if error:
        abort(400)
    else:
        return jsonify(body)


@app.route('/lists/create', methods=['POST'])
def create_list():
    error = False
    body = {}
    try:
        name = request.get_json()['name']
        user_id = request.get_json()['user_id']
        todolist = TodoList(name=name, user_id=user_id, completed=False)
        db.session.add(todolist)
        db.session.commit()
        global list_location
        list_location = todolist.id
        body['id'] = todolist.id
        body['completed'] = todolist.completed
        body['name'] = todolist.name
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
    if error:
        abort(400)
    else:
        return jsonify(body)


@app.route('/todos/<int:todo_id>/set-completed', methods=['POST'])
def set_completed_todo(todo_id):
    try:
        completed = request.get_json()['completed']
        print('completed', completed)
        todo = Todo.query.get(todo_id)
        todo.completed = completed
        db.session.commit()
    except:
        db.session.rollback()
    finally:
        db.session.close()
    return render_template('index.html')


@app.route('/lists/<int:list_id>/set-completed', methods=['POST'])
def set_completed_list(list_id):
    try:
        completed = request.get_json()['completed']
        print('completed', completed)
        todolist = TodoList.query.get(list_id)
        print(todolist)
        todos = Todo.query.filter_by(list_id=list_id).all()
        todolist.completed = completed
        for todo in todos:
            todo.completed = completed
            print(todos)
        db.session.commit()
    except:
        db.session.rollback()
    finally:
        db.session.close()
    return render_template('index.html')


@app.route('/lists/<int:list_id>')
# @requires_auth
def get_list_todos(list_id):
    if not session:
        return redirect(url_for('home'))
    global list_location
    list_location = list_id
    user=User.query.filter_by(email=session['profile']['email']).all(),
    list_location = list_id
    currentUserId = user[0][0].id
    print(list_location)
    print(session["profile"])
    return render_template('index.html',
                           user=User.query.filter_by(
                               email=session['profile']['email']).all(),
                           lists=TodoList.query.filter_by(user_id = currentUserId).order_by('id').all(),
                           active_list=TodoList.query.get(list_location),
                           userinfo=session['profile'],
                           #   userinfo_pretty=json.dumps(
                           #   session['jwt_payload'], indent=4),
                           todos=Todo.query.filter_by(list_id=list_id).order_by('id').all())


# Error handler
class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


@app.errorhandler(AuthError)
def handle_auth_error(ex):
    response = jsonify(ex.error)
    response.status_code = ex.status_code
    return response


@app.route("/api/public")
@cross_origin(headers=["Content-Type", "Authorization"])
def public():
    response = "Hello from a public endpoint! You don't need to be authenticated to see this."
    return jsonify(message=response)


# This needs authentication
@app.route("/api/private")
@cross_origin(headers=["Content-Type", "Authorization"])
def private():
    response = "Hello from a private endpoint! You need to be authenticated to see this."
    return jsonify(message=response)


def f():
    raise SystemExit(1)


def test_mytest():
    with pytest.raises(SystemExit):
        f()


if __name__ == '__main__':
    print('RUNNING THE SERVER...')
    app.run(ssl_context=('server_new.crt', 'server_new.key'))
