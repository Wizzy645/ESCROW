# Future Security Roadmap: Because this is a 3-day MVP, certain enterprise security features were bypassed to prioritize core Interswitch integration. Below is our architectural plan for securing the application before a production launch.

---

## CRITICAL VULNERABILITIES IDENTIFIED

### **1. HARDCODED SECRET KEY (CRITICAL)**
**File:** `app.py:23`
**Vulnerability:** Static, guessable secret allows session forgery.

**Current Code:**
```python
app.secret_key = 'milestone-hackathon-secret-key'
```

**Fix:**
```python
# app.py
app.secret_key = os.getenv('FLASK_SECRET_KEY')
if not app.secret_key:
    raise ValueError("FLASK_SECRET_KEY not set in environment!")
```

Then update your `.env` with a cryptographically secure key:
```bash
python -c "import secrets; print(f'FLASK_SECRET_KEY={secrets.token_hex(32)}')" >> .env
```

---

### **2. NO CSRF PROTECTION (CRITICAL)**
**Files:** All POST routes
**Vulnerability:** Attackers can submit forms from malicious sites to approve payouts, create contracts, etc.

**Fix - Add CSRF to app.py:**
```python
# Add after line 16
from flask_wtf.csrf import CSRFProtect

# Add after line 23
csrf = CSRFProtect(app)
app.config['WTF_CSRF_TIME_LIMIT'] = None  # For long-running sessions
```

**Fix - Update all HTML forms** (add this to EVERY fetch call):

**index.html:244** - Add CSRF token:
```javascript
const response = await fetch(endpoint, {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCsrfToken()
    },
    body: JSON.stringify({ email, password, full_name, role: 'buyer' })
});

// Add this function at the top of <script>
function getCsrfToken() {
    return document.querySelector('meta[name="csrf-token"]')?.content || '';
}
```

**Add to ALL HTML templates** (index.html, buyer_dashboard.html, etc.) in `<head>`:
```html
<meta name="csrf-token" content="{{ csrf_token() }}">
```

**Update EVERY fetch() call** in:
- `buyer_dashboard.html:141, 154, 201, 253`
- `create_contract.html:118`
- `seller_dashboard.html:165, 228`

Add the CSRF header:
```javascript
headers: {
    'Content-Type': 'application/json',
    'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
}
```

---

### **3. NO AUTHORIZATION CHECKS (CRITICAL - FINANCIAL RISK)**
**Files:** `app.py` - All contract/milestone routes
**Vulnerability:** Any logged-in user can approve ANY contract/milestone by knowing the ID.

**Fix - Add authorization to app.py:**
```python
# Add after line 247
@app.route('/milestone/<contract_id>/approve', methods=['POST'])
def approve_milestone(contract_id):
    # AUTHORIZATION CHECK
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    # Verify this user owns this contract
    contract_info = supabase.table('contracts').select('*').eq('id', contract_id).execute()

    if not contract_info.data or len(contract_info.data) == 0:
        return jsonify({"error": "Contract not found"}), 404

    if contract_info.data[0]['buyer_id'] != session['user_id']:
        return jsonify({"error": "You are not authorized to approve this contract"}), 403

    # ... rest of the function
```

**Add similar checks to:**
- `/contract/<contract_id>/fund` - Verify buyer owns contract
- `/milestone/<contract_id>/submit` - Verify seller is assigned to contract
- `/contract/create` - Verify user_id from session, NOT from request body

---

### **4. XSS VULNERABILITIES (HIGH)**
**Files:** `app.py:239-240, 302-304` (Email templates)
**Vulnerability:** Unsanitized user input in emails can inject malicious code.

**Fix - Sanitize all user inputs:**
```python
# Add at top of app.py after line 18
import bleach

# Add sanitization function after line 74
def sanitize_input(text, allow_links=False):
    if allow_links:
        return bleach.clean(text, tags=['a'], attributes={'a': ['href']}, strip=True)
    return bleach.clean(text, tags=[], strip=True)

# Update line 239
email_html = f"""
Your freelancer has submitted Milestone {milestone_num} for review.<br><br>
<b>Deliverable Link:</b> <a href="{sanitize_input(work_link, allow_links=True)}">{sanitize_input(work_link)}</a><br>
<b>Message from Freelancer:</b> {sanitize_input(work_message)}<br><br>
"""
```

---

### **5. NO RATE LIMITING (HIGH)**
**Files:** `app.py` - `/api/login` and `/api/signup`
**Vulnerability:** Brute force attacks, credential stuffing, spam signups.

**Fix - Add rate limiting:**
```python
# Add after line 16
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Add after csrf initialization
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"  # Use Redis in production
)

# Apply to routes
@app.route('/api/signup', methods=['POST'])
@limiter.limit("5 per hour")
def signup():
    # ... existing code

@app.route('/api/login', methods=['POST'])
@limiter.limit("10 per hour")
def login():
    # ... existing code
```

---

### **6. NO SECURITY HEADERS (HIGH)**
**Files:** `app.py`
**Vulnerability:** Missing CSP, clickjacking protection, etc.

