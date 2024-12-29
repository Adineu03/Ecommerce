import pandas as pd
import math
from collections import defaultdict

def get_recommendations(cart_items, orders, inventory_df):
    """
    cart_items: list of product_id currently in the customer's cart
    orders: list of order dicts, where each order has:
            {
                "order_id": int,
                "customer_id": str,
                "items": [(product_id, quantity), ...],
                "total_cost": float
            }
    inventory_df: pd.DataFrame of all products with columns:
                  [id, name, price, stock, popularity, ... (optionally more fields)]

    Return: list of recommended product_ids (top 3 best matches).
    """

    # 1) If cart is empty → recommend top 3 popular items
    if not cart_items:
        top_popular = (inventory_df
                       .sort_values(by="popularity", ascending=False)
                       .head(3)["id"].tolist())
        return top_popular

    # For convenience, let's set up a quick way to get product info as a dict
    # {product_id: {"price":..., "popularity":..., ...}}
    product_dict = inventory_df.set_index("id").to_dict("index")

    # 2) Collaborative Filtering: find other orders that contain any cart item
    #    Count how frequently each product is co-purchased with items in cart.
    co_purchase_counts = defaultdict(int)  # product_id -> frequency
    for order in orders:
        pids_in_order = [p[0] for p in order["items"]]
        # Check if this order has at least one item from the cart
        if any(pid in pids_in_order for pid in cart_items):
            # For each product in this order that isn't in the cart, increment
            for (pid, _) in order["items"]:
                if pid not in cart_items:
                    co_purchase_counts[pid] += 1

    # 3) Content-Based Similarity:
    #    We'll define a simple distance measure for two products A and B:
    #    distance(A,B) = sqrt( (priceA - priceB)^2 + (popA - popB)^2 )
    #    Then similarity = 1 / (1 + distance)
    #    For each product in cart, we find similar items and accumulate a similarity score.
    similarity_scores = defaultdict(float)  # product_id -> total similarity

    def product_distance(pid1, pid2):
        # safe retrieval
        p1 = product_dict[pid1]
        p2 = product_dict[pid2]
        price_dist = (p1["price"] - p2["price"])**2
        pop_dist = (p1["popularity"] - p2["popularity"])**2
        return math.sqrt(price_dist + pop_dist)

    def product_similarity(pid1, pid2):
        dist = product_distance(pid1, pid2)
        return 1.0 / (1.0 + dist)

    all_product_ids = set(inventory_df["id"].tolist())

    # For each product in the cart, compute similarity to every other product
    for cart_pid in cart_items:
        for candidate_pid in all_product_ids:
            if candidate_pid == cart_pid:
                continue
            # We skip if candidate is already in cart
            if candidate_pid in cart_items:
                continue
            similarity_scores[candidate_pid] += product_similarity(cart_pid, candidate_pid)

    # 4) Combine Collaborative Score + Similarity Score
    #    e.g., final_score = alpha * collaborative_frequency + beta * similarity
    #    We'll pick alpha=1.0, beta=1.0 for an equal mix
    final_scores = {}
    for pid in all_product_ids:
        if pid in cart_items:
            continue
        freq = co_purchase_counts[pid]    # how often this product is co-purchased
        sim  = similarity_scores[pid]     # total similarity to items in cart
        final_scores[pid] = freq + sim    # alpha=1.0, beta=1.0

    # If we have no final scores (e.g., no relevant orders or no similarities),
    # fallback to top popularity.
    if not final_scores:
        fallback = (inventory_df
                    .sort_values(by="popularity", ascending=False)
                    .head(3)["id"].tolist())
        return fallback

    # 5) Sort by final_scores in descending order
    sorted_pids = sorted(final_scores.items(), key=lambda x: x[1], reverse=True)
    # Return top 3 product_ids
    recommended_pids = [pid for (pid, _) in sorted_pids[:3]]
    return recommended_pids
