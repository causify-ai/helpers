import requests
from bs4 import BeautifulSoup

def get_page_title(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        title_tag = soup.find('title')
        return title_tag.string.strip() if title_tag else "No <title> tag found"
    except requests.RequestException as e:
        return f"Request failed: {e}"


import requests
from html.parser import HTMLParser

class TitleParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_title = False
        self.title = None

    def handle_starttag(self, tag, attrs):
        if tag.lower() == 'title':
            self.in_title = True

    def handle_data(self, data):
        if self.in_title and self.title is None:
            self.title = data.strip()

    def handle_endtag(self, tag):
        if tag.lower() == 'title':
            self.in_title = False

def get_title_streaming(url):
    try:
        with requests.get(url, stream=True, timeout=10) as r:
            r.raise_for_status()
            parser = TitleParser()
            for chunk in r.iter_content(chunk_size=1024, decode_unicode=True):
                parser.feed(chunk)
                if parser.title:
                    break
            return parser.title if parser.title else "No <title> tag found"
    except requests.RequestException as e:
        return f"Request failed: {e}"



if __name__ == "__main__":
    # Example list of URLs
    files = """
https://news.ycombinator.com/item?id=34336386
https://news.ycombinator.com/item?id=29671450
https://news.ycombinator.com/item?id=22778089
https://news.ycombinator.com/item?id=23331989
https://news.ycombinator.com/item?id=34801636
https://news.ycombinator.com/item?id=30371723
https://news.ycombinator.com/item?id=26953352
https://news.ycombinator.com/item?id=23209142
https://news.ycombinator.com/item?id=30228261
https://news.ycombinator.com/item?id=25950838
https://news.ycombinator.com/item?id=32799789
https://news.ycombinator.com/item?id=29315107
https://news.ycombinator.com/item?id=30984662
https://news.ycombinator.com/item?id=22168822
https://news.ycombinator.com/item?id=22652141
https://news.ycombinator.com/item?id=25279814
https://news.ycombinator.com/item?id=22106367
https://news.ycombinator.com/item?id=22446148
https://news.ycombinator.com/item?id=24487135
https://news.ycombinator.com/item?id=33696486
https://news.ycombinator.com/item?id=14265051
https://news.ycombinator.com/item?id=21534990
https://news.ycombinator.com/item?id=29347885
https://news.ycombinator.com/item?id=29876742
https://news.ycombinator.com/item?id=23550758
https://news.ycombinator.com/item?id=22504133
https://news.ycombinator.com/item?id=23339830
https://news.ycombinator.com/item?id=23755675
https://news.ycombinator.com/item?id=26872904
https://news.ycombinator.com/item?id=27760919
https://news.ycombinator.com/item?id=21614533
https://news.ycombinator.com/item?id=26602156
https://news.ycombinator.com/item?id=22291417
https://news.ycombinator.com/from?site=a16z.com&next=29816846
https://news.ycombinator.com/item?id=27855145
https://news.ycombinator.com/item?id=26930667
https://news.ycombinator.com/item?id=29711042
https://news.ycombinator.com/item?id=26580746
https://news.ycombinator.com/item?id=24601579
https://news.ycombinator.com/item?id=22161830
https://news.ycombinator.com/item?id=26612321
https://news.ycombinator.com/item?id=32081943
https://news.ycombinator.com/item?id=22962869
https://news.ycombinator.com/item?id=27350264
https://news.ycombinator.com/item?id=29677238
https://news.ycombinator.com/item?id=31441516
https://news.ycombinator.com/item?id=26164790
https://news.ycombinator.com/item?id=22291189
https://news.ycombinator.com/item?id=25575505
https://news.ycombinator.com/item?id=23549929
https://news.ycombinator.com/item?id=26524876
https://news.ycombinator.com/item?id=27593772
https://news.ycombinator.com/item?id=27768211
https://news.ycombinator.com/item?id=42405323
https://news.ycombinator.com/item?id=35506009
https://news.ycombinator.com/item?id=22033129
https://news.ycombinator.com/item?id=30970720
https://news.ycombinator.com/item?id=22278339
https://news.ycombinator.com/item?id=30247159
https://news.ycombinator.com/item?id=29367687
https://news.ycombinator.com/item?id=25107285
https://news.ycombinator.com/item?id=26225373
https://news.ycombinator.com/item?id=31212542
https://news.ycombinator.com/item?id=21505305
https://news.ycombinator.com/item?id=25874374
https://news.ycombinator.com/item?id=22827275
https://news.ycombinator.com/item?id=26058440
https://news.ycombinator.com/item?id=29899156
https://news.ycombinator.com/item?id=34322033
https://news.ycombinator.com/item?id=36015815
https://news.ycombinator.com/item?id=22925484
https://news.ycombinator.com/item?id=32937876
https://news.ycombinator.com/item?id=34934216
https://news.ycombinator.com/item?id=25445493
https://news.ycombinator.com/item?id=21404292
https://news.ycombinator.com/item?id=34821414
https://news.ycombinator.com/item?id=33942597
https://news.ycombinator.com/item?id=27763965
https://news.ycombinator.com/item?id=23018805
https://news.ycombinator.com/item?id=23593165
https://news.ycombinator.com/item?id=31114554
https://news.ycombinator.com/item?id=26053323
https://news.ycombinator.com/item?id=25550240
https://news.ycombinator.com/item?id=24949736
https://news.ycombinator.com/item?id=29353904
https://news.ycombinator.com/item?id=22207006
https://news.ycombinator.com/item?id=22731317
https://news.ycombinator.com/item?id=27805904
https://news.ycombinator.com/item?id=28640429
https://news.ycombinator.com/item?id=31168069
https://news.ycombinator.com/item?id=31699032
https://news.ycombinator.com/item?id=31123683
https://news.ycombinator.com/item?id=23921610
https://news.ycombinator.com/item?id=35020814
https://news.ycombinator.com/item?id=21959874
https://news.ycombinator.com/item?id=22895842
https://news.ycombinator.com/item?id=33625367
https://news.ycombinator.com/item?id=22429124
https://news.ycombinator.com/item?id=26036790
https://news.ycombinator.com/item?id=37059479
https://news.ycombinator.com/item?id=30060765
https://news.ycombinator.com/item?id=21610687
https://news.ycombinator.com/item?id=25716581
https://news.ycombinator.com/item?id=30822339
https://news.ycombinator.com/item?id=22094355
https://news.ycombinator.com/item?id=26034053
https://news.ycombinator.com/item?id=27695574
https://news.ycombinator.com/item?id=31286890
https://news.ycombinator.com/item?id=36154622
https://news.ycombinator.com/item?id=28155196
https://news.ycombinator.com/item?id=34843094
https://news.ycombinator.com/item?id=33477056
https://news.ycombinator.com/item?id=26747743
https://news.ycombinator.com/item?id=22059601
https://news.ycombinator.com/item?id=34391045
https://news.ycombinator.com/item?id=42174181
https://news.ycombinator.com/item?id=34152100
https://news.ycombinator.com/item?id=35697627
https://news.ycombinator.com/item?id=31455919
https://news.ycombinator.com/item?id=31200989
https://news.ycombinator.com/item?id=34752489
https://news.ycombinator.com/item?id=42357273
https://news.ycombinator.com/item?id=21481461
https://news.ycombinator.com/item?id=30120731
https://news.ycombinator.com/item?id=21442330
https://news.ycombinator.com/item?id=26899531
https://news.ycombinator.com/item?id=34857287
https://news.ycombinator.com/item?id=26799702
https://news.ycombinator.com/item?id=24059441
https://news.ycombinator.com/item?id=34165789
https://news.ycombinator.com/item?id=25428621
https://news.ycombinator.com/item?id=23626908
https://news.ycombinator.com/item?id=31431224
https://news.ycombinator.com/item?id=21411893
https://news.ycombinator.com/item?id=36079115
https://news.ycombinator.com/item?id=23725829
https://news.ycombinator.com/item?id=33985969
https://news.ycombinator.com/item?id=22270464
https://news.ycombinator.com/item?id=30925223
https://news.ycombinator.com/item?id=22325975
https://news.ycombinator.com/item?id=30046272
https://news.ycombinator.com/item?id=32390730
https://news.ycombinator.com/item?id=28704164
https://news.ycombinator.com/item?id=23151144
https://news.ycombinator.com/item?id=22492381
https://news.ycombinator.com/item?id=22340720
https://news.ycombinator.com/item?id=31958536
https://news.ycombinator.com/item?id=39094343
https://news.ycombinator.com/item?id=26631467
https://news.ycombinator.com/item?id=31945564
https://news.ycombinator.com/item?id=27736304
https://news.ycombinator.com/item?id=23026750
https://news.ycombinator.com/item?id=22544563
https://news.ycombinator.com/item?id=21564990
https://news.ycombinator.com/item?id=27099536
https://news.ycombinator.com/item?id=22082860
https://news.ycombinator.com/item?id=28006894
https://news.ycombinator.com/item?id=21706451
https://news.ycombinator.com/item?id=35343791
https://news.ycombinator.com/item?id=28045342
https://news.ycombinator.com/item?id=29583792
https://news.ycombinator.com/item?id=33001191
https://news.ycombinator.com/item?id=34032872
https://news.ycombinator.com/item?id=25304257
https://news.ycombinator.com/item?id=29361004
https://news.ycombinator.com/item?id=22627736
https://news.ycombinator.com/item?id=25789336
https://news.ycombinator.com/item?id=26762206
https://news.ycombinator.com/item?id=34906378
https://news.ycombinator.com/item?id=25789073
https://news.ycombinator.com/item?id=34261656
https://news.ycombinator.com/item?id=31335105
https://news.ycombinator.com/item?id=9638748
https://news.ycombinator.com/item?id=26247052
https://news.ycombinator.com/item?id=42902936
https://news.ycombinator.com/item?id=24958215
https://news.ycombinator.com/item?id=36092179
https://news.ycombinator.com/item?id=37202009 
    """
    url_list = files.split("\n")
    import time
    for url in url_list:
        #title = get_page_title(url)
        title = get_title_streaming(url)
        print("%s,%s" % (url, title))
        time.sleep(2)
