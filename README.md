# Campus Store Order Entry (Streamlit)

**Live app:** PASTE_YOUR_APP_URL_HERE

The app is password protected. The password is provided privately through the course submission.

A Streamlit web app connected to a Supabase database. Users pick a customer and a product, enter a quantity, review the order, and save it. Every saved order is pulled back from the database with a new query to verify it was saved.

## Files

| File | Purpose |
|------|---------|
| `app.py` | Streamlit interface: tables, order entry, review/confirm, verification, order history |
| `database.py` | All Supabase queries (customers, products, current price, insert order, get one order, get all orders) |
| `config.py` | Loads credentials from Streamlit secrets (deployed) or `.env` (local) |
| `requirements.txt` | Required Python packages |
| `.gitignore` | Keeps `.env`, `.streamlit/secrets.toml`, and cache files out of GitHub |
| `.env.example` | Template with placeholder values only |
| `screenshots/` | Screenshots from testing the deployed app |

## Running Locally

1. Clone this repo and open it in VS Code.
2. Install the packages:
   ```
   pip install -r requirements.txt
   ```
3. Copy `.env.example` into a new file named `.env` and fill in your own Supabase URL, Supabase secret key, and an app password.
4. Run the app:
   ```
   streamlit run app.py
   ```

## Deploying on Streamlit Community Cloud

1. Push the repo to GitHub.
2. Go to share.streamlit.io, click **Create app**, and select this repo, branch `main`, and main file `app.py`.
3. Under **Advanced settings → Secrets**, add:
   ```toml
   SUPABASE_URL = "your_supabase_project_url"
   SUPABASE_KEY = "your_supabase_secret_key"
   APP_PASSWORD = "your_app_password"
   ```
4. Click **Deploy**.

Real credentials are never committed. They live only in `.env` locally and in the deployment's secrets settings.

## How It Works

- **Password gate:** The app asks for a password before anything touches the database. It's checked on the server against the password in the deployment secrets using `hmac.compare_digest`.
- **Display:** Customers (ID, name) and products (ID, name, category, price formatted as currency) are loaded from Supabase. The **Refresh Data** button reloads everything from the database.
- **Order entry:** Dropdowns show customer and product names but return their IDs, which are what get saved. The quantity box only allows whole numbers of 1 or more.
- **Review and confirm:** **Review Order** gets the product's current price from Supabase and shows the customer, product, quantity, unit price, and total. The user must check a confirmation box and click **Submit Order**.
- **No duplicate orders:** The insert only runs inside the Submit button's click. After a successful save, the pending order is cleared from `st.session_state`, so reruns, refreshes, or changing other widgets can't insert it again.
- **Price changes:** Right before saving, the price is checked again. If it changed since the review, the app shows the new price and requires confirmation again.
- **Saving:** The order is saved with today's date and the database's current price. The database generates the order ID. A success message only shows after Supabase returns the saved row. Errors show a generic message with no credentials.
- **Verification:** The new order ID is used for a separate query to Supabase, and the returned record is shown in the Verified Order table. The total uses the stored `unit_price`. If verification fails, the app says the order was saved but couldn't be retrieved, and does not resubmit.
- **Order history:** All orders are loaded from Supabase, newest first. The table updates after a successful order and when Refresh Data is clicked.
- **Extra credit:** The **Filter by customer** dropdown shows only that customer's orders, along with their total value calculated from the stored unit prices.

## Testing Results (Deployed App)

| Test | Result |
|------|--------|
| Open the deployed app | ✅ Password screen shown; app loaded after entering the password |
| View customers and products | ✅ Both tables loaded from Supabase |
| Try an invalid quantity (`0`, `-2`, `1.5`) | ✅ Red error shown and the value wasn't accepted |
| Submit without confirmation | ✅ Warning shown; no order inserted |
| Confirm and submit a valid order | ✅ "Order 1004 saved!" Exactly one order inserted |
| View the verification table | ✅ Order 1004 retrieved from Supabase and shown in the Verified Order table |
| Refresh or interact with another widget | ✅ No duplicate. Order count stayed at 65 (60 original + orders 1000–1004) |
| Refresh order history | ✅ Order 1004 still visible at the top after Refresh Data |
| Extra credit: filter by customer | ✅ Showed only the selected customer's orders and their total value |

Total value of all orders after testing was $3,227.50, which matches the original $3,045.50 plus the five new orders.

## Screenshots

**Order entry and review**

![Order entry](screenshots/order-entry.png)

**Verified order**

![Verified order](screenshots/verified-order.png)

**Order history after testing**

![Order history](screenshots/order-history.png)

## Libraries and References

- Streamlit: https://docs.streamlit.io/develop/api-reference
- Streamlit secrets: https://docs.streamlit.io/develop/concepts/connections/secrets-management
- `st.session_state` and `st.cache_resource`: https://docs.streamlit.io/develop/api-reference/caching-and-state
- `supabase` (supabase-py): https://supabase.com/docs/reference/python/introduction
- `python-dotenv`: https://pypi.org/project/python-dotenv/
- `hmac.compare_digest` for the password check: https://docs.python.org/3/library/hmac.html