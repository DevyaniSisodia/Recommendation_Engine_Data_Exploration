import streamlit as st
import pandas as pd
import numpy as np
import requests
import os
from PIL import Image

# Set up the Streamlit page
st.set_page_config(page_title="Product Recommendation Engine", layout="wide")
st.title("AI-Powered Product Recommendation Dashboard")

# Load the dataset
@st.cache_data
def load_data():
    df = pd.read_excel('online_retail.xlsx')
    df_clean = df.dropna(subset=['CustomerID'])
    df_clean['CustomerID'] = df_clean['CustomerID'].astype(int)
    df_clean = df_clean[(df_clean['Quantity'] > 0) & (df_clean['UnitPrice'] > 0)]
    return df_clean

df = load_data()

# Sidebar for navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Product Recommendations", "User Recommendations", "Image-Based Recommendations"])

# API base URL
API_URL = "http://localhost:5000"

# Function to get product image
def get_product_image(product_id):
    image_path = f"product_images/{product_id}.jpg"
    if os.path.exists(image_path):
        return Image.open(image_path)
    else:
        # Create a default image
        img = Image.new('RGB', (300, 300), color=(100, 100, 100))
        return img

# Product Recommendations Page
if page == "Product Recommendations":
    st.header("Product Recommendations")
    
    # Get unique products
    products = df['StockCode'].unique()
    product_options = []
    for p in products[:100]:  # Limit to first 100 products
        desc = df[df['StockCode'] == p]['Description'].iloc[0]
        product_options.append(f"{p}: {desc}")
    
    # Product selection
    selected_product = st.selectbox("Select a product", product_options)
    selected_product_id = selected_product.split(":")[0].strip()
    
    if st.button("Get Recommendations"):
        try:
            # Get recommendations from API
            response = requests.get(f"{API_URL}/recommend/item/{selected_product_id}")
            
            if response.status_code == 200:
                recommendations = response.json()
                
                # Display recommendations
                st.subheader("Recommended Products")
                
                # Show selected product
                col1, col2 = st.columns([1, 3])
                with col1:
                    st.image(get_product_image(selected_product_id), caption="Selected Product")
                with col2:
                    st.write(f"**ID:** {selected_product_id}")
                    st.write(f"**Description:** {selected_product.split(':', 1)[1].strip()}")
                
                # Show recommendations
                st.write("---")
                st.write("**Recommendations:**")
                
                # Create rows with 3 recommendations each
                for i in range(0, len(recommendations), 3):
                    cols = st.columns(3)
                    for j in range(3):
                        if i+j < len(recommendations):
                            rec = recommendations[i+j]
                            with cols[j]:
                                st.image(get_product_image(rec['item_id']), caption=rec['item_id'])
                                st.write(f"**Description:** {rec['description']}")
                                if 'type' in rec:
                                    st.write(f"**Type:** {rec['type']}")
            else:
                st.error(f"Error: {response.json().get('error', 'Unknown error')}")
                
        except Exception as e:
            st.error(f"Error: {str(e)}")

# User Recommendations Page
elif page == "User Recommendations":
    st.header("User Recommendations")
    
    # Get unique users
    users = df['CustomerID'].unique()
    
    # User selection
    selected_user = st.selectbox("Select a user", users[:100])  # Limit to first 100 users
    
    if st.button("Get Recommendations"):
        try:
            # Get recommendations from API
            response = requests.get(f"{API_URL}/recommend/user/{selected_user}")
            
            if response.status_code == 200:
                recommendations = response.json()
                
                # Display recommendations
                st.subheader(f"Recommended Products for User {selected_user}")
                
                # Show user's purchase history
                user_purchases = df[df['CustomerID'] == selected_user]
                with st.expander("User's Purchase History"):
                    st.dataframe(user_purchases[['StockCode', 'Description', 'Quantity', 'UnitPrice']])
                
                # Show recommendations
                st.write("---")
                st.write("**Recommendations:**")
                
                # Create rows with 3 recommendations each
                for i in range(0, len(recommendations), 3):
                    cols = st.columns(3)
                    for j in range(3):
                        if i+j < len(recommendations):
                            rec = recommendations[i+j]
                            with cols[j]:
                                st.image(get_product_image(rec['item_id']), caption=rec['item_id'])
                                st.write(f"**Description:** {rec['description']}")
            else:
                st.error(f"Error: {response.json().get('error', 'Unknown error')}")
                
        except Exception as e:
            st.error(f"Error: {str(e)}")

# Image-Based Recommendations Page
else:
    st.header("Image-Based Recommendations")
    
    # Get products with images
    image_folder = "product_images"
    if os.path.exists(image_folder):
        product_ids = [f.split('.')[0] for f in os.listdir(image_folder) if f.endswith('.jpg')]
        product_options = []
        for p in product_ids:
            if p in df['StockCode'].values:
                desc = df[df['StockCode'] == p]['Description'].iloc[0]
                product_options.append(f"{p}: {desc}")
    else:
        product_options = []
        st.warning("No product images found. Please run the image generation script first.")
    
    # Product selection
    if product_options:
        selected_product = st.selectbox("Select a product", product_options)
        selected_product_id = selected_product.split(":")[0].strip()
        
        # Display selected product image
        st.image(get_product_image(selected_product_id), caption="Selected Product", width=300)
        
        if st.button("Get Visual Recommendations"):
            try:
                # Get recommendations from API
                response = requests.get(f"{API_URL}/recommend/image/{selected_product_id}")
                
                if response.status_code == 200:
                    recommendations = response.json()
                    
                    # Display recommendations
                    st.subheader("Visually Similar Products")
                    
                    # Create rows with 3 recommendations each
                    for i in range(0, len(recommendations), 3):
                        cols = st.columns(3)
                        for j in range(3):
                            if i+j < len(recommendations):
                                rec = recommendations[i+j]
                                with cols[j]:
                                    st.image(get_product_image(rec['item_id']), caption=rec['item_id'])
                                    st.write(f"**Description:** {rec['description']}")
                else:
                    st.error(f"Error: {response.json().get('error', 'Unknown error')}")
                    
            except Exception as e:
                st.error(f"Error: {str(e)}")
    else:
        st.error("No products with images available")

# Footer
st.markdown("---")
st.markdown("AI-Powered Recommendation Engine Demo")