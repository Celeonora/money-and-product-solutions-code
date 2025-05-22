# Money-and-Product-Solutions
The Money &amp; Product Solutions team take care of: Performance/kpi and continuous improvement, Incident management,  Financial compliance and audit management SME consultations(including for feature launches and experiments support)

## Deployment

### Streamlit Community Cloud (Recommended)
1. Push this repo to GitHub (if not already).
2. Go to https://streamlit.io/cloud and sign in with GitHub.
3. Click 'New app', select this repo, and set the main file to `dashboard.py`.
4. Click 'Deploy'.

### Local Usage
1. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the dashboard:
   ```bash
   streamlit run dashboard.py
   ```

### Docker (Optional)
1. Build the image:
   ```bash
   docker build -t my-streamlit-app .
   ```
2. Run the container:
   ```bash
   docker run -p 8501:8501 my-streamlit-app
   ```
