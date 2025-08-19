
import geopandas as gpd
import pandas as pd
import osmnx as ox

def categorize_pois(poi_list):
    mapping = {
        "art_centre": "tourism",
        "bakery": "amenity",
        "bar": "amenity",
        "biergarten": "amenity",
        "bench": "amenity",
        "books": "shop",
        "cafe": "amenity",
        "castle": "tourism",
        "cinema": "amenity",
        "church": "place_of_worship",
        "clothes": "shop",
        "convenience": "shop",
        "dance": "leisure",
        "drinking_water": "amenity",
        "fast_food": "amenity",
        "fountain": "amenity",
        "gallery": "tourism",
        "garden": "leisure",
        "ice_cream": "amenity",
        "information": "tourism",
        "monument": "tourism",
        "museum": "tourism",
        "nature_reserve": "leisure",
        "nightclub": "amenity",
        "park": "leisure",
        "pitch": "leisure",
        "place_of_worship": "place_of_worship",
        "pub": "amenity",
        "restaurant": "amenity",
        "shop": "shop",
        "sports_centre": "leisure",
        "stadium": "leisure",
        "supermarket": "shop",
        "temple": "place_of_worship",
        "toilets": "amenity"
    }

    categorized = {}
    for poi in poi_list:
        key = mapping.get(poi)
        if key:
            categorized.setdefault(key, []).append(poi)
        else:
            categorized.setdefault("unknown", []).append(poi)
    return categorized

def pois(polygon, tags):
    """
    Get the green areas within a polygon using OSMnx.
    """
    # Get the green areas within the polygon
    gdf = ox.geometries_from_polygon(polygon, tags=tags)

    cols = [col for col in gdf.columns if col in tags.keys()]
    cols.append('name')
    cols.append('geometry')
    
    if 'name' not in gdf.columns:
        gdf['name'] = None
    
    gdf = gdf[cols]
    gdf = gdf.reset_index()
    
    return gdf  

def add_pois_areas_to_gdf(gdf, pois_gdf, distance=100):
    """
    Add green areas to a GeoDataFrame.
    """

    gdf = gdf.to_crs("EPSG:3857")
    pois_gdf = pois_gdf.to_crs("EPSG:3857")
    gdf['buffer'] = gdf.geometry.buffer(distance)
    routes_gdf = gdf.set_geometry('buffer').sjoin(pois_gdf, how='left', predicate='intersects')
    routes_gdf = routes_gdf.to_crs("EPSG:4326")
    
    return routes_gdf

def aggregate_segment_pois_by_type(seg_df, detailed_categories=["tourism"]):
    # Simple categories: we ignore name and record the type directly.
    # simple_categories = ["highway", "footway", "wheelchair"]

    for cat in detailed_categories:
        if cat not in seg_df.columns:
            detailed_categories.remove(cat)
    
    if detailed_categories == []:
        return {}
        
    poi_info = {}

    # Process detailed categories:
    for cat in detailed_categories:
        # Initialize a dictionary for this category
        cat_info = {}
        # Select rows where the category is not null
        df_cat = seg_df[seg_df[cat].notnull()]
        if not df_cat.empty:
            for _, row in df_cat.iterrows():
                poi_type = row[cat]
                # Determine if there is a valid name for the POI.
                poi_name = row["name"] if "name" in row and pd.notnull(row["name"]) else None
                # If not seen before, initialize
                if poi_type not in cat_info:
                    if poi_name is not None:
                        cat_info[poi_type] = [poi_name]
                    else:
                        cat_info[poi_type] = 1
                else:
                    # If a name is provided and we already have a count (int) then convert to a list.
                    if poi_name is not None:
                        if isinstance(cat_info[poi_type], int):
                            cat_info[poi_type] = [poi_name]
                        else:
                            # Append the name if not already included
                            if poi_name not in cat_info[poi_type]:
                                cat_info[poi_type].append(poi_name)
                    else:
                        if isinstance(cat_info[poi_type], int):
                            cat_info[poi_type] += 1
                        # If already a list, we assume names are already present.
            poi_info[cat] = cat_info
    return poi_info