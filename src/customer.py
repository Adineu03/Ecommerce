class Customer:
    def __init__(self, customer_id, name, purchase_history=None):
        # purchase_history could be a list of order_ids or a list of tuples (order_id, product_list)
        self.customer_id = customer_id
        self.name = name
        self.purchase_history = purchase_history or []
