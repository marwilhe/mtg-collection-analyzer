from os import listdir
from os.path import isdir, isfile, join
import copy
import traceback
from msvcrt import getch

from menu import Menu
from collection import Card, Collection
from database import *
from gallery import *
from image_downloader import *
from collection_comparison import *
from set_information import *
from personal_collection import *

class Configuration:
    reference = ""
    decks = ""

def read_config():
    config = Configuration()
    if isfile("cfg/config.txt"):
        print(config.reference)
        with open("cfg/config.txt", encoding='utf8') as f:
            for line in f:
                splitted_line = line.split("=")             
                if splitted_line[0].rstrip() == "reference":
                    config.reference = splitted_line[1].rstrip()
                elif splitted_line[0].rstrip() == "decks":
                    config.decks = splitted_line[1].rstrip()
    return config

def print_sorted(collection, sort_key, reverse):
    collection.sort(key=sort_key, reverse=reverse)
    collection.print_consecutively()

def print_compressed(collection, equal_criteria):    
    collection.compress(equal_criteria=equal_criteria)
    collection.print_consecutively()

def print_filtered(collection, filter_func):
    collection.apply_filter(filter_func)
    collection.print_consecutively()
        
def create_selection_menu(selection_container, data_dirs, name = "Choose collection"): 
    coll_chooser = Menu(name)
    coll_chooser.add_close_condition(lambda: len(selection_container) > 0)
           
    for data_dir in data_dirs:
        if isdir(data_dir):
            for f in listdir(data_dir):
                if isfile(join(data_dir, f)) and f[-4:] == ".csv":
                    coll_chooser.add_action(f, lambda directory=data_dir, file=f: selection_container.append(Collection.from_filename(join(directory,file))))
                
    return coll_chooser
        
def create_selection_menu_with_default(config, selection_container, data_dirs = ["data"]):  
    pc = PersonalCollection.from_config(config)
    coll_chooser = create_selection_menu(selection_container, data_dirs)
    deck_chooser = create_selection_menu(selection_container, [config.decks], "Choose deck")
        
    selection_menu = Menu("Select Collection")
    selection_menu.add_close_condition(lambda: len(selection_container) > 0)
    selection_menu.add_action("Default collection", lambda: selection_container.append(pc.reference_collection))
    selection_menu.set_submenu(coll_chooser)
    
    selection_menu.add_action("Deck collection", lambda: selection_container.append(pc.deck_collection))
    selection_menu.set_submenu(deck_chooser)
            
    return selection_menu
    
def create_compare_menu(collection, compare_collection, fused_container):
    compare_menu = Menu("Compare collections " + collection.name + " / " + compare_collection.name)
    compare_menu.add_close_condition(lambda: True)
    
    compare_menu.add_action("SetMinus", lambda: fused_container.append(setminus(collection, compare_collection)))
    compare_menu.add_action("PriceDiff", lambda: fused_container.append(Collection.from_collection_diff(collection, compare_collection)))
    compare_menu.add_action("Intersect", lambda: fused_container.append(intersect(collection, compare_collection)))
    compare_menu.add_action("Show not contained", lambda: fused_container.append(missing_by_name(collection, compare_collection)))
    
    return compare_menu
    
def start_comparison(collection, config):
    selection_container = []            
    def selection_return():
        if len(selection_container) > 0:                               
            fused_container = []
            def compare_return():            
                if len(fused_container) > 0:        
                    collection_menu = create_collection_menu(fused_container[0], config)
                    collection_menu.open()
                    fused_container.clear()
                    return True
                    
            compare_menu = create_compare_menu(collection, selection_container[0], fused_container)
            compare_menu.add_return_action(lambda: compare_return())
            
            compare_menu.open()        
            
            selection_container.clear()
            return True
        
    selection_menu = create_selection_menu_with_default(config, selection_container)
    selection_menu.add_return_action(lambda: selection_return())
    
    selection_menu.open()    
    
