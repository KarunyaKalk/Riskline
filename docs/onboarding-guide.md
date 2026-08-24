# Startup Team Onboarding Guide (10-Minute Admin Quickstart)

Welcome to **Riskline**! Follow this quickstart guide to set up your team's organization workspace and evaluate your first deployment change in 10 minutes.

---

## Step 1: Provision Your Organization (1 Minute)
1. Open the Riskline web application in your browser.
2. Click **Create Organization**.
3. Fill in your **Organization Name** (e.g., `Acme Engineering`) and **Admin Email**.
4. Click **Provision Organization**. You are automatically signed in as Organization Admin.

---

## Step 2: Invite Your Teammates (3 Minutes)
1. Navigate to **Org Settings** (`/settings`).
2. Enter your teammate's work email and select their role (`Engineer`, `Business Ops`, `Admin`, or `Viewer`).
3. Click **Issue 48-Hr Invite Token**.
4. Copy the generated invite URL and share it with your teammate.

---

## Step 3: Submit Your First Change for AI Risk Analysis (3 Minutes)
1. Navigate to **Changes & Risk** (`/changes`).
2. Click **+ Submit New Change**.
3. Either:
   - Type a title (e.g. `Upgrade Postgres Schema / Rotate Auth Keys`) and paste migration details into the description box, OR
   - Drag and drop an architectural specification PDF file.
4. Click **Submit Change for Risk Analysis**.

---

## Step 4: Review Risk Breakdown & Action Checklist (2 Minutes)
1. In the **Changes** table, click **View Risk Breakdown**.
2. Review the side-by-side cards:
   - **Technical Summary**: Detailed breakdown for SREs and Engineers.
   - **Business Summary**: Risk exposure summary for Executives and Business Ops.
3. Review the **Recommended Action Checklist** to mitigate deployment risk.

---

## Step 5: Ask Questions via AI Assistant (1 Minute)
1. Click **AI Risk Assistant** in the top navigation header.
2. Select your desired Audience Mode (**Tech**, **Business**, or **Auto**).
3. Type questions such as *"What is the rollback procedure if key rotation fails?"* to stream grounded answers.
