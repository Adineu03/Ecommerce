import os
import json
import re
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import io

from inventory_manager import load_inventory, save_inventory
from order import Order
from ai_insights import generate_ai_insights
from recommender import get_recommendations

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
CUSTOMERS_FILE = os.path.join(DATA_DIR, 'customers.json')
ORDERS_FILE = os.path.join(DATA_DIR, 'orders.json')
BILL_FILE = os.path.join(DATA_DIR, 'bill_for_all.json')

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "password123"  # Demo credentials

def load_customers():
    if not os.path.exists(CUSTOMERS_FILE):
        with open(CUSTOMERS_FILE, 'w') as f:
            json.dump([], f, indent=4)
    with open(CUSTOMERS_FILE, 'r') as f:
        return json.load(f)

def save_customers(customers_list):
    with open(CUSTOMERS_FILE, 'w') as f:
        json.dump(customers_list, f, indent=4)

def load_orders():
    if not os.path.exists(ORDERS_FILE):
        with open(ORDERS_FILE, 'w') as f:
            json.dump([], f, indent=4)
    with open(ORDERS_FILE, 'r') as f:
        return json.load(f)

def save_orders(orders_list):
    with open(ORDERS_FILE, 'w') as f:
        json.dump(orders_list, f, indent=4)

def load_bill():
    if not os.path.exists(BILL_FILE):
        with open(BILL_FILE, 'w') as f:
            json.dump({}, f)
    with open(BILL_FILE, 'r') as f:
        return json.load(f)

def save_bill(bill):
    with open(BILL_FILE, 'w') as f:
        json.dump(bill, f, indent=4)

def get_customer_by_id(cust_id, customers):
    for c in customers:
        if c['customer_id'] == cust_id:
            return c
    return None

if "role" not in st.session_state:
    st.session_state["role"] = None
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "inventory_df" not in st.session_state:
    st.session_state["inventory_df"] = load_inventory()
if "orders" not in st.session_state:
    st.session_state["orders"] = load_orders()
if "customers" not in st.session_state:
    st.session_state["customers"] = load_customers()

if "current_customer_id" not in st.session_state:
    st.session_state["current_customer_id"] = None
if "current_order_number" not in st.session_state:
    st.session_state["current_order_number"] = 1

if "bill" not in st.session_state:
    st.session_state["bill"] = load_bill()

def update_inventory(new_df):
    st.session_state["inventory_df"] = new_df
    save_inventory(new_df)

def add_customer(cust_id):
    customers = st.session_state["customers"]
    if get_customer_by_id(cust_id, customers) is None:
        customers.append({"customer_id": cust_id, "name": cust_id, "purchase_history": []})
        save_customers(customers)
        st.session_state["customers"] = customers
        return True
    return False

def add_to_cart(product_id, qty):
    inv_df = st.session_state["inventory_df"]
    product_row = inv_df[inv_df["id"] == product_id]

    if product_row.empty:
        st.error("Invalid product ID")
        return

    product_id = int(product_id)
    product_name = str(product_row.iloc[0]["name"])
    price = float(product_row.iloc[0]["price"])
    qty = int(qty)
    subtotal = price * qty

    cust_id = st.session_state["current_customer_id"]
    order_num = st.session_state["current_order_number"]

    if cust_id not in st.session_state["bill"]:
        st.session_state["bill"][cust_id] = {}

    if order_num not in st.session_state["bill"][cust_id]:
        st.session_state["bill"][cust_id][order_num] = {"order_items": [], "total": 0.0}

    st.session_state["bill"][cust_id][order_num]["order_items"].append({
        "product_id": product_id,
        "product_name": product_name,
        "qty": qty,
        "subtotal": float(subtotal)
    })

    total = sum(item["subtotal"] for item in st.session_state["bill"][cust_id][order_num]["order_items"])
    st.session_state["bill"][cust_id][order_num]["total"] = float(total)

    save_bill(st.session_state["bill"])

