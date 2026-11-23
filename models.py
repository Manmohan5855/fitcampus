from datetime import datetime, date
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_premium = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    profile = db.relationship('FitnessProfile', backref='user', uselist=False, cascade="all, delete-orphan")
    workout_plans = db.relationship('WorkoutPlan', backref='user', lazy=True, cascade="all, delete-orphan")
    diet_plans = db.relationship('DietPlan', backref='user', lazy=True, cascade="all, delete-orphan")
    daily_logs = db.relationship('DailyLog', backref='user', lazy=True, cascade="all, delete-orphan")
    reminders = db.relationship('Reminder', backref='user', uselist=False, cascade="all, delete-orphan")
    reports = db.relationship('ConsistencyReport', backref='user', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.username}>"

class FitnessProfile(db.Model):
    __tablename__ = 'fitness_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(50), nullable=False)
    height = db.Column(db.Float, nullable=False)  # in cm
    weight = db.Column(db.Float, nullable=False)  # in kg
    target_weight = db.Column(db.Float, nullable=False)  # in kg
    fitness_goal = db.Column(db.String(100), nullable=False)  # e.g., "Weight Loss", "Weight Gain", "Muscle Gain", "General Fitness"
    activity_level = db.Column(db.String(100), nullable=False)  # e.g., "Sedentary", "Lightly Active", "Moderately Active", "Very Active"
    workout_preference = db.Column(db.String(100), nullable=False)  # e.g., "Home", "Gym"
    food_preference = db.Column(db.String(100), nullable=False)  # e.g., "Vegetarian", "Non-Vegetarian", "Mixed"
    daily_schedule = db.Column(db.String(200), nullable=True)  # e.g., "College hours 9am-4pm, busy evenings"
    experience_level = db.Column(db.String(100), nullable=False)  # e.g., "Beginner", "Intermediate"
    available_days = db.Column(db.Integer, default=4, nullable=False)  # Days per week
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<FitnessProfile {self.name} for User ID {self.user_id}>"

class WorkoutPlan(db.Model):
    __tablename__ = 'workout_plans'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    goal = db.Column(db.String(100))
    workout_preference = db.Column(db.String(100))
    experience_level = db.Column(db.String(100))
    plan_content = db.Column(db.Text, nullable=False)  # Renders markdown/HTML
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<WorkoutPlan {self.id} for User ID {self.user_id}>"

class DietPlan(db.Model):
    __tablename__ = 'diet_plans'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    goal = db.Column(db.String(100))
    food_preference = db.Column(db.String(100))
    calorie_guidance = db.Column(db.Integer)  # Target calories
    macros = db.Column(db.String(200))  # e.g. "Protein: 120g, Carbs: 200g, Fats: 60g"
    plan_content = db.Column(db.Text, nullable=False)  # Renders markdown/HTML
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<DietPlan {self.id} for User ID {self.user_id}>"

class DailyLog(db.Model):
    __tablename__ = 'daily_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.Date, default=date.today, nullable=False)
    weight = db.Column(db.Float, nullable=True)
    workout_completed = db.Column(db.Boolean, default=False)
    water_intake = db.Column(db.Float, default=0.0)  # in liters
    sleep_hours = db.Column(db.Float, default=0.0)
    calories_consumed = db.Column(db.Integer, default=0)
    mood = db.Column(db.String(100), nullable=True)  # e.g., "Energetic", "Tired", "Stressed", "Good"

    __table_args__ = (db.UniqueConstraint('user_id', 'date', name='_user_date_uc'),)

    def __repr__(self):
        return f"<DailyLog {self.date} for User ID {self.user_id}>"

class Reminder(db.Model):
    __tablename__ = 'reminders'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    workout_reminded = db.Column(db.Boolean, default=True)
    water_reminded = db.Column(db.Boolean, default=True)
    sleep_reminded = db.Column(db.Boolean, default=True)
    weekly_checkin = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f"<Reminder Settings for User ID {self.user_id}>"

class ConsistencyReport(db.Model):
    __tablename__ = 'consistency_reports'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    workout_completion_rate = db.Column(db.Float)  # e.g. 80.0 (%)
    average_water = db.Column(db.Float)  # in liters
    average_sleep = db.Column(db.Float)  # in hours
    weight_change = db.Column(db.Float)  # e.g. -0.5 kg
    consistency_score = db.Column(db.Float)  # overall out of 100
    ai_feedback = db.Column(db.Text)  # Feedback paragraph
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<ConsistencyReport {self.id} for User ID {self.user_id}>"
