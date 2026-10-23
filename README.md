# Arthur's Private Financial Tracker

A green-and-white personal finance web app built with Python, Streamlit, Plotly, and Supabase.

## Features
- Email/password account creation and sign-in
- Add income and expense transactions in IDR
- Monthly income, expense, net cash flow, and savings-rate overview
- Category spending chart and monthly cash-flow chart
- Filter and delete transactions
- Export transactions to CSV for backup
- Row Level Security (RLS): each signed-in user can only access their own rows

## Important privacy note
This is a starter personal-finance app, not a certified banking product. Use a unique password, never publish database keys, and do not commit `.streamlit/secrets.toml`. The app uses Supabase's public/anon key with Row Level Security. Never put a Supabase service-role key in this app.

## Run online (no localhost needed)

### 1. Create a Supabase project
1. Open https://supabase.com and create a project.
2. In **SQL Editor**, run all SQL in `supabase_setup.sql`.
3. In **Project Settings → API** (or API Keys), copy the Project URL and the publishable/anon key.
4. In **Authentication → Providers → Email**, configure email confirmation as you prefer.

### 2. Push this project to GitHub
Create a new repository, then upload these project files. Do not upload secrets.
If using Git:
```bash
git init
git add .
git commit -m "Build Arthur's Private Financial Tracker"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
git push -u origin main
```

### 3. Deploy on Streamlit Community Cloud
1. Open https://share.streamlit.io and sign in with GitHub.
2. Choose **Create app**, select your repository and branch `main`.
3. Set the main file path to `app.py`.
4. Open **Advanced settings → Secrets** and add:
```toml
SUPABASE_URL = "https://YOUR_PROJECT.supabase.co"
SUPABASE_ANON_KEY = "YOUR_SUPABASE_PUBLISHABLE_OR_ANON_KEY"
```
5. Deploy. Streamlit gives you a hosted HTTPS URL. Open that URL from your browser; no local server or localhost is needed.

## Optional local development
If you later want to test locally, create a virtual environment, install `requirements.txt`, add `.streamlit/secrets.toml`, then run `streamlit run app.py`. This is optional; the intended path above is online hosting.

## Progress log
See `PROGRESS.md` for a checklist of project milestones and deployment status.
