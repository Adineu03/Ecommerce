def generate_sales_report(orders, products):
    """
    Generate a simple sales report. 
    orders: list of dicts {order_id, customer_id, items, total_cost}
    products: dict {product_id: {...}}

    Returns a string summarizing total sales and top products.
    """
    total_sales = sum(o['total_cost'] for o in orders)
    product_sales = {}
    for o in orders:
        for pid, qty in o['items']:
            product_sales[pid] = product_sales.get(pid, 0) + (products[pid]['price'] * qty)

    top_products = sorted(product_sales.items(), key=lambda x: x[1], reverse=True)
    report = f"Total Sales: ${total_sales}\n"
    report += "Top Selling Products:\n"
    for pid, sales in top_products:
        report += f"Product ID {pid}: ${sales}\n"

    return report
