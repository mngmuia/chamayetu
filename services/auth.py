from services.db import db

def login(email, password):
    result = db().auth.sign_in_with_password({"email": email, "password": password})
    user = result.user
    rows = db().table("profiles").select("*").eq("id", user.id).limit(1).execute().data or []
    if not rows:
        db().auth.sign_out()
        raise RuntimeError("Login exists but no Chama Yetu profile is linked. Run sql/03_bootstrap_administrator.sql.")
    profile = rows[0]
    if not profile.get("group_id") or not profile.get("member_id"):
        db().auth.sign_out()
        raise RuntimeError("Profile exists but group/member links are missing. Run sql/03_bootstrap_administrator.sql again.")
    return user, profile

def logout():
    db().auth.sign_out()
