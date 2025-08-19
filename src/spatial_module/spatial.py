# %%
import geopandas as gpd
import pandas as pd
import json
import re
from geopy.geocoders import Nominatim
from shapely.geometry import box
from .routing import routing_graphhopper
from .enrichment import categorize_pois, add_pois_areas_to_gdf, pois, aggregate_segment_pois_by_type
from .filtering import filter_segments
from .visualization import visualize_rag, visualize_no_rag


# ----- CONFIGURATION -----
OWM_API_KEY = "XXXX"
ORS_API_KEY = "XXXX"
GRAPHHOPPER_API = "XXXX"

# %%
def spatialModule(start, end, pois_list=[], time_constraint=None, space_constraint=None):
    """
    Main function to handle spatial queries and routing.
    Args:
        start (str): Starting location as a string.
        end (str): Ending location as a string.
        pois_list (list, optional): List of points of interest. Defaults to None.
    Returns:
        dict: A dictionary containing the routing results and POIs.
    """
    
    geolocator = Nominatim(user_agent="my_app")
    locA = geolocator.geocode(start)
    locB = geolocator.geocode(end)
    
    if not locA or not locB:
        return "Try again, the locations could not be found."
    
    latA, lonA = locA.latitude, locA.longitude
    latB, lonB = locB.latitude, locB.longitude
    
    # bbox = box(lonA, latA, lonB, latB)
    # bbox = bbox.buffer(0.01)  # buffer by 0.01 degrees (approx 1 km)
    # bbox_bounds = bbox.bounds  # get the bounding box of the buffered area
    # bbox_gdf = gpd.GeoDataFrame(geometry=[bbox], crs="EPSG:4326")
    
    bbox = box(min(lonA, lonB), min(latA, latB), max(lonA, lonB), max(latA, latB))
    bbox = bbox.buffer(0.01)
    bbox = bbox.simplify(0)
    
    # ----- GET THE ROUTES -----
    routes = routing_graphhopper(lonA, latA, lonB, latB, mode='foot', graphhopper_api_key=GRAPHHOPPER_API, number_of_routes=1)
    
    # ----- POINTS OF INTEREST -----
    
    if pois_list != []:
        
        requested_pois = categorize_pois(pois_list)
        if 'shop' in requested_pois:
            requested_pois['shop'] = True
        print(f"Requested POIs: {requested_pois}")
        poi_keys_for_segments = list(requested_pois.keys())
        
    else:
        requested_pois = {
            "tourism": ["museum", "gallery", "monument", "information"]
        }
        poi_keys_for_segments = list(requested_pois.keys())
        
    requested_pois_gdf = pois(bbox, requested_pois)
    routes_gdf= add_pois_areas_to_gdf(routes, requested_pois_gdf, distance=100)
    
    routes_gdf['segment_id'] = routes_gdf.index
    routes_gdf = routes_gdf.to_crs("EPSG:4326")
    routes_gdf = routes_gdf.set_geometry('geometry')
    
    cols_to_drop_duplicates = ['route_id','segment_id']
        
    if 'name' in routes_gdf.columns:
         cols_to_drop_duplicates.append('name')
    
    # Add the columns that are relevant for deduplication
    cols_to_drop_duplicates += [col for col in routes_gdf.columns if col in poi_keys_for_segments]
        
    routes_gdf = routes_gdf.drop_duplicates(subset=cols_to_drop_duplicates)
    
    # ----- ROUTE SUMMARY ----- 
    routes_grouped = routes_gdf.groupby("route_id")
    routes_summary = []

    for route_id, group in routes_grouped:
        
        aggregated_geom = group.unary_union
        agg_gdf = gpd.GeoDataFrame(geometry=[aggregated_geom], crs=group.crs)
        centroid = agg_gdf.geometry.centroid.iloc[0]
        centroid_latlon = gpd.GeoSeries([centroid], crs=group.crs).to_crs("EPSG:4326").iloc[0]
        centroid_lat, centroid_lon = centroid_latlon.y, centroid_latlon.x
        # Calculate the route length in meters.
        route_length = agg_gdf.to_crs("EPSG:3857").geometry.length.iloc[0]
        route_length = round(route_length, 2)  # round to 2 decimal places
                
        # Calculate the total time to walk the route (assuming average walking speed of 1.39 m/s)
        time_to_walk_tot = route_length / 83 # 1.39 / 60  # in minutes
        time_to_walk_tot = round(time_to_walk_tot, 2)  # round to 2 decimal places    
        
        print(f"Processing route {route_id} with length {route_length} m and total time to walk {time_to_walk_tot} min")
        
        n_segments = 0
        tot_length = 0
        
        # Process each segment
        segments_info = []
        
        for seg_id, seg_group in group.groupby('segment_id'):
                
            n_segments += 1

            # Compute the segment geometry and its length
            segment_length = seg_group.to_crs("EPSG:3857").geometry.length.iloc[0]
            segment_length = round(segment_length, 2)  # round to 2 decimal places
            tot_length += segment_length
            
            # Compute time to walk the segment (assuming average walking speed of 1.39 m/s)
            # time_to_walk = segment_length / 1.39  # in seconds
            time_to_walk = tot_length / 83 #1.39 / 60  # in minutes
            time_to_walk = round(time_to_walk, 2)  # round to 2 decimal places
                
            categories_list = list(requested_pois.keys())
            poi_details = aggregate_segment_pois_by_type(seg_group, detailed_categories=categories_list)
            
            instruction = seg_group["instruction"].iloc[0] if "instruction" in seg_group.columns and pd.notna(seg_group["instruction"].iloc[0]) else "Continue"
        
            if "Turn" in instruction:
                instruction = instruction + f" after {round(segment_length)} meters"
            elif "Continue" in instruction:
                instruction = instruction + f" for {round(segment_length)} meters"
            elif "Walk" in instruction:
                instruction = instruction + f" for {round(segment_length)} meters"
            elif "Head" in instruction:
                instruction = instruction + f" for {round(segment_length)} meters"
            
            segments_info.append({
                "segment_id": seg_id,
                "instruction": instruction,
                "POIs": poi_details,
                "time_from_origin_min": time_to_walk,  # time to walk this segment in minutes
                "time_to_destination_min": round(time_to_walk_tot - time_to_walk, 2) if (time_to_walk_tot - time_to_walk)>0 else 0,  # time to walk this segment in minutes
                "distance_from_origin_m": round(tot_length, 2),  # distance of this segment in meters
                "distance_to_destination_m": round(route_length - tot_length, 2) if (route_length - tot_length)>0 else 0,  # distance to the end of the route in meters
            })
            
        route_dict = {
            "route_id": route_id,
            "from": start,
            "to": end,
            "length_tot_m": route_length,
            "time_to_walk_tot_min": time_to_walk_tot,  # total time in minutes
            "segments": segments_info
        }
        routes_summary.append(route_dict)
        
    # ---- FILTER THE RESULTS -----
    filtered_routes = []
    for route in routes_summary:
        filtered_segments = filter_segments(route, time_constraint, space_constraint, start, end)
        if filtered_segments['segments']:
            filtered_routes.append(filtered_segments)
    
    routes_summary = filtered_routes
            
    # ----- SAVE THE RESULTS -----
        
    if len(routes_summary) == 0:
        raise "No routes found. Please try again with different locations."
    else:
        with open('routes_summary.json', 'w') as f:
            json.dump(routes_summary[0], f, indent=4)
            
            filtered_segment_ids = [seg['segment_id'] for seg in routes_summary[0]['segments']]
            filtered_route_id = routes_summary[0]['route_id']
            
            # Filtra i segmenti dalla routes_gdf
            filtered_segments_gdf = routes_gdf[
                (routes_gdf['route_id'] == filtered_route_id) &
                (routes_gdf['segment_id'].isin(filtered_segment_ids))
            ]

            # Estrai tutti gli OSMID unici dai segmenti filtrati
            osmids = set()
            if 'osmid' in filtered_segments_gdf.columns:
                for val in filtered_segments_gdf['osmid']:
                    # Può essere singolo ID o lista
                    if isinstance(val, list):
                        osmids.update(val)
                    else:
                        osmids.add(val)
            
            # Filtra i POIs usando gli osmid
            pois_near_segments = requested_pois_gdf[requested_pois_gdf['osmid'].isin(osmids)].copy()

            
        return routes_summary[0], routes_gdf, pois_near_segments, locA, locB

