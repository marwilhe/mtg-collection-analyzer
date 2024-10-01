import os
from os.path import isfile,getmtime
from datetime import datetime
from msvcrt import getch
import sqlite3
import json
import requests

# Differences in Edition Codes between Deckbox and Scryfall
edition_code_map = {"HM": "HML", "FE": "FEM", "OD": "ODY", "WL": "WTH", "UZ": "USG", "6E": "6ED", "3E": "3ED", "4E": "4ED", "5E": "5ED", "7E": "7ED", "MI": "MIR", "EX": "EXO", "PS": "PLS", "IN": "INV", "EX_32": "TMED", "EX_87": "TM19", "EX_106": "TELD", "EX_124": "TSTX", "EX_130": "TAFR", "MM": "MMQ", "AQ": "ATQ", "AL": "ALL", "AP": "APC", "CH": "CHR", "IA": "ICE", "PLIST": "PLST", "NE": "NEM", "PO": "POR", "P2": "P02", "PR": "PCY", "DK": "DRK", "2U": "2ED", "CG": "UDS", "GU": "ULG", "VI": "VIS", "RE": "REN", "ST": "STH", "TE": "TMP", "UG": "UGL", "EX_141": "ANEO", "CSTD": "CST", "OV_7": "OCMD", "EX_49": "TM15", "EX_45": "TM14", "EX_68": "TMM3", "EX_101": "TMH1"}

database_format = ["id", "name", "edition", "edition_full", "nbr", "rarity", "oracle", "released_at", "power", "toughness", "price_usd", "price_usd_foil", "price_eur", "price_eur_foil", "img_uri"]

class Database:
    database_file = ""
    
    def set(self, db):
        self.database_file = db
        
    def is_valid(self):
        return isfile(self.database_file)

def download_card_data():
    try:
        r = requests.get("https://api.scryfall.com/bulk-data")
    except:
        return "", False
    if r.status_code == 200:
        data = r.json()['data']
        #data_idx = 0 # Oracle texts
        data_idx = 2 # Card variants
        uri = data[data_idx]['download_uri']
        name = data[data_idx]['name']+".json"
        size = int(int(data[data_idx]['size'])/1024/1024)
        last_update = data[data_idx]['updated_at'][:19]
        
        if isfile(name):
            creation_date = datetime.utcfromtimestamp(getmtime(name)).strftime("%Y-%m-%dT%H:%M:%S")
            if creation_date >= last_update:
                return name, False
            else:
                print("Scryfall database has changed. Server version: {0} Your version: {1}. Update? (y/n)".format(last_update,creation_date))
                answer = getch().decode('utf8')
                if answer != 'y':
                    return name, False
                else:
                    os.remove(name)
                    
        print("Downloading {0} ({1} MB)...".format(name,size),end='\r')
        file = requests.get(uri,stream=True)        
        with open(name,"wb") as f:
            for chunk in file.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
                    f.flush()
            
        print("Downloading {0} ({1} MB)... finished.".format(name,size))
        
        return name, True
        
    return "", False
        
def create_database(filename, update):
    if isfile(filename):
        print("Create database...",end='\r')
        db_name = filename[:-5]+'.db'
        
        if isfile(db_name):
            if update:
                os.remove(db_name)
            else:
                return db_name
        
        db_parameter_list = ""
        db_insert_list = ""
        db_qm_list = ""
        for tag in database_format:
            db_parameter_list += tag + " text, "
            db_insert_list += tag + ", "
            db_qm_list += "?, "
        db_parameter_list = db_parameter_list[:-2]
        db_insert_list = db_insert_list[:-2]
        db_qm_list = db_qm_list[:-2]
        
        conn = sqlite3.connect(db_name)
        conn.execute("CREATE TABLE Cards (" + db_parameter_list + ");")        
        with open(filename, 'r',  encoding='utf-8') as json_file:
            data = json.load(json_file)
            for item in data:
                insert_list = []
                
                if "promo_types" in item and "alchemy" in item["promo_types"]:
                    continue
                
                for tag in database_format:
                    if tag == "id":
                        insert_list.append(item["id"])
                    elif tag == "name":
                        insert_list.append(item["name"])
                    elif tag == "edition":
                        insert_list.append(item["set"].upper())
                    elif tag == "edition_full":
                        insert_list.append(item["set_name"])
                    elif tag == "nbr":
                        insert_list.append(''.join(filter(lambda x: x.isdigit(), list(item["collector_number"]))))
                    elif tag == "rarity":
                        insert_list.append(item["rarity"].capitalize())
                    elif tag == "oracle":                    
                        if "card_faces" in item:
                            oracle_text = ""
                            for face in item["card_faces"]:
                                oracle_text += face["oracle_text"] + " // "
                            oracle_text = oracle_text[:-4]
                        else:
                            oracle_text = item["oracle_text"]
                        insert_list.append(oracle_text)
                    elif tag == "released_at":
                        insert_list.append(item["released_at"])
                    elif tag == "power":
                        insert_list.append(item["power"] if "power" in item else "")
                    elif tag == "toughness":
                        insert_list.append(item["toughness"] if "toughness" in item else "")
                    elif tag == "price_usd":
                        insert_list.append(item["prices"]["usd"])
                    elif tag == "price_usd_foil":
                        insert_list.append(item["prices"]["usd_foil"])
                    elif tag == "price_eur":
                        insert_list.append(item["prices"]["eur"])
                    elif tag == "price_eur_foil":
                        insert_list.append(item["prices"]["eur_foil"])
                    elif tag == "img_uri":
                        if "image_uris" in item:
                            insert_list.append(item["image_uris"]["normal"])
                        elif "card_faces" in item and "image_uris" in item["card_faces"][0]:
                            insert_list.append(item["card_faces"][0]["image_uris"]["normal"])
                        else:
                            insert_list.append("")
                    else:
                        print("Database Creation Error. Tag " + tag + " not valid.")
                
                conn.execute("INSERT INTO Cards (" + db_insert_list + ") VALUES (" + db_qm_list + ")", tuple(insert_list))
        conn.execute("CREATE INDEX ed_idx ON Cards (edition, nbr)")
        conn.execute("CREATE INDEX edfull_idx ON Cards (edition_full, nbr)")
        conn.execute("CREATE INDEX name_idx ON Cards (name)")
        conn.execute("CREATE INDEX id_idx ON Cards (id)")
        conn.commit()
        conn.close()
        print("Create database... finished.")
        
        return db_name
        
    return ""
    