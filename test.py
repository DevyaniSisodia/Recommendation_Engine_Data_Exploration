import os
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont
import pandas as pd

def create_sample_product_images(df, output_folder, num_products=50):
    """Create sample product images for testing."""
    # Create output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)
    
    # Get unique products
    products = df['StockCode'].unique()[:num_products]
    
    # Create a simple image for each product
    for i, product_id in enumerate(products):
        # Get product info
        product_info = df[df['StockCode'] == product_id].iloc[0]
        
        # Create a base image (different color based on product category)
        img = Image.new('RGB', (300, 300), color=(i*5 % 256, 100, 150))
        draw = ImageDraw.Draw(img)
        
        # Add product ID and name
        draw.text((10, 10), f"ID: {product_id}", fill=(255, 255, 255))
        desc = product_info['Description']
        if isinstance(desc, str) and len(desc) > 20:
            desc = desc[:20] + "..."
        draw.text((10, 40), f"{desc}", fill=(255, 255, 255))
        
        # Add some random shapes to make images distinguishable
        for _ in range(5):
            x1 = np.random.randint(50, 250)
            y1 = np.random.randint(50, 250)
            x2 = x1 + np.random.randint(20, 50)
            y2 = y1 + np.random.randint(20, 50)
            shape_color = (np.random.randint(0, 255), np.random.randint(0, 255), np.random.randint(0, 255))
            draw.rectangle([x1, y1, x2, y2], outline=shape_color, width=2)
        
        # Save the image
        filename = os.path.join(output_folder, f"{product_id}.jpg")
        img.save(filename)
        
    print(f"Created {len(products)} sample product images in {output_folder}")
    return products

# Create sample images when run directly
if __name__ == "__main__":
    # Load the dataset
    df = pd.read_excel('online_retail.xlsx')
    
    # Create product images
    create_sample_product_images(df, "product_images", num_products=50)