import json
import requests
import re
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

def call_gemini_api(prompt):
    """
    Tries to call Gemini API via raw REST request to the v1 stable endpoints or v1beta fallback.
    Returns the string text or None if it fails.
    """
    # Try multiple common model URLs to handle various configurations
    endpoints = [
        # Stable v1 endpoints
        ("v1", "gemini-1.5-flash"),
        ("v1", "gemini-1.5-pro"),
        # Beta v1beta endpoints
        ("v1beta", "gemini-1.5-flash"),
        ("v1beta", "gemini-pro"),
    ]
    
    headers = {'Content-Type': 'application/json'}
    data = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }

    for version, model in endpoints:
        url = f"https://generativelanguage.googleapis.com/{version}/models/{model}:generateContent?key={API_KEY}"
        try:
            response = requests.post(url, headers=headers, json=data, timeout=8)
            if response.status_code == 200:
                res_data = response.json()
                # Parse content from response structure
                text = res_data['candidates'][0]['content']['parts'][0]['text']
                # Strip markdown code blocks if the model returned them
                text = re.sub(r"^```html\s*", "", text, flags=re.IGNORECASE)
                text = re.sub(r"\s*```$", "", text, flags=re.IGNORECASE)
                return text.strip()
        except Exception:
            continue
    return None

def generate_workout_plan(profile):
    """
    Generates a personalized workout plan using Gemini API.
    Falls back to a rich template generator if the API fails.
    """
    prompt = f"""
    You are an expert AI Fitness Coach. Generate a comprehensive and highly personalized workout plan for a college student based on these details:
    - Name: {profile.name}
    - Age: {profile.age}
    - Gender: {profile.gender}
    - Goal: {profile.fitness_goal} (e.g. Weight Loss, Muscle Gain, Weight Gain, General Fitness)
    - Workout Preference: {profile.workout_preference} (Home or Gym)
    - Available Days: {profile.available_days} days per week
    - Experience Level: {profile.experience_level} (Beginner or Intermediate)
    - Daily Schedule/Constraints: {profile.daily_schedule}

    Requirements for the response:
    - Return the response in clean, raw HTML containing nicely styled containers, grid layouts, cards, and tables. Do NOT wrap it in ```html markdown block.
    - Organize the plan into a "Weekly Split Summary" card, and day-by-day workout lists (e.g. Day 1, Day 2...).
    - For each day, list exercise name, sets, reps, rest time, and brief form cues.
    - Make it motivating, student-friendly, and compatible with their schedule.
    - If Home workout, focus on bodyweight, HIIT, or band work.
    - If Gym workout, focus on barbell, dumbbell, and machine compound lifts.
    - Keep formatting elegant using standard CSS classes like 'plan-card', 'workout-table', 'exercise-item'.
    """

    ai_response = call_gemini_api(prompt)
    if ai_response:
        return ai_response
    
    # Fallback Rule-Based Workout Generator
    return get_fallback_workout(profile)

def generate_diet_plan(profile):
    """
    Generates a personalized diet plan using Gemini API.
    Falls back to a rich template generator if the API fails.
    """
    prompt = f"""
    You are a student nutrition expert. Generate a detailed, student-budget friendly diet plan based on these details:
    - Name: {profile.name}
    - Age: {profile.age}
    - Weight: {profile.weight} kg
    - Height: {profile.height} cm
    - Target Weight: {profile.target_weight} kg
    - Fitness Goal: {profile.fitness_goal}
    - Activity Level: {profile.activity_level}
    - Food Preference: {profile.food_preference} (Vegetarian, Non-Vegetarian, Mixed)
    - Daily Schedule/Constraints: {profile.daily_schedule}

    Requirements for the response:
    - Return the response in clean, raw HTML (no ```html wrappers).
    - Provide a Daily Calorie and Macro Target summary card.
    - Structure meal suggestions for Breakfast, Lunch, Dinner, and Snacks.
    - Provide a special "Student Budget & Hostel Hacks" section (e.g., cheap protein sources, microwave recipes, eating out smart, making adjustments for hostel mess food).
    - Keep styling neat and modern using cards and lists.
    """

    ai_response = call_gemini_api(prompt)
    if ai_response:
        return ai_response

    # Fallback Rule-Based Diet Generator
    return get_fallback_diet(profile)

