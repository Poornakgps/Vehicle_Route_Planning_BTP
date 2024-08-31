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
        
merged_routes_alt_file = os.path.join(folder_path, f"merged_routes_{i}.alt.xml")
merged_routes_file = os.path.join(folder_path, f"merged_routes_{i}.xml")
merge_routes_alt(temp_routes_alt_file, merged_routes_alt_file, use_route_distribution=True)
merge_routes(temp_route_file, merged_routes_file)