**Fix:**
```python
# Add after line 16
from flask_talisman import Talisman

# Add after app initialization (line 23)
csp = {
    'default-src': "'self'",
    'script-src': ["'self'", "'unsafe-inline'", "https://cdn.tailwindcss.com", "https://webpay-ui.k8.isw.la"],
    'style-src': ["'self'", "'unsafe-inline'", "https://cdn.tailwindcss.com"],
    'img-src': ["'self'", "data:", "https:"],
    'connect-src': ["'self'"],
}

Talisman(app,
    content_security_policy=csp,
    force_https=False  # Set to True in production with SSL
)
```

---

### **7. WEAK SESSION SECURITY (HIGH)**
**Files:** `app.py`
**Vulnerability:** Session cookies vulnerable to theft and CSRF.

**Fix:**
```python
# Add after line 23
app.config.update(
    SESSION_COOKIE_SECURE=True,      # Only send over HTTPS
    SESSION_COOKIE_HTTPONLY=True,    # Prevent JS access
    SESSION_COOKIE_SAMESITE='Lax',   # CSRF protection
    PERMANENT_SESSION_LIFETIME=86400  # 24 hours
)
```

---

### **8. API KEYS IN .env FILE (CRITICAL)**
**Files:** `.env`
**Vulnerability:** Your .env file is tracked in Git with REAL credentials exposed!

**Immediate Actions:**
1. **Revoke ALL API keys immediately:**
   - Supabase: Generate new anon key
   - Interswitch: Generate new client credentials
   - Gmail: Generate new app password

2. **Remove .env from Git history:**
```bash
git filter-branch --force --index-filter "git rm --cached --ignore-unmatch .env" --prune-empty --tag-name-filter cat -- --all
git push origin --force --all
```

3. **Verify .gitignore includes .env:**
```bash
echo ".env" >> .gitignore
git add .gitignore
git commit -m "Ensure .env is ignored"
```

---

### **9. INPUT VALIDATION MISSING (MEDIUM)**
**Files:** `app.py` - All routes
**Vulnerability:** No server-side validation of emails, amounts, etc.

**Fix:**
```python
# Add after line 16
from email_validator import validate_email, EmailNotValidError

# Update signup route (line 148)
@app.route('/api/signup', methods=['POST'])
@limiter.limit("5 per hour")
def signup():
    data = request.get_json()

    # Validate email
    try:
        email = validate_email(data.get('email', '').strip()).email
    except EmailNotValidError:
        return jsonify({"error": "Invalid email address"}), 400

    # Validate password strength
    password = data.get('password', '')
    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters"}), 400

    # Sanitize inputs
    full_name = sanitize_input(data.get('full_name', '').strip())

    try:
        user_id = str(uuid.uuid4())
        hashed_pw = generate_password_hash(password)
        supabase.table('users').insert({
            "id": user_id,
            "email": email.lower(),
            "password": hashed_pw,
            "full_name": full_name,
            "role": data.get('role', 'buyer')
        }).execute()
        session['user_id'] = user_id
        session['role'] = data.get('role', 'buyer')
        return jsonify({"message": "Signup successful", "role": session['role']}), 201
    except Exception as e:
        return jsonify({"error": "Signup failed"}), 400  # Don't expose error details!
```

**Add amount validation to create_contract:**
```python
@app.route('/contract/create', methods=['POST'])
def create_contract():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()

    # Validate amount
    try:
        total_amt = int(data.get('total_amount', 0))
        if total_amt <= 0:
            return jsonify({"error": "Amount must be positive"}), 400
        if total_amt > 100000000:  # 100 million naira max
            return jsonify({"error": "Amount exceeds maximum"}), 400
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid amount"}), 400

    # Validate email
    try:
        seller_email = validate_email(data.get('seller_email', '').strip()).email
    except EmailNotValidError:
        return jsonify({"error": "Invalid seller email"}), 400

    # ... rest of function
```

---

### **10. SUPABASE ROW LEVEL SECURITY (CRITICAL)**
**Files:** Supabase Dashboard
**Vulnerability:** Anyone with your anon key can read/modify ALL data.

**Fix - Enable RLS in Supabase Dashboard:**

1. Go to Supabase Dashboard → Authentication → Policies
2. Enable RLS on ALL tables
3. Add these policies:

**Users Table:**
```sql
-- Users can only read their own data
CREATE POLICY "Users can view own data"
ON users FOR SELECT
USING (auth.uid()::text = id);

-- Users can only update their own data
CREATE POLICY "Users can update own data"
ON users FOR UPDATE
USING (auth.uid()::text = id);
```

**Contracts Table:**
```sql
-- Buyers can view their own contracts
CREATE POLICY "Buyers view own contracts"
ON contracts FOR SELECT
USING (buyer_id = auth.uid()::text);

-- Sellers can view contracts assigned to them
CREATE POLICY "Sellers view assigned contracts"
ON contracts FOR SELECT
USING (
  seller_email IN (
    SELECT email FROM users WHERE id = auth.uid()::text
  )
);

-- Only buyers can create contracts
CREATE POLICY "Buyers create contracts"
ON contracts FOR INSERT
WITH CHECK (buyer_id = auth.uid()::text);

-- Only buyers can update their contracts
CREATE POLICY "Buyers update own contracts"
ON contracts FOR UPDATE
USING (buyer_id = auth.uid()::text);
```

