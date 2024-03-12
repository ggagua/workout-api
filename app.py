from flask import Flask, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
import sqlite3
import uuid
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from functools import wraps
import datetime
import json

app = Flask(__name__)

app.config['SECRET_KEY'] = 'secretkeyvery'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///exercises.db'
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(50), unique=True)
    name = db.Column(db.String(50))
    password = db.Column(db.String(90))


class TokenBlacklist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    token_id = db.Column(db.String(255), unique=True, nullable=False)
    user_id = db.Column(db.String(50), nullable=False)
    blacklisted_at = db.Column(db.DateTime, default=datetime.datetime.utcnow(), nullable=False)


class Exercises(db.Model):
    exercise_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    instructions = db.Column(db.Text)
    target_muscles = db.Column(db.String(255))
    difficulty = db.Column(db.Integer)

    def serialize(self):
        return {
            'exercise_id': self.exercise_id,
            'name': self.name,
            'description': self.description,
            'instructions': self.instructions,
            'target_muscles': self.target_muscles,
            'difficulty': self.difficulty
        }


class WorkoutPlanFinal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    frequency = db.Column(db.String(50))
    goal = db.Column(db.String(255))
    session_duration = db.Column(db.Integer)
    selected_exercises = db.Column(db.String(5000))


class FitnessGoalsFinal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), nullable=False)
    current_weight = db.Column(db.Float, nullable=False)
    weight_goal = db.Column(db.Float, nullable=False)
    exercise_goals = db.relationship('ExerciseGoal', backref='fitness_goal', cascade='all, delete-orphan')

    def serialize(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'current_weight': self.current_weight,
            'weight_goal': self.weight_goal,
            'exercise_goals': [exercise_goal.serialize() for exercise_goal in self.exercise_goals]
        }


class ExerciseGoal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fitness_goal_id = db.Column(db.Integer, db.ForeignKey('fitness_goals_final.id'), nullable=False)
    exercise_name = db.Column(db.String(255), nullable=False)
    current_weight = db.Column(db.Float)
    current_reps = db.Column(db.Integer)
    target_weight = db.Column(db.Float)
    target_reps = db.Column(db.Integer)

    def serialize(self):
        return {
            'exercise_name': self.exercise_name,
            'current_weight': self.current_weight,
            'current_reps': self.current_reps,
            'target_weight': self.target_weight,
            'target_reps': self.target_reps
        }


with app.app_context():
    db.create_all()


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']

        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        if TokenBlacklist.query.filter_by(token_id=token).first():
            return jsonify({'message': 'Token is blacklisted!'}), 401

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = User.query.filter_by(public_id=data['public_id']).first()
        except:
            return jsonify({'message': 'Token is invalid!'}), 401

        return f(current_user, *args, **kwargs)

    return decorated


@app.route('/')
def hello():
    return jsonify('Welcome, this is the best place to arrange your workouts!')


@app.route('/logout', methods=['POST'])
@token_required
def immediate_logout(current_user):
    token_blacklist = TokenBlacklist(
        token_id=request.headers['x-access-token'],
        user_id=current_user.public_id,
        blacklisted_at=datetime.datetime.utcnow()
    )
    db.session.add(token_blacklist)
    db.session.commit()

    return jsonify({'message': 'Logout successful'})


@app.route('/exercises', methods=['GET'])
@token_required
def get_exercises(current_user):
    exercises = Exercises.query.all()
    serialized_exercises = [exercise.serialize() for exercise in exercises]
    return jsonify({'exercises': serialized_exercises})


@app.route('/exercises/<exercise_id>', methods=['GET'])
@token_required
def get_one_exercise(current_user, exercise_id):
    exercise = Exercises.query.filter_by(exercise_id=exercise_id).first()
    if exercise:
        serialized_exercise = exercise.serialize()
        return jsonify({'exercise': serialized_exercise})
    else:
        return jsonify({'message': 'Exercise not found'}), 404


