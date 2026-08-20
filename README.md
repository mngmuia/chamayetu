# Chama Yetu

GitHub-ready Streamlit and Supabase project for members, contributions, loans, investments, historical payments, administrator settings and BI.

## Clean deployment
1. Create a new empty Supabase project.
2. Run `sql/01_core_schema.sql`.
3. Run `sql/02_extended_modules.sql`.
4. In Supabase Authentication, create `mngmuia@gmail.com` with a new private password.
5. Run `sql/03_bootstrap_administrator.sql`.
6. Run `sql/04_verify_installation.sql`.
7. In Streamlit Community Cloud, set `SUPABASE_URL` and `SUPABASE_ANON_KEY` under App secrets.
8. Deploy using `app.py` as the entry point.

The bootstrap creates Peter Maingi Muia as administrator and links the administrator to Chama Yetu membership ADM-001. Settings are available only when the signed-in profile role is `admin`.

## Local run
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Security
Do not upload `.streamlit/secrets.toml`, passwords, service-role keys or database passwords to GitHub. The example secrets file contains placeholders only.