def generate_weekly_feedback(report_data):
    """
    Generates weekly suggestions based on user logs.
    """
    prompt = f"""
    You are an AI Health Coach. Give highly encouraging and constructive feedback for a student based on their weekly logs:
    - Workout Completion Rate: {report_data['workout_rate']}%
    - Average Daily Water Intake: {report_data['avg_water']} Liters
    - Average Daily Sleep: {report_data['avg_sleep']} Hours
    - Weight Change: {report_data['weight_change']} kg
    - Consistency Score: {report_data['consistency']}/100

    Provide:
    - Return the response in clean, raw HTML (no ```html wrappers).
    - 2-3 specific improvements they can make next week.
    - A motivational closing quote tailored for busy college students.
    """
    
    ai_response = call_gemini_api(prompt)
    if ai_response:
        return ai_response
        
    # Fallback Feedback Generator
    rate = report_data['workout_rate']
    score = report_data['consistency']
    change = report_data['weight_change']
    
    status = "excellent" if score >= 80 else "good" if score >= 60 else "needs improvement"
    
    html = f"""
    <div class="feedback-card">
        <h3>AI Coach Weekly Feedback</h3>
        <p>Your consistency score is <strong>{score}/100</strong>, which means your progress is <strong>{status.upper()}</strong> this week.</p>
        
        <div class="feedback-section">
            <h4>💡 Next Week's Action Steps:</h4>
            <ul>
    """
    if rate < 50:
        html += "<li><strong>Schedule Workouts:</strong> Block out 30 minutes in your calendar right between classes. Even a 20-minute workout is better than zero.</li>"
    else:
        html += "<li><strong>Progressive Overload:</strong> You did great with consistency! Try adding 1-2 reps or slightly more weight to your main movements next week.</li>"
        
    if report_data['avg_water'] < 2.5:
        html += "<li><strong>Hydration Hack:</strong> Keep a 1-liter bottle on your study desk. Take a sip every time you complete a study task or change classes.</li>"
    else:
        html += "<li><strong>Hydration Mastery:</strong> Your water intake was solid. Keep it up to boost recovery and mental focus during lectures.</li>"
        
    if report_data['avg_sleep'] < 7.0:
        html += "<li><strong>Sleep Hygiene:</strong> Sleep is where muscle builds and brains recover. Try to set a 'no screen' rule 30 minutes before bed, even during exams.</li>"
    else:
        html += "<li><strong>Rest Quality:</strong> Excellent sleep habits! Getting enough rest is your secret weapon for academic and physical performance.</li>"
        
    html += f"""
            </ul>
        </div>
        <div class="feedback-motivation">
            <blockquote>
                "Consistency beats intensity. Running 1 km every day is better than running 10 km once a month. Keep showing up for yourself!"
            </blockquote>
        </div>
    </div>
    """
    return html


# --- FALLBACK TEMPLATES WORKOUTS ---

