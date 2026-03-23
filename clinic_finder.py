import requests
import pandas as pd
import time

def find_care_facilities(city_name):
    print(f"🌍 Querying OpenStreetMap for medical and care facilities in {city_name}...")
    
    # The Overpass API endpoint
    overpass_url = "http://overpass-api.de/api/interpreter"
    
    # We use Overpass QL to ask for hospitals, clinics, and nursing homes
    overpass_query = f"""
    [out:json][timeout:50];
    area[name="{city_name}"]->.searchArea;
    (
      node["amenity"="hospital"](area.searchArea);
      way["amenity"="hospital"](area.searchArea);
      
      node["amenity"="nursing_home"](area.searchArea);
      way["amenity"="nursing_home"](area.searchArea);
      
      node["amenity"="clinic"](area.searchArea);
      way["amenity"="clinic"](area.searchArea);
    );
    out tags;
    """
    
    try:
        response = requests.post(overpass_url, data={'data': overpass_query})
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"⚠️ Error reaching the API: {e}")
        return []

    facilities = []
    
    # Parse the JSON response to extract the useful data
    for element in data.get('elements', []):
        tags = element.get('tags', {})
        
        # We only want facilities that actually have a website, 
        # otherwise our email scraper can't do its job!
        name = tags.get('name')
        website = tags.get('website') or tags.get('contact:website')
        
        if name and website:
            # Clean up the website URL if necessary
            if not website.startswith('http'):
                website = 'https://' + website
                
            facilities.append({
                "Clinic Name": name,
                "URL": website,
                "City": city_name
            })
            
    # Remove duplicates based on URL
    unique_facilities = {fac['URL']: fac for fac in facilities}.values()
    return list(unique_facilities)

# ==========================================
# 🚀 Execution & Export
# ==========================================
if __name__ == "__main__":
    # You can change this to any German city (e.g., "Berlin", "Frankfurt am Main", "Köln")
    target_city = "Sachsen" 
    
    print("🤖 Booting up Clinic Finder Bot...")
    results = find_care_facilities(target_city)
    
    if results:
        print(f"✅ Successfully found {len(results)} facilities with websites in {target_city}!")
        
        # Save to an Excel file so your scraper can read it
        df = pd.DataFrame(results)
        filename = f"found_clinics_{target_city.lower().replace(' ', '_')}.xlsx"
        df.to_excel(filename, index=False)
        print(f"📁 Saved to {filename}")
        
        # Preview the first few
        print("\nPreview of found leads:")
        print(df.head())
    else:
        print(f"❌ No facilities with websites found in {target_city}. Try a larger city.")
