"""
All the APIs for this todos application Currently we support the following 3 controllers:

1. **index** - The main view for Todos
2. **create_todo** - called to add a new todo
3. **delete_todo** - called to delete todo
4. **set_completed_todo** - called to set a todo as completed
"""

from flask import Flask, jsonify, request, render_template, redirect, url_for, abort
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import sys
from flask_migrate import Migrate
import pytest

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://AshNelson:ologinahtti1@localhost:5432/todoapp'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

migrate = Migrate(app, db)

list_location = 1


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
    # todos = db.relationship('Todo', backref='list', primaryjoin="Todo.id==TodoList.id")
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    completed = db.Column(db.Boolean, nullable=False, default=False)

    def __repr__(self):
        return f'<TodoList {self.id} {self.name}>'


class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(), nullable=False)
    last_name = db.Column(db.String(), nullable=False)
    email = db.Column(db.String(), nullable=False)
    image = db.Column(db.LargeBinary)
    password = db.Column(db.String(), nullable=False)
    created_at = db.Column(db.DateTime(), nullable=False)
    # user_list = db.relationship('TodoList', backref='userlist', primaryjoin="User.id==TodoList.id")

    def __repr__(self):
        return f'<Person ID: {self.id}, name: {self.first_name}>'


@app.route('/todos/<todo_id>', methods=['DELETE'])
def delete_todo(todo_id):
    try:
        Todo.query.filter_by(id=todo_id).delete()
        db.session.commit()
    except:
        db.session.rollback()
    finally:
        db.session.close()
    return jsonify({'success': True})


@app.route('/lists/<list_id>', methods=['DELETE'])
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


@app.route('/todos/<todo_id>/set-completed', methods=['POST'])
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

@app.route('/lists/<list_id>/set-completed', methods=['POST'])
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

@app.route('/lists/<list_id>')
def get_list_todos(list_id):
    global list_location
    list_location = list_id
    print(list_location)
    return render_template('index.html',
                           user=User.query.filter_by(id=1).all(),
                           lists=TodoList.query.order_by('id').all(),
                           active_list=TodoList.query.get(list_location),
                           todos=Todo.query.filter_by(list_id=list_id).order_by('id').all())


@app.route('/')
def index():
    return redirect(url_for('get_list_todos', list_id=list_location))


def f():
    raise SystemExit(1)


def test_mytest():
    with pytest.raises(SystemExit):
        f()


if __name__ == '__main__':
    app.run()
