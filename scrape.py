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