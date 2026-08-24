# Power BI Integration Setup Guide

This document walks through connecting **Microsoft Power BI Desktop** to the DevOps Risk Platform to build live executive dashboards and report on deployment risk trends.

---

## 1. Prerequisites
- An active account with **Admin** permissions in your DevOps Risk Platform organization.
- **Microsoft Power BI Desktop** installed on your workstation.

---

## 2. Step 1 — Issue a Read-Only Power BI API Key
1. Log in to the DevOps Risk Platform web dashboard.
2. Navigate to **Org Settings** (`/settings`).
3. Under **Organization Settings & Invites**, use the API Key Generator or issue a POST request to:
   ```http
   POST /api/v1/export/api-keys
   Content-Type: application/json
   Authorization: Bearer <your_admin_jwt>

   {
     "name": "Power BI Executive Dashboard Key"
   }
   ```
4. Copy the generated secret key (starts with `rk_live_...`). Save this securely; it is shown only once.

---

## 3. Step 2 — Connect Power BI Desktop to the API Feed

### Option A: Using Web Data Source with Custom Headers (Recommended)
1. Open **Power BI Desktop**.
2. Click **Get Data** -> **Web**.
3. Select **Advanced**.
4. In **URL Parts**, enter:
   `http://localhost:8000/api/v1/export/power-bi` (or your deployed server domain `https://risk.yourcompany.com/api/v1/export/power-bi`).
5. Under **HTTP request header parameters**, add:
   - Header: `X-API-Key`
   - Value: `rk_live_YOUR_API_KEY_HERE`
6. Click **OK**.

### Option B: Using Query Parameter (Alternative for simple URL refresh)
1. In Power BI Desktop, click **Get Data** -> **Web**.
2. Select **Basic**.
3. Enter the URL with the `api_key` parameter:
   `http://localhost:8000/api/v1/export/power-bi?api_key=rk_live_YOUR_API_KEY_HERE`
4. Click **OK**.

---

## 4. Step 3 — Data Transformation & Modeling
Power BI will parse the returned JSON into record tables:
- **`summary`**: Single row with `total_changes`, `avg_risk_score`, `high_risk_count`, `deployed_count`.
- **`changes`**: Table containing `change_id`, `title`, `status`, `risk_score`, `risk_level`, `technical_summary`, `business_summary`, `created_at`.
- **`milestones`**: Table containing `milestone_id`, `title`, `status`, `progress_pct`, `target_date`.

1. Click **Transform Data** (Power Query Editor).
2. Expand the `changes` list into a table (`To Table`).
3. Click the expand icon on the column header to extract fields (`title`, `risk_score`, `risk_level`, `created_at`).
4. Set column data types:
   - `risk_score` -> Decimal Number
   - `created_at` -> Date/Time
5. Click **Close & Apply**.

---

## 5. Step 4 — Schedule Automatic Data Refresh
In Power BI Service (Cloud):
1. Publish your report to your workspace.
2. Go to **Dataset Settings** -> **Data Source Credentials**.
3. Select **Anonymous** (since authentication is handled via the embedded `X-API-Key` header or query string).
4. Enable **Scheduled Refresh** (e.g. Daily or Hourly).
