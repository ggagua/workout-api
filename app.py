from flask import Flask, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
import sqlite3
import uuid
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from functools import wraps
import datetime
import json
from sqlalchemy import and_
from flask_swagger_ui import get_swaggerui_blueprint


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secretkeyvery'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///exercises.db'
db = SQLAlchemy(app)

SWAGGER_URL = '/api/docs'
API_URL = '/static/swagger.json'


swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "Workout RESTful API"
    },
    # oauth_config={  # OAuth config. See https://github.com/swagger-api/swagger-ui#oauth2-configuration .
    #    'clientId': "your-client-id",
    #    'clientSecret': "your-client-secret-if-required",
    #    'realm': "your-realms",
    #    'appName': "your-app-name",
    #    'scopeSeparator': " ",
    #    'additionalQueryStringParams': {'test': "hello"}
    # }
)

app.register_blueprint(swaggerui_blueprint)



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



class WorkoutSession(db.Model):
    id = db.Column(db.Integer, primary_key=True, unique=True)
    user_id = db.Column(db.String(50), nullable=False)
    workout_plan_id = db.Column(db.Integer, nullable=False)
    exercise_name = db.Column(db.String(255), nullable=False)
    sets = db.Column(db.Integer, nullable=True)
    reps = db.Column(db.Integer, nullable=True)
    completed = db.Column(db.Boolean, default=False)
    rest_time = db.Column(db.Integer, nullable=True)

    def serialize(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'workout_plan_id': self.workout_plan_id,
            'exercise_name': self.exercise_name,
            'sets': self.sets,
            'reps': self.reps,
            'completed': self.completed,
            'rest_time': self.rest_time
        }


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


    if 'name' not in data:
        return jsonify({'message': 'Username not provided in the request.'}), 400

    existing_user = User.query.filter_by(name=data['name']).first()

    if existing_user:
        return jsonify({'message': 'Username already exists. Choose a different username.'}), 400

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

@app.route('/workout-mode/start', methods=['POST'])
@token_required
def start_workout_mode(current_user):
    data = request.get_json()

    workout_plan_id = data.get('workout_plan_id')
    rest_time = data.get('rest_time')

    if not workout_plan_id or not rest_time:
        return jsonify({'message': 'Workout plan ID and rest time are required to start the workout mode'}), 400

    workout_plan = WorkoutPlanFinal.query.get(workout_plan_id)

    if not workout_plan:
        return jsonify({'message': 'Workout plan not found'}), 404

    existing_sessions = WorkoutSession.query.filter_by(user_id=current_user.public_id,
                                                       workout_plan_id=workout_plan_id,
                                                       completed=False).all()
    for existing_session in existing_sessions:
        existing_session.completed = True
    db.session.commit()

    exercises_list = json.loads(workout_plan.selected_exercises)

    if not exercises_list:
        return jsonify({'message': 'No exercises found in the workout plan'}), 400

    first_exercise = exercises_list[0]
    new_session = WorkoutSession(
        user_id=current_user.public_id,
        workout_plan_id=workout_plan_id,
        exercise_name=first_exercise['name'],
        sets=first_exercise.get('sets', 0),
        reps=first_exercise.get('reps', 0),
        rest_time=rest_time
    )

    db.session.add(new_session)
    db.session.commit()

    return jsonify({'message': 'Workout mode started successfully!', 'workout_session': new_session.serialize()}), 201


@app.route('/workout-mode/start/complete', methods=['POST'])
@token_required
def complete_current_exercise(current_user):
    current_session = WorkoutSession.query.filter_by(user_id=current_user.public_id, completed=False).first()

    if current_session:
        current_session.completed = True
        db.session.commit()

        workout_plan_id = current_session.workout_plan_id
        next_exercise = get_next_exercise(current_user, workout_plan_id)

        if next_exercise:
            return jsonify({'message': 'Exercise completed, moving to the next one', 'next_exercise': next_exercise})
        else:
            WorkoutSession.query.filter(
                and_(
                    WorkoutSession.user_id == current_user.public_id,
                    WorkoutSession.workout_plan_id == workout_plan_id
                )
            ).delete()

            db.session.commit()
        return jsonify({'message': 'No next exercise found. You finished your workout!'}), 400

    return jsonify({'message': 'No active workout session found'}), 404

def get_next_exercise(current_user, workout_plan_id):
    workout_plan = db.session.get(WorkoutPlanFinal, workout_plan_id)
    current_session = WorkoutSession.query.filter_by(user_id=current_user.public_id, completed=True).first()

    if workout_plan:
        exercises_list = json.loads(workout_plan.selected_exercises)
        completed_exercises = {exercise.exercise_name for exercise in
                               WorkoutSession.query.filter_by(user_id=current_user.public_id,
                                                              workout_plan_id=workout_plan_id,
                                                              completed=True).all()}

        for exercise in exercises_list:
            if exercise['name'] not in completed_exercises:
                new_session = WorkoutSession(
                    user_id=current_user.public_id,
                    workout_plan_id=workout_plan_id,
                    exercise_name=exercise['name'],
                    sets=exercise.get('sets', 0),
                    reps=exercise.get('reps', 0),
                    rest_time=current_session.rest_time
                )
                db.session.add(new_session)
                db.session.commit()
                return new_session.serialize()

    return None


if __name__ == '__main__':
    app.run(port=8000, debug=True)
