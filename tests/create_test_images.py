import os
from datetime import datetime, timedelta  # Import both classes separately
from PIL import Image, ImageDraw

def setup_test_images():
    # Base directory for image storage
    base_dir = "/root/api/image_storage"
    
    # Test SKUs
    test_skus = ["TEST-SKU-123", "TEST-SKU-456"]
    
    # Clear existing test directory if it exists
    for sku in test_skus:
        sku_dir = os.path.join(base_dir, sku)
        if os.path.exists(sku_dir):
            import shutil
            shutil.rmtree(sku_dir)
    
    # Create directories
    for sku in test_skus:
        sku_dir = os.path.join(base_dir, sku)
        os.makedirs(sku_dir, exist_ok=True)
        
        # Create multiple timestamp sets for each SKU
        for i in range(3):
            # Generate timestamps (newest first)
            days_ago = i * 2  # 0, 2, 4 days ago
            timestamp = (datetime.now().replace(hour=10, minute=30) - 
                        timedelta(days=days_ago))  # Fixed this line
            timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
            
            # Create a test image with text
            img = Image.new('RGB', (400, 300), color=(255, 255, 255))
            d = ImageDraw.Draw(img)
            d.text((10, 10), f"SKU: {sku}", fill=(0, 0, 0))
            d.text((10, 30), f"Timestamp: {timestamp_str}", fill=(0, 0, 0))
            d.text((10, 50), "Original Image", fill=(0, 0, 0))
            
            # Save the image
            image_path = os.path.join(sku_dir, f"{timestamp_str}_image.jpg")
            img.save(image_path)
            
            # Create segmentation image (gray with black text)
            img_seg = Image.new('RGB', (400, 300), color=(200, 200, 200))
            d = ImageDraw.Draw(img_seg)
            d.text((10, 10), f"SKU: {sku}", fill=(0, 0, 0))
            d.text((10, 30), f"Timestamp: {timestamp_str}", fill=(0, 0, 0))
            d.text((10, 50), "Segmentation Image", fill=(0, 0, 0))
            
            # Save the segmentation image
            imageseg_path = os.path.join(sku_dir, f"{timestamp_str}_imageseg.jpg")
            img_seg.save(imageseg_path)
            
            # Create color image (colorful with black text)
            img_color = Image.new('RGB', (400, 300), color=(100, 180, 240))
            d = ImageDraw.Draw(img_color)
            d.text((10, 10), f"SKU: {sku}", fill=(0, 0, 0))
            d.text((10, 30), f"Timestamp: {timestamp_str}", fill=(0, 0, 0))
            d.text((10, 50), "Color Image", fill=(0, 0, 0))
            
            # Save the color image
            imagecolor_path = os.path.join(sku_dir, f"{timestamp_str}_imagecolor.jpg")
            img_color.save(imagecolor_path)
    
    print(f"Test images created in {base_dir}")
    print(f"SKUs: {', '.join(test_skus)}")

# Create test images
setup_test_images()