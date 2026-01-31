from flask import Flask, render_template, request, redirect, url_for, session, flash
from database.db import get_db_connection

app = Flask(__name__)

# Secret key is needed for session management
# In production, use a secure random key
app.secret_key = 'your_secret_key_here'

@app.route('/')
def home():
    """
    Home page route.
    """
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Login route. Handles both GET (show form) and POST (submit form).
    """
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        try:
            supabase = get_db_connection()
            response = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            # Store session in Flask
            session['user'] = response.user.email
            session['user_id'] = response.user.id # Store UUID
            session['access_token'] = response.session.access_token
            
            flash("Login successful!", "success")
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            error_msg = getattr(e, 'message', str(e))
            flash(f"Login failed: {error_msg}", "error")
        
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    try:
        supabase = get_db_connection()
        supabase.auth.sign_out()
    except:
        pass
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    Registration route. Handles both GET (show form) and POST (submit form).
    """
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash("Passwords do not match!", "error")
            return render_template('register.html')
            
        try:
            supabase = get_db_connection()
            response = supabase.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": {
                        "full_name": name
                    }
                }
            })
            
            # Check if email confirmation is required
            if response.user and response.user.identities == []:
                 flash("User already exists. Please login.", "info")
                 return redirect(url_for('login'))
            
            # Insert user details into the 'users' table
            # Supabase Auth handles authentication, but we store profile info in our own table
            try:
                user_data = {
                    "id": response.user.id,
                    "email": email,
                    "full_name": name
                }
                supabase.table('users').insert(user_data).execute()
            except Exception as db_error:
                # Log this error but don't fail the whole registration if auth worked
                print(f"Database insertion error: {db_error}")

            # If email confirmation is disabled, Supabase returns a session immediately
            if response.session:
                session['user'] = response.user.email
                session['user_id'] = response.user.id # Store UUID
                session['access_token'] = response.session.access_token
                flash("Registration successful! Welcome.", "success")
                return redirect(url_for('dashboard'))
            else:
                flash("Registration successful! Please check your email to verify your account.", "success")
                return redirect(url_for('login'))
            
        except Exception as e:
            error_msg = getattr(e, 'message', str(e))
            flash(f"Registration failed: {error_msg}", "error")
            
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    """
    Dashboard route. Protected area for logged-in users.
    """
    if 'user' not in session:
        flash("Please login to access the dashboard.", "warning")
        return redirect(url_for('login'))
    
    plans = []
    try:
        supabase = get_db_connection(session.get('access_token'))
        user_id = session.get('user_id')
        if user_id:
             response = supabase.table('study_plans').select("*").eq('user_id', user_id).order('created_at', desc=True).execute()
             plans = response.data
    except Exception as e:
        print(f"Error fetching plans: {e}")
        
    return render_template('dashboard.html', user=session['user'], plans=plans)

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    supabase = get_db_connection(session.get('access_token'))

    # Get User ID from session
    user_id = session.get('user_id')
    
    if not user_id:
        # If user is logged in but has no ID in session (legacy session), force logout
        flash("Session expired. Please login again.", "warning")
        return redirect(url_for('logout'))
        
    try:
        if request.method == 'POST':
            profile_data = {
                "id": user_id, 
                "full_name": request.form.get('full_name'),
                "university": request.form.get('university'),
                "degree": request.form.get('degree'),
                "major": request.form.get('major'),
                "current_semester": int(request.form.get('current_semester')) if request.form.get('current_semester') else 0,
                "graduation_year": int(request.form.get('graduation_year')) if request.form.get('graduation_year') else None
            }
            
            print(f"DEBUG: Updating profile for {user_id} with data: {profile_data}")
            
            # Upsert into profiles table
            res = supabase.table('profiles').upsert(profile_data).execute()
            print(f"DEBUG: Upsert result: {res}")
            
            flash("Profile updated successfully!", "success")
            return redirect(url_for('profile'))
            
        # GET request - fetch profile
        profile_response = supabase.table('profiles').select("*").eq('id', user_id).execute()
        profile = profile_response.data[0] if profile_response.data else None
        
        return render_template('profile.html', profile=profile)
        
        return render_template('profile.html', profile=profile)
        
    except Exception as e:
        print(f"DEBUG ERROR in /profile: {e}") # Print to console
        flash(f"Error accessing profile: {str(e)}", "error")
        return redirect(url_for('dashboard'))

@app.route('/create_plan', methods=['GET', 'POST'])
def create_plan():
    if 'user' not in session:
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        title = request.form.get('title')
        goal = request.form.get('goal')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        
        subjects = request.form.getlist('subjects[]')
        topics = request.form.getlist('topics[]')
        
        user_id = session.get('user_id')
        
        try:
            supabase = get_db_connection(session.get('access_token'))
            
            # 1. Create the Plan
            plan_data = {
                "user_id": user_id,
                "title": title,
                "goal": goal,
                "start_date": start_date,
                "end_date": end_date
            }
            plan_res = supabase.table('study_plans').insert(plan_data).execute()
            
            if not plan_res.data:
                raise Exception("Failed to create plan record")
                
            plan_id = plan_res.data[0]['id']
            
            # 2. Add Subjects
            subjects_data = []
            subjects_info_for_ai = [] # Keep track for AI
            
            for i in range(len(subjects)):
                if subjects[i].strip(): # Only add if name is not empty
                    sub_name = subjects[i].strip()
                    sub_topics = topics[i].strip() if i < len(topics) else ""
                    
                    subjects_data.append({
                        "plan_id": plan_id,
                        "name": sub_name,
                        "topics": sub_topics
                    })
                    subjects_info_for_ai.append({'name': sub_name, 'topics': sub_topics})
            
            if subjects_data:
                # Insert subjects and get their IDs back to link tasks
                # Supabase insert with select returns data
                sub_res = supabase.table('subjects').insert(subjects_data).execute()
                created_subjects = sub_res.data
                
                # 3. AI PLAN GENERATION
                # We need to map subject names back to their new IDs to save tasks correctly
                subject_name_to_id = {s['name']: s['id'] for s in created_subjects}
                
                from ai_planner import ManualPlanner
                planner = ManualPlanner()
                generated_schedule = planner.generate_plan(subjects_info_for_ai, start_date, end_date)
                
                tasks_data = []
                for item in generated_schedule:
                    # Find which subject ID this task belongs to
                    s_id = subject_name_to_id.get(item['subject'])
                    if s_id:
                        tasks_data.append({
                            "subject_id": s_id,
                            "description": item['task'],
                            "due_date": item['date'],
                            "is_completed": False
                        })
                
                if tasks_data:
                     supabase.table('tasks').insert(tasks_data).execute()
                
            flash("Study Plan created! AI has generated your schedule.", "success")
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            print(f"Error creating plan: {e}")
            flash(f"Error creating plan: {str(e)}", "error")
            return redirect(url_for('create_plan'))
            
    return render_template('create_plan.html')

if __name__ == '__main__':
    app.run(debug=True)
