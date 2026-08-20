# Chama Yetu Clean Rebuild

A clean Streamlit + Supabase foundation implementing roles, members, contributions, manual M-Pesa verification, loans, investments, monthly returns, balance-weighted member allocation, double-entry accounting scaffolding, reconciliations, reports and audit logs.

## Important
This is a deployable foundation, not a CPA certification tool. Accounting policies, tax mappings and final financial statement formats require review by a practising CPA before production reporting.

## Setup
1. Create a new Supabase project and rotate any previously shared credentials.
2. In Supabase SQL Editor run `sql/001_schema.sql`, then `sql/002_functions_rls.sql`.
3. Create the first user in Supabase Authentication.
4. Edit and run the relevant statements in `sql/003_seed.sql` with the real Auth user UUID.
5. Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and enter the new project URL and anon key.
6. Install: `pip install -r requirements.txt`
7. Run: `streamlit run app.py`

## Deployment
Commit all files except `.streamlit/secrets.toml` to a new GitHub repository. On Streamlit deployment, add `SUPABASE_URL` and `SUPABASE_ANON_KEY` in Secrets.

## Security
Never commit a database password, service-role key or secrets file. The app uses the anon key and Supabase Auth; protected access is enforced with RLS. Complete RLS policies for every additional write workflow before production.

## Production completion checklist
- Add maker-checker screens for loans, investments, journals and reconciliations.
- Add bank statement line import and matching UI.
- Add full journal posting mappings and control accounts.
- Add formal financial statement templates and disclosures reviewed by a CPA.
- Add automated M-Pesa callback processing only after obtaining credentials.
- Add automated tests for all RLS policies and accounting postings.
