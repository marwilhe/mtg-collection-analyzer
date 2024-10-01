import copy
import sqlite3
from msvcrt import getch

from menu import Menu
from database import database_format, edition_code_map
from gallery import show_gallery

def get_available_editions(collection):
    return list(set((card.edition_full, edition_code_map[card.edition] if card.edition in edition_code_map else card.edition) for card in collection.card_list))

def get_edition_statistics(collection, database, edcode):                    
    conn = sqlite3.connect(database.database_file)
    cur=conn.cursor()
                        
    cur.execute('SELECT * FROM Cards WHERE edition=? GROUP BY name',(edcode,))
    rows = cur.fetchall()
    
    if len(rows) == 0:
        print("No edition named {0} found!".format(edcode))
        return "", {}
    
    class CardPlaceholder:
        name = ""
        rarity = ""
        edition = ""
        edition_full = ""
        image_url = ""
        owned = False
        owned_exact = False
    
    ed_list = []
    for row in rows:
        ed_list.append(CardPlaceholder())
        for idx, tag in enumerate(database_format):
            if tag == "name":
                ed_list[-1].name = row[idx]
            if tag == "rarity":
                ed_list[-1].rarity = row[idx]     
            if tag == "edition":
                ed_list[-1].edition = row[idx]
            if tag == "edition_full":
                ed_list[-1].edition_full = row[idx]
            if tag == "img_uri":
                ed_list[-1].image_url = row[idx]
    
    conn.close()
    
    ed_list.sort(key=lambda card: card.name)
    coll_list = collection.card_list
    coll_list.sort(key=lambda card: card.name)
    
    ed_idx = 0
    coll_idx = 0
    while coll_idx < len(coll_list) and ed_idx < len(ed_list):
        if ed_list[ed_idx].name < coll_list[coll_idx].name:
            ed_idx += 1
        elif ed_list[ed_idx].name > coll_list[coll_idx].name:
            coll_idx += 1
        else:
            ed_list[ed_idx].owned = True
            if ed_list[ed_idx].edition == coll_list[coll_idx].edition or ed_list[ed_idx].edition_full == coll_list[coll_idx].edition_full:
                ed_list[ed_idx].owned_exact = True
            coll_idx += 1
            
    statistics = {}
    for card in ed_list:
        if card.name in ["Plains", "Island", "Swamp", "Mountain", "Forest"]:
            continue
            
        if not card.rarity in statistics:
            # Total / Owned / Owned Exact / Missing / Exact Missing / Exact Owned
            statistics[card.rarity] = [0,0,0,[],[],[]]
            
        statistics[card.rarity][0] += 1
        if card.owned:
            statistics[card.rarity][1] += 1
            if card.owned_exact:
                statistics[card.rarity][2] += 1
                statistics[card.rarity][5].append(card)
            else:
                statistics[card.rarity][4].append(card)
        else:
            statistics[card.rarity][3].append(card)

    return statistics

def analyze_collection_statistics(edition_name, statistics):                
    stat_menu = Menu("== Statistics for {0} ==".format(edition_name))
    stat_menu.add_startup_action(lambda: print_rarities())
    stat_menu.add_action("Print missing", lambda: print_missing())
    stat_menu.add_action("Print missing (Gallery)", lambda: print_gallery(3))
    stat_menu.add_action("Print missing exactly (Gallery)", lambda: print_gallery(4))
    stat_menu.add_action("Print owned (Gallery)", lambda: print_gallery(5))
    
    rarity_selection_container = []
    sel_rarity_menu = Menu("Select rarity")
    sel_rarity_menu.add_action("All", lambda: rarity_selection_container.extend(key for key in statistics.keys()))
    for key in statistics.keys():
        sel_rarity_menu.add_action(key, lambda k=key: rarity_selection_container.append(k))
    sel_rarity_menu.add_close_condition(lambda: len(rarity_selection_container) > 0)
    
    def print_rarities():
        print("")
        for rarity, stats in statistics.items():
            print("{0:20s} {1:d}/{2:d} ({3:d} exact)".format(rarity+":", stats[1], stats[0], stats[2]))
            
        print("")
        
    def print_missing():        
        sel_rarity_menu.open()
        if len(rarity_selection_container) > 0:    
            for sel_rarity in rarity_selection_container:
                print("== {0} Missing ==".format(sel_rarity))
                for card in statistics[sel_rarity][3]:
                    print(card.name)
                
                print("")
                print("== {0} Missing Exactly ==".format(sel_rarity))
                for card in statistics[sel_rarity][4]:
                    print(card.name)
                print("")
                
            rarity_selection_container.clear()
            print("Press any key to continue...")
            getch()
            
    def print_gallery(stat_idx):
        sel_rarity_menu.open()
        if len(rarity_selection_container) > 0:
            card_list = []
            for sel_rarity in rarity_selection_container:
                card_list = card_list + statistics[sel_rarity][stat_idx]
                
            show_gallery(card_list,ffoil=lambda card: False,ftitle=lambda card: "")
            rarity_selection_container.clear()
        
    stat_menu.open()
