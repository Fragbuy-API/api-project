import requests
import json

def send_order_to_partner(username, password, json_file_path):
    """
    Send order data to partner using their authentication and passthrough API.
    
    Args:
        username (str): Authentication username
        password (str): Authentication password
        json_file_path (str): Path to the JSON file containing order data
    
    Returns:
        tuple: (success (bool), message (str))
    """
    try:
        # Step 1: Authentication
        auth_url = 'https://dev.fragcan.ca:4278/configuration/v1/PestPasswordAuth/login'
        
        auth_data = {
            "userName": username,
            "password": password
        }
        
        auth_response = requests.post(
            auth_url,
            headers={
                'accept': '*/*',
                'Content-Type': 'application/json;odata.metadata=minimal;odata.streaming=true'
            },
            json=auth_data,
            verify=True
        )
        
        if auth_response.status_code != 200:
            return False, f"Authentication failed. Status code: {auth_response.status_code}, Response: {auth_response.text}"
        
        # Extract token from response
        token = auth_response.text.strip('"')
        
        # Step 2: Load the JSON data
        with open(json_file_path, 'r') as file:
            order_data = json.load(file)
        
        # Step 3: Send data to passthrough endpoint
        passthrough_url = 'https://dev.fragcan.ca:4278/proship/ILS/Utility/passthrough'
        
        # Double encode the JSON as per their example
        payload = json.dumps(json.dumps(order_data))
        
        response = requests.post(
            passthrough_url,
            headers={
                'accept': 'text/plain',
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            },
            data=payload,
            verify=True
        )
        
        if response.status_code == 200:
            return True, f"Data sent successfully! Response: {response.text}"
        else:
            return False, f"Failed to send data. Status code: {response.status_code}, Response: {response.text}"
            
    except Exception as e:
        return False, f"Error: {str(e)}"

# Usage
if __name__ == "__main__":
    # Replace with the actual credentials they provided
    username = "PESTAdmin"
    password = "6ZtIvfh!(_RD"
    json_file_path = "sample_json_data.json"
    
    success, message = send_order_to_partner(username, password, json_file_path)
    print(message)