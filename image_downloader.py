from PIL import Image
import numpy as np
import cv2
import requests

def download_images(card_list,database,folder,horizontal=1,vertical=1):
    print("Downloading...")
    hidx = 0
    vidx = 0
    combined_image = []
    image_row = []
    
    cur = None
    if not database is None:
        conn = sqlite3.connect(database)
        cur=conn.cursor()
    for card in card_list:
        img_url = ""
        if not cur is None:
            edition_full_name = card.edition_full
            if edition_full_name[0:8] == "Extras: ":
                edition_full_name = edition_full_name[8:] + " Tokens"
            
            if edition_full_name[0:8] == "Promos: ":
                edition_full_name = edition_full_name[8:] + " Promos"
            
            cur.execute('SELECT * FROM Cards WHERE name=? and edition_full=? AND nbr=?',(card.name,edition_full_name,card.card_number,))
            rows = cur.fetchall()
            
            if len(rows) == 0:                          
                cur.execute('SELECT * FROM Cards WHERE name=? and edition_full=?',(card.name,edition_full_name,))
                rows = cur.fetchall()
                
            if len(rows) == 0:                          
                cur.execute('SELECT * FROM Cards WHERE name=?',(card.name,))
                rows = cur.fetchall()
            
            if len(rows) > 0:
                for idx, tag in enumerate(database_format):
                    if tag == "img_uri":
                        img_url = rows[0][idx]
                        break
                        
        if img_url == "":        
            img_url = card.image_url
            
        if img_url != "":
            response = requests.get(img_url, stream=True)
            pil_img = Image.open(response.raw)
            pil_img = pil_img.resize((672,936))              
            img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
            
            filename = card.name.replace("/","")+".png"
            print(filename)
            
            if hidx < horizontal:
                image_row.append(img)
                hidx += 1
                
            if hidx == horizontal:
                combined_image.append(image_row)
                image_row = []
                hidx = 0
                vidx += 1
                
            if vidx == vertical:
                #print(len(combined_image),[len(row) for row in combined_image])
                outimg = cv2.vconcat([cv2.hconcat(row) for row in combined_image])
                combined_image = []                         
                hidx = 0
                vidx = 0
                
                cv2.imwrite(folder+"/"+filename,outimg)
                
            
    if hidx != 0 or vidx != 0:
        if hidx != 0:
            while hidx < horizontal:
                image_row.append(image_row[-1])
                hidx += 1
                
            combined_image.append(image_row)
            image_row = []
            vidx += 1
            
        if vidx != 0:
            while vidx < vertical:
                combined_image.append(combined_image[-1])
                vidx += 1
            
        #print(len(combined_image),[len(row) for row in combined_image])
        outimg = cv2.vconcat([cv2.hconcat(row) for row in combined_image])
        cv2.imwrite(folder+"/"+filename,outimg)