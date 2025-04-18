import cv2
import numpy as np
import os
from sklearn.metrics.pairwise import cosine_similarity

class ImageProcessor:
    def __init__(self, image_folder):
        """Initialize the image processor with a folder containing product images."""
        self.image_folder = image_folder
        self.image_features = {}
        self.image_paths = {}
        
    def extract_features(self, image_path):
        """Extract features from an image using a pre-trained model."""
        # Load image
        img = cv2.imread(image_path)
        if img is None:
            return None
            
        # Resize for consistency
        img = cv2.resize(img, (224, 224))
        
        # Convert to feature vector (using color histograms as a simple method)
        # In a real application, you'd use a CNN like VGG or ResNet here
        hist_features = []
        color_spaces = [cv2.COLOR_BGR2HSV, cv2.COLOR_BGR2Lab]
        
        for color_space in color_spaces:
            # Convert color space
            converted_img = cv2.cvtColor(img, color_space)
            
            # Calculate histogram for each channel
            for i in range(3):
                hist = cv2.calcHist([converted_img], [i], None, [32], [0, 256])
                hist = cv2.normalize(hist, hist).flatten()
                hist_features.extend(hist)
        
        return np.array(hist_features)
    
    def process_image_folder(self):
        """Process all images in the folder and extract features."""
        print(f"Processing images in {self.image_folder}...")
        for filename in os.listdir(self.image_folder):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                product_id = filename.split('.')[0]  # Assuming filename format is "product_id.jpg"
                image_path = os.path.join(self.image_folder, filename)
                
                # Extract features
                features = self.extract_features(image_path)
                if features is not None:
                    self.image_features[product_id] = features
                    self.image_paths[product_id] = image_path
        
        print(f"Processed {len(self.image_features)} images")
        
    def find_similar_images(self, product_id, num_similar=5):
        """Find similar products based on image features."""
        if product_id not in self.image_features:
            return []
            
        # Get features for the query product
        query_features = self.image_features[product_id]
        
        # Calculate similarity to all other products
        similarities = {}
        for pid, features in self.image_features.items():
            if pid != product_id:
                sim = cosine_similarity(query_features.reshape(1, -1), features.reshape(1, -1))[0][0]
                similarities[pid] = sim
        
        # Sort by similarity and return top matches
        similar_products = sorted(similarities.items(), key=lambda x: x[1], reverse=True)[:num_similar]
        return [pid for pid, _ in similar_products]

# Example usage
if __name__ == "__main__":
    processor = ImageProcessor("./product_images")
    processor.process_image_folder()
    
    # Test with a sample product
    sample_product = list(processor.image_features.keys())[0]
    similar_products = processor.find_similar_images(sample_product)
    
    print(f"Products similar to {sample_product}:")
    for pid in similar_products:
        print(f"- {pid}")