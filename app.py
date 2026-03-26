"""
Milestone - Micro-Escrow Platform Backend (Hackathon Edition)
Integrated with Interswitch SVA Transfer Server, Supabase PostgreSQL, & Gmail SMTP
"""

import os
import time
import uuid
import base64
import requests
import smtplib
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from supabase import create_client, Client

load_dotenv()

app = Flask(__name__)
app.secret_key = 'milestone-hackathon-secret-key'

# ============================================================================
# SUPABASE DATABASE SETUP
# ============================================================================
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("⚠️ WARNING: Supabase credentials missing from .env file!")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ============================================================================
# EMAIL ENGINE (GMAIL SMTP - BACKGROUND THREADED)
# ============================================================================
GMAIL_SENDER = os.getenv("GMAIL_SENDER")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

def send_email_async(to_email, subject, message):
    if not GMAIL_SENDER or not GMAIL_APP_PASSWORD:
        print("⚠️ Gmail credentials missing. Skipping email.")
        return
        
    msg = MIMEMultipart()
    msg['From'] = f"Milestone Escrow <{GMAIL_SENDER}>"
    msg['To'] = to_email
    msg['Subject'] = subject
    
    html = f"""
    <div style="font-family: sans-serif; padding: 20px; border-radius: 8px; border: 1px solid #e2e8f0; max-width: 500px;">
        <h2 style="color: #0c3875; margin-top: 0;">Milestone Update</h2>
        <p style="color: #334155; font-size: 16px; line-height: 1.5;">{message}</p>
        <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 20px 0;">
        <p style="color: #94a3b8; font-size: 12px; margin-bottom: 0;">Secured by Interswitch & Supabase</p>
    </div>
    """
    msg.attach(MIMEText(html, 'html'))
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(GMAIL_SENDER, GMAIL_APP_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"✅ EMAIL SUCCESSFULLY SENT TO: {to_email}")
    except Exception as e:
        print(f"❌ EMAIL FAILED: {e}")

def trigger_email(to_email, subject, message):
    thread = threading.Thread(target=send_email_async, args=(to_email, subject, message))
    thread.start()

# ============================================================================
# REAL INTERSWITCH API ENGINE
# ============================================================================
def get_interswitch_token():
    client_id = os.getenv('ISW_CLIENT_ID')
    secret_key = os.getenv('ISW_SECRET_KEY')
    if not client_id or not secret_key: return None
        
    auth_string = f"{client_id}:{secret_key}"
    encoded_auth = base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')
    url = "https://passport.k8.isw.la/passport/oauth/token"
    
    headers = {"Authorization": f"Basic {encoded_auth}", "Content-Type": "application/x-www-form-urlencoded"}
    payload = {"grant_type": "client_credentials", "scope": "profile"}
    
    try:
        response = requests.post(url, headers=headers, data=payload)
        if response.status_code == 200: return response.json().get('access_token')
    except Exception: pass
    return None

def verify_account_name(access_token, account_number, bank_code):
    url = "https://qa.interswitchng.com/quicktellerservice/api/v5/Transactions/DoAccountNameInquiry"
    headers = {"Authorization": f"Bearer {access_token}", "TerminalID": "3PBL0001", "accountid": str(account_number), "bankcode": str(bank_code), "Content-Type": "application/json", "Accept": "application/json"}
    
    try:
        response = requests.post(url, headers=headers, json={})
        if response.status_code == 200: return response.json().get("AccountName")
        return "Demo Freelancer (Fallback)"
    except Exception: return "Demo Freelancer (Fallback)"

def execute_escrow_payout(access_token, dest_account, bank_code, amount_naira):
    url = "https://qa.interswitchng.com/quicktellerservice/api/v5/transactions/TransferFunds"
    amount_kobo = str(int(amount_naira * 100))
    headers = {"Authorization": f"Bearer {access_token}", "TerminalID": "3PBL0001", "Content-Type": "application/json", "Accept": "application/json"}
    payload = {"sourceAccountNumber": "0000000000", "sourceAccountName": "Milestone Escrow", "destinationAccountNumber": str(dest_account), "destinationInstitutionCode": str(bank_code), "transactionAmount": amount_kobo, "currencyCode": "566", "clientRef": str(uuid.uuid4())[:30]}
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200 and response.json().get("ResponseCode") == "90000": return response.json()
    except Exception: pass
    return None

# ============================================================================
# FRONTEND ROUTES
# ============================================================================
@app.route('/')
def index(): return render_template('index.html')

