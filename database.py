# database.py
# all the supabase calls live here so app.py can focus on the page itself
from datetime import date
import streamlit as st
from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY


@st.cache_resource
def get_client():
    # makes the supabase connection once and reuses it, since streamlit reruns the script a lot
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def get_customers():
    response = get_client().table("customers").select("customer_id, name").order("customer_id").execute()
    return response.data


def get_products():
    response = get_client().table("products").select("product_id, product_name, category, price").order("product_id").execute()
    return response.data


def get_product_price(product_id):
    # asks supabase for the price right now, returns None if the product isn't there
    response = get_client().table("products").select("price").eq("product_id", product_id).execute()
    if response.data:
        return float(response.data[0]["price"])
    return None


def insert_order(customer_id, product_id, quantity, unit_price):
    # no order_id here on purpose, the database makes that itself
    new_order = {
        "customer_id": customer_id,
        "product_id": product_id,
        "quantity": quantity,
        "order_date": date.today().isoformat(),
        "unit_price": unit_price,
    }
    response = get_client().table("orders").insert(new_order).execute()
    # supabase sends back the saved row with its new order_id. empty means it didn't save
    if response.data:
        return response.data[0]
    return None


def get_order(order_id):
    # brand new query to double check one specific order made it into the database
    response = get_client().table("orders").select("*").eq("order_id", order_id).execute()
    if response.data:
        return response.data[0]
    return None


def get_orders():
    # every order, newest first, for the order history table
    response = get_client().table("orders").select("*").order("order_id", desc=True).execute()
    return response.data