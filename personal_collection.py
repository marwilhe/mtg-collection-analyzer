from collection import *
from collection_comparison import *
from os import listdir
from os.path import isdir, isfile, join

class PersonalCollection:
    
    def __init__(self, config):
        self.config = config
    
        if isdir(config.reference):
            self.reference_path = config.reference
        else:
            self.reference_path = "data"
            
        self.reference_collection = Collection.from_filename(join(self.reference_path, "reference.csv"))
        
        self.decks = []
        if isdir(config.decks):
            for f in listdir(config.decks):
                if isfile(join(config.decks, f)) and f[-4:] == ".csv":
                    self.decks.append(Collection.from_filename(join(config.decks,f)))
        self.deck_collection = coll_union(self.decks)
        
    @classmethod
    def from_config(cls, config):
        return cls(config)