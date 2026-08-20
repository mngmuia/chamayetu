from services.db import client

def login(email, password):
    result = client().auth.sign_in_with_password({"email": email, "password": password})
    user = result.user
    profile = client().table("profiles").select("*").eq("user_id", user.id).single().execute().data
    return user, profile

def logout():
    client().auth.sign_out()
