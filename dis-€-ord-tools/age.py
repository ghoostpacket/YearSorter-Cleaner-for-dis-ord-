import base64, time, os, time
from datetime import datetime, timedelta

imagesFolder = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(imagesFolder, exist_ok=True)

def calculateAge(token):
    b64id = token.split(".")[0] + '=='
    base64_bytes = base64.b64decode(b64id.encode('ascii'))
    id = base64_bytes.decode('ascii')

    bin2 = bin(int(id))[2:]
    unixbin = ''
    unix = ''
    m = 64 - len(bin2)
    unixbin = bin2[0:42-m]
    unix = int(unixbin, 2) + 1420070400000
    unix = unix // 1000

    ts = datetime.utcfromtimestamp(unix).strftime('%Y')
    # ts = datetime.utcfromtimestamp(unix).strftime('%b %Y')
    return ts

with open("tokens.txt", encoding="utf-8") as f:
    tokens = []
    for l in f:
        l = l.replace("\n", "")
        if l.count(":") != 3:
            with open("nopassword.txt", "a") as f:
                f.write(l + "\n")
            continue
        #if not any (line in l for line in ["hotmail.com", "gmail.com", "outlook.com"]):
            #with open("diffemail.txt", "a") as f:
                #f.write(l + "\n")
            #continue
        # with open("done.txt", "a") as f:
        #     f.write(l + "\n")
        # continue
        
        email = l.split(":")[0]
        token = l.split(":")[3]
        tokenAge = calculateAge(token)
        print(email, tokenAge)
        
        # if "Feb 2022" in tokenAge or "Jan 2022" in tokenAge:
            # with open("samedate.txt", "a", encoding="utf-8") as f:
                # f.write(l + "\n")
            # continue
        # if "@hotmail" in email or "@outlook" in email:
            # with open("hotmails.txt", "a", encoding="utf-8") as f:
                # f.write(l + "\n")
            # continue
        # elif ".ru" in email or "tormails" in email:
            # with open("mailrutormail.txt", "a", encoding="utf-8") as f:
                # f.write(l + "\n")
            # continue
        # else:
            # with open("othermails.txt", "a", encoding="utf-8") as f:
                # f.write(l + "\n")
            # continue
        
        
        
        with open("output/" + tokenAge + ".txt", "a", encoding="utf-8") as f:
            f.write(l + "\n")
        continue
        
        # if "2024" in tokenAge or "2023" in tokenAge:
            # with open("sorted/" + tokenAge + ".txt", "a") as f:
                # f.write(l + "\n")
            # continue
           
        # elif "2016" in tokenAge or "2015" in tokenAge:
            # with open("sorted/" + tokenAge + ".txt", "a") as f:
                # f.write(l + "\n")
            # continue
        with open("old.txt", "a", encoding="utf-8") as f:
            f.write(l + "\n")