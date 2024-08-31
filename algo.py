import subprocess
import xml.etree.ElementTree as ET
import os
from datetime import datetime
import sys

def generate_routes(trips_file, network_file, output_file):
    """
    Generates routes using SUMO's duarouter.
    """
    subprocess.run(['duarouter', '-n', network_file, '-r', trips_file, '-o', output_file], check=True)

def extract_edges_from_routes(file_path):
    """Extract edges from the routes XML file and return as a list of lists."""

    tree = ET.parse(file_path)
    root = tree.getroot()
    
    all_edges = []

    for vehicle in root.findall('vehicle'):
        route_elem = vehicle.find('route')
        if route_elem is not None:
            edges_str = route_elem.get('edges', '')
            edges = edges_str.split()
            all_edges.append(edges)
    
    return all_edges

def extract_trips(file_path):
    """Extract edges from the trips XML file."""
    tree = ET.parse(file_path)
    root = tree.getroot()

    edges = []
    for trip in root.findall('trip'):
        from_edge = trip.get('from')
        to_edge = trip.get('to')
        edges.append((from_edge, to_edge))
    
    return edges

def parse_routes_alt(file_path):
    """
    Parses the routes.alt.xml file and extracts the cost for each vehicle.
    """
    try:
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

    except ET.ParseError as e:
        print(f"Error parsing the XML file: {e}")
        return {}

def create_trips_file(from_edge, to_edge, folder_path, iteration, trip_id, truck_id, order):
    """
    Creates or updates a trips file with the specified source, destination, and trip_id.
    If the file already exists, the new trip is appended to it.
    """
    trips_file = os.path.join(folder_path, f"trips_{iteration}.xml")
    new_trip = f'<trip id="{trip_id}_{truck_id}_{order}" depart="0.00" from="{from_edge}" to="{to_edge}"/>\n'
    
    if os.path.isfile(trips_file): 
        with open(trips_file, 'r+') as f:
            content = f.read().strip()
            
            if new_trip.strip() not in content:

                if content.endswith('</routes>'):
                    content = content[:-len('</routes>')] 
                f.seek(0)  
                f.write(content + new_trip + '</routes>')
                f.truncate()  
    else:
        with open(trips_file, 'w') as f:
            f.write("""<?xml version="1.0" encoding="UTF-8"?>
<routes xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/routes_file.xsd">
"""+ new_trip + '</routes>')

def merge_routes_alt(input_file, output_file, use_route_distribution=False):
    """
    Merge routes from input_file to output_file, considering route distribution.
    """
    # print(f"Processing files: {input_file} -> {output_file}")
    try:
        tree = ET.parse(input_file)
        root = tree.getroot()
    except FileNotFoundError:
        print(f"Error: The file {input_file} was not found.")
        return
    except ET.ParseError as e:
        print(f"Error parsing {input_file}: {e}")
        return

    merged_root = ET.Element('routes')
    
    vehicles_info = {}

    for vehicle in root.findall('vehicle'):
        vehicle_id_parts = vehicle.get('id').split('_')
        vehicle_index = vehicle_id_parts[1]  

        if vehicle_index not in vehicles_info:
            vehicles_info[vehicle_index] = {'cost': 0.0, 'edges': []}

        if use_route_distribution:
            route_dist_elem = vehicle.find('routeDistribution')
            if route_dist_elem is not None:
                for route_elem in route_dist_elem.findall('route'):
                    route_edges = route_elem.get('edges').split()
                    route_cost = float(route_elem.get('cost', 0))

                    if vehicles_info[vehicle_index]['edges']:
                        if vehicles_info[vehicle_index]['edges'][-1] == route_edges[0]:
                            route_edges = route_edges[1:]
                    
                    vehicles_info[vehicle_index]['edges'].extend(route_edges)
                    vehicles_info[vehicle_index]['cost'] += route_cost
            else:
                print(f"Warning: 'routeDistribution' element not found for vehicle {vehicle.get('id')}.")
        else:
            route_elem = vehicle.find('route')
            if route_elem is not None:
                route_edges = route_elem.get('edges').split()

                if vehicles_info[vehicle_index]['edges']:
                    if vehicles_info[vehicle_index]['edges'][-1] == route_edges[0]:
                        route_edges = route_edges[1:]

                vehicles_info[vehicle_index]['edges'].extend(route_edges)
            else:
                print(f"Warning: 'route' element not found for vehicle {vehicle.get('id')}.")

    for vehicle_index, info in vehicles_info.items():
        vehicle_elem = ET.SubElement(merged_root, 'vehicle', id=vehicle_index, depart='0.00')
        
        if use_route_distribution:
            route_distribution_elem = ET.SubElement(vehicle_elem, 'routeDistribution', last='0')
            new_route_elem = ET.SubElement(route_distribution_elem, 'route', cost=f"{info['cost']:.2f}", probability='1.00000000')
            new_route_elem.set('edges', ' '.join(info['edges']))
        else:
            new_route_elem = ET.SubElement(vehicle_elem, 'route')
            new_route_elem.set('edges', ' '.join(info['edges']))

    merged_tree = ET.ElementTree(merged_root)
    try:
        merged_tree.write(output_file, encoding='UTF-8', xml_declaration=True)
        # print(f"Merged routes file '{output_file}' created successfully.")
    except Exception as e:
        print(f"Error writing to {output_file}: {e}")
        
