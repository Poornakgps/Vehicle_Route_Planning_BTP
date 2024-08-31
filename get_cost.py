import xml.etree.ElementTree as ET

def parse_routes_alt(file_path):
    """
    Parses the routes.alt.xml file and extracts the cost for each vehicle.
    """
    tree = ET.parse(file_path)
    root = tree.getroot()

    costs = {}

    for vehicle in root.findall('vehicle'):
        vehicle_id = vehicle.get('id')
        route_distribution = vehicle.find('routeDistribution')
        if route_distribution is not None:
            for route in route_distribution.findall('route'):
                cost = float(route.get('cost', 0))
                costs[vehicle_id] = cost
    
    return costs

def main():
    routes_alt_file = 'routes.alt.xml'
    
    costs = parse_routes_alt(routes_alt_file)
    
    for vehicle_id, cost in costs.items():
        print(f"Vehicle ID: {vehicle_id}, Cost: {cost}")

if __name__ == "__main__":
    main()