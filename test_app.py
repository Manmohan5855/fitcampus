import unittest
from datetime import date
from werkzeug.security import generate_password_hash
from app import app, db
from models import User, FitnessProfile, DailyLog, WorkoutPlan, DietPlan

class FitCampusTest(unittest.TestCase):

    def setUp(self):
        # Configure app for testing
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:' # Use in-memory database for speed
        self.app = app.test_client()
        
        with app.app_context():
            db.create_all()
            
    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_landing_page(self):
        """Test that the landing page renders correctly."""
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'FitCampus AI', response.data)
        self.assertIn(b'AI Fitness Coach', response.data)

    def test_user_registration_and_login(self):
        """Test registering a new user and signing in."""
        # 1. Register User
        reg_response = self.app.post('/signup', data={
            'username': 'teststudent',
            'password': 'testpassword',
            'confirm_password': 'testpassword'
        }, follow_redirects=True)
        self.assertEqual(reg_response.status_code, 200)
        self.assertIn(b'Account created successfully', reg_response.data)

        # Verify in DB
        with app.app_context():
            user = User.query.filter_by(username='teststudent').first()
            self.assertIsNotNone(user)
            self.assertTrue(user.reminders.workout_reminded)

        # Log out user first to clear session
        logout_response = self.app.get('/logout', follow_redirects=True)
        self.assertEqual(logout_response.status_code, 200)
        self.assertIn(b'FitCampus AI', logout_response.data)

        # 2. Login User
        login_response = self.app.post('/login', data={
            'username': 'teststudent',
            'password': 'testpassword'
        }, follow_redirects=True)
        self.assertEqual(login_response.status_code, 200)
        self.assertIn(b'Welcome back to FitCampus AI', login_response.data)

    def test_profile_creation_and_plan_generation(self):
        """Test setting up a fitness profile and generating custom splits."""
        # Register and log in user
        self.app.post('/signup', data={
            'username': 'profileuser',
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)

        # Post Profile Details
        profile_response = self.app.post('/profile/setup', data={
            'name': 'Rohan',
            'age': '21',
            'gender': 'Male',
            'height': '178',
            'weight': '70',
            'target_weight': '75',
            'fitness_goal': 'Muscle Gain',
            'activity_level': 'Lightly Active',
            'workout_preference': 'Gym',
            'food_preference': 'Vegetarian',
            'available_days': '4',
            'daily_schedule': 'Busy lectures, mess food only',
            'experience_level': 'Beginner'
        }, follow_redirects=True)

        self.assertEqual(profile_response.status_code, 200)
        self.assertIn(b'AI training plans configured successfully', profile_response.data)

        # Verify DB records
        with app.app_context():
            user = User.query.filter_by(username='profileuser').first()
            self.assertIsNotNone(user.profile)
            self.assertEqual(user.profile.name, 'Rohan')
            self.assertEqual(user.profile.fitness_goal, 'Muscle Gain')
            
            # Verify that Workout and Diet plans were created
            active_workout = WorkoutPlan.query.filter_by(user_id=user.id, is_active=True).first()
            self.assertIsNotNone(active_workout)
            self.assertIn('Day 1', active_workout.plan_content)

            active_diet = DietPlan.query.filter_by(user_id=user.id, is_active=True).first()
            self.assertIsNotNone(active_diet)
            self.assertIn('Protein', active_diet.plan_content)
            self.assertIn('Soya Chunk', active_diet.plan_content)

    def test_daily_logger(self):
        """Test progress logs insert/update operations."""
        # Register and log in
        self.app.post('/signup', data={
            'username': 'loggeruser',
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)

        # Setup Profile
        self.app.post('/profile/setup', data={
            'name': 'Rohan', 'age': '21', 'gender': 'Male', 'height': '178', 'weight': '70',
            'target_weight': '75', 'fitness_goal': 'Muscle Gain', 'activity_level': 'Lightly Active',
            'workout_preference': 'Gym', 'food_preference': 'Vegetarian', 'available_days': '4',
            'daily_schedule': '', 'experience_level': 'Beginner'
        }, follow_redirects=True)

        # Log daily metrics via traditional post form
        log_response = self.app.post('/tracker', data={
            'date': date.today().strftime('%Y-%m-%d'),
            'weight': '70.8',
            'water_intake': '2.8',
            'sleep_hours': '7.5',
            'calories_consumed': '2300',
            'mood': 'Good',
            'workout_completed': 'y'
        }, follow_redirects=True)

        self.assertEqual(log_response.status_code, 200)

        with app.app_context():
            user = User.query.filter_by(username='loggeruser').first()
            log = DailyLog.query.filter_by(user_id=user.id, date=date.today()).first()
            self.assertIsNotNone(log)
            self.assertEqual(log.weight, 70.8)
            self.assertEqual(log.water_intake, 2.8)
            self.assertTrue(log.workout_completed)

        # Log daily metrics via AJAX endpoint
        ajax_response = self.app.post('/tracker/quick-log', json={
            'action': 'water',
            'amount': 0.25
        })
        self.assertEqual(ajax_response.status_code, 200)
        self.assertTrue(ajax_response.json['success'])

        with app.app_context():
            user = User.query.filter_by(username='loggeruser').first()
            log = DailyLog.query.filter_by(user_id=user.id, date=date.today()).first()
            self.assertEqual(log.water_intake, 3.05) # 2.8 + 0.25

if __name__ == '__main__':
    unittest.main()
