CHAMA YETU FRONTEND PRIVACY PATCH

This patch hides id, group_id, user_id and other UUID/control fields from frontend tables. The fields remain in Supabase.

1. Upload services/ui_helpers.py to the existing services folder.
2. Add this import to app.py:
   from services.ui_helpers import public_frame, MEMBER_COLUMNS, MEMBER_LABELS
3. Replace the existing members() function with the function in app_members_replacement.py.
4. Commit, then reboot Streamlit.

Visible member columns: Member Code, Full Name, Email, Phone, Status and Date Joined.
