# MORQEVA — Cloud deployment

This is the only deployment path you need. After it is online, use the Streamlit URL on laptop and phone; you do not need to launch MORQEVA with PowerShell for normal use.

## 1. Create the cloud database (Supabase)
1. Create a free Supabase project.
2. Open **SQL Editor → New query**.
3. Paste the contents of `db/schema.sql` and click **Run**.
4. In Supabase, click **Connect** and copy the **Session pooler** PostgreSQL connection string (port **5432**). Do not use the Transaction pooler on port 6543 for this Streamlit/SQLAlchemy app.
5. Replace the password placeholder in that URL with your database password. If the password contains reserved URL characters, percent-encode them.

## 2. Create the Gemini key
1. Create a Gemini API key in Google AI Studio.
2. MORQEVA uses Gemini to turn one seed/title into research, facts, 5 hooks, exactly 10 scenes, English/Darija captions, Flow prompts, Vibes prompts, Symphony fallback prompts and SFX/music cues.
3. **Verified Real / Folklore** mode uses Google Search grounding. Current Gemini API rules require a billing-enabled project for Search grounding. Google currently includes the first 5,000 Gemini 3.x grounded search requests per month on the paid tier before per-search charges. Keep billing alerts enabled.

## 3. Put the code on GitHub
1. Create a repository called `morqeva`.
2. Upload the **contents** of this project folder to the repository root.
3. Never upload `.streamlit/secrets.toml` or any API/database secret.

## 4. Deploy on Streamlit Community Cloud
1. Sign in to Streamlit Community Cloud and connect your GitHub account.
2. Click **Create app**.
3. Select the `morqeva` repository and entrypoint `app.py`.
4. Choose the app URL `morqeva.streamlit.app` if available (or the closest available name).
5. Open **Advanced settings → Secrets** and paste:

```toml
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"
GEMINI_MODEL = "gemini-3.6-flash"
ENABLE_GROUNDING = true

[connections.sql]
url = "postgresql+psycopg2://YOUR_SUPABASE_SESSION_POOLER_URL"
```

Example format only:
`postgresql+psycopg2://postgres.PROJECT_REF:PASSWORD@aws-0-REGION.pooler.supabase.com:5432/postgres`

6. Click **Deploy**.

## 5. Keep MORQEVA private
In Streamlit app settings → **Sharing** → **Who can view this app** → choose **Only specific people can view this app**. Add the emails that should have access.

## Result
Your Streamlit URL is now MORQEVA. Open the same URL on desktop or phone. New story blueprints and production status are stored in the cloud PostgreSQL database, so they persist across devices and restarts.
