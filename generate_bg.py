from PIL import Image, ImageDraw, ImageFont, ImageFilter
import math, random

W,H=1080,1920
im=Image.new('RGB',(W,H),(241,237,226)); d=ImageDraw.Draw(im)
# Photorealistic-feeling premium office lobby: layered stone, glass and warm light.
for y in range(H):
    t=y/H
    c=(int(238-15*t),int(234-13*t),int(224-8*t))
    d.line((0,y,W,y),fill=c)
# distant blue glass wall with vertical mullions
d.rectangle((0,400,W,1475),fill=(177,200,205))
for x in range(-80,1200,190):
    d.polygon([(x,400),(x+126,400),(x+195,1470),(x+55,1470)],fill=(191,211,211))
    d.line((x+126,405,x+195,1470),fill=(226,222,202),width=12)
# skyline and a hazy daylight gradient through windows
for x,w,h in [(18,140,310),(170,170,450),(365,130,350),(650,150,480),(835,180,390),(1030,120,300)]:
    top=1050-h
    d.rectangle((x,top,x+w,1050),fill=(163,187,194),outline=(213,221,214),width=4)
    for yy in range(top+25,1040,65): d.line((x+8,yy,x+w-8,yy),fill=(190,208,207),width=3)
# warm limestone wall panels frame the background
d.rectangle((0,0,W,405),fill=(230,220,197))
d.polygon([(0,0),(W,0),(W,175),(0,280)],fill=(242,232,211))
for x in range(0,W,270):
    d.line((x,0,x,420),fill=(218,205,179),width=4)
# soft recessed ceiling light bands
d.arc((-150,-280,1230,430),5,175,fill=(255,248,221),width=42)
d.arc((-120,-245,1200,405),5,175,fill=(205,178,128),width=5)
d.line((0,405,W,405),fill=(244,226,189),width=14)
# natural, subtle warm lighting pools along wall
for x in (130,540,925):
    d.ellipse((x-95,290,x+95,510),fill=(237,223,192))
    d.ellipse((x-68,320,x+68,440),fill=(244,234,211))
# polished stone floor, extending behind the speaker with no cutout/blank panel
d.rectangle((0,1050,W,1525),fill=(222,216,200))
for y in range(1080,1530,95): d.line((0,y,W,y),fill=(204,197,180),width=3)
for x in range(80,W,240): d.line((x,1050,x-45,1525),fill=(205,198,182),width=3)
# gold-toned side wall inlays
for x in (18,1040):
    d.rectangle((x,470,x+16,1450),fill=(187,147,82))
    d.line((x+26,470,x+26,1450),fill=(246,232,199),width=5)
# No text, title cards, or graphic overlays: background only.
# premium stone reception counter at bottom, natural material instead of flat blank frame
d.rectangle((0,1530,W,1920),fill=(183,151,103))
d.rectangle((0,1530,W,1560),fill=(235,224,199))
d.line((0,1560,W,1560),fill=(130,105,73),width=5)
for x in range(40,W,180):
    d.line((x,1585,x+75,1920),fill=(198,173,137),width=3)
im.save('背景标题_1080x1920.png',format='PNG',optimize=True)
