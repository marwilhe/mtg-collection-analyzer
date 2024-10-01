from database import database_format, edition_code_map
from os.path import isfile, basename
from msvcrt import getch
import csv
import copy
import sqlite3

class Card:
    # Static variables
    titles = ["Count","Name","Edition Code","Card Number","Condition","Language","Foil","Signed","Artist Proof","Type","Cost","Rarity","Price", "Edition", "Image URL", "Scryfall ID"]
    mask_dic = {
                'a': ["Amount",lambda card: "{0:>4d}".format(card.amount)],
                'n': ["Name",lambda card: "{0:60s}".format(card.name+(" (Foil)" if card.foil else ""))],
                'i': ["Id",lambda card: "{0:11s}".format("("+card.edition+"/"+str(card.card_number)+")")],
                'l': ["Lang",lambda card: "{0:8s}".format(card.language if card.language!="" else "n/a")],
                'm': ["Main Type",lambda card: "{0:25s}".format(card.primary_type)],
                'r': ["Rarity",lambda card: "{0:10s}".format(card.rarity)],
                'c': ["CMC",lambda card: "{0:2d}".format(card.cmc)],
                'r': ["Color", lambda card: "{0:5s}".format(card.color)],
                'p': ["Price",lambda card: "{0:>8s}".format("{0:4.2f}$".format(card.total_price if card.summed else card.price))],
                'f': ["PriceDiff",lambda card: "{0:>8s}".format("{0:3.2f}$".format(card.price_diff) if card.price_diff != 0 else "")],
                'd': ["Price$",lambda card: "{0:>8s}".format("{0:4.2f}$".format(card.total_price_usd if card.summed else card.price_usd) if card.price_usd != 0 else "")],
                'e': ["Price\u20ac",lambda card: "{0:>8s}".format("{0:4.2f}\u20ac".format(card.total_price_eur if card.summed else card.price_eur) if card.price_eur != 0 else "")],
                'v': ["P/T",lambda card: "{0:5s}".format(card.power + "/" + card.toughness if card.power != "" else "")],
                'o': ["Oracle",lambda card: "{0}".format("\n     "+card.oracle_text.replace('\n',' ')+"\n" if card.oracle_text != "" else "")]
            }
            
    # Instance variables
    name = ""
    edition = ""
    edition_full = ""
    condition = ""
    language = ""
    card_type = ""
    main_type = ""
    primary_type = ""
    card_cost = ""
    cmc = 0
    rarity = ""
    card_number = 0
    color = ""
    image_url = ""
    scryfall_id = ""
    scryfall_image_url = ""
    
    amount = 0
    price = 0.0
    price_usd = 0.0
    price_eur = 0.0
    price_diff = 0
    total_price = 0
    total_price_usd = 0
    total_price_eur = 0
    foil = False
    signed = False
    artist_proof = False
    
    oracle_text = ""
    released_at = ""   
    power = ""
    toughness = ""
    
    summed = False

    def __init__(self, parts, mask):
        if self.titles[0] in mask:
            self.amount = int(parts[mask[self.titles[0]]])
        if self.titles[1] in mask:
            self.name = parts[mask[self.titles[1]]]
        if self.titles[2] in mask:
            self.edition = parts[mask[self.titles[2]]].upper()
        if self.titles[3] in mask:
            cnstring = parts[mask[self.titles[3]]]
            if cnstring.isnumeric():
                self.card_number = int(cnstring)
        if self.titles[4] in mask:
            self.condition = parts[mask[self.titles[4]]]
        if self.titles[5] in mask:
            self.language = parts[mask[self.titles[5]]]
        if self.titles[6] in mask:
            self.foil = (parts[mask[self.titles[6]]]=="foil")
        if self.titles[7] in mask:
            self.signed = (parts[mask[self.titles[7]]]=="signed")
        if self.titles[8] in mask:
            self.artist_proof = (parts[mask[self.titles[8]]]=="artist proof")
        if self.titles[9] in mask:
            self.card_type = parts[mask[self.titles[9]]]
            self.extract_main_type()
        if self.titles[10] in mask:
            self.card_cost = parts[mask[self.titles[10]]]
            self.card_cost_to_cmc()
            self.card_cost_to_color()
        if self.titles[11] in mask:
            self.rarity = parts[mask[self.titles[11]]]
        if self.titles[12] in mask:
            self.price = float(parts[mask[self.titles[12]]][1:])
            self.total_price = self.price * self.amount
        if self.titles[13] in mask:
            self.edition_full = parts[mask[self.titles[13]]]
        if self.titles[14] in mask:
            self.image_url = parts[mask[self.titles[14]]]
        if self.titles[15] in mask:
            self.scryfall_id = parts[mask[self.titles[15]]]
            
    def get_csv_row(self, write_prices):
        row = []
        for title in self.titles:
            if title == "Count":
                row.append(str(self.amount))
            elif title == "Name":
                row.append(self.name)
            elif title == "Edition":
                row.append(self.edition_full)
            elif title == "Edition Code":
                row.append(self.edition)
            elif title == "Card Number":
                row.append(self.card_number)
            elif title == "Condition":
                row.append(self.condition)
            elif title == "Language":
                row.append(self.language)
            elif title == "Foil":
                row.append("foil" if self.foil else "")
            elif title == "Signed":
                row.append("signed" if self.signed else "")
            elif title == "Artist Proof":
                row.append("artist proof" if self.artist_proof else "")
            elif title == "Type":
                row.append(self.card_type)
            elif title == "Cost":
                row.append(self.card_cost)
            elif title == "Rarity":
                row.append(self.rarity)
            elif title == "Price":
                if write_prices:
                    row.append("$"+str(self.price))
                else:
                    row.append("$0.00")
            elif title == "Image URL":
                row.append(self.image_url)
            elif title == "Scryfall ID":
                row.append(self.scryfall_id)
            else:
                row.append("")
                
        return row
        
    def adjust_amount(self, new_amount):
        self.amount = new_amount
        self.total_price = new_amount * self.price
        self.total_price_usd = new_amount * self.price_usd
        self.total_price_eur = new_amount * self.price_eur
        self.summed = False
        
    def card_cost_to_cmc(self):
        parts = self.card_cost.split("//")[0].split("{")
        for part in parts:
            if part == "":
                continue
            elif part[:-1] == 'X':
                continue
            elif part[:-1].isnumeric():
                self.cmc = self.cmc + int(part[:-1])
            else:
                self.cmc = self.cmc + 1
                
    
    def card_cost_to_color(self):
        for c in ["W","U","B","R","G"]:
            if c in self.card_cost:
                self.color += c
                    
    def is_unedition(self):
        return self.edition in ["UG", "UNH", "UST", "UND", "UNF"]
                    
    def color_sort_key(self):
    # White: 0, Blue: 1, Black: 2, Red: 3, Green: 4, Colorless: 5, Multicolor: 6, Land: 7
        key = "Color"
        if len(self.color) == 0:
            if self.main_type == "Land":
                key += "7"
            else:
                key += "5"
        else:
            if len(self.color) > 1:
                key += "6"
                key += str(len(self.color))
        
            for c in self.color:
                if c == "W":
                    key += "0"
                elif c == "U":
                    key += "1"
                elif c == "B":
                    key += "2"
                elif c == "R":
                    key += "3"
                elif c == "G":
                    key += "4"
                    
        return key
        
    def rarity_sort_key(self):
        key = "Rarity"
        if self.rarity == "Rare" or self.rarity == "Mythic":
            key += "0"
        elif self.rarity == "Uncommon":
            key += "1"
        elif self.rarity == "Common" and self.foil:
            key += "2"
        else:
            key += "3"
        return key
            
    def type_sort_key(self):
        typemap = {"Battle": 4,"Creature": 1,"Artifact": 2,"Enchantment": 3,"Instant": 5,"Sorcery": 6,"Planeswalker": 0,"Land": 7}
        return "Type" + str(typemap.get(self.main_type, 99))
                
    def extract_main_type(self):
        types_by_priority = ["Battle","Creature","Land","Artifact","Enchantment","Instant","Sorcery","Planeswalker"]
        
        parts = self.card_type.split("//")        
        for t in types_by_priority:
            if t in parts[0]:
                self.main_type = t
                break
                
        for part in parts:
            subpart = part.split("-")
            self.primary_type += subpart[0] + "//"
            
        self.primary_type = self.primary_type[:-2]
                
    def update_scryfall(self, row):
        for idx, tag in enumerate(database_format):
            if tag == "oracle":
                self.oracle_text = row[idx]
            elif tag == "released_at":
                self.released_at = row[idx]
            elif tag == "power":
                self.power = row[idx]
            elif tag == "toughness":            
                self.toughness = row[idx]
            elif tag == "price_usd":
                self.price_usd = float(row[idx]) if row[idx] else 0
                self.total_price_usd = self.price_usd * self.amount
            elif tag == "price_eur":
                self.price_eur = float(row[idx]) if row[idx] else 0
                self.total_price_eur = self.price_eur * self.amount
            elif tag == "img_uri":
                self.scryfall_image_url = row[idx]
        
        if self.foil: # After first loop to respect default value
            for idx, tag in enumerate(database_format):
                if tag == "price_usd_foil":
                    self.price_usd = float(row[idx]) if row[idx] else self.price_usd
                    self.total_price_usd = self.price_usd * self.amount
                elif tag == "price_eur_foil":                    
                    self.price_eur = float(row[idx]) if row[idx] else self.price_eur
                    self.total_price_eur = self.price_eur * self.amount
        
    def create_mask(hlparts):
        mask = {}
        for title in Card.titles:
            for idx in range(len(hlparts)):
                if hlparts[idx] == title:
                    mask[title] = idx
                    break
        return mask        
        
    def print_full(card):
        card.print_masked("animlrcp")
        
    def print_content(card):
        print("{0:>4d} {1:40s} {2:40s} {3:10s} {4}{5}".format(card.amount,card.name, card.card_type, card.card_cost, card.power + "/" + card.toughness if card.power != "" else "", "\n     "+card.oracle_text.replace('\n',' ')+"\n" if card.oracle_text != "" else ""))
        
    def print_masked(card, mask):
        for c in mask:
            print(Card.mask_dic[c][1](card),end=' ')
        print("") # New line
        
    def image(card):
        return card.image_url if card.image_url != "" else card.scryfall_image_url
        
    def gallery_title(card):
        return "Amount: {0:d}, Price: {1}{2}".format(card.amount, "{0:3.2f}$".format(card.price) if card.price != 0 else "n/a", " (" + card.language[0] + ")" if card.language != "" else "")
        
    def sort_key(card):
        return card.name+card.edition+str(card.card_number)+card.language+str(card.foil)+card.condition
        
    def value_key(card):
        return card.name+card.edition+str(card.card_number)+str(card.foil)
        
    def collection_key(card):
        return card.rarity_sort_key() + card.color_sort_key() + str(card.cmc).zfill(3) + card.type_sort_key() + card.name
        
    def properties_as_string(is_compressed, is_augmented):
        basic_properties = ["name", "amount", "edition", "card_number", "condition", "language", "card_type", "main_type", "primary_type", "card_cost", "cmc", "rarity", "color", "foil"]
        basic_properites_uncompressed = ["price"]
        basic_properties_compressed = ["total_price"]
        
        augmented_properties = ["oracle_text", "released_at", "power", "toughness"]
        augmented_properties_uncompressed = ["price_usd", "price_eur"]
        augmented_properties_compressed = ["total_price_usd", "total_price_eur"]
        
        property_list = basic_properties
        if is_augmented:
            property_list += augmented_properties
        
        if is_compressed:
            property_list += basic_properties_compressed
        else:
            property_list += basic_properites_uncompressed
            
        if is_augmented:
            if is_compressed:
                property_list += augmented_properties_compressed
            else:
                property_list += augmented_properties_uncompressed
        
        properties = ""
        for p in property_list:
            properties += p + ", "
            
        properties = properties[:-2]
        if not is_augmented:
            properties += " - Connect to Scryfall for more options!"
            
        return properties
        
