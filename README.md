# mtg-collection-analyzer
Python-based command line analyzer for Magic: The Gathering collections created using deckbox.org

PREREQUISITES
1. You need Python. If you don't have Python installed on your PC, download and install Python first (python.org).
2. You need to have an account on deckbox.org and inserted your collection there by manual insertion or using one of the import functions. For testing the script you can use the provided sample collection instead.

HOW TO USE
1. Export your collection on deckbox.org by clicking on "Inventory -> Tools -> Export". Include the columns Type, Cost, Rarity, Price, Image URL and Scryfall ID, then Click "Export". Place the created file in the "data" folder.
2. Start the file "main.py" using the command line. On Windows this may be done by navigating to the main folder ("mtg-collection-analyzer"), clicking into the folder bar and typing "cmd". In the command window then type in "python main.py".
3. Select "Choose collection" by typing "1" to select and analyze your collection.

MANAGE YOUR PERSONAL COLLECTION
1. Create a deckbox export of your collection and name it "reference.csv". Place it in the data folder or create a file "config.txt" in the folder "cfg" with the line "reference=<Path to the reference folder>".
2. Create separate deckbox exports for your decks (as collections). Place them in a directory of your choice and link this directory in the config-file using "decks=<Path to the deck folder>"
3. In the "Select collection" menu you can now choose the reference collection or the decks.