import csv


def store_airports(csv_file):
    """
    This method should only be called once.

    :return:
    """
    airport_list = []
    with open(csv_file, 'r', newline='') as csvfile:
        fieldnames = ['ICAO_code', 'airport_name', 'country_name', 'latitude', 'longitude']
        reader = csv.DictReader(csvfile, fieldnames=fieldnames)
        for row in reader:
            airport_list.append(row)
        airport_list.pop(0)
    return airport_list


def check_airport(airport_list, validate):
    for airport in airport_list:
        if validate == airport["ICAO_code"]:
            return airport
    return None
