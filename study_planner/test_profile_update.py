from database.db import get_db_connection
import os
from dotenv import load_dotenv

load_dotenv()

def test_upsert():
    supabase = get_db_connection()
    # Let's try to find a user first
    try:
        user_res = supabase.table('users').select("*").limit(1).execute()
        if not user_res.data:
            print("No users found in 'users' table. Register a user first.")
            return
            
        user_id = user_res.data[0]['id']
        print(f"Found user_id: {user_id}")
        
        profile_data = {
            "id": user_id,
            "full_name": "Test Update",
            "university": "Test Uni",
            "degree": "Test Degree",
            "major": "Test Major",
            "current_semester": 1,
            "graduation_year": 2026
        }
        
        print(f"Attempting upsert with: {profile_data}")
        res = supabase.table('profiles').upsert(profile_data).execute()
        print(f"Upsert Response: {res}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_upsert()