def place_final_order():
    cust_id = st.session_state["current_customer_id"]
    order_num = st.session_state["current_order_number"]
    if cust_id not in st.session_state["bill"] or order_num not in st.session_state["bill"][cust_id]:
        st.error("No items in cart!")
        return False

    order_data = st.session_state["bill"][cust_id][order_num]
    items = [(item["product_id"], item["qty"]) for item in order_data["order_items"]]

    new_order_id = len(st.session_state["orders"]) + 1
    products_dict = st.session_state["inventory_df"].set_index("id").to_dict(orient="index")

    # Create an Order object
    new_order = Order(new_order_id, cust_id, items)
    new_order.calculate_total(products_dict)

    # Deduct stock
    inv_df = st.session_state["inventory_df"]
    for pid, qty in items:
        idx = inv_df.index[inv_df["id"] == pid][0]
        inv_df.at[idx, "stock"] = int(inv_df.at[idx, "stock"] - qty)
    update_inventory(inv_df)

    st.session_state["orders"].append({
        "order_id": new_order.order_id,
        "customer_id": new_order.customer_id,
        "items": items,
        "total_cost": new_order.total_cost
    })
    save_orders(st.session_state["orders"])

    # Update customer purchase history
    customers = st.session_state["customers"]
    cust = get_customer_by_id(cust_id, customers)
    if cust is not None:
        cust["purchase_history"].append({"order_id": new_order.order_id, "items": items})
        save_customers(customers)

    # Clear bill for this order
    st.session_state["bill"][cust_id].pop(order_num)
    save_bill(st.session_state["bill"])

    st.session_state["current_order_number"] += 1
    return new_order.order_id

def download_invoice(order_id):
    # Find the order
    placed_order = None
    for o in st.session_state["orders"]:
        if o["order_id"] == order_id:
            placed_order = o
            break
    if placed_order is None:
        return None

    inv_df = st.session_state["inventory_df"].set_index("id")
    df = pd.DataFrame(placed_order["items"], columns=["product_id", "quantity"])
    df["product_name"] = df["product_id"].apply(lambda x: inv_df.at[x, "name"] if x in inv_df.index else "")
    df["price"] = df["product_id"].apply(lambda x: float(inv_df.at[x, "price"]) if x in inv_df.index else 0.0)
    df["subtotal"] = df["price"] * df["quantity"]
    df["order_id"] = placed_order["order_id"]
    df["customer_id"] = placed_order["customer_id"]
    df["total_cost"] = placed_order["total_cost"]
    return df

