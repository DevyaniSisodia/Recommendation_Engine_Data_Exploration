from flask import Flask, request, jsonify
import pandas as pd
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import normalize
import pickle
import os
from image_processor import ImageProcessor

app = Flask(__name__)

# Load our recommendation model and data
def load_recommendation_data():
    global purchase_matrix, model, df_clean, image_processor
    
    # Load and clean data
    df = pd.read_excel('online_retail.xlsx')
    df_clean = df.dropna(subset=['CustomerID'])
    df_clean['CustomerID'] = df_clean['CustomerID'].astype(int)
    df_clean = df_clean[(df_clean['Quantity'] > 0) & (df_clean['UnitPrice'] > 0)]
    
    # Create purchase matrix
    purchase_matrix = df_clean.pivot_table(
        index='CustomerID', 
        columns='StockCode', 
        values='Quantity', 
        aggfunc='sum', 
        fill_value=0
    )
    
    # Create item matrix
    item_matrix = purchase_matrix.T
    item_matrix_normalized = normalize(item_matrix.values)
    
    # Create model
    model = NearestNeighbors(metric='cosine', algorithm='brute')
    model.fit(item_matrix_normalized)
    
    # Create image processor if folder exists
    if os.path.exists("product_images"):
        image_processor = ImageProcessor("product_images")
        image_processor.process_image_folder()
    else:
        image_processor = None
        print("No product images folder found. Image-based recommendations will be unavailable.")
    
    print("Recommendation data loaded successfully!")

# Load data when app starts
load_recommendation_data()

# API endpoint for item recommendations
@app.route('/recommend/item/<item_id>', methods=['GET'])
def recommend_item_api(item_id):
    try:
        # Convert item_id to appropriate type
        item_id = item_id.strip()
        
        # Check if item exists
        if item_id not in purchase_matrix.columns:
            return jsonify({"error": "Item not found"}), 404
        
        # Get recommendations
        num_recommendations = int(request.args.get('num', 5))
        
        # Find the index of the item
        item_idx = purchase_matrix.columns.get_loc(item_id)
        
        # Get similar items
        distances, indices = model.kneighbors(
            normalize(purchase_matrix.T.values)[item_idx].reshape(1, -1), 
            n_neighbors=num_recommendations+1
        )
        
        # Get the item codes for recommendations (skip the first as it's the item itself)
        similar_items = [purchase_matrix.columns[idx] for idx in indices.flatten()[1:]]
        
        # Get the item descriptions
        recommendations = []
        for item in similar_items:
            desc = df_clean[df_clean['StockCode'] == item]['Description'].iloc[0]
            recommendations.append({"item_id": item, "description": desc, "type": "collaborative"})
        
        # Get image-based recommendations if available
        if image_processor and item_id in image_processor.image_features:
            img_similar_items = image_processor.find_similar_images(item_id)
            for item in img_similar_items:
                if item in df_clean['StockCode'].values:
                    desc = df_clean[df_clean['StockCode'] == item]['Description'].iloc[0]
                    recommendations.append({"item_id": item, "description": desc, "type": "image-based"})
        
        return jsonify(recommendations[:num_recommendations])
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# API endpoint for user recommendations
@app.route('/recommend/user/<int:user_id>', methods=['GET'])
def recommend_user_api(user_id):
    try:
        # Check if user exists
        if user_id not in purchase_matrix.index:
            return jsonify({"error": "User not found"}), 404
        
        # Get number of recommendations from query parameters
        num_recommendations = int(request.args.get('num', 5))
        
        # Get user's purchase history
        user_purchases = purchase_matrix.loc[user_id]
        
        # Items the user has already purchased
        already_purchased = user_purchases[user_purchases > 0].index.tolist()
        
        # Get recommendations for each item the user has purchased
        all_recommendations = []
        for item in already_purchased[:5]:  # Limit to avoid too many computations
            item_idx = purchase_matrix.columns.get_loc(item)
            distances, indices = model.kneighbors(
                normalize(purchase_matrix.T.values)[item_idx].reshape(1, -1), 
                n_neighbors=4
            )
            similar_items = [purchase_matrix.columns[idx] for idx in indices.flatten()[1:]]
            all_recommendations.extend(similar_items)
        
        # Remove duplicates and items already purchased
        unique_recommendations = []
        seen_items = set()
        for item in all_recommendations:
            if item not in seen_items and item not in already_purchased:
                desc = df_clean[df_clean['StockCode'] == item]['Description'].iloc[0]
                unique_recommendations.append({"item_id": item, "description": desc})
                seen_items.add(item)
                if len(unique_recommendations) >= num_recommendations:
                    break
        
        return jsonify(unique_recommendations)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# New endpoint for image-based recommendations only
@app.route('/recommend/image/<item_id>', methods=['GET'])
def recommend_image_api(item_id):
    try:
        # Check if image processor is available
        if not image_processor:
            return jsonify({"error": "Image-based recommendations not available"}), 503
            
        # Check if item exists
        if item_id not in image_processor.image_features:
            return jsonify({"error": "Item image not found"}), 404
        
        # Get number of recommendations from query parameters
        num_recommendations = int(request.args.get('num', 5))
        
        # Get similar items based on image
        similar_items = image_processor.find_similar_images(item_id, num_recommendations)
        
        # Get the item descriptions
        recommendations = []
        for item in similar_items:
            if item in df_clean['StockCode'].values:
                desc = df_clean[df_clean['StockCode'] == item]['Description'].iloc[0]
                recommendations.append({"item_id": item, "description": desc})
        
        return jsonify(recommendations)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)