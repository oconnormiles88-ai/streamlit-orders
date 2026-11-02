# app.py
# streamlit version of the order entry program, hooked up to supabase
import hmac
import streamlit as st
from config import SUPABASE_URL, SUPABASE_KEY, APP_PASSWORD
from database import get_customers, get_products, get_product_price, insert_order, get_order, get_orders

st.set_page_config(page_title="Campus Store Orders", page_icon="🛒", layout="wide")


def money(amount):
    # turns a number into something like "$1,234.50"
    return f"${float(amount):,.2f}"


def check_password():
    # password gate, this runs before anything touches the database
    if st.session_state.get("logged_in"):
        return True

    if not APP_PASSWORD:
        st.error("The app password hasn't been set up yet. Add APP_PASSWORD to the app's secrets.")
        return False

    password = st.text_input("Enter the app password", type="password")
    if password:
        # compare_digest is a safer way to check passwords than ==
        if hmac.compare_digest(password.encode(), APP_PASSWORD.encode()):
            st.session_state["logged_in"] = True
            st.rerun()
        else:
            st.error("Wrong password.")
    return False


def load_data():
    # pulls fresh customers, products, and orders from supabase and keeps them in session_state
    customers = {}
    for customer in get_customers():
        customers[customer["customer_id"]] = customer

    products = {}
    for product in get_products():
        products[product["product_id"]] = product

    orders = get_orders()

    st.session_state["customers"] = customers
    st.session_state["products"] = products
    st.session_state["orders"] = orders


def build_order_rows(orders, customers, products):
    # turns raw order records into table rows. total uses the unit_price stored in the database
    rows = []
    for order in orders:
        unit_price = float(order["unit_price"])
        customer = customers.get(order["customer_id"])
        product = products.get(order["product_id"])
        rows.append({
            "Order ID": order["order_id"],
            "Customer": customer["name"] if customer else f"Customer {order['customer_id']}",
            "Product": product["product_name"] if product else f"Product {order['product_id']}",
            "Quantity": order["quantity"],
            "Unit Price": money(unit_price),
            "Total": money(order["quantity"] * unit_price),
            "Order Date": order["order_date"],
        })
    return rows


def submit_order(pending):
    # only ever runs when Submit is clicked, so normal reruns can't create extra orders

    # check the price one more time right before saving in case it changed since the review
    try:
        latest_price = get_product_price(pending["product_id"])
    except Exception:
        st.error("Couldn't reach Supabase to check the price. Nothing was saved, please try again.")
        return
    if latest_price is None:
        st.error("That product couldn't be found anymore. Nothing was saved.")
        return
    if latest_price != pending["unit_price"]:
        # price changed, so update it and make them confirm again with a fresh checkbox
        pending["unit_price"] = latest_price
        st.session_state["review_id"] += 1
        st.session_state["warning_message"] = f"Heads up, the price changed to {money(latest_price)}. Check the new total and confirm again."
        st.rerun()

    try:
        saved = insert_order(pending["customer_id"], pending["product_id"], pending["quantity"], latest_price)
    except Exception:
        # generic on purpose so the url and key never show up on screen
        st.error("Couldn't save the order to Supabase. Please try again.")
        return
    if saved is None:
        st.error("Supabase didn't confirm the order, so it was not saved.")
        return

    # it's saved for real, so clear the review and remember the new order id for verification
    st.session_state["pending"] = None
    st.session_state["last_order_id"] = saved["order_id"]
    st.session_state["success_message"] = f"Order {saved['order_id']} saved!"
    try:
        st.session_state["orders"] = get_orders()
    except Exception:
        st.session_state["warning_message"] = "The order saved, but the order history couldn't update. Hit Refresh Data."
    st.rerun()


# ---------- the page starts here ----------
st.title("🛒 Campus Store Order Entry")
st.write("Pick a customer and a product, review the order, and save it to the Supabase database. "
         "Every saved order gets pulled back from the database to prove it's really there.")

if not check_password():
    st.stop()

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("Supabase settings are missing. Add SUPABASE_URL and SUPABASE_KEY to the app's secrets.")
    st.stop()

# first time the page loads, grab everything from supabase
if "customers" not in st.session_state:
    try:
        load_data()
    except Exception:
        st.error("Couldn't load data from Supabase. Check the connection settings and try again.")
        st.stop()

if "review_id" not in st.session_state:
    st.session_state["review_id"] = 0

if st.button("🔄 Refresh Data"):
    try:
        load_data()
        st.success("Data refreshed from Supabase.")
    except Exception:
        st.error("Couldn't refresh data from Supabase. Try again in a moment.")

customers = st.session_state["customers"]
products = st.session_state["products"]

# ----- customer and product tables -----
st.header("Customers and Products")
left, right = st.columns(2)

