class Order:
    def __init__(self, order_id, customer_id, product_list):
        """
        product_list is a list of (product_id, quantity)
        """
        self.order_id = order_id
        self.customer_id = customer_id
        self.product_list = product_list
        self.total_cost = 0.0

    def calculate_total(self, products_dict):
        """
        products_dict: { product_id: { 'name':..., 'price':..., 'stock':..., 'popularity':... } }
        """
        total = 0
        for pid, qty in self.product_list:
            total += products_dict[pid]['price'] * qty
        self.total_cost = total
        return self.total_cost
