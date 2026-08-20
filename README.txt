CHAMA YETU INVESTMENT UPGRADE

1. Run investment_upgrade.sql in Supabase SQL Editor.
2. Confirm the signed-in auth.users ID has a public.profiles row with role='admin' and is_active=true.
3. Replace the repository app.py with the supplied app.py.
4. Add SUPABASE_URL and SUPABASE_ANON_KEY to Streamlit secrets.
5. Add the GL accounts and investment_posting_groups before using automatic GL posting.

The app calls post_investment_transaction only when 'Post transaction to the General Ledger' is selected. Add that database RPC after configuring the Chama's chart of accounts and posting groups. Draft/approved investment transactions can be captured immediately.
