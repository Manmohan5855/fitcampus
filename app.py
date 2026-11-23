import os
from datetime import datetime, date, timedelta
from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, FitnessProfile, WorkoutPlan, DietPlan, DailyLog, Reminder, ConsistencyReport
import gemini_integration

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fitcampus-development-secret')
# Use /tmp directory for SQLite on Vercel since the environment filesystem is read-only
if os.environ.get('VERCEL'):
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/fitcampus.db'
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fitcampus.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Create database tables and seed defaults on import (essential for serverless runs on Vercel)
with app.app_context():
    db.create_all()
    # Seed default admin if not existing
    if not User.query.filter_by(username='admin').first():
        admin = User(
            username='admin',
            password_hash=generate_password_hash('password123'),
            is_admin=True,
            is_premium=True
        )
        db.session.add(admin)
        
    # Seed default student if not existing
    if not User.query.filter_by(username='student').first():
        student = User(
            username='student',
            password_hash=generate_password_hash('password123'),
            is_premium=False
        )
        db.session.add(student)
        
    db.session.commit()

# Login Manager setup
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Global coach tip cache (Admin editable)
GLOBAL_COACH_TIP = "Hydration hack for hostel life: Keep a 1-liter copper bottle on your study desk. Fill it up every morning. Take a sip every time you complete a study task or slide transition in class!"

# --- PUBLIC ROUTES ---

