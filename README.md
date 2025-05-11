# Transcript Analysis Application

This application provides a Streamlit-based interface for interacting with a scheduling AI assistant that analyzes user-uploaded or database-retrieved transcripts to extract meeting times, availability, preferences, and action items. It includes secure login functionality and conditionally renders personalized content based on user-specific data.

---

## 🔧 Setup Instructions

> **Note**: Python 3.12 is recommended for compatibility with all features and dependencies.

1. **[Optional] Create and activate a virtual environment**
   - This is recommended but optional based on your development setup.
   ```bash
   # Linux / Mac
   python3.12 -m venv venv
   source venv/bin/activate

   # Windows
   python -m venv venv
   .\venv\Scripts\activate
   ```

2. **Navigate to the application source directory**
   > The application_source directory is the source root.
   ```bash
   cd /application_source
   ```

3. **Set the PYTHONPATH to include the application source**
   - This ensures all modules can be properly located and imported.

   ```bash
   # Linux / Mac
   export PYTHONPATH=$(pwd)

   # Windows (Command Prompt)
   set PYTHONPATH=%cd%

   # Windows (PowerShell)
   $env:PYTHONPATH = (Get-Location).Path
   ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Secrets configuration**
   - Manually create a folder named `secrets` in the root directory (in application_source).
   - Place the provided secret files (you will receive them separately) inside the `secrets/` folder.

---

## 🚀 Application Run Instructions

To launch the application:

```bash
streamlit run ui/home_page.py --server.port 8501
```

> After running the command, a local URL (usually `http://localhost:8501`) will be generated. You can open this in your web browser to access the application UI.

> ⚠️ **Note**: If you are running streamlit for first time in new environment, you might be prompted to enter email id. This can be skipped by pressing [Enter] key.
---

## 🧑‍💻 Usage Instructions

1. **Login**
   - The application opens with a login screen.
   - Use the credentials:
     - `SR001`
     - `SR002`
   - The password field accepts any input (it's a placeholder and not enforced currently).

2. **Transcript Analysis Options**
   - After login, you'll be redirected to the second page.
   - You can either:
     - Upload a transcript manually.
     - Dummy transcripts can be found in folder `data/demo_data/test`
     - Proceed with analysis using existing data from the database.
     - The analysis results will be shown for top 3 customers (no matter how many transcripts are uploaded)
   > ⚠️ **Note**: The analysis option will only be available if transcripts exist for the user in the database. New users won’t see this option.

3. **Post Analysis Flow**
   - After the analysis is completed, the application will guide you to a page that displays available time slots.

---

Feel free to fork, clone, and extend the project as needed. For any setup issues or feature requests, please contact the development team.