with left:
    st.subheader("Customers")
    customer_rows = []
    for customer_id, customer in customers.items():
        customer_rows.append({"ID": customer_id, "Name": customer["name"]})
    st.dataframe(customer_rows, hide_index=True)

with right:
    st.subheader("Products")
    product_rows = []
    for product_id, product in products.items():
        product_rows.append({
            "ID": product_id,
            "Product": product["product_name"],
            "Category": product["category"],
            "Price": money(product["price"]),
        })
    st.dataframe(product_rows, hide_index=True)

# ----- order entry -----
st.divider()
st.header("Place an Order")

# the dropdowns show names, but the value they hand back is the id, which is what gets saved
customer_id = st.selectbox(
    "Customer",
    options=list(customers.keys()),
    format_func=lambda cid: f"{customers[cid]['name']} (ID {cid})",
    index=None,
    placeholder="Choose a customer",
)
product_id = st.selectbox(
    "Product",
    options=list(products.keys()),
    format_func=lambda pid: f"{products[pid]['product_name']} ({money(products[pid]['price'])})",
    index=None,
    placeholder="Choose a product",
)
# min_value=1 and step=1 means only positive whole numbers can be entered
quantity = st.number_input("Quantity", min_value=1, step=1, value=1)

# if they change anything after reviewing, the old review doesn't count anymore
pending = st.session_state.get("pending")
if pending and (pending["customer_id"], pending["product_id"], pending["quantity"]) != (customer_id, product_id, quantity):
    st.session_state["pending"] = None
    st.info("You changed the order, so click Review Order again.")

if st.button("Review Order"):
    if customer_id is None or product_id is None:
        st.error("Pick a customer and a product first.")
    elif customer_id not in customers or product_id not in products:
        st.error("That customer or product doesn't exist. Hit Refresh Data and try again.")
    elif not isinstance(quantity, int) or quantity < 1:
        st.error("Quantity has to be a positive whole number.")
    else:
        try:
            current_price = get_product_price(product_id)
        except Exception:
            current_price = None
        if current_price is None:
            st.error("Couldn't get the current price from Supabase. Please try again.")
        else:
            st.session_state["pending"] = {
                "customer_id": customer_id,
                "product_id": product_id,
                "quantity": quantity,
                "unit_price": current_price,
            }
            # new review means a new, unchecked confirmation box
            st.session_state["review_id"] += 1

# messages saved from the last click, like the success message after saving
if "success_message" in st.session_state:
    st.success(st.session_state.pop("success_message"))
if "warning_message" in st.session_state:
    st.warning(st.session_state.pop("warning_message"))

# ----- review and confirm -----
pending = st.session_state.get("pending")
if pending:
    st.subheader("Review Your Order")
    total = pending["quantity"] * pending["unit_price"]
    st.write(f"**Customer:** {customers[pending['customer_id']]['name']}")
    st.write(f"**Product:** {products[pending['product_id']]['product_name']}")
    st.write(f"**Quantity:** {pending['quantity']}")
    st.write(f"**Unit Price:** {money(pending['unit_price'])}")
    st.write(f"**Total:** {money(total)}")

    confirmed = st.checkbox("I confirm this order is correct", key=f"confirm_{st.session_state['review_id']}")
    if st.button("Submit Order", type="primary"):
        if not confirmed:
            st.warning("Check the confirmation box first. Nothing was saved.")
        else:
            submit_order(pending)

# ----- verification -----
if "last_order_id" in st.session_state:
    st.divider()
    st.header("Verified Order")
    order_id = st.session_state["last_order_id"]
    # brand new query to supabase, not just the info that was typed in
    try:
        saved_order = get_order(order_id)
    except Exception:
        saved_order = None
    if saved_order is None:
        st.warning(f"Order {order_id} was saved, but it couldn't be retrieved for verification. It was not submitted again.")
    else:
        st.caption("This record was pulled fresh from Supabase.")
        st.dataframe(build_order_rows([saved_order], customers, products), hide_index=True)

# ----- order history -----
st.divider()
st.header("Order History")

# extra credit: filter the history by customer (0 means show everyone)
filter_id = st.selectbox(
    "Filter by customer",
    options=[0] + list(customers.keys()),
    format_func=lambda cid: "All customers" if cid == 0 else customers[cid]["name"],
)

history = st.session_state["orders"]
if filter_id != 0:
    filtered = []
    for order in history:
        if order["customer_id"] == filter_id:
            filtered.append(order)
    history = filtered

# total value uses each order's stored unit_price
total_value = 0
for order in history:
    total_value += order["quantity"] * float(order["unit_price"])

count_col, value_col = st.columns(2)
count_col.metric("Orders", len(history))
value_col.metric("Total Value", money(total_value))
st.dataframe(build_order_rows(history, customers, products), hide_index=True)