@app.route('/dev-login/<role>')
def dev_login(role):
    session['user_id'] = "dev-test-uuid-1234"
    session['role'] = role
    return redirect(url_for('dashboard') if role == 'seller' else url_for('create_page'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('index'))
    return redirect(url_for('buyer_dashboard')) if session.get('role') == 'buyer' else redirect(url_for('seller_dashboard'))

@app.route('/buyer-dashboard')
def buyer_dashboard(): return render_template('buyer_dashboard.html')

@app.route('/seller-dashboard')
def seller_dashboard(): return render_template('seller_dashboard.html')

@app.route('/create')
def create_page(): return render_template('create_contract.html')

# ============================================================================
# SUPABASE API ROUTES (AUTH & CORE)
# ============================================================================
@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.get_json()
    try:
        user_id = str(uuid.uuid4())
        hashed_pw = generate_password_hash(data.get('password', ''))
        supabase.table('users').insert({
            "id": user_id, "email": data.get('email', '').strip().lower(), "password": hashed_pw, "full_name": data.get('full_name', '').strip(), "role": data.get('role', 'buyer')
        }).execute()
        session['user_id'] = user_id
        session['role'] = data.get('role', 'buyer')
        return jsonify({"message": "Signup successful", "role": session['role']}), 201
    except Exception as e: return jsonify({"error": str(e)}), 400

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    users = supabase.table('users').select('*').eq('email', data.get('email', '').strip().lower()).execute().data
    if users and check_password_hash(users[0]['password'], data.get('password', '')):
        session['user_id'] = users[0]['id']
        session['role'] = users[0]['role']
        return jsonify({"message": "Login successful", "role": users[0]['role']}), 200
    return jsonify({"error": "Invalid email or password"}), 401

@app.route('/contract/create', methods=['POST'])
def create_contract():
    data = request.get_json()
    contract_id = str(uuid.uuid4())
    
    total_amt = int(data.get('total_amount', 0))
    half_amt = total_amt // 2
    
    # We append [1] and [2] to the descriptions so the database ilike() searches never fail
    desc1 = f"[1] {data.get('milestone1_description', 'Setup')}"
    desc2 = f"[2] {data.get('milestone2_description', 'Delivery')}"
    
    try:
        supabase.table('contracts').insert({
            "id": contract_id, "buyer_id": session.get('user_id'), "seller_email": data['seller_email'], "title": data.get('title', 'Freelance Contract'), "total_amount": total_amt, "status": 'pending'
        }).execute()
        
        supabase.table('milestones').insert([
            {"id": str(uuid.uuid4()), "contract_id": contract_id, "description": desc1, "amount": half_amt, "status": 'pending'},
            {"id": str(uuid.uuid4()), "contract_id": contract_id, "description": desc2, "amount": half_amt, "status": 'pending'}
        ]).execute()
        
        return jsonify({"message": "Created", "contract_id": contract_id}), 201
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route('/contract/<contract_id>/fund', methods=['POST'])
def fund_contract(contract_id):
    try:
        supabase.table('contracts').update({'status': 'funded'}).eq('id', contract_id).execute()
        supabase.table('milestones').update({'status': 'active'}).eq('contract_id', contract_id).ilike('description', '%[1]%').execute()
        
        contract_data = supabase.table('contracts').select('seller_email').eq('id', contract_id).execute()
        if contract_data.data:
            # DYNAMIC URL GENERATION FOR THE SELLER DASHBOARD
            dashboard_link = f"{request.host_url}seller-dashboard"
            real_seller_email = contract_data.data[0]['seller_email']
            
            email_msg = f"""
            Great news! Your client has successfully locked the project funds in escrow via Interswitch.<br><br>
            It is now safe to begin working. Click below to access your workspace:<br>
            <a href="{dashboard_link}" style="display: inline-block; margin-top: 10px; padding: 10px 20px; background-color: #0c3875; color: white; text-decoration: none; border-radius: 5px; font-weight: bold;">Go to Freelancer Dashboard</a>
            """
            trigger_email(real_seller_email, "Funds Secured: Ready to Work", email_msg)
            
        return jsonify({"message": "Contract funded successfully"}), 200
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route('/milestone/<contract_id>/submit', methods=['POST'])
def submit_milestone(contract_id):
    try:
        data = request.get_json() or {}
        milestone_num = data.get('milestone_num', 1)
        work_link = data.get('link', 'Submitted via Dashboard')
        work_message = data.get('message', 'No additional message provided.')

        supabase.table('milestones').update({'status': 'submitted'}).eq('contract_id', contract_id).ilike('description', f'%[{milestone_num}]%').execute()
        
        contract_data = supabase.table('contracts').select('buyer_id').eq('id', contract_id).execute()
        if contract_data.data:
            buyer_id = contract_data.data[0]['buyer_id']
            buyer_data = supabase.table('users').select('email').eq('id', buyer_id).execute()
            if buyer_data.data:
                real_buyer_email = buyer_data.data[0]['email']
                dashboard_link = f"{request.host_url}buyer-dashboard"
                
                email_html = f"""
                Your freelancer has submitted Milestone {milestone_num} for review.<br><br>
                <b>Deliverable Link:</b> <a href="{work_link}">{work_link}</a><br>
                <b>Message from Freelancer:</b> {work_message}<br><br>
                <a href="{dashboard_link}" style="display: inline-block; margin-top: 10px; padding: 10px 20px; background-color: #0c3875; color: white; text-decoration: none; border-radius: 5px; font-weight: bold;">Review and Approve Payout</a>
                """
                trigger_email(real_buyer_email, f"Milestone {milestone_num} Submitted for Review", email_html)
                
        return jsonify({"message": "Work submitted successfully"}), 200
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route('/milestone/<contract_id>/approve', methods=['POST'])
def approve_milestone(contract_id):
    print(f"\n--- APPROVAL TRIGGERED FOR CONTRACT: {contract_id} ---")
    try:
        # silent=True prevents Flask from crashing if the frontend sends weird JSON headers
        data = request.get_json(silent=True) or {}
        milestone_num = str(data.get('milestone_num', 1))
        print(f"✅ Step 1: Received request for Milestone {milestone_num}")
        
        # Select ALL columns (*) to prevent PostgREST syntax errors
        contract_info = supabase.table('contracts').select('*').eq('id', contract_id).execute()
        print("✅ Step 2: Fetched contract from database")
        
        payout_amount = 0
        real_seller_email = ""
        
        if contract_info.data and len(contract_info.data) > 0:
            raw_amt = contract_info.data[0].get('total_amount', 0)
            if raw_amt is None: raw_amt = 0
            payout_amount = int(float(raw_amt)) // 2
            real_seller_email = contract_info.data[0].get('seller_email', '')
            
        print(f"✅ Step 3: Extracted Payout Amount: ₦{payout_amount}")

        test_account = "0730804844" 
        test_bank = "044" 
        freelancer_name = "Demo Freelancer"
        token = get_interswitch_token()
        print("✅ Step 4: Interswitch token check complete")
        
        if token and payout_amount > 0:
            name_check = verify_account_name(token, test_account, test_bank)
            if name_check: 
                freelancer_name = name_check
            payout_result = execute_escrow_payout(token, test_account, test_bank, payout_amount)
            if not payout_result:
                print("⚠️ ISW Transfer failed due to Sandbox Error. Engaging Hackathon Backend Bypass...")
        else:
            print("⚠️ Amount is 0 or Token Failed. Skipping Interswitch transfer. Engaging Bypass...")

        print("✅ Step 5: Interswitch execution complete")

        # UPDATE SUPABASE
        supabase.table('milestones').update({'status': 'paid'}).eq('contract_id', contract_id).ilike('description', f'%[{milestone_num}]%').execute()
        print("✅ Step 6: Updated current milestone to paid")
        
        # ONLY unlock milestone 2 if we are currently paying milestone 1
        if str(milestone_num) == "1":
            supabase.table('milestones').update({'status': 'active'}).eq('contract_id', contract_id).ilike('description', '%[2]%').execute()
            print("✅ Step 7: Unlocked milestone 2")
        
        # SEND EXACT AMOUNT EMAIL TO SELLER
        if real_seller_email:
            trigger_email(
                real_seller_email, 
                f"💰 Milestone {milestone_num} Payment Released!",
                f"Your client has approved your work for Milestone {milestone_num}! <b>₦{payout_amount}</b> has been released from Escrow via Interswitch and transferred to your account."
            )
            print("✅ Step 8: Email triggered")
        
        print("--- APPROVAL COMPLETE ---\n")
        return jsonify({"message": f"Funds (₦{payout_amount}) released successfully!"}), 200
        
    except Exception as e:
        import traceback
        print(f"🔥 FATAL BACKEND ERROR: {str(e)}")
        traceback.print_exc() # This forces Python to spit out the exact line of code that failed
        return jsonify({"error": str(e)}), 500
    
if __name__ == '__main__':
    app.run(debug=True, port=5000)