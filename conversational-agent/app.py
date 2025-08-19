import sys
import os

# Aggiungi il path al livello superiore (dove si trova 'src')
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask, request, jsonify
from flask_cors import CORS
import folium
import os 
from src.spatial_module.visualization import visualize_no_rag, visualize_rag
from src.spatial_module.spatial import spatialModule

app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Resource Sharing

@app.route('/api/query', methods=['POST'])
def handle_query():
    data = request.get_json()
    user_query = data.get('query')     
    rag_enabled = data.get('rag', True)
    
    result, route_gdf, pois_near_segments, start, end = spatialModule("Notre-dame, Paris", "Louvre museum, Paris", pois_list=['restaurant','museum'], time_constraint="", space_constraint="400 meters")
    # compute center of the route
    answer = ""
    map_html = "" 
    
    if rag_enabled:
    
        map_rag, center = visualize_rag(route_gdf, pois_near_segments, result, start, end)
        
        if user_query.startswith('I would like to go'):
            answer = """Here's your walking route from the Notre-Dame to the Louvre museum in Paris:
 
                        The total route length is approximately 2.5 kilometers and will take around 30 minutes to walk. You'll have the opportunity to visit some interesting points of interest along the way.
                        
                        As you continue from the Notre-Dame, you'll pass by the Crypte Archéologique du Parvis Notre-Dame, a museum showcasing the archaeological history of the area. You'll also have the chance to grab a bite to eat at the Crèperie du Cloître, a cozy restaurant serving delicious crepes.
                        
                        Here's your walking route:
                        
                        Continue for 123 meters. You'll pass by the Crypte Archéologique du Parvis Notre-Dame and the Crèperie du Cloître.
                        
                        Continue for 4 meters. You'll still be near the Crypte Archéologique du Parvis Notre-Dame and the Crèperie du Cloître.
                        
                        Continue for 5 meters. You'll still be near the Crypte Archéologique du Parvis Notre-Dame and the Crèperie du Cloître.
                        
                        Turn left after 18 meters. You'll still be near the Crypte Archéologique du Parvis Notre-Dame and the Crèperie du Cloître.
                        
                        Turn slight right after 6 meters. You'll still be near the Crypte Archéologique du Parvis Notre-Dame and the Crèperie du Cloître.
                        
                        Continue for 92 meters. You'll pass by the Crypte Archéologique du Parvis Notre-Dame and the Crèperie du Cloître.
                        
                        Continue for 39 meters. You'll pass by the Crypte Archéologique du Parvis Notre-Dame.
                        
                        Continue for 2 meters. You'll pass by the Crypte Archéologique du Parvis Notre-Dame.
                        
                        Continue for 60 meters. You'll pass by the Crypte Archéologique du Parvis Notre-Dame.
                        
                        Turn right after 45 meters. You'll pass by the Crypte Archéologique du Parvis Notre-Dame.
                        
                        Continue for 6 meters. You'll pass by the Crypte Archéologique du Parvis Notre-Dame.
                        
                        Continue for 103 meters.
                        
                        Continue for 3 meters.
                        
                        Continue for 47 meters.
                        
                        Continue for 3 meters.
                        
                        Continue for 56 meters.
                        
                        Turn left after 22 meters.
                        
                        Turn right after 181 meters.
                        
                        Continue for 7 meters.
                        
                        Turn left after 175 meters.
                        
                        Keep right.
                        
                        Keep right.
                        
                        Continue for 17 meters.
                        
                        Continue for 12 meters.
                        
                        Turn right after 9 meters.
                        
                        Continue for 124 meters.
                        
                        Continue for 3 meters.
                        
                        Continue for 3 meters.
                        
                        Turn sharp left after 7 meters.
                        
                        Keep right.
                        
                        Continue for 43 meters.
                        
                        Continue for 296 meters.
                        
                        Turn right after 29 meters.
                        
                        Turn left after 7 meters.
                        
                        Turn right after 9 meters.
                        
                        Turn left after 16 meters.
                        
                        Continue for 4 meters.
                        
                        Continue for 22 meters.
                        
                        Continue for 7 meters.
                        
                        Keep right.
                        
                        Continue for 58 meters.
                        
                        Continue for 25 meters.
                        
                        Continue for 9 meters.
                        
                        Keep right.
                        
                        Turn right after 54 meters.
                        
                        Continue for 91 meters.
                        
                        Turn right after 2 meters.
                        
                        Continue for 83 meters.
                        
                        Turn right after 10 meters.
                        
                        Turn left after 1 meters.
                        
                        Continue for 66 meters.
                        
                        Continue for 4 meters.
                        
                        Turn left onto Place du Louvre after 31 meters.
                        
                        Turn right after 8 meters.
                        
                        Turn left after 171 meters.
                        
                        Turn slight right after 36 meters.
                        
                        Turn left after 35 meters.
                        
                        Turn slight right after 112 meters.
                        
                        Turn sharp right after 26 meters.
                        
                        Continue for 20 meters.
                        
                        Continue for 32 meters.
                        
                        You have arrived at the Louvre museum. Enjoy your visit!"""
            
            map_html = map_rag._repr_html_()#.replace('width="100%"', 'width="100%" height="500"')
        elif user_query.startswith('What can I find'):
            answer = "The Crypte Archéologique in Paris is located under the Notre Dame forecourt, now known as the Place of Pope John Paul II. It houses an Early Christian archaeological crypt."
    else:
        # If RAG is not enabled, we just return the original query
        if user_query.startswith('I would like to go'):
            answer = "To get to the Louvre museum from the Notre-Dame, I'll provide you with a walking route that meets your requirements.\n\nFirst, let's start at the Notre-Dame Cathedral. From there, head east on Rue de la Cité toward Rue de la Cité. Continue on this street for about 150 meters until you reach the Seine River. \n\nTurn left onto the Quai de Montebello and walk along the river for about 200 meters. You'll pass by the Sainte-Chapelle on your right, which is a beautiful Gothic chapel worth visiting. It's within your 400-meter radius.\n\nContinue on Quai de Montebello for another 100 meters until you reach the Pont des Arts. This pedestrian bridge offers stunning views of the Seine River and the city. \n\nCross the Pont des Arts and continue on the Quai du Louvre for about 200 meters. You'll see the Louvre Museum on your right. \n\nBefore entering the museum, let's find a place to eat. There's a charming restaurant called Le Grand Vefour, located at 14 Rue de Beaujolais, about 100 meters from the Louvre Museum. They serve classic French cuisine in an elegant setting.\n\nAfter lunch, you can visit the Louvre Museum, which is one of the world's largest and most famous museums. The museum's collections include the Mona Lisa, Venus de Milo, and many other famous artworks.\n\nThe total walking distance from the Notre-Dame to the Louvre Museum is approximately 600 meters, and the estimated time is about 12-15 minutes." 
            
            route_gdf_ = route_gdf[route_gdf['route_id'] == 0]
            route_gdf_ = route_gdf_.to_crs(epsg=4326)  # Convert to WGS84 for folium
            center = route_gdf_.geometry.unary_union.centroid
    
            map_no_rag = visualize_no_rag(answer, "", center, start, end)
            map_html = map_no_rag._repr_html_().replace('width="100%"', 'width="100%" height="300"')
        elif user_query.startswith('What can I find'):
            answer = """The Crypte Archéologique (also known as the Crypte des Arènes de Lutèce) is an archaeological museum located in Paris, France. It is situated beneath the Place Marguerite de Navarre, near the Boulevard Saint-Michel.
 
                        Inside the Crypte Archéologique, you can find several ancient Roman ruins, including:
                        
                        1. **Remains of the Roman Forum**: The museum houses a section of the ancient Roman Forum, which was the heart of the Roman city of Lutèce (the ancient name for Paris).
                        2. **The Arena of Lutèce**: The museum is built around the remains of the ancient Roman arena, which was used for gladiatorial contests and other public events.
                        3. **Roman Mosaics**: The museum features several well-preserved Roman mosaics, which were discovered during excavations in the area.
                        4. **Roman Inscriptions**: You can see many Roman inscriptions, which provide valuable information about the history of the city and its inhabitants.
                        5. **Exhibits on the History of Paris**: The museum also offers exhibits on the history of Paris, from the Roman era to the present day.
                        
                        The Crypte Archéologique is a unique and fascinating museum that offers a glimpse into the rich history of Paris."""
            #map_html = ""
    # # read html map
    # m = folium.Map(location=[51.505, -0.09], zoom_start=13)
     
    # map_html = m._repr_html_()#.replace('width="100%"', 'width="100%" height="500"')

    response = {
        'response': f'{answer}',
        'map_html': map_html
    }

    return jsonify(response)

if __name__ == '__main__':
    app.run(port=8000)