def create_collection_menu(collection, config):
    collection_menu = Menu("Collection{0}".format(": " + collection.name if collection.name != "" else ""))
    
    analyze_menu = create_analysis_menu(collection)
    collection_menu.set_submenu(analyze_menu)
    collection_menu.add_action("Compare with other collection", lambda: start_comparison(collection, config))
    collection_menu.add_action("Show edition list", lambda: show_edition_list())
            
    def compare_collections():
        selection_menu.open()
        
        if len(selected_collections) == 0:
            return
            
    database = Database()
    def show_edition_list():
        if not database.is_valid():
            json_file, update = download_card_data()
            database.set(create_database(json_file, update))
            collection.augment_from_database(database)
                        
        if not database.is_valid():
            print("Connection to Scryfall failed.")
        else:
            editions = get_available_editions(collection)
            editions.sort()
            
            i = 0
            while i < len(editions):
                edition, edcode = editions[i]
                if "Theme" in edition or "Extras" in edition or "Gateway" in edition or "Oversized" in edition or "Promo" in edition or "Duel Deck" in edition or "Friday Night Magic" in edition or "Alternate" in edition or "Foreign White Bordered" in edition or "Art Series" in edition or "Event" in edition:
                    del editions[i]
                else:
                    i += 1
                        
            statistics_by_edcode = {}
            edition_by_edcode = {}
            tmp_coll = copy.deepcopy(collection)
            for edition,edcode in editions:
                statistics_by_edcode[edcode] = get_edition_statistics(tmp_coll, database, edcode)
                edition_by_edcode[edcode] = edition
            
            edcode_container = []
            edition_chooser = Menu("Choose edition...")
            edition_chooser.add_action("By code", lambda: analyze_by_code()) 
            
            def create_list_chooser_menu(name, sort_by_owned = False):
                list_chooser = Menu(name)
                list_chooser.add_close_condition(lambda: len(edcode_container) > 0)
                list_chooser.add_return_action(lambda: list_chooser_return())
                            
                if sort_by_owned:           
                    owned_perc = {}
                    for edition,edcode in editions:
                        ed_stat = statistics_by_edcode[edcode]
                        
                        owned = 0
                        total = 0
                        for stat in ed_stat.values():
                            owned += stat[2]
                            total += stat[0]
                        owned_perc[edcode] = owned / total
                    sorted_editions = sorted(editions, key = lambda edition_pair: owned_perc[edition_pair[1]], reverse = True)
                else:
                    sorted_editions = editions
                    
                for edition,edcode in sorted_editions:
                    ed_stat = statistics_by_edcode[edcode]                
                    edition_line = "{0:60}".format(edition)
                    for rarity in ["Common", "Uncommon", "Rare", "Mythic", "Special"]:
                        if rarity in ed_stat:
                            edition_line += " {0:3.0f}% ({1})".format((ed_stat[rarity][2] * 100) / ed_stat[rarity][0], rarity[0])
                    list_chooser.add_action(edition_line, lambda edc=edcode: edcode_container.append(edc))
                    
                return list_chooser
                                                                
            list_chooser_sort_name = create_list_chooser_menu("From List")
            list_chooser_sort_owned = create_list_chooser_menu("From List (Sort by owned)", sort_by_owned = True) 
            edition_chooser.set_submenu(list_chooser_sort_name)
            edition_chooser.set_submenu(list_chooser_sort_owned)
        
            def analyze_by_code():
                print("Enter edition code")
                edcode = input().strip()
                
                if not edcode in statistics_by_edcode:
                    print("Edition {0} not found.".format(edcode))
                    return
                    
                analyze_collection_statistics(edition_by_edcode[edcode], statistics_by_edcode[edcode])
                
            def list_chooser_return():
                if len(edcode_container) > 0:
                    analyze_collection_statistics(edition_by_edcode[edcode_container[0]], statistics_by_edcode[edcode_container[0]])
                    edcode_container.clear()
                    return True

            edition_chooser.open()
     
    return collection_menu
    
