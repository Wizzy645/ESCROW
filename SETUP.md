# Setup Guide - Milestone Escrow Platform

## Prerequisites
- Python 3.8 or higher
- Supabase account
- pip (Python package manager)

## Installation Steps

### 1. Clone or Download the Project
```bash
cd milestone
```

### 2. Create Virtual Environment (Recommended)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Set Up Supabase

#### a. Create a Supabase Project
1. Go to https://supabase.com
2. Create a new project
3. Note your project URL and anon key

#### b. Create Database Tables
Run this SQL in your Supabase SQL Editor:

```sql
-- Users table
CREATE TABLE IF NOT EXISTS public."Users" (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT UNIQUE NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('buyer', 'seller')),
    full_name TEXT,
    bank_account_number TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW())
);

-- Contracts table
CREATE TABLE IF NOT EXISTS public."Contracts" (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    buyer_id UUID NOT NULL REFERENCES public."Users"(id) ON DELETE CASCADE,
    seller_email TEXT NOT NULL,
    title TEXT NOT NULL,
    total_amount INTEGER NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('pending', 'funded', 'completed')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW())
);

-- Milestones table
CREATE TABLE IF NOT EXISTS public."Milestones" (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contract_id UUID NOT NULL REFERENCES public."Contracts"(id) ON DELETE CASCADE,
    description TEXT NOT NULL,
    amount INTEGER NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('pending', 'active', 'submitted', 'paid')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW())
);

-- Enable Row Level Security
ALTER TABLE public."Users" ENABLE ROW LEVEL SECURITY;
ALTER TABLE public."Contracts" ENABLE ROW LEVEL SECURITY;
ALTER TABLE public."Milestones" ENABLE ROW LEVEL SECURITY;

-- RLS Policies for Users table
CREATE POLICY "Users can view their own data"
    ON public."Users" FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "Users can update their own data"
    ON public."Users" FOR UPDATE
    USING (auth.uid() = id);

-- RLS Policies for Contracts
CREATE POLICY "Buyers can view their contracts"
    ON public."Contracts" FOR SELECT
    USING (buyer_id = auth.uid());

CREATE POLICY "Sellers can view their contracts"
    ON public."Contracts" FOR SELECT
    USING (seller_email = (SELECT email FROM public."Users" WHERE id = auth.uid()));

CREATE POLICY "Authenticated users can create contracts"
    ON public."Contracts" FOR INSERT
    WITH CHECK (auth.role() = 'authenticated');

-- RLS Policies for Milestones
CREATE POLICY "Users can view milestones for their contracts"
    ON public."Milestones" FOR SELECT
    USING (
        contract_id IN (
            SELECT id FROM public."Contracts"
            WHERE buyer_id = auth.uid()
            OR seller_email = (SELECT email FROM public."Users" WHERE id = auth.uid())
        )
    );
```

### 5. Configure Environment Variables

#### a. Generate Secret Key
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

#### b. Create .env File
Copy `.env.example` to `.env` and fill in your values:

```bash
# Windows
copy .env.example .env

# Linux/Mac
cp .env.example .env
```

#### c. Edit .env File
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key-here
FLASK_SECRET_KEY=your-generated-secret-key-here
FLASK_ENV=development
```

### 6. Run the Application
```bash
python app.py
```

The application will start on http://localhost:5000

## Testing the Application

### Quick Test with Dev Login
1. Open http://localhost:5000
2. Click "Test as Buyer" or "Test as Seller" buttons
3. This bypasses authentication for quick testing

### Test Real Authentication
1. Open http://localhost:5000
2. Click "Sign Up" tab
3. Enter:
   - Full Name: John Doe
   - Email: test@example.com
   - Password: Must meet strength requirements
     - At least 8 characters
     - Uppercase, lowercase, number, special char
4. Click "Sign Up as Buyer"
5. You'll be redirected to the contract creation page

### Test Password Requirements
Try these passwords to see validation:
- ❌ `weak` - Too short
- ❌ `password` - No uppercase, number, special char
- ❌ `Password1` - No special character
- ✅ `SecurePass123!` - Meets all requirements

### Test Rate Limiting
1. Try logging in with wrong password 5 times
2. Account will be locked for 15 minutes
3. Error message will show remaining lockout time

## Security Features Implemented

✅ Password strength validation
✅ Rate limiting (5 signups/hour, 10 logins/hour)
✅ Account lockout after 5 failed attempts
✅ CSRF protection
✅ Security headers (CSP, X-Frame-Options, etc.)
✅ Input validation and sanitization
✅ Secure session management
✅ Audit logging
✅ Generic error messages (no user enumeration)

## Production Deployment

### Important Changes for Production:

1. **Enable HTTPS**
   - Update `app.py` line 76: `force_https=True`
   - Configure SSL certificate

2. **Use Redis for Rate Limiting**
   ```python
   # In app.py, update Limiter configuration:
   storage_uri="redis://localhost:6379"
   ```

3. **Update Session Settings**
   - Already configured for production
   - Ensure you're using HTTPS

4. **Environment Variables**
   - Set strong `FLASK_SECRET_KEY`
   - Set `FLASK_ENV=production`
   - Never commit `.env` to version control

5. **Monitoring**
   - Set up log monitoring
   - Configure alerts for security events
   - Review `app.log` regularly

## Troubleshooting

### "Missing Supabase credentials"
- Check your `.env` file exists
- Verify `SUPABASE_URL` and `SUPABASE_KEY` are correct

### "ModuleNotFoundError"
- Activate virtual environment
- Run `pip install -r requirements.txt`

### Rate Limit Errors
- Wait for the cool-down period
- In development, restart the server to reset

### Session Issues
- Clear browser cookies
- Check `FLASK_SECRET_KEY` is set
- Verify session configuration

### Database Errors
- Check Supabase tables are created
- Verify Row Level Security policies
- Check user permissions

## Additional Resources

- [SECURITY.md](./SECURITY.md) - Detailed security documentation
- [Supabase Documentation](https://supabase.com/docs)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)

## Support

For security issues, please review SECURITY.md first.
For other issues, check the troubleshooting section above.

## License

This is a hackathon/educational project. Use at your own risk in production.
