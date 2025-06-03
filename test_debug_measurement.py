import requests
import json

# Test the debug endpoint to see exactly what JSON is being sent
def test_debug_endpoint():
    """Test the debug measurement endpoint with sample data"""
    
    BASE_URL = "http://155.138.159.75/api/v1"
    
    # Sample data similar to what the device actually sends (based on database)
    test_data = {
        "barcode": "na",  # Matches what's in database
        "shape": "unknown",
        "device": "qboid-device",
        "attributes": {"origin": " italy", "origin2": " germany"},  # Matches database format
        # Test with file paths like the device sends
        "image": "/sdcard/qboid/data/2025_06_03/2025_06_03_07_30_07/Frames/result_img_1.png",
        "imageseg": "/sdcard/qboid/data/2025_06_03/2025_06_03_07_30_07/Frames/color0_segmented_1.png",
        "imagecolor": "/sdcard/qboid/data/2025_06_03/2025_06_03_07_30_07/Frames/color0_1.png"
    }
    
    # Also test with a proper barcode
    test_data_proper = {
        "timestamp": "2025-06-03T07:30:00.000000",
        "l": 150,
        "w": 50,
        "h": 200,
        "weight": 450,
        "barcode": "8003650007391",  # Real barcode from database
        "shape": "rectangular",
        "device": "qboid-scanner-01",
        "note": "Debug test with proper data",
        "attributes": {
            "origin": " italy",
            "origin2": " germany"
        },
        "image": "/sdcard/qboid/data/2025_06_03/2025_06_03_07_30_07/Frames/result_img_1.png",
        "imageseg": "/sdcard/qboid/data/2025_06_03/2025_06_03_07_30_07/Frames/color0_segmented_1.png",
        "imagecolor": "/sdcard/qboid/data/2025_06_03/2025_06_03_07_30_07/Frames/color0_1.png"
    }
    
    # Test both formats
    test_cases = [
        ("Device-like data (minimal)", test_data),
        ("Proper measurement data", test_data_proper)
    ]
    
    for test_name, data in test_cases:
        print(f"\n🧪 Testing: {test_name}")
        print(f"Sending to: {BASE_URL}/measurement_debug")
        print(f"Test data structure:")
        for key, value in data.items():
            if key in ['image', 'imageseg', 'imagecolor']:
                print(f"  {key}: {value}")
            else:
                print(f"  {key}: {value}")
        
        try:
            response = requests.post(f"{BASE_URL}/measurement_debug", json=data)
        
        print(f"\n📤 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success!")
            print(f"📋 Debug Info:")
            if 'debug_info' in result:
                debug = result['debug_info']
                print(f"  Image types detected:")
                for img_field, img_type in debug['image_types'].items():
                    print(f"    {img_field}: {img_type}")
                print(f"  SKU extracted: {debug['sku_extracted']}")
            
            if 'processing' in result:
                proc = result['processing']
                print(f"📊 Processing Results:")
                print(f"  SKU lookup success: {proc['sku_lookup']['success']}")
                if proc['sku_lookup']['success']:
                    print(f"  Found SKU: {proc['sku_lookup']['sku']}")
                print(f"  Updates made: {proc['updates']['fields_updated']}")
                if proc['errors']:
                    print(f"  Errors: {proc['errors']}")
        else:
            print(f"❌ Error: {response.status_code}")
            try:
                error_detail = response.json()
                print(f"Error details: {json.dumps(error_detail, indent=2)}")
            except:
                print(f"Raw response: {response.text}")
                
    except Exception as e:
        print(f"❌ Exception: {str(e)}")

if __name__ == "__main__":
    print("🔍 Qboid Measurement Debug Test")
    print("=" * 50)
    test_debug_endpoint()
