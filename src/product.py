class Product:
    def __init__(self, product_id, name, price, stock, popularity=0):
        self.product_id = product_id
        self.name = name
        self.price = price
        self.stock = stock
        self.popularity = popularity

    def apply_discount(self, discount_rate):
        return self.price * (1 - discount_rate)
