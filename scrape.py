from bs4 import BeautifulSoup
import psycopg2
import time
from psycopg2.extensions import AsIs
import requests
import urllib.request
from urllib.request import urlretrieve


def scrape_soup(id_num):

    speakerid = str(id_num).zfill(5)

    urlstr = 'http://accent.gmu.edu/searchsaa.php?function=detail&speakerid=' + str(speakerid)
    
    try:
        url = urllib.request.urlopen(urlstr).read()
    except:
        print("Connected party timed out. Trying again in 5 seconds...")
        time.sleep(5)
        try:
            url = urllib.request.urlopen(urlstr).read()
        except:
            print("Cound not connect to remote server.")
            return {}

    soup = BeautifulSoup(url, "html.parser")

    bio = soup.find_all("ul", class_="bio")

    details = {'speakerid':speakerid}

    for el in bio:
        for element in el:
            line_soup = BeautifulSoup(str(element), "html.parser")
            #print(line_soup.prettify())

            for line in line_soup.findAll("li"):
                label = line.findAll("em")
                #details[label[0].string] = line.string
                attributes = line.text.split(":")
                attributes[0] = clean(attributes[0]).replace(" ", "_").replace("(", "").replace(")", "")
                attributes[1] = clean(attributes[1])
                if "," in attributes[0]:
                    sub_attribute = attributes[0].strip().split(",")
                    sub_value = attributes[1].strip().split(",")
                    details[sub_attribute[0]] = clean(sub_value[0])
                    details[sub_attribute[1][1:]] = clean(sub_value[1])
                else:
                    details[attributes[0]] = attributes[1]

    audio = soup.find("source")
    
    try:
        urlretrieve(audio['src'], "audio/" + speakerid + ".mp3")
    except:
        print("Connected party had URL error while downloading audio. Trying again in 5 seconds...")
        time.sleep(5)
        try:
            urlretrieve(audio['src'], "audio/" + speakerid + ".mp3")
        except:
            print("Cound not connect to remote server to download audio.")
            details['speakerid'] = "*****"

    details.update(loc_to_coord(details['birth_place']))

    return details

def clean(dirty_string):
    if "(map)" in dirty_string:
        return dirty_string.replace("(map)", "")[1:]
    elif "\n" in dirty_string:
        return dirty_string[1:dirty_string.rfind("\n")]
    else:
        cleaner = dirty_string.strip()
        if cleaner.isdigit():
            return int(cleaner)
        if cleaner == 'none':
            return None
        else:
            return cleaner

def loc_to_coord(location_str):

    geo_url = "http://www.mapquestapi.com/geocoding/v1/address"

    params = { "key" : "2uqjFr4svp1HHPPdGV8ivxALz9z7ZyT8", 
                         "location" : location_str,
                         "thumbMaps" : "false",
                         "maxResults " : "1" }

    response = requests.get(geo_url, params=params).json()

    try:
        birth_country = response['results'][0]['locations'][0]['adminArea1']
        if location_str.endswith("usa ") and birth_country == "US":
            coords = response['results'][0]['locations'][0]['latLng']
            coords['birth_country'] = birth_country
        else:
            coords = {}
            coords['birth_country'] = '??'
    except:
        return {}

    return coords

def insert_into_db(speaker_info, conn, cur, num):
    # print(speaker_info)

    columns = speaker_info.keys()
    values = [speaker_info[column] for column in columns]

    insert_template = 'insert into speaker_info (%s) values %s'
    insert_statement = cur.mogrify(insert_template, (AsIs(','.join(columns)), tuple(values)))
    

    try:
        cur.execute(insert_statement)
        conn.commit()
    except:
        conn.rollback()
        print("Problem inserting speaker #" + str(num))
        print(insert_statement)

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
            return {'region':'New England', 'region_code':1}
        elif lat > 36.50 and lat < 41.15 and lng > -78.88 and lng < -71.65:
            # Odd case, since the New York area is contained within Mid-Atlantic. Might not work right.
            if lat > 40.30 and lng > -74.57:
                return {'region':'New York', 'region_code':3}
            return {'region':'Mid-Atlantic', 'region_code':2}
        elif lat > 36.50 and lat < 41.15 and lng > -84.92 and lng < -78.88:
            return {'region':'Appalachia', 'region_code':4}
        elif lat > 24.60 and lat < 36.50 and lng > -84.92 and lng < -75.19:
            return {'region':'Lowland South', 'region_code':5}
        elif lat > 25.90 and lat < 36.50 and lng > -103.0 and lng < -84.92:
            return {'region':'Inland South', 'region_code':6}
        elif lat > 36.50 and lat < 41.15 and lng > -103.0 and lng < -84.92:
            return {'region':'Midlands', 'region_code':7}
        elif lat > 41.15 and lat < 49.00 and lng > -88.95 and lng < -73.50:
            return {'region':'Great Lakes', 'region_code':8}
        elif lat > 41.15 and lat < 50.00 and lng > -103.0 and lng < -88.95:
            return {'region':'Upper Midwest', 'region_code':9}
        elif lng > -125.0 and lng < -103.0:
            return {'region':'Western', 'region_code':10}
        else:
            return {'region':'General', 'region_code':0}
    else:
        return {'region':'Not USA', 'region_code':-1}

def main():

    connection = psycopg2.connect("dbname=accentclassify user=accent password=classify")
    cursor = connection.cursor()


    """
    postgres table schema:
      id                            serial      PRIMARY KEY
      speakerid                     char(5)     unique ID that maps to .mp3 of the same name
      sex                           varchar     
      birth_place                   varchar
      birth_country                 varchar
      english_residence             varchar
      length_of_english_residence   varchar
      age                           decimal
      age_of_english_onset          decimal
      lat                           decimal
      lng                           decimal
      english_learning_method       varchar
      native_language               varchar
      other_languages               varchar
    """
    table_schema = ("id serial PRIMARY KEY, speakerid char(5), sex varchar, birth_place varchar, "
                    "birth_country varchar, english_residence varchar, length_of_english_residence varchar, "
                    "age decimal, age_of_english_onset decimal, lat decimal, lng decimal, "
                    "english_learning_method varchar, native_language varchar, other_languages varchar")

    # try:
    #     cursor.execute("CREATE TABLE speaker_info (" + table_schema + ");")
    # except:
    #     connection.rollback()
    #     try:
    #         cursor.execute("DROP TABLE speaker_info;")
    #         cursor.execute("CREATE TABLE speaker_info (" + table_schema + ")")
    #     except:
    #         connection.rollback()
    #         print("Problem interacting with database, halting execution.")
    #         return
    # connection.commit()

    for i in range(1, 672):
        new_speaker = scrape_soup(i)
        insert_into_db(new_speaker, connection, cursor, i)
        print("Finished with speaker #" + str(str(i).zfill(5)))

    #cursor.execute("SELECT * FROM speaker_info;")    
    #print(cursor.fetchone())
    cursor.close()
    connection.close()

main()