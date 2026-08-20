# Add near the top of app.py:
from services.ui_helpers import public_frame, MEMBER_COLUMNS, MEMBER_LABELS

# Replace the existing members() function with this:
def members():
    st.title("Members")
    with st.form("member_form", clear_on_submit=True):
        left, right = st.columns(2)
        full_name = left.text_input("Full Name")
        membership_number = right.text_input("Member Code")
        email = left.text_input("Email")
        phone = right.text_input("Phone")
        if st.form_submit_button("Create member"):
            add("members", {
                "group_id": G,
                "full_name": full_name.strip(),
                "membership_number": membership_number.strip().upper(),
                "email": email.strip().lower() or None,
                "phone": phone.strip() or None,
                "status": "active",
            })
            st.success("Member created")
            st.rerun()
    member_rows = data("members", {"group_id": G}, "membership_number")
    display_members = public_frame(member_rows, preferred=MEMBER_COLUMNS, rename=MEMBER_LABELS)
    st.dataframe(
        display_members,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Member Code": st.column_config.TextColumn(width="small"),
            "Full Name": st.column_config.TextColumn(width="medium"),
            "Email": st.column_config.TextColumn(width="medium"),
            "Phone": st.column_config.TextColumn(width="small"),
            "Status": st.column_config.TextColumn(width="small"),
            "Date Joined": st.column_config.DateColumn(format="DD MMM YYYY"),
        },
    )