@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    hashed_password = generate_password_hash(data['password'], method='pbkdf2:sha256')

    new_user = User(public_id=str(uuid.uuid4()), name=data['name'], password=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'New user created!'})


@app.route('/login')
def login():
    auth = request.authorization

    if not auth or not auth.username or not auth.password:
        return make_response('Could not verify', 401, {'WWW-Authenticate': 'Basic realm="Login required!"'})

    user = User.query.filter_by(name=auth.username).first()

    if not user:
        return make_response('Could not verify', 401, {'WWW-Authenticate': 'Basic realm="Login required!"'})

    if check_password_hash(user.password, auth.password):
        token = jwt.encode(
            {'public_id': user.public_id, 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=45)},
            app.config['SECRET_KEY'], algorithm="HS256")

        return jsonify({'token': token})

    return make_response('Could not verify', 401, {'WWW-Authenticate': 'Basic realm="Login required!"'})


@app.route('/workout-plans', methods=['POST'])
@token_required
def create_workout_plan(current_user):
    data = request.get_json()

    if 'workout_name' not in data or 'frequency' not in data or 'goal' not in data or 'session_duration' not in data \
            or 'selected_exercises' not in data:
        return jsonify({'message': 'Invalid data provided'}), 400

    workout_name = data['workout_name']
    frequency = data['frequency']
    goal = data['goal']
    session_duration = data['session_duration']
    selected_exercises = data['selected_exercises']

    new_selected_exercises = []

    for exercise_data in selected_exercises:
        name = exercise_data['name'].strip()
        exercise = Exercises.query.filter(Exercises.name.ilike(name)).first()
        if exercise:
            exercise_info = {
                'name': exercise.name,
                'difficulty': exercise.difficulty,
                'target_muscles': exercise.target_muscles,
                'instructions': exercise.instructions,
                'sets': exercise_data.get('sets'),
                'reps': exercise_data.get('reps'),
                'duration': exercise_data.get('duration'),
                'distance': exercise_data.get('distance')
            }
            new_selected_exercises.append(exercise_info)
        else:
            return jsonify({'message': 'Exercise is not available in our database'}), 400

    new_workout_plan = WorkoutPlanFinal(
        user_id=current_user.public_id,
        name=workout_name,
        frequency=frequency,
        goal=goal,
        session_duration=session_duration,
        selected_exercises=json.dumps(new_selected_exercises)
    )

    db.session.add(new_workout_plan)
    db.session.commit()

    return jsonify({'message': 'Workout plan created successfully'}), 201


@app.route('/workout-plans', methods=['GET'])
@token_required
def get_workout_plans(current_user):
    workout_plans = WorkoutPlanFinal.query.filter_by(user_id=current_user.public_id).all()
    if workout_plans:
        response_data = []

        for plan in workout_plans:
            plan_data = {
                'id': plan.id,
                'name': plan.name,
                'frequency': plan.frequency,
                'goal': plan.goal,
                'session_duration': plan.session_duration,
                'selected_exercises': []
            }

            exercises_list = json.loads(plan.selected_exercises)

            for exercise_data in exercises_list:
                exercise_info = {
                    'name': exercise_data.get('name'),
                    'sets': exercise_data.get('sets'),
                    'reps': exercise_data.get('reps'),
                    'duration': exercise_data.get('duration'),
                    'distance': exercise_data.get('distance'),
                    'difficulty': exercise_data.get('difficulty'),
                    'target_muscles': exercise_data.get('target_muscles'),
                    'instructions': exercise_data.get('instructions')
                }
                plan_data['selected_exercises'].append(exercise_info)

            response_data.append(plan_data)

        return jsonify({'workout_plans': response_data})
    return jsonify({'message': 'Workout plans not found'}), 404


@app.route('/workout-plans/<int:workout_id>', methods=['GET'])
@token_required
def get_workout_plan(current_user, workout_id):
    workout_plan = WorkoutPlanFinal.query.filter_by(id=workout_id, user_id=current_user.public_id).first()

    if workout_plan:
        plan_data = {
            'id': workout_plan.id,
            'name': workout_plan.name,
            'frequency': workout_plan.frequency,
            'goal': workout_plan.goal,
            'session_duration': workout_plan.session_duration,
            'selected_exercises': json.loads(workout_plan.selected_exercises)
        }

        return jsonify({'workout_plan': plan_data}), 200
    else:
        return jsonify({'message': 'Workout plan not found'}), 404