**Milestones Table:**
```sql
-- Users can view milestones for their contracts
CREATE POLICY "View own milestones"
ON milestones FOR SELECT
USING (
  contract_id IN (
    SELECT id FROM contracts
    WHERE buyer_id = auth.uid()::text
    OR seller_email IN (SELECT email FROM users WHERE id = auth.uid()::text)
  )
);
```

---

### **11. ERROR INFORMATION LEAKAGE (MEDIUM)**
**Files:** `app.py:160, 170, 195, 217, etc.`
**Vulnerability:** Exposing exception details to users.

**Fix:**
```python
# Replace all `return jsonify({"error": str(e)}), XXX` with:
except Exception as e:
    import logging
    logging.error(f"Error in signup: {str(e)}")
    return jsonify({"error": "An error occurred. Please try again."}), 500
```

---

## SUMMARY OF FILES TO MODIFY

| File | Changes Required |
|------|------------------|
| **app.py** | Add CSRF, rate limiting, Talisman, session config, authorization checks, input validation, sanitization |
| **index.html** | Add CSRF meta tag, update all fetch() calls with CSRF token |
| **buyer_dashboard.html** | Add CSRF meta tag, update all fetch() calls |
| **create_contract.html** | Add CSRF meta tag, update fetch() |
| **seller_dashboard.html** | Add CSRF meta tag, update all fetch() calls |
| **.env** | Regenerate ALL API keys, remove from Git history |
| **Supabase Dashboard** | Enable RLS, add policies |

---

## INTERSWITCH-SPECIFIC SECURITY CONCERNS

### **Payment Amount Tampering**
**Risk:** Client-side JavaScript calculates payment amounts. Attackers can modify values before sending to Interswitch.

**Fix:**
```python
# Server-side validation before initiating payment
@app.route('/contract/<contract_id>/fund', methods=['POST'])
def fund_contract(contract_id):
    # Fetch ACTUAL amount from database
    contract = supabase.table('contracts').select('total_amount').eq('id', contract_id).single().execute()

    # Use SERVER amount, not client amount
    payment_reference = str(uuid.uuid4())
    amount = contract.data['total_amount']  # Don't trust client!

    # Pass to Interswitch
    return jsonify({
        "merchant_code": MERCHANT_CODE,
        "pay_item_id": PAY_ITEM_ID,
        "txn_ref": payment_reference,
        "amount": amount * 100,  # Convert to kobo
    })
```

### **API Key Exposure**
**Risk:** Interswitch credentials visible in browser DevTools.

**Fix:**
```python
# NEVER send API keys to frontend
# Current code at app.py:195 exposes merchant_code and pay_item_id
# These should be used only server-side

# Good: Generate payment session server-side
@app.route('/contract/<contract_id>/init-payment', methods=['POST'])
def init_payment(contract_id):
    # Server generates payment session
    payment_data = {
        "merchant_code": MERCHANT_CODE,  # Never exposed to client
        "amount": get_contract_amount(contract_id)
    }
    # Return only safe data to client
    return jsonify({"payment_ref": payment_data['txn_ref']})
```

### **Webhook Authentication**
**Risk:** Fake payment confirmations from attackers.

**Fix:**
```python
# Add webhook endpoint with signature verification
@app.route('/webhook/interswitch', methods=['POST'])
def interswitch_webhook():
    # Verify webhook signature
    signature = request.headers.get('X-Interswitch-Signature')
    payload = request.get_data()

    expected_sig = hmac.new(
        INTERSWITCH_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(signature, expected_sig):
        return jsonify({"error": "Invalid signature"}), 403

    # Process payment confirmation
    data = request.get_json()
    update_contract_status(data['txn_ref'], data['status'])
    return jsonify({"status": "ok"}), 200
```

---

## PRODUCTION DEPLOYMENT CHECKLIST

### **Before Launch**
- [ ] Rotate ALL API keys (Supabase, Interswitch, Gmail)
- [ ] Generate cryptographically secure `FLASK_SECRET_KEY`
- [ ] Enable HTTPS and set `force_https=True` in Talisman
- [ ] Enable Supabase Row Level Security on all tables
- [ ] Replace in-memory rate limiting with Redis
- [ ] Add server-side amount validation for all payments
- [ ] Implement webhook signature verification for Interswitch
- [ ] Add logging and monitoring (Sentry, Datadog, etc.)
- [ ] Run OWASP ZAP security scan
- [ ] Test all CSRF tokens are working
- [ ] Verify .env is excluded from Git
- [ ] Enable 2FA for admin accounts
- [ ] Set up automated backups for Supabase

### **Monitoring & Alerts**
- [ ] Alert on failed login attempts > 5 per minute
- [ ] Alert on rate limit violations
- [ ] Alert on failed Interswitch transactions
- [ ] Monitor for SQL injection attempts
- [ ] Track unauthorized API access attempts

---

## CONTACT
For security concerns during hackathon demo, contact: [Your Email]

## LAST UPDATED
2026-03-26
