# Milestone - Micro-Escrow Freelance Platform

## Live Demo
**https://escrow-q0lk.onrender.com**
*(Note: As this MVP is hosted on Render's Free Tier, outbound SMTP email notifications are firewalled by the provider. However, the UI state synchronization and Interswitch integrations are fully functional on the live link. To see the real-time email functionality in action, please run the app locally using the setup instructions below.)*

## 🎨 Figma Design
**https://www.figma.com/design/pPGIdJqzYU721o34s14xRA/Milestone-Project?node-id=0-1&p=f&t=yC51yFRCeknu2Rcy-0**
*Our complete UI/UX design process, wireframes, and high-fidelity interactive prototypes.*

## Project Overview
Milestone is an automated micro-escrow platform designed to solve the biggest problem in the African freelance economy: Trust. Freelancers fear working without upfront payment, and clients fear paying upfront for incomplete work. Milestone solves this by securing client funds upfront via Interswitch, and automatically releasing payouts to the freelancer via the Quickteller Transfer API once milestones are approved. 

*Built for the Enyata Buildathon 2026.*

## Team Contributions

As required by the Enyata Buildathon guidelines, below is the detailed breakdown of our team's technical and non-technical contributions:

* **Olamide Adesina - Backend Engineer & Integration Lead**
  * **Technical:** Architected the Python/Flask backend and integrated Supabase (PostgreSQL) for contract state management. 
  * **Technical:** Engineered the core financial engine using Interswitch APIs (Web Checkout for Pay-Ins, and a fault-tolerant Graceful Degradation S2S Transfer API integration for Payouts to bypass Sandbox limitations).
  * **Technical:** Built the asynchronous background-threaded SMTP engine for real-time email notifications. Wired the Vanilla JavaScript frontends to the backend API.

* **Ayomide Oyewole - Product Designer & UI/UX Lead**
  * **Non-Technical / Design:** Led product research and designed the end-to-end user experience to prioritize trust and simplicity. 
  * **Design:** Created the low-fidelity wireframes and high-fidelity interactive Designs entirely in Figma. 
  * **Technical:** Directed the frontend visual architecture, ensuring the final HTML and TailwindCSS implementation Semi-perfect match with the Figma design system across both the Buyer and Seller dashboards.

## Judge's Interactive Walkthrough (How to Test)

To experience the real-time sync of the Micro-Escrow workflow, please open **two side-by-side tabs in the same browser window** (do not use Incognito, as the MVP utilizes `localStorage` for real-time state synchronization between the two dashboards).

### Step 1: The Setup
* **Tab 1 (Buyer):** Open `https://escrow-q0lk.onrender.com/create`
* **Tab 2 (Seller):** Open `https://escrow-q0lk.onrender.com/seller-dashboard`

### Step 2: The Rules (Contract Creation)
* **Action (Tab 1):** On the Buyer screen, enter a test email, set the total project price in Naira (e.g., ₦150,000), and define the two milestones. Click "Create Escrow Contract".
* **Context:** The system generates the contract and forces the Buyer to secure the funds before the Seller's workspace is activated.

### Step 3: The Lock-In (Fund Escrow)
* **Action (Tab 1):** The Buyer clicks to fund the escrow wallet.
* **Action:** Enter the Interswitch test card details into the Web Checkout popup to lock the funds safely. 
* **Result:** The backend secures the funds. Switch to **Tab 2 (Seller)**—you will see the dashboard has instantly unlocked and updated in real-time, notifying the Freelancer that it is safe to begin working.

### Step 4: The Work (Seller Submission)
* **Action (Tab 2):** Click "Submit Milestone 1 for Approval". Paste a test link (e.g., a Vercel link) and a message into the modal, then send it.
* **Result:** The Seller's button locks to prevent spam, and **Tab 1 (Buyer)** instantly updates to show 50% completion.

### Step 5: The Payout (Buyer Approval)
* **Action (Tab 1):** Click the blue "Approve & Payout Milestone 1" button.
* **Result:** The backend triggers the Interswitch Transfer API (bypassing the sandbox restriction gracefully via our fallback protocol), routing funds to the Seller. Both dashboards instantly update to show Milestone 1 as "Paid".

### Step 6: Project Completion
* **Action (Tab 2):** Repeat the submission process for the final milestone.
* **Action (Tab 1):** The Buyer approves the final milestone.
* **Result:** Both dashboards flash green and update to "COMPLETED". The escrow balance drops to ₦0.00 as all funds have been safely distributed.

## Security Architecture
We have included a `SECURITY.md` file in this repository detailing our future roadmap for production-level security implementations (including CSRF tokens, strict Row Level Security in Supabase, and CSP headers) that were deferred to prioritize core API integrations during the 72-hour MVP window.

## 🛠 Built With
* **Backend:** Python, Flask
* **Database:** Supabase (PostgreSQL)
* **Payment Infrastructure:** Interswitch (Web Checkout API & Quickteller Transfer API)
* **Frontend:** HTML5, Vanilla JavaScript, TailwindCSS
* **Design & Prototyping:** Figma
* **Notifications:** smtplib (Gmail SMTP)

## ⚙️ Local Setup Instructions
If judges wish to run this application locally to test the threaded email engine:

1. Clone the repository: 
   `git clone https://github.com/[YOUR_GITHUB_USERNAME]/[YOUR_REPO_NAME].git`
2. Navigate into the directory: 
   `cd [YOUR_REPO_NAME]`
3. Install the required Python dependencies: 
   `pip install -r requirements.txt`
4. Create a `.env` file in the root directory with the following variables (keys have been revoked/hidden for security):
   ```env
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_key
   ISW_CLIENT_ID=your_interswitch_client_id
   ISW_SECRET_KEY=your_interswitch_secret
   GMAIL_SENDER=your_email@gmail.com
   GMAIL_APP_PASSWORD=your_app_password
   FLASK_SECRET_KEY=your_secret_key