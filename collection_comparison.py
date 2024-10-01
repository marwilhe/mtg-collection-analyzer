import copy

from collection import Collection,Card
    
# Returns collection1 - collection2
def setminus(collection1, collection2, criteria = Card.sort_key, adjust_amount = True):
    collection1.compress(criteria)
    collection2.compress(criteria)
    
    card_list = []
    missing_cards = 0
    new_cards = 0
    
    idx1 = 0
    idx2 = 0
    while idx1 < len(collection1.card_list) and idx2 < len(collection2.card_list):
        card1 = collection1.card_list[idx1]
        card2 = collection2.card_list[idx2]
        if criteria(card1) == criteria(card2):
            if card1.amount > card2.amount:
                #print("{0}x{1} > {2}x{3}".format(card1.amount, criteria(card1), card2.amount, criteria(card2)))
                if adjust_amount:
                    new_card = copy.deepcopy(card1)
                    new_card.adjust_amount(card1.amount - card2.amount)
                    card_list.append(new_card)
                    new_cards += new_card.amount
            elif card2.amount > card1.amount:
                missing_cards += card2.amount - card1.amount
            
            idx1 += 1
            idx2 += 1
        elif criteria(card1) < criteria(card2):
            #print("{0} < {1}".format(criteria(card1),criteria(card2)))
            card_list.append(copy.deepcopy(card1))
            new_cards += card1.amount
            idx1 += 1
        else:
            missing_cards += card2.amount
            idx2 += 1

    while idx1 < len(collection1.card_list):
        card1 = collection1.card_list[idx1]
        card_list.append(copy.deepcopy(card1))
        new_cards += card1.amount
        idx1 += 1
            
    while idx2 < len(collection2.card_list):
        missing_cards += collection2.card_list[idx2].amount
        idx2 += 1
            
    print("{0} new cards; {1} cards missing in new collection".format(new_cards,missing_cards))
    return Collection(card_list, name = collection1.name + ' \ ' + collection2.name)
    
def intersect(coll1, coll2, criteria = Card.sort_key, adjust_amount = True):
    collection1 = copy.deepcopy(coll1)
    collection2 = copy.deepcopy(coll2)
    
    collection1.compress(criteria)
    collection2.compress(criteria)
    
    card_list = []
    
    idx1 = 0
    idx2 = 0
    while idx1 < len(collection1.card_list) and idx2 < len(collection2.card_list):
        card1 = collection1.card_list[idx1]
        card2 = collection2.card_list[idx2]
        if criteria(card1) == criteria(card2):
            new_card = copy.deepcopy(card1)
            if adjust_amount:
                new_card.adjust_amount(min(card1.amount, card2.amount))
            card_list.append(new_card)
            
            idx1 += 1
            idx2 += 1
        elif criteria(card1) < criteria(card2):
            idx1 += 1
        else:
            idx2 += 1
            
    return Collection(card_list, name = collection1.name + " ^ " + collection2.name)
    
def disjoint_union(collection1,collection2):
    return Collection(copy.deepcopy(collection1.card_list+collection2.card_list), name = collection1.name + " U " + collection2.name)
    
def coll_union(collections):
    card_list = []
    name = ""
    
    for collection in collections:
        card_list += copy.deepcopy(collection.card_list)
        name += collection.name + " U "
    name = name[:-3]
    
    union_collection = Collection(card_list, name)
    union_collection.compress(Card.sort_key)
    
    return union_collection
    
def missing_by_name(reference_collection, new_collection):
    ref_coll = copy.deepcopy(reference_collection)
    new_coll = copy.deepcopy(new_collection)
    
    ref_coll.sort(key = lambda card: card.name)
    new_coll.sort(key = lambda card: card.name)
    
    ref_coll_idx = 0
    new_coll_idx = 0
    
    missing_list = []
    while new_coll_idx < len(new_coll.card_list):
        new_card = new_coll.card_list[new_coll_idx]
        ref_card = ref_coll.card_list[ref_coll_idx]
        if new_card.name > ref_card.name:
            ref_coll_idx += 1
        elif new_card.name == ref_card.name:
            new_coll_idx += 1
        else:
            missing_list.append(new_card)
            new_coll_idx += 1
    
    return Collection(missing_list, name = new_coll.name + " (-) " + ref_coll.name)