def create_analysis_menu(collection, return_collection_container = None):
    collection_history = []
    active_collection = copy.deepcopy(collection)
    
    menu_name = "Analyze collection" if return_collection_container is None else "Choose cards"
    
    analyze_menu = Menu(menu_name)    
    analyze_menu.add_action("Print", lambda: active_collection.print_consecutively())
    analyze_menu.add_action("Print masked", lambda: print_masked())
    analyze_menu.add_action("Show Gallery", lambda: show_gallery(active_collection.card_list))
    analyze_menu.add_action("Sort", lambda: sort_collection())
    analyze_menu.add_action("Filter", lambda: filter_collection())
    analyze_menu.add_action("Compress", lambda: compress_collection())
    
    if return_collection_container is None:
        special_menu = analyze_menu.add_submenu("Special Action")
        special_menu.add_action("Print content", lambda: active_collection.print_consecutively_with_func(Card.print_content))
        special_menu.add_action("Print statistics", lambda: print_statistics())
        special_menu.add_action("Export to file", lambda: export_to_file())
        special_menu.add_action("Connect to Scryfall", lambda: connect_to_scryfall())
    
    analyze_menu.add_action("Undo", lambda: undo_collection())
    analyze_menu.add_action("Reset", lambda: reset_collection())
    
    if not return_collection_container is None:
        analyze_menu.add_action("Return current collection", lambda: return_current_collection())
        analyze_menu.add_close_condition(lambda: len(return_collection_container) > 0)
    
    
    def handle_ex(ex):            
        print(type(ex).__name__ + "! Print Traceback? (y/n)")
        if getch().decode('utf8') == 'y':
            traceback.print_exc()
        active_collection.set(collection_history[-1])    
        
    print_mask = list("anirlp")
    def print_masked():
        print("Create new mask? (y/n)")
        if getch().decode('utf8') == 'y':
            output = "Input mask. Values: "
            for indicator,value_pair in Card.mask_dic.items():
                output += "{0} ({1}), ".format(value_pair[0], indicator)
            output = output[:-2]
            print(output)
            new_mask = list(input())
            print_mask.clear()
            for char in new_mask:
                print_mask.append(char)
            
        first_line = ""
        idx = 0
        while idx < len(print_mask):
            if print_mask[idx] in Card.mask_dic:
                first_line += Card.mask_dic[print_mask[idx]][0] + " "
                idx += 1
            else:
                del print_mask[idx]
                
        active_collection.print_consecutively_with_func(lambda card: Card.print_masked(card,print_mask))
        
    def sort_collection():
        collection_history.append(copy.deepcopy(active_collection))                
        continue_sorting = True
        
        while continue_sorting:
            print("\nInput sorting key (use 'card' as classname; available properties: {0}):".format(active_collection.properties_as_string()))
            criteria = input()
            try:
                func = lambda card: eval(criteria)                        
                print("Reverse? (y/n)")
                rin = getch().decode('utf8')
                if rin == "y":
                    reverse = True
                else:
                    reverse = False
                print_sorted(active_collection,sort_key=func, reverse=reverse)
            except Exception as ex:
                handle_ex(ex)
                continue
            continue_sorting = False
            
    def filter_collection():
        collection_history.append(copy.deepcopy(active_collection))
        continue_filtering = True
        
        while continue_filtering:
            print("\nInput filter criteria (use 'card' as classname; available properties: {0}):".format(active_collection.properties_as_string()))
            criteria = input()
            try:
                func = lambda card: eval(criteria)                    
                print_filtered(active_collection,filter_func=func)
            except Exception as ex:
                handle_ex(ex)
                continue
                
            continue_filtering = False
            
    def compress_collection():
        collection_history.append(copy.deepcopy(active_collection))
        continue_compress = True
        
        while continue_compress:
            print("\nInput equality criteria (use 'card' as classname; available properties: {0}):".format(active_collection.properties_as_string()))
            criteria = input()
            try:
                func = lambda card : eval(criteria)
                print_compressed(active_collection,equal_criteria=func)
            except Exception as ex:
                handle_ex(ex)
                continue
        
            continue_compress = False
            
    def print_statistics():
        nbr_entries = len(active_collection.card_list)
        if nbr_entries == 0:
            print("Collection is empty!")
            return
            
        tmp_collection = copy.deepcopy(active_collection)
        tmp_collection.compress(lambda card: card.name)
        nbr_different_cards = len(tmp_collection.card_list)
        
        def get_amount_price_greater_than(ref_price):            
            tmp_collection = copy.deepcopy(active_collection)
            tmp_collection.apply_filter(lambda card: card.price >= ref_price)
            if len(tmp_collection.card_list) == 0:
                return 0, 0
                
            tmp_collection.compress(lambda card: True)
            assert(len(tmp_collection.card_list) == 1)
            return tmp_collection.card_list[0].amount, tmp_collection.card_list[0].total_price
        
        nbr_cards_total, price_total = get_amount_price_greater_than(0)
        amount_greater_30, price_greater_30 = get_amount_price_greater_than(0.3)
        amount_greater_50, price_greater_50 = get_amount_price_greater_than(0.5)
        amount_greater_100, price_greater_100 = get_amount_price_greater_than(1)
        
        print("\n=== Statistics ===\n")
        print("There are {0} different entries with {1} different cards.".format(nbr_entries, nbr_different_cards))
        print("Total cards  : {0:5d} ({1:.2f} $)".format(nbr_cards_total, price_total))
        print("Cards > 30ct : {0:5d} ({1:.2f} $)".format(amount_greater_30, price_greater_30))
        print("Cards > 50ct : {0:5d} ({1:.2f} $)".format(amount_greater_50, price_greater_50))
        print("Cards > 1$   : {0:5d} ({1:.2f} $)".format(amount_greater_100, price_greater_100))
            
    def export_to_file():    
        print("Enter filename: ")
        filename = input()
        active_collection.save_to_file("data/" + filename + ".csv")
        
    database = Database()
    def connect_to_scryfall():
        json_file, update = download_card_data()
        database.set(create_database(json_file, update))
        active_collection.augment_from_database(database)
            
    def undo_collection():
        if len(collection_history) > 0:
            active_collection.set(collection_history[-1])
            del collection_history[-1]
            active_collection.print_consecutively()
        else:
            print("Nothing to undo!")
            
    def reset_collection():
        collection_history.append(copy.deepcopy(active_collection))
        active_collection.set(collection)
        
    def return_current_collection():
        return_collection_container.append(copy.deepcopy(active_collection))
    
    return analyze_menu
        
def main():
    config = read_config()
    
    selection_container = []            
    def selection_return():
        if len(selection_container) == 0:
            return False            
            
        collection_menu = create_collection_menu(selection_container[0], config)
        collection_menu.open()
        
        selection_container.clear()
        return True
        
    selection_menu = create_selection_menu_with_default(config, selection_container)
    selection_menu.add_return_action(lambda: selection_return())
    
    selection_menu.open()
    
if __name__ == "__main__":
    main()