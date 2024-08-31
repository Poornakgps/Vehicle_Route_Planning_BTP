import xml.etree.ElementTree as ET

import xml.etree.ElementTree as ET

def extract_edges_from_routes(route_file):
    tree = ET.parse(route_file)
    root = tree.getroot()

    edges = []

    for vehicle in root.findall('vehicle'):
        route = vehicle.find('route')
        if route is not None:
            edge_list = route.get('edges')
            if edge_list:
                edge_items = edge_list.split()
                edges.extend(edge_items)
    return edges

route_file = 'routes.xml'
edges = extract_edges_from_routes(route_file)
print(edges)


if __name__ == "__main__":
    route_file = 'routes.xml'
    edges = extract_edges_from_routes(route_file)
    print("Edges found in the routes file:", edges)