class Collection:
    card_list = []
    is_compressed = False
    is_augmented = False
    name = ""
    
    def __init__(self, data, name=""):
        self.card_list = data
        self.name = name
        
    def set(self, other):
        self.card_list = copy.deepcopy(other.card_list)
        self.is_compressed = other.is_compressed
        self.is_augmented = other.is_augmented
        self.name = other.name
        
    def set_name(self, name):
        self.name = name
        
    def has_name(self):
        return self.name != ""
    
    @classmethod
    def from_collection(cls, collection):
        new_collection = cls()
        new_collection.set(collection)
        return new_collection
        
    @classmethod
    def from_collection_diff(cls, collection1, collection2, equal_criteria = lambda card: Card.sort_key(card)):
        collection1.compress(equal_criteria)
        collection2.compress(equal_criteria)
        
        card_list = []
        
        idx1 = 0
        idx2 = 0
        while idx1 < len(collection1.card_list) and idx2 < len(collection2.card_list):
            card1 = collection1.card_list[idx1]
            card2 = collection2.card_list[idx2]
            if equal_criteria(card1) == equal_criteria(card2):
                new_card = copy.deepcopy(card1)
                #new_card.adjust_amount(card1.amount - card2.amount)
                new_card.price_diff = card1.price - card2.price
                card_list.append(new_card)
                
                idx1 = idx1 + 1
                idx2 = idx2 + 1
            elif equal_criteria(card1) < equal_criteria(card2):
                idx1 = idx1 + 1
            else:
                idx2 = idx2 + 1
    
        return cls(card_list, collection1.name + " - " + collection2.name)

    @classmethod
    def from_filename(cls, filename):
        if not isfile(filename):
            return cls([], name="Empty")
            
        card_list = []
        with open(filename, encoding='utf8') as f:
            reader = csv.reader(f, delimiter=',')
            titleline = next(reader) # Skip title line
            mask = Card.create_mask(titleline)
            for row in reader:
                if len(row) > 1:
                    card_list.append(Card(row,mask))
            
        return cls(card_list, name=basename(filename)[:-4])
        
    def save_to_file(self, filename, write_prices = True):
        with open(filename, 'w', newline='', encoding='utf8') as f:
            writer = csv.writer(f, delimiter=',')
            writer.writerow(Card.titles)
            for card in self.card_list:                      
                writer.writerow(card.get_csv_row(write_prices))
        
    def sort(self, key=Card.sort_key, reverse=False):
        self.card_list.sort(key=key, reverse=reverse)      
                    
    def contains(self, card):
        for coll_card in self.card_list:
            if Card.sort_key(card) == Card.sort_key(coll_card):
                return True
        return False
                    
    def compress(self, equal_criteria):
        self.sort(key=equal_criteria)
        idx = 1
        while idx < len(self.card_list):
            if equal_criteria(self.card_list[idx]) == equal_criteria(self.card_list[idx-1]):
                self.card_list[idx-1].amount = self.card_list[idx-1].amount + self.card_list[idx].amount
                self.card_list[idx-1].total_price = self.card_list[idx-1].total_price + self.card_list[idx].total_price
                self.card_list[idx-1].total_price_usd = self.card_list[idx-1].total_price_usd + self.card_list[idx].total_price_usd
                self.card_list[idx-1].total_price_eur = self.card_list[idx-1].total_price_eur + self.card_list[idx].total_price_eur
                del self.card_list[idx]
            else:
                idx = idx + 1
        self.is_compressed = True
            
    def apply_filter(self, filter_func):
        idx = 0
        while idx < len(self.card_list):
            if not filter_func(self.card_list[idx]):
                del self.card_list[idx]
            else:
                idx = idx + 1
            
    def print_consecutively(self):
        self.print_consecutively_with_func(Card.print_full)
            
    def print_consecutively_with_func(self, output_func):            
        curr_idx = 0
        cont = True
        while cont:
            for i in range(20):
                if curr_idx >= len(self.card_list):
                    cont = False
                    break
                    
                card = self.card_list[curr_idx]
                if self.is_compressed:
                    card.summed = True
                output_func(card)
                curr_idx = curr_idx + 1
                
            if cont:
                print ("\nContinue? y/n")
                try:
                    c = getch().decode('utf8')
                except:
                    c = ""
                if c != 'y':
                    cont = False
                    
    def augment_from_database(self, database):
        if not self.is_augmented and database.is_valid():
            print("Read data from database...",end='\r')
            conn = sqlite3.connect(database.database_file)
            cur=conn.cursor()
            
            nbr_not_exactly_found = 0
            nbr_not_found = 0
            for card in self.card_list:
                rows = []
                
                if card.scryfall_id != "":
                    cur.execute('SELECT * FROM Cards WHERE id=?',(card.scryfall_id,))
                    rows = cur.fetchall()
                
                if len(rows) == 0:
                    edition_code = edition_code_map[card.edition] if card.edition in edition_code_map else card.edition
                    cur.execute('SELECT * FROM Cards WHERE name=? and edition=? AND nbr=?',(card.name, edition_code, card.card_number))
                    rows = cur.fetchall()
                                
                if len(rows) == 0: # Full edition name needed
                    edition_full_name = card.edition_full
                    if edition_full_name[0:8] == "Extras: ":
                        edition_full_name = edition_full_name[8:]
                        if not "Art Series" in edition_full_name:                        
                            edition_full_name += " Tokens"
                    
                    if edition_full_name[0:8] == "Promos: ":
                        edition_full_name = edition_full_name[8:] + " Promos"
                        
                    edition_full_name = edition_full_name.replace('"', '')
                    
                    cur.execute('SELECT * FROM Cards WHERE name=? and edition_full=? AND nbr=?',(card.name, edition_full_name, card.card_number))
                    rows = cur.fetchall()
                if len(rows) == 0: # Collector number may be wrong                    
                    cur.execute('SELECT * FROM Cards WHERE name=? AND edition=?',(card.name, edition_code))
                    rows = cur.fetchall()
                if len(rows) == 0: # Name might be wrong for tokens
                    cur.execute('SELECT * FROM Cards WHERE (edition_full=? OR edition=?) AND nbr=?',(edition_full_name, edition_code, card.card_number))
                    rows = cur.fetchall()
                if len(rows) == 0:
                    #card.print_full()
                    nbr_not_exactly_found += 1
                    cur.execute('SELECT * FROM Cards WHERE name=?',(card.name,))
                    rows = cur.fetchall()
                    
                if len(rows) == 0:
                    nbr_not_found += 1
                else:
                    card.update_scryfall(rows[0])
                    
            self.is_augmented = True
            conn.close()
            print("Read data from database... Done!" + (" (" + str(nbr_not_exactly_found-nbr_not_found) + " cards defaulted, " + str(nbr_not_found) + " cards not found)" if nbr_not_exactly_found > 0 else ""))
            
    def properties_as_string(self):        
        return Card.properties_as_string(self.is_compressed, self.is_augmented)