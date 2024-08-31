import sumolib
import subprocess
import xml.etree.ElementTree as ET
import folium

def generate_routes(trips_file, network_file, output_file):
    """
    Generates routes using SUMO's duarouter.
    """
    subprocess.run(['duarouter', '-n', network_file, '-r', trips_file, '-o', output_file])

def get_route_edges(route_file):
    """
    Extracts the sequence of edges from the route file.
    """
    tree = ET.parse(route_file)
    root = tree.getroot()

    edges = []
    for vehicle in root.findall("vehicle"):
        route = vehicle.find("route")
        if route is not None:
            edges = route.get('edges').split()
            break
    return edges

def get_edge_coordinates(edge_id, net_file):
    """
    Retrieves coordinates for a given edge.
    """
    net = sumolib.net.readNet(net_file)
    edge = net.getEdge(edge_id)
    return edge.getFromNode().getCoord(), edge.getToNode().getCoord()

def get_path_coordinates(edges, net_file):
    """
    Retrieves coordinates for a list of edges.
    """
    coords = []
    for edge_id in edges:
        from_coords, to_coords = get_edge_coordinates(edge_id, net_file)
        coords.append(from_coords)
        coords.append(to_coords)
    return coords


def create_trips_file(from_edge, to_edge, trips_file):
    """
    Creates a trips file with the specified source and destination.
    """
    with open(trips_file, 'w') as f:
        f.write(f"""<?xml version="1.0" encoding="UTF-8"?>
<routes xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/routes_file.xsd">
    <trip id="0" depart="0.00" from="{from_edge}" to="{to_edge}"/>
</routes>""")

def main():
    network_file = 'kharagpur.net.xml'
    trips_file = 'trips.xml'
    route_file = 'routes.xml'
    
    from_edge = '1025056904#9'
    to_edge = '-1024116590#6'
    new_order = "-121645907#14"
    
    create_trips_file(from_edge, to_edge, trips_file)
    
    generate_routes(trips_file, network_file, route_file)
    
    edges = get_route_edges(route_file)
    
    path_coords = get_path_coordinates(edges, network_file)

if __name__ == "__main__":
    main()
