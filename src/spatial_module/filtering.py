import re

def extract_number(s):
    match = re.search(r'\d+(\.\d+)?', s)
    return float(match.group()) if match else None

def parse_constraints(time_constraint_str, distance_constraint_str, origin_name, destination_name):
    time_limit = extract_number(time_constraint_str) if time_constraint_str else None
    if time_limit is None and time_constraint_str and (
        origin_name.lower() in time_constraint_str.lower() or destination_name.lower() in time_constraint_str.lower()):
        time_limit = 5.0  # default time in minutes

    distance_limit = extract_number(distance_constraint_str) if distance_constraint_str else None
    if distance_limit is None and distance_constraint_str and (
        origin_name.lower() in distance_constraint_str.lower() or destination_name.lower() in distance_constraint_str.lower()):
        distance_limit = 300.0  # default distance in meters

    return time_limit, distance_limit

def filter_segments(route_json, time_constraint_str, distance_constraint_str, origin_name, destination_name):
    time_limit, distance_limit = parse_constraints(time_constraint_str, distance_constraint_str, origin_name, destination_name)

    # If no constraints at all, return original route
    if time_limit is None and distance_limit is None:
        return route_json

    updated_segments = []
    for segment in route_json.get("segments", []):
        time_from_origin = segment.get("time_from_origin_min", float('inf'))
        distance_from_origin = segment.get("distance_from_origin_m", float('inf'))

        keep_pois = True
        if time_limit is not None and time_from_origin > time_limit:
            keep_pois = False
        if distance_limit is not None and distance_from_origin > distance_limit:
            keep_pois = False

        if not keep_pois:
            segment["POIs"] = {}  # or [] depending on your structure

        updated_segments.append(segment)

    print(f"Processed {len(updated_segments)} segments. Time limit={time_limit}, Distance limit={distance_limit}")

    return {
        "route_id": route_json.get("route_id"),
        "from": route_json.get("from"),
        "to": route_json.get("to"),
        "length_tot_m": route_json.get("length_tot_m"),
        "time_to_walk_tot_min": route_json.get("time_to_walk_tot_min"),
        "segments": updated_segments
    }