@app.route('/workout-plans/<int:workout_plan_id>', methods=['DELETE'])
@token_required
def delete_workout_plan(current_user, workout_plan_id):
    workout_plan = WorkoutPlanFinal.query.filter_by(id=workout_plan_id, user_id=current_user.public_id).first()

    if workout_plan:
        db.session.delete(workout_plan)
        db.session.commit()
        return jsonify({'message': 'Workout plan deleted successfully'}), 200
    else:
        return jsonify({'message': 'Workout plan not found'}), 404


@app.route('/fitness-goals', methods=['POST'])
@token_required
def create_fitness_goal(current_user):
    data = request.get_json()
    if 'current_weight' not in data or 'goal_weight' not in data or 'exercises_goals' not in data:
        return jsonify({'message': 'Missing required goal information'}), 400

    exercise_goals = []
    for exercise_data in data['exercises_goals']:
        if 'name' not in exercise_data or ('weight' not in exercise_data and 'reps' not in exercise_data) or (
                'weight_goal' not in exercise_data and 'reps_goal' not in exercise_data):
            return jsonify({'message': 'Missing required exercise goal information'}), 400
        name = exercise_data['name'].strip()
        print(name)
        exercise = Exercises.query.filter(Exercises.name.ilike(name)).first()
        print(exercise)
        if exercise:
            exercise_data['name'] = exercise.name
            print(exercise_data['name'])
        else:
            return jsonify({'message': 'Exercise is not available in our database'}), 400

        exercise_goal = ExerciseGoal(
            exercise_name=exercise_data.get('name'),
            current_weight=exercise_data.get('weight'),
            current_reps=exercise_data.get('reps'),
            target_weight=exercise_data.get('weight_goal'),
            target_reps=exercise_data.get('reps_goal')
        )
        exercise_goals.append(exercise_goal)

    goal = FitnessGoalsFinal(
        user_id=current_user.public_id,
        current_weight=data['current_weight'],
        weight_goal=data['goal_weight'],
        exercise_goals=exercise_goals
    )
    db.session.add(goal)
    db.session.commit()

    return jsonify({'message': 'Fitness goal created successfully!'})


@app.route('/fitness-goals', methods=['GET'])
@token_required
def get_fitness_goals(current_user):
    goals = FitnessGoalsFinal.query.filter_by(user_id=current_user.public_id).all()
    if goals:
        return jsonify([goal.serialize() for goal in goals])
    return jsonify({'message': 'Fitness goals not found'}), 404


@app.route('/fitness-goals/<int:goal_id>', methods=['GET'])
@token_required
def get_fitness_goal_by_id(current_user, goal_id):
    goal = FitnessGoalsFinal.query.filter_by(id=goal_id, user_id=current_user.public_id).first()

    if goal:
        goal_data = {
            'current_weight': goal.current_weight,
            'weight_goal': goal.weight_goal,
            'exercise_goals': [exercise_goal.serialize() for exercise_goal in goal.exercise_goals]
        }

        return jsonify({'fitness_goal': goal_data}), 200
    else:
        return jsonify({'message': 'Fitness goal not found'}), 404


@app.route('/fitness-goals/<int:goal_id>', methods=['DELETE'])
@token_required
def delete_fitness_goal(current_user, goal_id):
    goal = FitnessGoalsFinal.query.filter_by(id=goal_id, user_id=current_user.public_id).first()

    if goal:
        db.session.delete(goal)
        db.session.commit()
        return jsonify({'message': 'Fitness goal deleted successfully'}), 200
    else:
        return jsonify({'message': 'Fitness goal not found'}), 404


if __name__ == '__main__':
    app.run(port=8000, debug=True)
