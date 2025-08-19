# %%
import geopandas as gpd
import pandas as pd
import json
import folium
import numpy as np
from shapely.geometry import Point, Polygon, MultiPolygon
from geopy.geocoders import Nominatim
from shapely.geometry import box
import spacy
import time
from folium.features import DivIcon

def visualize_rag(route_gdf, pois_near_segments, result, start_point, end_point):
    """
    Visualizes the routing and POIs on a map.
    
    Args:
        route_gdf (GeoDataFrame): GeoDataFrame containing route geometries.
        pois_near_segments (GeoDataFrame): GeoDataFrame containing POIs near segments.
        result (dict): Dictionary containing routing results and POIs.
        
    Returns:
        None
    """
    route_gdf = route_gdf.to_crs(epsg=4326)  # Ensure route_gdf is in WGS84
    pois_near_segments = pois_near_segments.to_crs(epsg=4326)  # Ensure pois_near_segments is in WGS84

    base_icon_mapping = {
    "art_centre": ("tourism", "fa-solid fa-landmark"),
    "bakery": ("amenity", "fa-solid fa-bread-slice"),
    "bar": ("amenity", "fa-solid fa-beer"),
    "biergarten": ("amenity", "fa-solid fa-beer"),
    "bench": ("amenity", "fa-solid fa-chair"),
    "books": ("shop", "fa-solid fa-book"),
    "cafe": ("amenity", "fa-solid fa-coffee"),
    "castle": ("tourism", "fa-solid fa-chess-rook"),
    "cinema": ("amenity", "fa-solid fa-film"),
    "church": ("place_of_worship", "fa-solid fa-church"),
    "clothes": ("shop", "fa-solid fa-tshirt"),
    "convenience": ("shop", "fa-solid fa-store"),
    "dance": ("leisure", "fa-solid fa-music"),
    "drinking_water": ("amenity", "fa-solid fa-tint"),
    "fast_food": ("amenity", "fa-solid fa-burger"),
    "fountain": ("amenity", "fa-solid fa-faucet"),
    "gallery": ("tourism", "fa-solid fa-landmark"),
    "garden": ("leisure", "fa-solid fa-seedling"),
    "ice_cream": ("amenity", "fa-solid fa-ice-cream"),
    "information": ("tourism", "fa-solid fa-info-circle"),
    "monument": ("tourism", "fa-solid fa-monument"),
    "museum": ("tourism", "fa-solid fa-landmark"),
    "nature_reserve": ("leisure", "fa-solid fa-tree"),
    "nightclub": ("amenity", "fa-solid fa-martini-glass"),
    "park": ("leisure", "fa-solid fa-tree"),
    "pitch": ("leisure", "fa-solid fa-futbol"),
    "place_of_worship": ("place_of_worship", "fa-solid fa-church"),
    "pub": ("amenity", "fa-solid fa-beer"),
    "restaurant": ("amenity", "fa-solid fa-utensils"),
    "shop": ("shop", "fa-solid fa-shopping-bag"),
    "sports_centre": ("leisure", "fa-solid fa-dumbbell"),
    "stadium": ("leisure", "fa-solid fa-futbol"),
    "supermarket": ("shop", "fa-solid fa-shopping-cart"),
    "temple": ("place_of_worship", "fa-solid fa-om"),
    "toilets": ("amenity", "fa-solid fa-restroom")
    }

    available_colors = [
        "red", "blue", "green", "purple", "orange", "darkred", "lightred",
        "beige", "darkblue", "darkgreen", "cadetblue", "darkpurple", "white",
        "pink", "lightblue", "lightgreen", "gray", "black", "lightgray",
        "lightgray", "orange", "cadetblue", "lightgreen", "darkblue", "lightblue",
        "lightred", "green", "darkgreen", "darkpurple", "beige", "pink", "darkred",
        "gray", "purple", "blue", "black"
    ]
    
    # Filter for the first route
    if 'route_id' in route_gdf.columns:
        route_gdf = route_gdf[route_gdf['route_id'] == 0]
    
    route_gdf = route_gdf[route_gdf['route_id'] == 0]  # Filter for the first route
    # save the buffered routes to another GeoDataFrame
    # select only segmen_id into result
    segment_ids = []
    for id in result['segments']:
        if id['POIs'] != {}:
            segment_ids.append(id['segment_id'])
        
    route_gdf_ = route_gdf[route_gdf['segment_id'].isin(segment_ids)]
    buffered_routes = route_gdf_[['buffer']].copy()
    buffered_routes['geometry'] = buffered_routes['buffer']
    buffered_routes = buffered_routes.drop(columns=['buffer'])
    buffered_routes = buffered_routes.dissolve()
    
    pois_near_segments = pois_near_segments[pois_near_segments['osmid'].isin(route_gdf_['osmid'].unique())]

    icon_mapping = {}
    for (key, (category, icon)), color in zip(base_icon_mapping.items(), available_colors):
        icon_mapping[key] = (category, icon, color)

    pois_near_segments['icon'] = "fa-solid fa-question"
    pois_near_segments['color'] = "gray"  # Default color

    for key, (category, icon, color) in icon_mapping.items():
        if category in pois_near_segments.columns:
            pois_near_segments.loc[pois_near_segments[category] == key, "icon"] = icon
            pois_near_segments.loc[pois_near_segments[category] == key, "color"] = color
        
    center = route_gdf.geometry.unary_union.centroid 
        
    m = folium.Map((center.y, center.x), zoom_start=14)

    # Aggiungi i POI come marker
    for _, row in pois_near_segments.iterrows():
        geom = row['geometry']
        
        if geom is None:
            continue

        # Se è un Point lo usi direttamente, se è un poligono prendi il centroide
        if isinstance(geom, (Polygon, MultiPolygon)):
            point = geom.centroid
        elif isinstance(geom, Point):
            point = geom
        else:
            continue  # ignora geometrie non supportate

        # Crea icona Font Awesome
        icon_str = row['icon']
        icon_name = icon_str.split()[-1].replace("fa-", "")
        icon_color = row['color']  # Usa il colore associato o un default

        # estrae "landmark" da "fa-solid fa-landmark"
        icon = folium.Icon(icon=icon_name, prefix='fa', color=icon_color)

        # Crea marker con popup
        import pandas as pd

        if pd.notna(row['name']):
            popup_text = row['name']
        else:
            popup_text = next((key for key, (_, icon, _) in icon_mapping.items() if icon == row['icon']), "POI")

        popup_text = popup_text.replace("_", " ").title()
            
        folium.Marker(
            location=[point.y, point.x],
            popup=popup_text,
            icon=icon
        ).add_to(m)

    buffered_routes.explore(style_kwds={
        'color': 'yellowgreen',
        'weight': 1,
        'opacity': 0.1
    }, m=m)

    route_gdf[route_gdf['route_id'] == 0].explore(style_kwds={
        'color': 'green',
        'weight': 3,
        'opacity': 1
    }, m=m)

    folium.Marker(
        location=[start_point.latitude, start_point.longitude],
        popup="Start",
        icon=folium.Icon(color='green', icon='play', prefix='fa')
    ).add_to(m)

    folium.Marker( 
        location=[end_point.latitude, end_point.longitude],
        popup="End",
        icon=folium.Icon(color='red', icon='flag-checkered', prefix='fa')
    ).add_to(m)

    return m, center
