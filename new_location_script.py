import requests
import pandas as pd
import time


API_KEY = "" # Replace with your actual Google API key


# Set the Replicate API token
import os
os.environ["GROQ_API_KEY"] = "" #replace with your own groq api key 
from groq import Groq
# Function to get coordinates of a district using Geocoding API
def get_coordinates(district_name):
    geocoding_url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": district_name + ", Sri Lanka",
        "key": API_KEY
    }
    response = requests.get(geocoding_url, params=params)
    
    if response.status_code == 200:
        data = response.json()
        if data["results"]:
            location = data["results"][0]["geometry"]["location"]
            return location["lat"], location["lng"]
        else:
            print(f"No results found for the district name: {district_name}")
            return None
    else:
        print("Error:", response.status_code)
        return None

# Function to get detailed information (phone number, rating) of a place
def get_place_details(place_id):
    details_url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "place_id": place_id,
        "fields": "name,formatted_address,formatted_phone_number,website,rating",
        "key": API_KEY
    }
    response = requests.get(details_url, params=params)
    
    if response.status_code == 200:
        return response.json().get("result", {})
    else:
        print("Place Details request failed with status:", response.status_code)
        return {}

# Function to extract sub-location using Replicate API
def extract_sub_location(address):
    model = "meta/meta-llama-3-70b-instruct"  # Specify the model
    prompt = f"give me only one exact subloaction for this address so I can directly add your output to my excel sheet. example address -: People's Bank 70 D. S. Senanayake Mawatha, Colombo 00700, subloaction: Senanayake Mawatha example address2: No. 55 McCallum Rd, Colombo 01000, Sri Lanka Sublocation2:McCallum Rd  for you -: {address} sublocation: ? only give me the sublocation name as output no other text needed"

    client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),
)

    chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": prompt,
        }
    ],
    model="llama3-8b-8192",
)
    return chat_completion.choices[0].message.content.strip()  # Clean the response

# Function to get bank/ATM details for a district
def get_bank_atm_details(district_name, radius=5000):
    coordinates = get_coordinates(district_name)
    if not coordinates:
        return []
    
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    bank_atm_data = []
    
    for place_type in ["bank", "atm"]:
        params = {
            "location": f"{coordinates[0]},{coordinates[1]}",
            "radius": radius,
            "type": place_type,
            "key": API_KEY
        }
        
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            places = response.json().get("results", [])
            print(f"Found {len(places)} {place_type}(s) in {district_name}")
            
            for place in places:
                place_id = place.get("place_id")
                if place_id:
                    # Get detailed information for each bank/ATM
                    details = get_place_details(place_id)
                    address = details.get("formatted_address", "")
                    sub_location = extract_sub_location(address)  # Extract sub-location using Replicate

                    data = {
                            "District": district_name,
                            "Place Name": details.get("name", "N/A"),  # Default to "N/A" if not found
                            "Address": address if address else "N/A",  # Default to "N/A" if address is empty
                            "Sub location": sub_location if sub_location else "N/A",  # Default to "N/A" if sub_location is empty
                            "Phone Number": details.get("formatted_phone_number", "N/A"),  # Default to "N/A" if phone number is missing
                            "Rating": details.get("rating", "N/A"),  # Default to "N/A" if rating is missing
                            "Google Map Link": f"https://www.google.com/maps/place/?q=place_id:{place_id}" if place_id else "N/A"  # Default to "N/A" if place_id is missing
}
                    bank_atm_data.append(data)
        else:
            print(f"Nearby Search request for {place_type} failed with status:", response.status_code)
    
    return bank_atm_data

# Function to save data into Excel
def save_to_excel(data):
    # Convert data into DataFrame
    df = pd.DataFrame(data)
    
    # Save to Excel
    df.to_excel("district_bank_atm_sri_lanka.xlsx", index=False, engine="openpyxl")
    # print("Data saved to bank_atm_sri_lanka.xlsx")
    print("district5_bank_atm_sri_lanka.xlsx")

# Main function to gather data for all districts in Sri Lanka
def get_all_banks_atms_for_sri_lanka(districts):
    all_data = []
    for district in districts:
        print(f"Getting data for {district}...")
        district_data = get_bank_atm_details(district)
        all_data.extend(district_data)
        # Sleep to avoid hitting API rate limits
        time.sleep(1)
    
    # Save all data to Excel
    save_to_excel(all_data)

# List of districts in Sri Lanka (you can add more districts)
districts = [
    "Ampara", "Anuradhapura", "Badulla", "Batticaloa", "Colombo",
    "Galle", "Gampaha", "Hambantota", "Jaffna", "Kalutara",
    "Kandy", "Kegalle", "Kilinochchi", "Kurunegala", "Mannar",
    "Matale", "Matara", "Monaragala", "Mullaitivu", "Nuwara Eliya",
    "Polonnaruwa", "Puttalam", "Ratnapura", "Trincomalee", "Vavuniya"
]




get_all_banks_atms_for_sri_lanka(districts)