def fig_to_png_bytes(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    buf.seek(0)
    return buf.getvalue()

### Pages ###

def login_page():
    st.title("Welcome to the E-Commerce App")

    role = st.radio("Select Role", ["Customer", "Administrator"])

    if role == "Administrator":
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                st.session_state["role"] = "admin"
                st.session_state["logged_in"] = True
                st.experimental_rerun()
            else:
                st.error("Invalid Credentials!")
    else:
        # Customer
        st.write("Customer ID must be alphanumeric (no spaces or special chars).")
        cust_id = st.text_input("Enter Customer ID")

        # Validate if user typed something
        if st.button("Proceed"):
            # Check if alphanumeric
            if not cust_id or not cust_id.isalnum():
                st.error("Customer ID must be alphanumeric. Please try again.")
            else:
                customers = st.session_state["customers"]
                existing_customer = get_customer_by_id(cust_id, customers)
                if existing_customer:
                    # Login
                    st.session_state["current_customer_id"] = cust_id
                    st.session_state["role"] = "customer"
                    st.session_state["logged_in"] = True
                    st.experimental_rerun()
                else:
                    st.info(f"Customer {cust_id} does not exist. Creating new customer...")
                    created = add_customer(cust_id)
                    if created:
                        st.session_state["current_customer_id"] = cust_id
                        st.session_state["role"] = "customer"
                        st.session_state["logged_in"] = True
                        st.experimental_rerun()
                    else:
                        st.error("Could not create customer, please try a different ID.")

def place_orders_page():
    st.title("Place Orders")
    inv_df = st.session_state["inventory_df"]

    search_term = st.text_input("Search for a product (we will only consider the first 4 characters)")

    # Only take first 4 characters
    search_key = search_term[:4] if len(search_term) >= 4 else search_term
    if search_key:
        # We'll do a "starts with" check
        filtered = inv_df[inv_df["name"].str.startswith(search_key, na=False)]
    else:
        filtered = inv_df

    product_name_list = filtered["name"].tolist()
    if product_name_list:
        selected_product = st.selectbox("Select Product", product_name_list)
    else:
        st.warning("No products found with that partial search.")
        selected_product = None

    if selected_product:
        p_row = filtered[filtered["name"] == selected_product].iloc[0]
        product_id = p_row["id"]
        qty = st.number_input("Quantity", min_value=1, step=1, value=1)
        if st.button("Add to Cart"):
            if qty > p_row["stock"]:
                st.warning("Insufficient stock!")
            else:
                add_to_cart(product_id, qty)
                st.success(f"Added {qty} of {selected_product} to cart.")

    # Show current cart
    cust_id = st.session_state["current_customer_id"]
    order_num = st.session_state["current_order_number"]
    if cust_id in st.session_state["bill"] and order_num in st.session_state["bill"][cust_id]:
        cart_items = st.session_state["bill"][cust_id][order_num]["order_items"]
        if cart_items:
            df_cart = pd.DataFrame(cart_items)
            total = st.session_state["bill"][cust_id][order_num]["total"]
            st.subheader("Current Cart")
            st.dataframe(df_cart[["product_name","qty","subtotal"]])
            st.write("**Total**:", total)

            # Recommendations
            cart_pids = [item["product_id"] for item in cart_items]
            recs = get_recommendations(cart_pids, st.session_state["orders"], inv_df)
            if recs:
                st.write("**Recommended Products for You**:")
                rec_names = inv_df[inv_df["id"].isin(recs)]["name"].tolist()
                st.write(", ".join(rec_names))

            if st.button("Place Order"):
                order_id = place_final_order()
                if order_id:
                    st.success("Order placed successfully!")
                    invoice_df = download_invoice(order_id)
                    if invoice_df is not None and not invoice_df.empty:
                        st.write("Download your invoice:")
                        csv = invoice_df.to_csv(index=False).encode("utf-8")
                        st.download_button("Download Invoice CSV", data=csv, file_name=f"invoice_{cust_id}.csv", mime='text/csv')
    else:
        # If cart is empty, recommend top popular items anyway
        recs = get_recommendations([], st.session_state["orders"], inv_df)
        if recs:
            st.write("**Recommended Products (Global Popularity)**:")
            rec_names = inv_df[inv_df["id"].isin(recs)]["name"].tolist()
            st.write(", ".join(rec_names))

def manage_products_page():
    st.title("Manage Products (Admin)")
    inv_df = st.session_state["inventory_df"]

    # Delete product
    with st.expander("Delete a Product"):
        del_pid = st.text_input("Enter Product ID to Delete")
        if st.button("Delete Product"):
            if del_pid:
                try:
                    del_pid = int(del_pid)
                    if del_pid in inv_df["id"].values:
                        inv_df = inv_df[inv_df["id"] != del_pid]
                        update_inventory(inv_df)
                        st.success(f"Product ID {del_pid} deleted.")
                        st.experimental_rerun()
                    else:
                        st.error("Product ID not found.")
                except ValueError:
                    st.error("Invalid Product ID")

    st.subheader("Products Table")
    st.dataframe(inv_df)

    st.subheader("Add or Update a Product")
    product_id = st.text_input("Product ID (required)")
    name = st.text_input("Name")
    price = st.number_input("Price", min_value=0.0, step=1.0)
    stock = st.number_input("Stock", min_value=0, step=1)
    # We'll treat "Add or Update" as one button:
    # We only enable it if `product_id` is not empty
    add_update_btn = st.button("Add/Update Product")

    if add_update_btn:
        if not product_id:
            st.error("Product ID is required!")
        else:
            try:
                pid_int = int(product_id)
            except ValueError:
                st.error("Product ID must be an integer.")
                return

            # Check if product exists
            existing = inv_df[inv_df["id"] == pid_int]
            if not existing.empty:
                # Update
                row_index = existing.index[0]
                # If no name was given, auto-fill from existing
                if not name:
                    name = existing.loc[row_index, "name"]
                # If price=0, maybe keep existing price if we wanted to. Or force admin to fill it.
                if price == 0:
                    price = existing.loc[row_index, "price"]
                if stock == 0:
                    stock = existing.loc[row_index, "stock"]

                inv_df.at[row_index, "name"] = name
                inv_df.at[row_index, "price"] = price
                inv_df.at[row_index, "stock"] = stock
                # popularity remains same

                update_inventory(inv_df)
                st.success(f"Product ID {pid_int} updated.")
                st.experimental_rerun()
            else:
                # New product
                if not name:
                    st.error("Product name is required for a new product!")
                    return
                # popularity as average
                avg_pop = inv_df["popularity"].mean()
                if pd.isna(avg_pop):
                    avg_pop = 50
                new_row = {
                    "id": pid_int,
                    "name": name,
                    "price": float(price),
                    "stock": int(stock),
                    "popularity": float(avg_pop)
                }
                updated_df = pd.concat([inv_df, pd.DataFrame([new_row])], ignore_index=True)
                update_inventory(updated_df)
                st.success(f"New product ID {pid_int} added.")
                st.experimental_rerun()

def ai_insights_page():
    st.title("AI Insights (Admin)")
    orders = st.session_state["orders"]
    inv_df = st.session_state["inventory_df"]
    if st.button("Generate AI Insights"):
        summary = generate_ai_insights(orders, inv_df)
        st.write(summary)

def analytics_page():
    st.title("Analytics (Admin)")
    inv_df = st.session_state["inventory_df"]
    orders = st.session_state["orders"]

    # Show total sales
    total_sales = sum(o["total_cost"] for o in orders)
    st.markdown(f"**Total Sales:** `${total_sales}`")

    # Show orders table merged with product details
    if orders:
        all_items = []
        for o in orders:
            for pid, qty in o["items"]:
                # Safely find price, name, etc
                row = inv_df[inv_df["id"] == pid]
                if not row.empty:
                    price = float(row.iloc[0]["price"])
                    pname = row.iloc[0]["name"]
                else:
                    price = 0
                    pname = "Unknown"
                all_items.append({
                    "order_id": o["order_id"],
                    "customer_id": o["customer_id"],
                    "product_id": pid,
                    "product_name": pname,
                    "quantity": qty,
                    "price": price,
                    "subtotal": price * qty
                })
        df_orders = pd.DataFrame(all_items)
        st.subheader("Orders Detail")
        st.dataframe(df_orders)

        # -- We want at least 10 different visualizations. Examples below:

        # 1. Popularity bar chart
        fig1, ax1 = plt.subplots()
        ax1.bar(inv_df["name"], inv_df["popularity"])
        ax1.set_xlabel("Products")
        ax1.set_ylabel("Popularity")
        ax1.set_title("Product Popularity")
        plt.xticks(rotation=45)
        plt.tight_layout()
        st.pyplot(fig1)

        # 2. Pie chart of product contribution to total sales
        product_sales = df_orders.groupby("product_name")["subtotal"].sum().to_dict()
        fig2, ax2 = plt.subplots()
        ax2.pie(product_sales.values(), labels=product_sales.keys(), autopct='%1.1f%%')
        ax2.set_title("Contribution to Total Sales")
        st.pyplot(fig2)

        # 3. Monthly sales line chart (we'll fake monthly data from orders, for example)
        # If you had timestamps in orders, you’d parse & group by month. Here we just show a placeholder
        sales_over_time = pd.DataFrame({
            "month": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
            "sales": [100, 200, 150, 300, 250, total_sales]
        })
        fig3, ax3 = plt.subplots()
        ax3.plot(sales_over_time["month"], sales_over_time["sales"], marker='o')
        ax3.set_title("Sales Over Time")
        st.pyplot(fig3)

        # 4. Scatter plot: Price vs Popularity
        fig4, ax4 = plt.subplots()
        ax4.scatter(inv_df["price"], inv_df["popularity"])
        ax4.set_xlabel("Price")
        ax4.set_ylabel("Popularity")
        ax4.set_title("Price vs. Popularity")
        st.pyplot(fig4)

        # 5. Stacked bar for product stock vs. sold (approx). We'll just pick random sold data for demonstration
        product_ids = inv_df["id"].tolist()
        sold_counts = []
        for pid in product_ids:
            subdf = df_orders[df_orders["product_id"] == pid]
            sold_counts.append(subdf["quantity"].sum())
        fig5, ax5 = plt.subplots()
        ax5.bar(inv_df["name"], inv_df["stock"], label="Stock", alpha=0.7)
        ax5.bar(inv_df["name"], sold_counts, bottom=inv_df["stock"], label="Sold", alpha=0.7)
        ax5.set_xticklabels(inv_df["name"], rotation=45)
        ax5.set_title("Stock vs. Sold Stacked Bar")
        ax5.legend()
        st.pyplot(fig5)

        # 6. Horizontal bar chart of product price
        fig6, ax6 = plt.subplots()
        ax6.barh(inv_df["name"], inv_df["price"])
        ax6.set_xlabel("Price")
        ax6.set_title("Product Price (Horizontal)")
        st.pyplot(fig6)

        # 7. Boxplot of product prices
        fig7, ax7 = plt.subplots()
        ax7.boxplot(inv_df["price"], vert=False)
        ax7.set_title("Boxplot of Product Prices")
        st.pyplot(fig7)

        # 8. Another line chart: popularity trend sorted by name
        sorted_inv = inv_df.sort_values(by="name")
        fig8, ax8 = plt.subplots()
        ax8.plot(sorted_inv["name"], sorted_inv["popularity"], marker='o')
        ax8.set_title("Popularity by Product (alphabetical)")
        plt.xticks(rotation=45)
        st.pyplot(fig8)

        # 9. Heatmap-like approach (though we have limited data). We can do a pivot table of product vs. sales.
        # For demonstration, let's show a pivot on product_id vs. quantity sold
        pivot_data = df_orders.pivot_table(index="product_name", values="quantity", aggfunc='sum').fillna(0)
        # We'll just show a dataframe for the "heatmap"
        st.write("Product vs. Quantity pivot:")
        st.dataframe(pivot_data)

        # 10. Radar chart or some advanced chart can be done if needed. 
        # We'll just show a "line" chart in Streamlit for pivot_data
        st.line_chart(pivot_data)

    else:
        st.write("No orders placed yet.")

def ai_insights_page():
    st.title("AI Insights (Admin)")
    orders = st.session_state["orders"]
    inv_df = st.session_state["inventory_df"]
    if st.button("Generate AI Insights"):
        summary = generate_ai_insights(orders, inv_df)
        st.write(summary)

### Main App Flow ###

if not st.session_state["logged_in"]:
    login_page()
else:
    if st.session_state["role"] == "admin":
        page = st.sidebar.selectbox("Menu", ["Manage Products", "Analytics", "AI Insights", "Logout"])
        if page == "Manage Products":
            manage_products_page()
        elif page == "Analytics":
            analytics_page()
        elif page == "AI Insights":
            ai_insights_page()
        elif page == "Logout":
            st.session_state["logged_in"] = False
            st.session_state["role"] = None
            st.experimental_rerun()
    else:
        # Customer
        page = st.sidebar.selectbox("Menu", ["Place Orders", "Logout"])
        if page == "Place Orders":
            place_orders_page()
        elif page == "Logout":
            st.session_state["logged_in"] = False
            st.session_state["role"] = None
            st.session_state["current_customer_id"] = None
            st.experimental_rerun()