def merge_routes(input_file, output_file):
    """
    Merge routes from input_file to output_file for 'route.xml', ensuring continuous edge paths.
    """
    # print(f"Processing files: {input_file} -> {output_file}")

    try:
        tree = ET.parse(input_file)
        root = tree.getroot()
    except FileNotFoundError:
        print(f"Error: The file {input_file} was not found.")
        return
    except ET.ParseError as e:
        print(f"Error parsing {input_file}: {e}")
        return

    merged_root = ET.Element('routes')

    vehicles_info = {}

    for vehicle in root.findall('vehicle'):
        vehicle_id = vehicle.get('id')
        parts = vehicle_id.split('_')
        vehicle_id = parts[1]

        if vehicle_id not in vehicles_info:
            vehicles_info[vehicle_id] = {'edges': []}

        route_elem = vehicle.find('route')
        if route_elem is not None:
            route_edges = route_elem.get('edges').split()

            if vehicles_info[vehicle_id]['edges']:
                if vehicles_info[vehicle_id]['edges'][-1] == route_edges[0]:
                    route_edges = route_edges[1:]

            vehicles_info[vehicle_id]['edges'].extend(route_edges)
        else:
            print(f"Warning: 'route' element not found for vehicle {vehicle_id}.")

    for vehicle_id, info in vehicles_info.items():
        vehicle_elem = ET.SubElement(merged_root, 'vehicle', id=vehicle_id, depart='0.00')

        new_route_elem = ET.SubElement(vehicle_elem, 'route')
        new_route_elem.set('edges', ' '.join(info['edges']))

    merged_tree = ET.ElementTree(merged_root)
    try:
        merged_tree.write(output_file, encoding='UTF-8', xml_declaration=True)
        # print(f"Merged routes file '{output_file}' created successfully.")
    except Exception as e:
        print(f"Error writing to {output_file}: {e}")
        
def get(from_edge, to_edge, folder_path, i, trips, network_file, truck_id):
    print(truck_id)
    temp_trips_file = os.path.join(folder_path, f"trips_{i}.xml")
    temp_route_file = os.path.join(folder_path, f"routes_{i}.xml")
    temp_routes_alt_file = os.path.join(folder_path, f"routes_{i}.alt.xml")
    truck =0
    for j, (from_edge1, to_edge1) in enumerate(trips):
        if j<4:
            truck = 1
        elif j<7:
            truck = 2
        else:
            truck = 3

        create_trips_file(from_edge1, to_edge1, folder_path, i, j, truck, 0)

    create_trips_file(from_edge, to_edge, folder_path, i, i, truck_id, 0)
    generate_routes(temp_trips_file, network_file, temp_route_file)
    
    merged_routes_alt_file = os.path.join(folder_path, f"merged_routes_{i}.alt.xml")
    merged_routes_file = os.path.join(folder_path, f"merged_routes_{i}.xml")
    merge_routes_alt(temp_routes_alt_file, merged_routes_alt_file, use_route_distribution=True)
    merge_routes(temp_route_file, merged_routes_file)
    costs = parse_routes_alt(merged_routes_alt_file)
    cost_sum = sum(costs.values())
    print(f"Total cost for iteration {i}: {round(cost_sum, 3)}")
    return cost_sum , merged_routes_file, merged_routes_alt_file

        
