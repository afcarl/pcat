from __init__ import *

for strgextn in ['/imag/', '/data/outp/']:
    
    path = os.environ["PCAT_DATA_PATH"] + strgextn

    for strgfile in os.listdir(path):
        pathfile = path + strgfile
        if os.path.isdir(pathfile) and strgfile[:8].isdigit():
            
            try:
                numb = int(pathfile[pathfile.rfind('_')+1:])
            
                if not os.path.exists(pathfile + '/anim') or not os.listdir(pathfile + '/anim'):# or numb < 100000:
                    os.system('rm -rf ' + pathfile)
            except:
                pass