def get_fallback_workout(profile):
    goal = profile.fitness_goal.lower()
    pref = profile.workout_preference.lower()
    days = min(max(int(profile.available_days), 2), 6)
    exp = profile.experience_level.lower()
    
    html = f"""
    <div class="plan-header-card">
        <h2>{profile.name}'s Custom AI Workout Split</h2>
        <p class="subtitle">🎯 Goal: {profile.fitness_goal} | 📍 Location: {profile.workout_preference} | ⚡ Level: {profile.experience_level} | 📅 {days} Days/Week</p>
    </div>
    """
    
    # Define splits
    exercises = {
        "push": [
            ("Chest Press / Pushups", "3-4", "8-12", "90s", "Keep elbows at 45 degrees, squeeze chest."),
            ("Overhead Shoulder Press", "3", "10-12", "90s", "Press straight up, engage core."),
            ("Incline Dumbbell Flyes / Decline Pushups", "3", "12-15", "60s", "Focus on upper chest stretch."),
            ("Tricep Overhead Extensions / Bench Dips", "3", "12-15", "60s", "Keep elbows close to head."),
            ("Lateral Raises", "4", "15", "45s", "Lead with elbows, control the drop.")
        ],
        "pull": [
            ("Lat Pulldown / Pullups", "3-4", "8-12", "90s", "Pull down to upper chest, drive elbows."),
            ("Dumbbell Row / Bed-Sheet Rows", "3", "10-12", "90s", "Pull towards hip, keep back flat."),
            ("Face Pulls / Rear Delt Flyes", "3", "15", "60s", "Pull towards bridge of nose, hold 1s."),
            ("Bicep Hammer Curls", "3", "12-15", "60s", "Keep upper arms static, squeeze biceps."),
            ("Shrugs / Reverse Flyes", "3", "15", "45s", "Shrug straight up, squeeze traps.")
        ],
        "legs": [
            ("Squats (Goblet or Bodyweight)", "4", "10-15", "90s", "Sit back, hips below knees, chest up."),
            ("Romanian Deadlifts (Dumbbell/Bag)", "3", "10-12", "90s", "Hinge hips back, feel hamstrings."),
            ("Walking Lunges", "3", "12 per leg", "60s", "Step far enough to form 90-degree angles."),
            ("Calf Raises", "4", "15-20", "45s", "Hold at top for 2s, slow descent."),
            ("Plank", "3", "45s hold", "45s", "Keep body in straight line, squeeze glutes.")
        ],
        "fullbody_a": [
            ("Goblet Squats / Air Squats", "3-4", "12-15", "90s", "Sit back, hips below knees."),
            ("Dumbbell Floor Press / Pushups", "3-4", "10-12", "90s", "Slow control down, explode up."),
            ("Dumbbell Row / Backpack Rows", "3", "10-12", "90s", "Flat back, pull to belly button."),
            ("Dumbbell Romanian Deadlifts", "3", "12", "90s", "Hinge at hips, slight knee bend."),
            ("Dumbbell Shoulder Press", "3", "12", "60s", "Press upwards, control back down."),
            ("Plank to Pushup / Bicycle Crunches", "3", "15 reps", "60s", "Keep core tight throughout.")
        ],
        "fullbody_b": [
            ("Lunges (Dumbbell or Bodyweight)", "3", "12 per leg", "90s", "Step far, control drop."),
            ("Incline Press / Decline Pushups", "3", "12", "90s", "Keep tension on upper chest."),
            ("Lat Pulldown / Pullups / Band Lat Pulls", "3", "10-12", "90s", "Pull elbows down, squeeze lats."),
            ("Glute Bridges", "3", "15-20", "60s", "Squeeze glutes at top, hold 1s."),
            ("Lateral Raises", "3", "15", "60s", "Raise arms to sides, lead with elbows."),
            ("Russian Twists", "3", "20 reps", "45s", "Follow hands with eyes, engage obliques.")
        ],
        "cardio_hiit": [
            ("Jumping Jacks", "4", "45s active", "30s", "Stay light on feet, quick pace."),
            ("Bodyweight Squats", "4", "45s active", "30s", "Maximum reps with good form."),
            ("Mountain Climbers", "4", "45s active", "30s", "Drive knees to chest, flat back."),
            ("Burpees or High Knees", "4", "30s active", "45s", "High energy, explode up."),
            ("Plank Hold", "4", "45s active", "30s", "Keep core braced.")
        ]
    }
    
    # Generate schedule based on available days
    schedule = []
    if days == 2:
        schedule = [("Day 1", "Full Body Routine A", exercises["fullbody_a"]),
                    ("Day 2", "Full Body Routine B", exercises["fullbody_b"])]
    elif days == 3:
        if goal == "weight loss":
            schedule = [("Day 1", "Full Body Routine A", exercises["fullbody_a"]),
                        ("Day 2", "HIIT & Cardio Routine", exercises["cardio_hiit"]),
                        ("Day 3", "Full Body Routine B", exercises["fullbody_b"])]
        else:
            schedule = [("Day 1", "Push Focus (Chest, Shoulders, Triceps)", exercises["push"]),
                        ("Day 2", "Pull Focus (Back, Biceps, Rear Delts)", exercises["pull"]),
                        ("Day 3", "Legs & Core Focus", exercises["legs"])]
    elif days == 4:
        schedule = [("Day 1", "Push Workout (Chest/Shoulders/Triceps)", exercises["push"]),
                    ("Day 2", "Pull Workout (Back/Biceps)", exercises["pull"]),
                    ("Day 3", "Legs & Abs Workout", exercises["legs"]),
                    ("Day 4", "Full Body Conditioning", exercises["fullbody_a"])]
    elif days >= 5:
        schedule = [("Day 1", "Push Focus (Chest, Shoulders, Triceps)", exercises["push"]),
                    ("Day 2", "Pull Focus (Back, Biceps)", exercises["pull"]),
                    ("Day 3", "Legs Focus", exercises["legs"]),
                    ("Day 4", "Upper Body Power Split", exercises["fullbody_a"]),
                    ("Day 5", "Lower Body & Core Split", exercises["fullbody_b"])]
        if days == 6:
            schedule.append(("Day 6", "HIIT & Core Conditioning", exercises["cardio_hiit"]))

    # Render split summary card
    html += """
    <div class="plan-card split-summary">
        <h3>📅 Weekly Split Overview</h3>
        <div class="split-grid">
    """
    for day_name, split_title, _ in schedule:
        html += f"""
            <div class="split-day-card">
                <span class="day-badge">{day_name}</span>
                <span class="split-name">{split_title}</span>
            </div>
        """
    html += """
        </div>
    </div>
    """
    
    # Render detailed tables
    for day_name, split_title, ex_list in schedule:
        html += f"""
        <div class="plan-card day-card">
            <h3 class="day-title">💪 {day_name}: {split_title}</h3>
            <div class="table-responsive">
                <table class="workout-table">
                    <thead>
                        <tr>
                            <th>Exercise</th>
                            <th>Sets</th>
                            <th>Reps</th>
                            <th>Rest</th>
                            <th>Coach's Form Cue</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        for name, sets, reps, rest, cue in ex_list:
            # Personalize slightly for home workouts
            if pref == "home":
                name = name.split(" / ")[-1] if " / " in name else name
            else:
                name = name.split(" / ")[0] if " / " in name else name
                
            html += f"""
                        <tr>
                            <td><strong>{name}</strong></td>
                            <td>{sets}</td>
                            <td>{reps}</td>
                            <td>{rest}</td>
                            <td><small class="form-cue">{cue}</small></td>
                        </tr>
            """
        html += """
                    </tbody>
                </table>
            </div>
        </div>
        """
        
    # Student specific tip
    html += """
    <div class="plan-card hostel-hack-card">
        <h3>🎓 Student Fitness Hack</h3>
        <p><strong>Time-saving:</strong> If you are swamped with assignments or exams, don't skip the gym entirely. Do a "supersets" style workout where you pair push and pull exercises back-to-back. You can complete the whole routine in under 30 minutes!</p>
    </div>
    """
    return html


def get_fallback_diet(profile):
    goal = profile.fitness_goal.lower()
    food = profile.food_preference.lower()
    weight = profile.weight
    height = profile.height
    age = profile.age
    gender = profile.gender
    activity = profile.activity_level.lower()
    
    # Calculate BMR
    if gender.lower() == 'male':
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age - 161
        
    # Calculate TDEE
    multiplier = 1.2
    if "light" in activity:
        multiplier = 1.375
    elif "mod" in activity:
        multiplier = 1.55
    elif "very" in activity or "active" in activity:
        multiplier = 1.725
        
    tdee = int(bmr * multiplier)
    
    # Goal adjustments
    if "loss" in goal:
        target_cal = tdee - 500
        protein_g = int(weight * 1.8)
        fat_g = int((target_cal * 0.25) / 9)
        carb_g = int((target_cal - (protein_g * 4) - (fat_g * 9)) / 4)
        goal_text = "Caloric Deficit (Weight Loss)"
    elif "gain" in goal or "muscle" in goal:
        target_cal = tdee + 350
        protein_g = int(weight * 2.0)
        fat_g = int((target_cal * 0.25) / 9)
        carb_g = int((target_cal - (protein_g * 4) - (fat_g * 9)) / 4)
        goal_text = "Caloric Surplus (Muscle / Weight Gain)"
    else:
        target_cal = tdee
        protein_g = int(weight * 1.5)
        fat_g = int((target_cal * 0.25) / 9)
        carb_g = int((target_cal - (protein_g * 4) - (fat_g * 9)) / 4)
        goal_text = "Maintenance (General Fitness)"

    html = f"""
    <div class="plan-header-card">
        <h2>{profile.name}'s Custom AI Diet Recommendations</h2>
        <p class="subtitle">🎯 Goal: {profile.fitness_goal} | 🍎 Preference: {profile.food_preference} | ⚡ Focus: {goal_text}</p>
    </div>
    
    <div class="plan-card calorie-card">
        <h3>📊 Daily Macro Targets</h3>
        <div class="macro-grid">
            <div class="macro-box calories">
                <span class="macro-val">{target_cal} kcal</span>
                <span class="macro-label">Total Calories</span>
            </div>
            <div class="macro-box protein">
                <span class="macro-val">{protein_g}g</span>
                <span class="macro-label">Protein (4 kcal/g)</span>
            </div>
            <div class="macro-box carbs">
                <span class="macro-val">{carb_g}g</span>
                <span class="macro-label">Carbs (4 kcal/g)</span>
            </div>
            <div class="macro-box fats">
                <span class="macro-val">{fat_g}g</span>
                <span class="macro-label">Fats (9 kcal/g)</span>
            </div>
        </div>
    </div>
    """
    
    # Food selection
    breakfast_opt = []
    lunch_opt = []
    dinner_opt = []
    snack_opt = []
    
    if food == "vegetarian":
        breakfast_opt = [
            "<strong>Oatmeal with Milk & Peanut Butter:</strong> 50g oats, 250ml milk, 1.5 tbsp peanut butter, 1 chopped banana. (Protein: 18g, Cal: ~480)",
            "<strong>Paneer Bhurji with Brown Bread:</strong> 80g low-fat paneer cooked with onions, tomatoes, and 2 slices of whole wheat bread. (Protein: 22g, Cal: ~380)"
        ]
        lunch_opt = [
            "<strong>Dal-Rice with Curd & Salad:</strong> 1.5 cups cooked lentils (dal), 1 cup cooked brown/white rice, 1 cup low-fat curd (dahi). (Protein: 20g, Cal: ~500)",
            "<strong>Soya Chunk Curry & Roti:</strong> 50g soya chunks cooked in home spices, 3 thin whole-wheat rotis, side green salad. (Protein: 32g, Cal: ~450)"
        ]
        dinner_opt = [
            "<strong>High-Protein Tofu/Paneer Stir-Fry:</strong> 100g Tofu or Paneer cubed and sauteed with mixed veggies (broccoli, bell peppers, carrots) and 1 tsp oil, served with 1 cup cooked quinoa or rice. (Protein: 22g, Cal: ~450)",
            "<strong>Chickpea (Chole) Salad:</strong> 1.5 cups boiled chickpeas mixed with cucumbers, tomatoes, lemon juice, roasted cumin, and 30g boiled peanuts. (Protein: 18g, Cal: ~400)"
        ]
        snack_opt = [
            "<strong>Roasted Chana (Chickpeas) & Milk:</strong> 1 handful roasted chana + 1 glass hot low-fat milk. (Protein: 15g, Cal: ~280)",
            "<strong>Sprouted Moong Salad:</strong> 1 cup sprouted moong with lemon juice, onions, green chilies. (Protein: 12g, Cal: ~180)"
        ]
    elif food == "non-vegetarian":
        breakfast_opt = [
            "<strong>Scrambled Eggs & Toast:</strong> 3 whole eggs, scrambled with 1 tsp butter, served with 2 slices of whole wheat toast and 1 apple. (Protein: 24g, Cal: ~420)",
            "<strong>Chicken Salad Toast:</strong> 100g shredded boiled chicken breast mixed with 1 tbsp low-fat yogurt, spread over 2 slices of toasted brown bread. (Protein: 32g, Cal: ~350)"
        ]
        lunch_opt = [
            "<strong>Chicken Breast with Rice & Veggies:</strong> 150g grilled/boiled chicken breast, 1 cup cooked rice, steamed broccoli/beans. (Protein: 42g, Cal: ~520)",
            "<strong>Fish Curry & Rice:</strong> 120g grilled or lightly curried fish fillet, 1 cup steamed rice, side salad. (Protein: 28g, Cal: ~450)"
        ]
        dinner_opt = [
            "<strong>Egg Bhurji with Roti:</strong> 3 eggs (2 whole, 1 white) scrambled with onions, tomatoes, green chilies, served with 3 rotis. (Protein: 25g, Cal: ~440)",
            "<strong>Chicken Stir-Fry with Veggies:</strong> 150g chicken breast cubes cooked with bell peppers, onions, carrots, and soy sauce, served with salad. (Protein: 38g, Cal: ~380)"
        ]
        snack_opt = [
            "<strong>Boiled Eggs & Banana:</strong> 2 boiled eggs + 1 medium banana. (Protein: 13g, Cal: ~230)",
            "<strong>Whey Protein Shake / Peanut Butter Toast:</strong> 1 scoop whey in water OR 1 slice whole wheat bread with 1.5 tbsp peanut butter. (Protein: 25g/10g, Cal: ~150/250)"
        ]
    else: # Mixed
        breakfast_opt = [
            "<strong>Eggs and Oats Combo:</strong> 2 boiled eggs + 40g oats cooked in milk with 1 tsp honey. (Protein: 22g, Cal: ~410)",
            "<strong>Paneer Roll:</strong> 70g paneer wrapped in 1 whole-wheat flatbread with mint chutney and onions. (Protein: 18g, Cal: ~380)"
        ]
        lunch_opt = [
            "<strong>Soya chunk Rice or Chicken Rice:</strong> 100g chicken or 50g soya chunks cooked with 1 cup rice and spices. (Protein: 30-35g, Cal: ~500)",
            "<strong>Dal Roti with Omelette:</strong> 1 cup dal, 2 rotis, 2-egg omelette. (Protein: 25g, Cal: ~480)"
        ]
        dinner_opt = [
            "<strong>Grilled Chicken/Paneer & Quinoa:</strong> 120g chicken breast or paneer, served with 1 cup cooked quinoa/rice and green peas. (Protein: 30g, Cal: ~460)",
            "<strong>Egg Curry & Roti:</strong> 2 boiled eggs in spice curry gravy + 3 chapatis. (Protein: 18g, Cal: ~430)"
        ]
        snack_opt = [
            "<strong>Peanut Butter Banana Shake:</strong> 1 glass milk, 1 banana, 1.5 tbsp peanut butter blended together. (Protein: 16g, Cal: ~420)",
            "<strong>Roasted Chana and Almonds:</strong> 30g roasted chana + 10 almonds. (Protein: 10g, Cal: ~220)"
        ]

    # Render Meals
    html += f"""
    <div class="diet-plan-meals">
        <div class="plan-card meal-card">
            <h3 class="meal-title">🍳 Breakfast (Morning Energy)</h3>
            <ul class="meal-list">
                <li>{breakfast_opt[0]}</li>
                <li><span class="or-badge">OR</span> {breakfast_opt[1]}</li>
            </ul>
        </div>
        
        <div class="plan-card meal-card">
            <h3 class="meal-title">🍛 Lunch (Mid-Day Fuel)</h3>
            <ul class="meal-list">
                <li>{lunch_opt[0]}</li>
                <li><span class="or-badge">OR</span> {lunch_opt[1]}</li>
            </ul>
        </div>
        
        <div class="plan-card meal-card">
            <h3 class="meal-title">🏋️ Snacks (Pre/Post Workout)</h3>
            <ul class="meal-list">
                <li>{snack_opt[0]}</li>
                <li><span class="or-badge">OR</span> {snack_opt[1]}</li>
            </ul>
        </div>
        
        <div class="plan-card meal-card">
            <h3 class="meal-title">🥗 Dinner (Recovery Meal)</h3>
            <ul class="meal-list">
                <li>{dinner_opt[0]}</li>
                <li><span class="or-badge">OR</span> {dinner_opt[1]}</li>
            </ul>
        </div>
    </div>
    
    <div class="plan-card budget-hacks-card">
        <h3>🎓 Student Budget & Hostel Hacks</h3>
        <div class="hacks-grid">
            <div class="hack-item">
                <h5>🥚 Cheap Protein Powerhouses</h5>
                <p><strong>Eggs & Soya Chunks:</strong> Soya chunks cost almost nothing and have 52g protein per 100g. Boiling them and adding them to rice/salads is a cheat code for student bodybuilding. Eggs are cheap and easy to store in rooms.</p>
            </div>
            <div class="hack-item">
                <h5>🥛 Mess Food Adjustment</h5>
                <p><strong>Mess Survival:</strong> Hostel mess food is often high in carbs and low in protein. Hack it by eating mess dal and rice, but supplement it by adding a bowl of roasted chana, raw paneer, or 3 boiled eggs bought from outside.</p>
            </div>
            <div class="hack-item">
                <h5>🔌 Electric Kettle Cookery</h5>
                <p><strong>Kettle Hacks:</strong> You can boil eggs, make oatmeal, or boil potatoes right inside an electric kettle in your hostel room. Easy, fast, and no stove needed!</p>
            </div>
        </div>
    </div>
    """
    return html
