from platform import system
from threading import Thread
from time import sleep
from PIL import Image
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import requests

from collection import Card

def plt_maximize():
    # See discussion: https://stackoverflow.com/questions/12439588/how-to-maximize-a-plt-show-window-using-python
    backend = plt.get_backend()
    cfm = plt.get_current_fig_manager()
    if backend == "wxAgg":
        cfm.frame.Maximize(True)
    elif backend == "TkAgg":
        if system() == "Windows":
            cfm.window.state("zoomed")  # This is windows only
        else:
            cfm.resize(*cfm.window.maxsize())
    elif backend == "QT4Agg":
        cfm.window.showMaximized()
    elif callable(getattr(cfm, "full_screen_toggle", None)):
        if not getattr(cfm, "flag_is_max", None):
            cfm.full_screen_toggle()
            cfm.flag_is_max = True
    else:
        raise RuntimeError("plt_maximize() is not implemented for current backend:", backend)   
        
def show_gallery(card_list, fimg = Card.image, ffoil = lambda card: card.foil, ftitle = Card.gallery_title):
    if len(card_list) == 0:
        return False
        
    if fimg(card_list[0]) == "":
        print("No Image URLs available.")
        return False
        
    foiling = mpimg.imread('img/rainbow.png')
        
    class InfoWrapper:
        card_list = []
        image_cache = {}
        fimg = None
        ffoil = None
        ftitle = None
        curr_idx = 0
        fig = None
        preloading_active = False
        stop_preloading = False
            
    fig, axes = plt.subplots(2,5)
    for i in range(2):
        for j in range(5):
            axes[i,j].axis('off')
    
    iw = InfoWrapper()
    iw.card_list = card_list
    iw.fimg = fimg
    iw.ffoil = ffoil
    iw.ftitle = ftitle
    iw.fig = fig
    
    def preload_data(iw, idx):
        for i in range(10):
            if idx >= len(iw.card_list) or iw.stop_preloading:
                break
                
            card = iw.card_list[idx]
            
            if card in iw.image_cache:
                continue
            else:                    
                response = requests.get(iw.fimg(card), stream=True)
                img = Image.open(response.raw)
                img = img.resize((488,680))
                iw.image_cache[card] = img
            
            idx += 1
        iw.preloading_active = False
        iw.stop_preloading = False
        
    def plot_next(iw):
        if iw.curr_idx >= len(iw.card_list):
            return
            
        if iw.preloading_active:
            iw.stop_preloading = True
            
        while iw.preloading_active:
            sleep(1)
            
        start_nbr = iw.curr_idx + 1
        data_available = True
        for i in range(10):      
            ax = axes[i // 5, i % 5]  
            
            if iw.curr_idx >= len(iw.card_list):
                ax.clear()
                ax.axis('off')
                continue
                                       
            card = iw.card_list[iw.curr_idx]
            
            if card in iw.image_cache:
                img = iw.image_cache[card]
            else:                    
                response = requests.get(iw.fimg(card), stream=True)
                img = Image.open(response.raw)
                img = img.resize((488,680))
                iw.image_cache[card] = img

            
            ax.imshow(img)
            if iw.ffoil(card):
                ax.imshow(foiling,alpha=0.3)
            ax.set_title(iw.ftitle(card))
            
            iw.curr_idx += 1
            
        plt.suptitle("Cards {0}-{1}/{2}".format(start_nbr, iw.curr_idx, len(iw.card_list)))
        iw.fig.canvas.draw()
        
        preloading_thread = Thread(target = preload_data, args = (iw, iw.curr_idx, ))
        iw.preloading_active = True
        preloading_thread.start()
        
    def plot_prev(iw):
        if iw.curr_idx > 10:
            if iw.curr_idx % 10 != 0:
                iw.curr_idx = (iw.curr_idx // 10 + 1) * 10
            iw.curr_idx = max(0, iw.curr_idx-20)
            plot_next(iw)
    
    def plot_next_event(iw, e):
        if e.key == "right" or e.key == "down" or e.key == "enter" or e.key == " ":
            plot_next(iw)
        elif e.key == "left" or e.key == "up":
            plot_prev(iw)
        elif e.key == "escape":
            plt.close()
            
            
    cid = fig.canvas.mpl_connect('key_press_event', lambda e: plot_next_event(iw, e))

    plt_maximize()       
    plot_next(iw)
    plt.show()
    
    return True