def main():
    network_file = 'kharagpur.net.xml'
    new_order = "-1214260859"
    trips_file_path = 'trips.xml'  # Path to your trips XML file

    # Extract trips from the trips XML file
    trips = extract_trips(trips_file_path)

    timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    folder_path = f"output_{timestamp}"
    os.makedirs(folder_path, exist_ok=True)

    min_cost = float('inf')
    best_path_file = ""
    worst_path_file = ""
    max_cost = 0
    truck1 = 0
    trip1 = 0
    truck2 = 0
    trip2 = 0
    to = ""
    truck = 0

    output_file = os.path.join(folder_path, "output.txt")

    with open(output_file, 'w') as f:
        sys.stdout = f
        
        for i, (from_edge, to_edge) in enumerate(trips):
            if '-'+ to != from_edge:
                truck = truck + 1
            if '-' + to != from_edge and i != 0:
                (cost, merge_routes1, merge_routes_alt1) = get(to, new_order, folder_path, 11 + i, trips, network_file, truck - 1)
                if cost < min_cost:
                    min_cost = cost
                    best_path_file = merge_routes1
                    trip1 = 11 + i
                if cost > max_cost:
                    max_cost = cost
                    worst_path_file = merge_routes_alt1
                    trip2 = 11 + i
            to1 = ""
            truck1 = 0
            for j, (from_edge1, to_edge1) in enumerate(trips):
                if i == j:
                    break
                if '-' + to1!= from_edge1:
                    truck1 = truck1 + 1
                if i != j:
                    print(truck1)
                    create_trips_file(from_edge1, to_edge1, folder_path, i, j, truck1, 0)
                to1 = to_edge1
  
            temp_trips_file = os.path.join(folder_path, f"trips_{i}.xml")
            temp_route_file = os.path.join(folder_path, f"routes_{i}.xml")
            temp_routes_alt_file = os.path.join(folder_path, f"routes_{i}.alt.xml")
            
            create_trips_file(from_edge, new_order, folder_path, i, i, truck, 0)
            create_trips_file(new_order, to_edge, folder_path, i, i, truck, 1)
            to1 = ""
            truck1 = 0
            for j, (from_edge1, to_edge1) in enumerate(trips):
                if '-'+ to1!= from_edge1:
                    truck1 = truck1 + 1
                if j <= i:
                    to1 = to_edge1
                    continue

                if i != j:
                    create_trips_file(from_edge1, to_edge1, folder_path, i, j, truck1, 0)
                to1 = to_edge1
            
            generate_routes(temp_trips_file, network_file, temp_route_file)
            
            merged_routes_alt_file = os.path.join(folder_path, f"merged_routes_{i}.alt.xml")
            merged_routes_file = os.path.join(folder_path, f"merged_routes_{i}.xml")
            merge_routes_alt(temp_routes_alt_file, merged_routes_alt_file, use_route_distribution=True)
            merge_routes(temp_route_file, merged_routes_file)

            costs = parse_routes_alt(merged_routes_alt_file)
            cost_sum = sum(costs.values())
            print(f"Total cost for iteration {i}: {round(cost_sum, 3)}")

            if cost_sum < min_cost:
                min_cost = cost_sum
                best_path_file = merged_routes_file
                trip1 = i
            if cost_sum > max_cost:
                max_cost = cost_sum
                worst_path_file = merged_routes_file
                trip2 = i
            to = to_edge

        if '-' + to != from_edge:
            (cost, merge_routes1, merge_routes_alt1) = get(to, new_order, folder_path, 11 + 22, trips, network_file, truck)
            if cost < min_cost:
                min_cost = cost
                best_path_file = merge_routes1
                trip1 = 11 + 33
            if cost > max_cost:
                max_cost = cost
                worst_path_file = merge_routes_alt1
                trip2 = 33
            
        print(f"Minimum cost: {round(min_cost, 3)} at {best_path_file}")
        print(f"Maximum cost: {round(max_cost, 3)} at {worst_path_file}")

    sys.stdout = sys.__stdout__

if __name__ == "__main__":
    main()

