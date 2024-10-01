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

PRINT CONTENT OF YOUR COLLECTION
1. Select your collection, go to the analysis menu and choose "Print" (0) for a quick command line overview!
![print](https://github.com/user-attachments/assets/d3ee55c7-06af-4f43-9657-17c414d5e422)

SHOW YOUR COLLECTION IN GALLERY
1. Select your collection, go to the analysis menu and choose "Show Gallery (2)" to open the gallery. Cards are shown in the order of their current sorting.
![gallery](https://github.com/user-attachments/assets/9004b1bd-9af5-40c8-b676-4f3afddd558d)

FILTER/SORT/COMPRESS YOUR COLLECTION
In order to search for specific cards / cards with specific properties you can use arbitrary python commands in the respective submenu. E.g. to find all your green cards which do something with +1/+1 counters do the following:
1. Select your collection and go to the analysis menu.
2. As you want to search the oracle text you need to connect to Scryfall first. Go to "Special Action" (6) and choose "Connect to Scryfall" (3).
3. Go back to the main menu (4 or Esc) and choose Filter (4).
4. Type in '"+1/+1 counter" in card.oracle_text and "G" in card.color' to search for all cards who do something with +1/+1 counters and are green.
5. Look at your cards in the printed list or open the gallery for a better overview.
![advanced_filters](https://github.com/user-attachments/assets/ec5ccd66-696b-4954-a3d8-710f134180fe)

SHOW STATISTICS OF YOUR COLLECTION
1. Select your collection, go to the analysis menu and choose "Special Action" (6).
2. Choose "Print statistics" to show the total value and number of cards in of your collection
![statistics](https://github.com/user-attachments/assets/b89694fb-a082-4756-8472-29ed6c12809f)

SHOW EDITION COMPLETION
1. Select your collection and choose "Show edition list" (2). The analyzer will automatically connect to Scryfall.
2. Choose "From List" or "From List (Sort by owned)" to get a list of the editions present in your collection and your completion status. Use the submenus to get more detailed information on which cards you own and which are missing.
![show_edition_completion](https://github.com/user-attachments/assets/3e4687b5-8b0c-47b8-ad5d-c09d20b30030)

