import psycopg2
import time
from psycopg2.extensions import AsIs
import requests
import numpy as np


def classify_region(lat, lng):
    """
    4 corners of each bounding box, in lat, long coordinates.
    Regions are numbered, mapping to corresponding region code in postgres

    New England - 1
    41.15,-66.00
    47.50,-73.50
    41.15,-73.50
    47.50,-66.00

    Mid-Atlantic - 2
    41.15,-71.65
    36.50,-71.65
    41.15,-78.88
    36.50,-78.88

    New York/Long Island - 3
    40.30,-71.65
    41.15,-74.57
    40.30,-74.57
    41.15,-71.65

    Appalachia - 4
    41.15,-78.88
    36.50,-78.88
    41.15,-84.92
    36.50,-84.92

    Lowland South - 5
    24.60,-75.19
    36.50,-84.92
    24.60,-84.92
    36.50,-75.19

    Inland South - 6
    25.90,-84.92
    36.50,-103.0
    25.90,-103.0
    36.50,-84.92

    Midlands - 7
    36.50,-84.92
    41.15,-103.0
    36.50,-103.0
    41.15,-84.92

    Great Lakes - 8
    41.15,-73.50
    49.00,-88.95
    41.15,-88.95
    49.00,-73.50

    Upper Midwest - 9
    41.15,-88.95
    50.00,-103.0
    41.15,-103.0
    50.00,-88.95

    Western - 10
    28.50,-103.0
    49.50,-125.0
    28.50,-125.0
    49.50,-103.0

    General - 0
    <anything else>

    """

    #make sure lat/lng is in USA
    if lat > 28.50 and lat < 50.00 and lng > -125.0 and lng < -66.0:
        if lat > 41.15 and lat < 47.50 and lng > -73.50 and lng < -66.0:
            return ['New England', 1]
        elif lat > 36.50 and lat < 41.15 and lng > -78.88 and lng < -71.65:
            # Odd case, since the New York area is contained within Mid-Atlantic. Might not work right.
            if lat > 40.30 and lng > -74.57:
                return ['New York', 3]
            return ['Mid-Atlantic', 2]
        elif lat > 36.50 and lat < 41.15 and lng > -84.92 and lng < -78.88:
            return ['Appalachia', 4]
        elif lat > 24.60 and lat < 36.50 and lng > -84.92 and lng < -75.19:
            return ['Lowland South', 5]
        elif lat > 25.90 and lat < 36.50 and lng > -103.0 and lng < -84.92:
            return ['Inland South', 6]
        elif lat > 36.50 and lat < 41.15 and lng > -103.0 and lng < -84.92:
            return ['Midlands', 7]
        elif lat > 41.15 and lat < 49.00 and lng > -88.95 and lng < -73.50:
            return ['Great Lakes', 8]
        elif lat > 41.15 and lat < 50.00 and lng > -103.0 and lng < -88.95:
            return ['Upper Midwest', 9]
        elif lng > -125.0 and lng < -103.0:
            return ['Western', 10]
        else:
            return ['General', 0]
    else:
        return ['Not USA', -1]


def potgres_query():

    connection = psycopg2.connect("dbname=accentclassify user=accent password=classify")
    cursor = connection.cursor()

    # SELECT COUNT(*) FROM speaker_info WHERE birth_place LIKE '% usa%';
    cursor.execute("SELECT (speakerid, sex, lat, lng) FROM speaker_info WHERE birth_place LIKE '% usa%'");
    query_out = cursor.fetchall()

    speaker_results = []
    for result in query_out:
        result_list = list(result[0][1:-1].split(','))
        # result_list[2], result_list[3] = float(result_list[2]), float(result_list[3])
        speaker_results.append(result_list + classify_region(float(result_list[2]), float(result_list[3])))

    cursor.close()
    connection.close()

    return speaker_results


def main():

    speaker_results = potgres_query()

    speakerids = np.asarray(speaker_results)[:,0]
    # s_file = open('speakerids.txt', 'w')
    # for speakerid in speakerids:
    #     s_file.write("%s\n" % speakerid)

    print(np.asarray(speaker_results))
    # convert_audio(np.asarray(speaker_results)[:,0])


# main()