# # %%
# # Example usage:
# result, route_gdf, pois_near_segments, start, end = spatialModule("Notre-dame, Paris", "Louvre museum, Paris", pois_list=['restaurant','museum'], time_constraint="", space_constraint="400 meters")
# # %%
# text = """
# To get to the Louvre museum from the Notre-Dame, I'll provide you with a walking route that meets your requirements.\n\nFirst, let's start at the Notre-Dame Cathedral. From there, head east on Rue de la Cité toward Rue de la Cité. Continue on this street for about 150 meters until you reach the Seine River. \n\nTurn left onto the Quai de Montebello and walk along the river for about 200 meters. You'll pass by the Sainte-Chapelle on your right, which is a beautiful Gothic chapel worth visiting. It's within your 400-meter radius.\n\nContinue on Quai de Montebello for another 100 meters until you reach the Pont des Arts. This pedestrian bridge offers stunning views of the Seine River and the city. \n\nCross the Pont des Arts and continue on the Quai du Louvre for about 200 meters. You'll see the Louvre Museum on your right. \n\nBefore entering the museum, let's find a place to eat. There's a charming restaurant called Le Grand Vefour, located at 14 Rue de Beaujolais, about 100 meters from the Louvre Museum. They serve classic French cuisine in an elegant setting.\n\nAfter lunch, you can visit the Louvre Museum, which is one of the world's largest and most famous museums. The museum's collections include the Mona Lisa, Venus de Milo, and many other famous artworks.\n\nThe total walking distance from the Notre-Dame to the Louvre Museum is approximately 600 meters, and the estimated time is about 12-15 minutes.
# """

# m_rag, center = visualize_rag(route_gdf, pois_near_segments, result, start, end)
# m_no_rag = visualize_no_rag(text, GRAPHHOPPER_API, center, start, end)
# %%