# %%
def visualize_no_rag(text, GRAPHHOPPER_API, center, start_point, end_point):
        
    nlp = spacy.load("en_core_web_sm")  # o meglio ancora: un modello Hugging Face
    geolocator = Nominatim(user_agent="my_app")
    entities = {}
    doc = nlp(text)

    # Extract and geocode place-related entities
    labels_of_interest = {"ORG", "LOC", "FAC", "WORK_OF_ART"}

    for ent in doc.ents:
        if ent.label_ in labels_of_interest:
            ent_text = ent.text
            if ent_text.lower().startswith("the "):
                ent_text = ent_text[4:]

            if ent_text in entities:
                continue

            try:
                loc = geolocator.geocode(ent_text + ", Paris")
                if loc:
                    entities[ent_text] = {
                        'location': (loc.latitude, loc.longitude),
                        'raw': loc.raw.get('type', 'unknown')
                    }
                    time.sleep(1)  # avoid overloading the API
            except Exception as e:
                continue

    # # Display ordered points
    # print("Found locations:")
    # for name, data in entities.items():
    #     print(f"{name}: {data['location']} ({data['raw']})")

    # --- Compute routes between consecutive points ---

    # Sort locations in order of appearance in text
    # ordered_names = [ent.text[4:] if ent.text.lower().startswith("the ") else ent.text
    #                 for ent in doc.ents if ent.text in entities]

    # # Remove duplicates while preserving order
    # seen = set()
    # ordered_names = [x for x in ordered_names if not (x in seen or seen.add(x))]

    # final_route = gpd.GeoDataFrame()

    # for i in range(len(ordered_names) - 1):
    #     src = entities[ordered_names[i]]['location'][::-1]  # (lon, lat)
    #     dst = entities[ordered_names[i+1]]['location'][::-1]
    #     try:
    #         route = routing_graphhopper(
    #             src[0], src[1], dst[0], dst[1],
    #             mode='foot', graphhopper_api_key=GRAPHHOPPER_API, number_of_routes=1
    #         )
            
    #         route = route[route['route_id'] == 0]  # Filter for the first route
    #         final_route = pd.concat([final_route, route], ignore_index=True)
            
    #     except Exception as e:
    #         print(f"Failed to route from {ordered_names[i]} to {ordered_names[i+1]}: {e}")
    # %%
            
    # %%
    m = folium.Map(location=(center.y, center.x), zoom_start=14)
    i = 1
    
    for ent_text, ent_data in entities.items():
        print(ent_text, ent_data)
        lat, lon = ent_data['location']
        folium.Marker(
            location=[lat, lon],
            popup=ent_text,
            icon=DivIcon(
            icon_size=(30, 30),
            icon_anchor=(15, 15),
            html=f"""
            <div style="
                background-color: #dc143c;
                color: white;
                border-radius: 50%;
                width: 30px;
                height: 30px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: bold;
                font-size: 14px;
                border: 2px solid #ffffff;
                box-shadow: 0 0 3px rgba(0,0,0,0.4);
            ">
                {i}
            </div>
            """)
        ).add_to(m)
        i += 1
        
    # final_route.explore(m=m, style_kwds={
    #     'color': 'red',
    #     'weight': 3,
    #     'opacity': 1
    # })
    
    folium.Marker(
        location=[start_point.latitude, start_point.longitude],
        popup="Start",
        icon=folium.Icon(color='green', icon='play', prefix='fa')
    ).add_to(m)

    folium.Marker( 
        location=[end_point.latitude, end_point.longitude],
        popup="End",
        icon=folium.Icon(color='red', icon='flag-checkered', prefix='fa')
    ).add_to(m)
    
    return m
# %%