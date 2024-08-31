def update_trips_with_new_order(trips_file, new_order, folder_path, truck_id):
    """
    Update the trips file by inserting a new order and checking all combinations of paths.
    """
    trips = extract_edges_from_trips(trips_file)
    
    all_combinations = []
    for i in range(len(trips) - 1):
        from_edge = trips[i]
        to_edge = trips[i + 1]
        all_combinations.append((from_edge, new_order, to_edge))
    
    for idx, (from_edge, new_edge, to_edge) in enumerate(all_combinations):
        trip_id = f"{idx}_{truck_id}"
        create_trips_file(from_edge, new_edge, folder_path, trip_id, truck_id, 0)
        create_trips_file(new_edge, to_edge, folder_path, trip_id, truck_id, 1)
    
    output_file = os.path.join(folder_path, f"merged_routes_{truck_id}.xml")
    generate_routes(trips_file, 'kharagpur.net.xml', output_file)
    
    print(f"Updated routes file '{output_file}' created successfully.")