@app.route('/')
def index():
    return render_template('landing.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        
        if not username or not password:
            flash('Username and password are required.', 'error')
            return redirect(url_for('signup'))
            
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('signup'))
            
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists. Please choose a different one.', 'error')
            return redirect(url_for('signup'))
            
        # Create user
        user = User(
            username=username,
            password_hash=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.flush() # get ID
        
        # Create default reminder configurations
        reminder = Reminder(user_id=user.id)
        db.session.add(reminder)
        
        db.session.commit()
        
        login_user(user)
        flash('Account created successfully! Let\'s build your profile.', 'success')
        return redirect(url_for('profile_setup'))
        
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash('Welcome back to FitCampus AI!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'error')
            
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have logged out successfully.', 'success')
    return redirect(url_for('index'))

# --- USER ROUTINES ---

@app.route('/dashboard')
@login_required
def dashboard():
    profile = current_user.profile
    
    # Get or create today's log
    today_date = date.today()
    today_log = DailyLog.query.filter_by(user_id=current_user.id, date=today_date).first()
    if not today_log:
        today_log = DailyLog(user_id=current_user.id, date=today_date)
        db.session.add(today_log)
        db.session.commit()
        
    # Get last 7 daily logs for weight tracking graph
    recent_logs = DailyLog.query.filter(
        DailyLog.user_id == current_user.id, 
        DailyLog.weight.isnot(None)
    ).order_by(DailyLog.date.desc()).limit(7).all()
    
    # Order them chronologically for the chart
    recent_logs.reverse()
    
    weight_labels = [log.date.strftime('%b %d') for log in recent_logs]
    weight_values = [log.weight for log in recent_logs]
    
    return render_template(
        'dashboard.html',
        profile=profile,
        today_log=today_log,
        weight_labels=weight_labels,
        weight_values=weight_values,
        coach_tip=GLOBAL_COACH_TIP
    )

@app.route('/profile/setup', methods=['GET', 'POST'])
@login_required
def profile_setup():
    profile = current_user.profile
    
    if request.method == 'POST':
        name = request.form.get('name')
        age = int(request.form.get('age', 0))
        gender = request.form.get('gender')
        height = float(request.form.get('height', 0.0))
        weight = float(request.form.get('weight', 0.0))
        target_weight = float(request.form.get('target_weight', 0.0))
        fitness_goal = request.form.get('fitness_goal')
        activity_level = request.form.get('activity_level')
        workout_preference = request.form.get('workout_preference')
        food_preference = request.form.get('food_preference')
        available_days = int(request.form.get('available_days', 4))
        daily_schedule = request.form.get('daily_schedule')
        experience_level = request.form.get('experience_level')
        
        is_new = False
        if not profile:
            is_new = True
            profile = FitnessProfile(user_id=current_user.id)
            
        profile.name = name
        profile.age = age
        profile.gender = gender
        profile.height = height
        profile.weight = weight
        profile.target_weight = target_weight
        profile.fitness_goal = fitness_goal
        profile.activity_level = activity_level
        profile.workout_preference = workout_preference
        profile.food_preference = food_preference
        profile.available_days = available_days
        profile.daily_schedule = daily_schedule
        profile.experience_level = experience_level
        
        if is_new:
            db.session.add(profile)
            
        # Log the starting weight for today's logs automatically if not logged
        today_log = DailyLog.query.filter_by(user_id=current_user.id, date=date.today()).first()
        if today_log:
            if not today_log.weight:
                today_log.weight = weight
        else:
            today_log = DailyLog(user_id=current_user.id, date=date.today(), weight=weight)
            db.session.add(today_log)
            
        db.session.commit()
        
        # If it was new profile creation, auto-generate workout and diet splits!
        if is_new:
            # Generate plans in database
            workout_content = gemini_integration.generate_workout_plan(profile)
            new_workout = WorkoutPlan(
                user_id=current_user.id,
                goal=fitness_goal,
                workout_preference=workout_preference,
                experience_level=experience_level,
                plan_content=workout_content
            )
            
            diet_content = gemini_integration.generate_diet_plan(profile)
            new_diet = DietPlan(
                user_id=current_user.id,
                goal=fitness_goal,
                food_preference=food_preference,
                calorie_guidance=None, # will be populated in fallback or generated HTML
                plan_content=diet_content
            )
            
            db.session.add(new_workout)
            db.session.add(new_diet)
            db.session.commit()
            
            flash('Profile details and AI training plans configured successfully!', 'success')
            return redirect(url_for('dashboard'))
            
        flash('Fitness Profile updated successfully.', 'success')
        return redirect(url_for('dashboard'))
        
    return render_template('profile_setup.html', profile=profile)

@app.route('/workout')
@login_required
def workout():
    profile = current_user.profile
    # Get active plan
    active_plan = WorkoutPlan.query.filter_by(user_id=current_user.id, is_active=True).first()
    
    # Get plan history
    history_plans = WorkoutPlan.query.filter_by(user_id=current_user.id, is_active=False).order_by(WorkoutPlan.created_at.desc()).all()
    
    return render_template(
        'workout.html',
        profile=profile,
        active_plan=active_plan,
        history_plans=history_plans
    )

@app.route('/workout/regenerate', methods=['POST'])
@login_required
def regenerate_workout():
    profile = current_user.profile
    if not profile:
        flash('Please setup your profile before generating splits.', 'error')
        return redirect(url_for('profile_setup'))
        
    # Deactivate existing plan
    WorkoutPlan.query.filter_by(user_id=current_user.id, is_active=True).update({'is_active': False})
    
    # Generate new plan
    content = gemini_integration.generate_workout_plan(profile)
    new_plan = WorkoutPlan(
        user_id=current_user.id,
        goal=profile.fitness_goal,
        workout_preference=profile.workout_preference,
        experience_level=profile.experience_level,
        plan_content=content
    )
    db.session.add(new_plan)
    db.session.commit()
    
    flash('AI Workout Split regenerated successfully!', 'success')
    return redirect(url_for('workout'))

@app.route('/workout/view/<int:plan_id>')
@login_required
def view_old_workout(plan_id):
    plan = WorkoutPlan.query.get_or_404(plan_id)
    if plan.user_id != current_user.id:
        flash('Unauthorized.', 'error')
        return redirect(url_for('workout'))
        
    return render_template(
        'view_item.html',
        title=f"Workout Plan from {plan.created_at.strftime('%b %d, %Y')}",
        subtitle=f"Goal: {plan.goal} | Splits Location: {plan.workout_preference}",
        content=plan.plan_content,
        back_url=url_for('workout'),
        type='workout'
    )

@app.route('/diet')
@login_required
def diet():
    profile = current_user.profile
    # Get active plan
    active_plan = DietPlan.query.filter_by(user_id=current_user.id, is_active=True).first()
    
    # Get history
    history_plans = DietPlan.query.filter_by(user_id=current_user.id, is_active=False).order_by(DietPlan.created_at.desc()).all()
    
    return render_template(
        'diet.html',
        profile=profile,
        active_plan=active_plan,
        history_plans=history_plans
    )

@app.route('/diet/regenerate', methods=['POST'])
@login_required
def regenerate_diet():
    profile = current_user.profile
    if not profile:
        flash('Please setup your profile before generating diet plans.', 'error')
        return redirect(url_for('profile_setup'))
        
    # Deactivate existing plan
    DietPlan.query.filter_by(user_id=current_user.id, is_active=True).update({'is_active': False})
    
    # Generate new plan
    content = gemini_integration.generate_diet_plan(profile)
    new_plan = DietPlan(
        user_id=current_user.id,
        goal=profile.fitness_goal,
        food_preference=profile.food_preference,
        plan_content=content
    )
    db.session.add(new_plan)
    db.session.commit()
    
    flash('AI Diet Recommendations regenerated successfully!', 'success')
    return redirect(url_for('diet'))

@app.route('/diet/view/<int:plan_id>')
@login_required
def view_old_diet(plan_id):
    plan = DietPlan.query.get_or_404(plan_id)
    if plan.user_id != current_user.id:
        flash('Unauthorized.', 'error')
        return redirect(url_for('diet'))
        
    return render_template(
        'view_item.html',
        title=f"Diet Plan from {plan.created_at.strftime('%b %d, %Y')}",
        subtitle=f"Goal: {plan.goal} | Category: {plan.food_preference}",
        content=plan.plan_content,
        back_url=url_for('diet'),
        type='diet'
    )

@app.route('/tracker', methods=['GET', 'POST'])
@login_required
def tracker():
    profile = current_user.profile
    if request.method == 'POST':
        date_str = request.form.get('date')
        log_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        weight_val = request.form.get('weight')
        water_val = request.form.get('water_intake')
        sleep_val = request.form.get('sleep_hours')
        cal_val = request.form.get('calories_consumed')
        mood = request.form.get('mood')
        workout_completed = request.form.get('workout_completed') == 'y'
        
        # Check if record already exists
        log = DailyLog.query.filter_by(user_id=current_user.id, date=log_date).first()
        if not log:
            log = DailyLog(user_id=current_user.id, date=log_date)
            db.session.add(log)
            
        if weight_val:
            log.weight = float(weight_val)
            # Update user's current weight in profile too if logging for today/recent
            if log_date == date.today() and profile:
                profile.weight = float(weight_val)
        if water_val:
            log.water_intake = float(water_val)
        if sleep_val:
            log.sleep_hours = float(sleep_val)
        if cal_val:
            log.calories_consumed = int(cal_val)
        if mood:
            log.mood = mood
        log.workout_completed = workout_completed
        
        db.session.commit()
        flash(f'Progress metrics saved successfully for {log_date.strftime("%B %d, %Y")}.', 'success')
        return redirect(url_for('tracker'))
        
    logs = DailyLog.query.filter_by(user_id=current_user.id).order_by(DailyLog.date.desc()).all()
    today_date = date.today().strftime('%Y-%m-%d')
    return render_template('tracker.html', profile=profile, logs=logs, today_date=today_date)

@app.route('/tracker/quick-log', methods=['POST'])
@login_required
def quick_log():
    data = request.get_json() or {}
    action = data.get('action')
    today = date.today()
    
    log = DailyLog.query.filter_by(user_id=current_user.id, date=today).first()
    if not log:
        log = DailyLog(user_id=current_user.id, date=today)
        db.session.add(log)
        
    message = ""
    if action == 'water':
        amt = float(data.get('amount', 0.25))
        log.water_intake += amt
        message = f"Added {int(amt*1000)}ml water. Keep hydrating!"
    elif action == 'sleep':
        hrs = float(data.get('amount', 1.0))
        log.sleep_hours += hrs
        message = f"Added {int(hrs)} Hour sleep log."
    elif action == 'workout':
        status = bool(data.get('status', True))
        log.workout_completed = status
        message = "Workout split completed! Great consistency!" if status else "Workout status reset."
        
    db.session.commit()
    
    # Return new log metrics for AJAX update
    return jsonify({
        'success': True,
        'message': message,
        'data': {
            'water_intake': log.water_intake,
            'sleep_hours': log.sleep_hours,
            'workout_completed': log.workout_completed,
            'calories_consumed': log.calories_consumed
        }
    })

@app.route('/weekly-reports')
@login_required
def weekly_reports():
    reports = ConsistencyReport.query.filter_by(user_id=current_user.id).order_by(ConsistencyReport.created_at.desc()).all()
    return render_template('weekly_reports.html', reports=reports)

@app.route('/weekly-reports/compile', methods=['POST'])
@login_required
def generate_report():
    today = date.today()
    start_date = today - timedelta(days=7)
    
    # Gather logs for past 7 days
    logs = DailyLog.query.filter(
        DailyLog.user_id == current_user.id,
        DailyLog.date >= start_date,
        DailyLog.date <= today
    ).all()
    
    if not logs:
        flash('No daily logs found for the past week. Please complete some tracking logs before compiling a report.', 'error')
        return redirect(url_for('weekly_reports'))
        
    # Calculate stats
    total_days = 7
    workouts_done = sum(1 for log in logs if log.workout_completed)
    avg_water = sum(log.water_intake for log in logs) / len(logs)
    avg_sleep = sum(log.sleep_hours for log in logs) / len(logs)
    
    # Find weight changes
    weight_logs = [log.weight for log in logs if log.weight is not None]
    weight_change = 0.0
    if len(weight_logs) >= 2:
        weight_change = weight_logs[-1] - weight_logs[0]
        
    # Calculate Consistency Score (out of 100)
    # Weights: 40% workout completion rate, 30% water target (>= 2.5L), 30% sleep target (>= 7 hrs)
    workout_rate = (workouts_done / current_user.profile.available_days) * 100 if current_user.profile else (workouts_done / 4) * 100
    workout_rate = min(workout_rate, 100)
    
    water_score = min((avg_water / 2.5) * 100, 100) if avg_water > 0 else 0
    sleep_score = min((avg_sleep / 7.0) * 100, 100) if avg_sleep > 0 else 0
    
    consistency = (workout_rate * 0.4) + (water_score * 0.3) + (sleep_score * 0.3)
    
    report_data = {
        'workout_rate': round(workout_rate, 1),
        'avg_water': round(avg_water, 2),
        'avg_sleep': round(avg_sleep, 1),
        'weight_change': round(weight_change, 2),
        'consistency': round(consistency, 1)
    }
    
    # Generate AI Suggestions paragraph
    ai_feedback = gemini_integration.generate_weekly_feedback(report_data)
    
    # Create Report row
    report = ConsistencyReport(
        user_id=current_user.id,
        start_date=start_date,
        end_date=today,
        workout_completion_rate=workout_rate,
        average_water=avg_water,
        average_sleep=avg_sleep,
        weight_change=weight_change,
        consistency_score=consistency,
        ai_feedback=ai_feedback
    )
    db.session.add(report)
    db.session.commit()
    
    flash('Weekly Consistency Report compiled successfully!', 'success')
    return redirect(url_for('weekly_reports'))

@app.route('/weekly-reports/view/<int:report_id>')
@login_required
def view_old_report(report_id):
    rep = ConsistencyReport.query.get_or_404(report_id)
    if rep.user_id != current_user.id:
        flash('Unauthorized.', 'error')
        return redirect(url_for('weekly_reports'))
        
    # Render using the report HTML feedback
    html_content = f"""
    <div class="stats-grid" style="grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 30px;">
        <div class="card stat-card" style="background: rgba(255, 255, 255, 0.02); padding: 15px;">
            <span class="stat-val" style="color: var(--primary); font-size: 22px;">{round(rep.consistency_score, 0)}%</span>
            <span class="stat-label" style="font-size: 10px;">Consistency</span>
        </div>
        <div class="card stat-card" style="background: rgba(255, 255, 255, 0.02); padding: 15px;">
            <span class="stat-val" style="color: var(--success); font-size: 22px;">{round(rep.workout_completion_rate, 0)}%</span>
            <span class="stat-label" style="font-size: 10px;">Workout Rate</span>
        </div>
        <div class="card stat-card" style="background: rgba(255, 255, 255, 0.02); padding: 15px;">
            <span class="stat-val" style="color: var(--accent); font-size: 22px;">{round(rep.average_sleep, 1)}h</span>
            <span class="stat-label" style="font-size: 10px;">Avg Sleep</span>
        </div>
        <div class="card stat-card" style="background: rgba(255, 255, 255, 0.02); padding: 15px;">
            <span class="stat-val" style="color: var(--warning); font-size: 22px;">{rep.weight_change} kg</span>
            <span class="stat-label" style="font-size: 10px;">Weight Delta</span>
        </div>
    </div>
    {rep.ai_feedback}
    """
    
    return render_template(
        'view_item.html',
        title=f"Weekly Report ({rep.start_date.strftime('%b %d')} - {rep.end_date.strftime('%b %d, %Y')})",
        subtitle=f"Compiled consistency report records",
        content=html_content,
        back_url=url_for('weekly_reports'),
        type='reports'
    )

@app.route('/reminders', methods=['GET', 'POST'])
@login_required
def reminder_settings():
    reminder = current_user.reminders
    if not reminder:
        reminder = Reminder(user_id=current_user.id)
        db.session.add(reminder)
        db.session.commit()
        
    if request.method == 'POST':
        reminder.workout_reminded = request.form.get('workout_reminded') == 'y'
        reminder.water_reminded = request.form.get('water_reminded') == 'y'
        reminder.sleep_reminded = request.form.get('sleep_reminded') == 'y'
        reminder.weekly_checkin = request.form.get('weekly_checkin') == 'y'
        db.session.commit()
        
        flash('Reminder configurations updated successfully.', 'success')
        return redirect(url_for('reminder_settings'))
        
    return render_template('reminder_settings.html', reminder=reminder)

# --- ADMIN PANEL ROUTES ---

def admin_required(f):
    # Helper decorator for admin blocks
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Access denied. Administrator privileges required.', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    users = User.query.order_by(User.id.asc()).all()
    
    # Calculate stats
    stats = {
        'total_users': User.query.count(),
        'total_workouts': WorkoutPlan.query.count(),
        'total_diets': DietPlan.query.count(),
        'total_logs': DailyLog.query.count()
    }
    
    return render_template(
        'admin.html',
        users=users,
        stats=stats,
        current_tip=GLOBAL_COACH_TIP
    )

@app.route('/admin/toggle-premium/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def admin_toggle_premium(user_id):
    usr = User.query.get_or_404(user_id)
    usr.is_premium = not usr.is_premium
    db.session.commit()
    flash(f'Toggled Tier details for User: {usr.username}.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/toggle-admin/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def admin_toggle_admin(user_id):
    usr = User.query.get_or_404(user_id)
    # prevent locking self out
    if usr.id == current_user.id:
        flash('You cannot revoke your own administrator privileges.', 'error')
        return redirect(url_for('admin_dashboard'))
        
    usr.is_admin = not usr.is_admin
    db.session.commit()
    flash(f'Toggled Role attributes for User: {usr.username}.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete-user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def admin_delete_user(user_id):
    usr = User.query.get_or_404(user_id)
    if usr.id == current_user.id:
        flash('You cannot delete your own active administrator account.', 'error')
        return redirect(url_for('admin_dashboard'))
        
    db.session.delete(usr)
    db.session.commit()
    flash('User account deleted permanently.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/update-tip', methods=['POST'])
@login_required
@admin_required
def admin_update_tip():
    global GLOBAL_COACH_TIP
    tip = request.form.get('coach_tip', '').strip()
    if tip:
        GLOBAL_COACH_TIP = tip
        flash('Global Coach tip updated successfully!', 'success')
    else:
        flash('Tip content cannot be blank.', 'error')
    return redirect(url_for('admin_dashboard'))

# --- APP STARTUP & SEEDING ---

if __name__ == '__main__':
    print("Database synced successfully! Starting server...")
    app.run(host='0.0.0.0', port=5000, debug=True)
