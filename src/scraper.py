import requests
from bs4 import BeautifulSoup
import json
import hashlib
import re
import time
import random
import logging
from datetime import datetime, timedelta
from urllib.parse import urljoin
import feedparser

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger(__name__)

HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'}
SESSION = requests.Session()
SESSION.headers.update(HEADERS)
MAX_AGE_DAYS = 30
REQUEST_DELAY = (1.5, 3.5)

AGGREGATOR_SOURCES = [
    {"name": "ContestBee", "url": "https://www.contestbee.com/", "type": "contestbee"},
    {"name": "ContestBee - Sweepstakes", "url": "https://www.contestbee.com/sweepstakes/", "type": "contestbee"},
    {"name": "ContestBee - Gift Cards", "url": "https://www.contestbee.com/gift-cards/", "type": "contestbee"},
    {"name": "ContestBee - Travel", "url": "https://www.contestbee.com/travel/", "type": "contestbee"},
    {"name": "ContestBee - Cars", "url": "https://www.contestbee.com/cars/", "type": "contestbee"},
    {"name": "ContestBee - Electronics", "url": "https://www.contestbee.com/electronics/", "type": "contestbee"},
    {"name": "ContestBee - Cash", "url": "https://www.contestbee.com/cash/", "type": "contestbee"},
    {"name": "ContestGirl", "url": "https://www.contestgirl.com/", "type": "contestgirl"},
    {"name": "ContestGirl - Sweepstakes", "url": "https://www.contestgirl.com/sweepstakes/", "type": "contestgirl"},
    {"name": "ContestGirl - Cars", "url": "https://www.contestgirl.com/cars-trucks/", "type": "contestgirl"},
    {"name": "ContestGirl - Travel", "url": "https://www.contestgirl.com/travel/", "type": "contestgirl"},
    {"name": "ContestGirl - Cash", "url": "https://www.contestgirl.com/cash-prizes/", "type": "contestgirl"},
    {"name": "Sweepstakes Fanatics", "url": "https://www.sweepstakesfanatics.com/", "type": "generic_list", "link_selector": "h2.entry-title a, h3.entry-title a"},
    {"name": "I Love Giveaways", "url": "https://ilovegiveaways.com/", "type": "generic_list", "link_selector": "h2.entry-title a, h3.entry-title a"},
    {"name": "Giveaway Frenzy", "url": "https://www.giveawayfrenzy.com/", "type": "generic_list", "link_selector": "h2 a, h3 a"},
    {"name": "Contestchest", "url": "https://www.contestchest.com/", "type": "generic_list", "link_selector": "h2 a, h3 a"},
    {"name": "Sweeties Sweeps", "url": "https://www.sweetiessweeps.com/", "type": "generic_list", "link_selector": "h2.entry-title a"},
    {"name": "Sweepstakes Lovers", "url": "https://www.sweepstakeslovers.com/", "type": "generic_list", "link_selector": "h2.entry-title a"},
    {"name": "Reddit r/sweepstakes", "url": "https://www.reddit.com/r/sweepstakes/.rss", "type": "rss"},
    {"name": "Reddit r/giveaways", "url": "https://www.reddit.com/r/giveaways/.rss", "type": "rss"},
    {"name": "Reddit r/Freebies", "url": "https://www.reddit.com/r/Freebies/.rss", "type": "rss"},
    {"name": "Reddit r/contests", "url": "https://www.reddit.com/r/contests/.rss", "type": "rss"},
]

BRAND_SOURCES = [
    {"name": "Motor Trend Sweepstakes", "url": "https://www.motortrend.com/sweepstakes/", "type": "brand_generic"},
    {"name": "Car and Driver Sweeps", "url": "https://www.caranddriver.com/sweepstakes/", "type": "brand_generic"},
    {"name": "Road and Track Sweeps", "url": "https://www.roadandtrack.com/sweepstakes/", "type": "brand_generic"},
    {"name": "Outside Magazine", "url": "https://www.outsideonline.com/sweepstakes/", "type": "brand_generic"},
    {"name": "Backpacker Magazine", "url": "https://www.backpacker.com/sweepstakes/", "type": "brand_generic"},
    {"name": "Field and Stream", "url": "https://www.fieldandstream.com/sweepstakes/", "type": "brand_generic"},
    {"name": "Popular Mechanics", "url": "https://www.popularmechanics.com/sweepstakes/", "type": "brand_generic"},
    {"name": "HGTV Sweepstakes", "url": "https://www.hgtv.com/sweepstakes/", "type": "brand_generic"},
    {"name": "Food Network Sweeps", "url": "https://www.foodnetwork.com/sweepstakes/", "type": "brand_generic"},
    {"name": "Good Housekeeping", "url": "https://www.goodhousekeeping.com/sweepstakes/", "type": "brand_generic"},
    {"name": "Country Living Sweeps", "url": "https://www.countryliving.com/sweepstakes/", "type": "brand_generic"},
    {"name": "House Beautiful", "url": "https://www.housebeautiful.com/sweepstakes/", "type": "brand_generic"},
    {"name": "Travel and Leisure", "url": "https://www.travelandleisure.com/sweepstakes/", "type": "brand_generic"},
    {"name": "Conde Nast Traveler", "url": "https://www.cntraveler.com/sweepstakes/", "type": "brand_generic"},
    {"name": "Taste of Home", "url": "https://www.tasteofhome.com/sweepstakes/", "type": "brand_generic"},
    {"name": "Mens Journal", "url": "https://www.mensjournal.com/sweepstakes/", "type": "brand_generic"},
    {"name": "Womens Health", "url": "https://www.womenshealthmag.com/sweepstakes/", "type": "brand_generic"},
    {"name": "Harley Davidson", "url": "https://www.harley-davidson.com/us/en/sweepstakes.html", "type": "brand_generic"},
    {"name": "Polaris", "url": "https://www.polaris.com/en-us/promotions/", "type": "brand_generic"},
    {"name": "Bass Pro Sweeps", "url": "https://www.basspro.com/shop/en/sweepstakes", "type": "brand_generic"},
    {"name": "Cabelas Sweepstakes", "url": "https://www.cabelas.com/shop/en/sweepstakes", "type": "brand_generic"},
    {"name": "Home Depot Sweeps", "url": "https://sweepstakes.homedepot.com/", "type": "brand_generic"},
    {"name": "Samsung Promotions", "url": "https://www.samsung.com/us/promotions/", "type": "brand_generic"},
    {"name": "LG Promotions", "url": "https://www.lg.com/us/promotions/", "type": "brand_generic"},
    {"name": "Pechanga Casino", "url": "https://www.pechanga.com/promotions", "type": "brand_generic"},
    {"name": "Morongo Casino", "url": "https://www.morongocasinoresort.com/promotions/", "type": "brand_generic"},
    {"name": "Agua Caliente Casino", "url": "https://www.aguacalientecasinos.com/promotions/", "type": "brand_generic"},
    {"name": "San Manuel Casino", "url": "https://www.sanmanuel.com/promotions", "type": "brand_generic"},
    {"name": "Soboba Casino", "url": "https://www.soboba.com/promotions/", "type": "brand_generic"},
    {"name": "Harrahs SoCal", "url": "https://www.harrahssocal.com/promotions/", "type": "brand_generic"},
    {"name": "Viejas Casino", "url": "https://www.viejas.com/promotions/", "type": "brand_generic"},
    {"name": "Pala Casino", "url": "https://www.palacasino.com/promotions/", "type": "brand_generic"},
    {"name": "Hollywood Park Casino", "url": "https://hollywoodparkcasino.com/promotions/", "type": "brand_generic"},
    {"name": "Bicycle Casino", "url": "https://www.bicycle-casino.com/promotions/", "type": "brand_generic"},
    {"name": "Commerce Casino", "url": "https://www.commercecasino.com/promotions/", "type": "brand_generic"},
    {"name": "MGM Grand", "url": "https://www.mgmgrand.com/en/entertainment/promotions.html", "type": "brand_generic"},
    {"name": "Caesars", "url": "https://www.caesars.com/caesars-palace/promotions", "type": "brand_generic"},
    {"name": "Wynn Las Vegas", "url": "https://www.wynnlasvegas.com/Entertainment/Promotions", "type": "brand_generic"},
    {"name": "Hard Rock Casino", "url": "https://www.hardrockcafe.com/promotions/", "type": "brand_generic"},
    {"name": "Foxwoods Casino", "url": "https://www.foxwoods.com/promotions/", "type": "brand_generic"},
    {"name": "Mohegan Sun", "url": "https://www.mohegansun.com/promotions.html", "type": "brand_generic"},
    {"name": "Golden Nugget", "url": "https://www.goldennugget.com/promotions/", "type": "brand_generic"},
    {"name": "Coca Cola", "url": "https://us.coca-cola.com/promotions", "type": "brand_generic"},
    {"name": "Frito Lay", "url": "https://www.fritolay.com/promotions", "type": "brand_generic"},
    {"name": "Dole", "url": "https://www.dole.com/en/promotions", "type": "brand_generic"},
    {"name": "Southwest Airlines", "url": "https://www.southwest.com/html/air/promotions/", "type": "brand_generic"},
    {"name": "Visit California", "url": "https://www.visitcalifornia.com/promotions/", "type": "brand_generic"},
]

ALL_SOURCES = AGGREGATOR_SOURCES + BRAND_SOURCES

CA_EXCLUDE = [
    r'void\s+in\s+california', r'void\s+in\s+ca\b',
    r'california\s+residents?\s+not\s+eligible',
    r'not\s+open\s+to\s+california', r'excluding\s+california',
    r'uk\s+only', r'united\s+kingdom\s+only',
    r'canada\s+only', r'canadian\s+residents?\s+only',
    r'eu\s+only', r'australia\s+only',
]

SOCIAL_EXCLUDE = [
    r'follow\s+us', r'follow\s+@', r'like\s+our\s+page',
    r'share\s+this\s+post', r'tag\s+\d+\s+friend',
    r'retweet\s+to\s+enter', r'must\s+follow',
    r'comment\s+below\s+to\s+win', r'dm\s+us\s+to\s+enter',
]

CONTEST_KEYWORDS = [
    'sweepstakes','giveaway','contest','prize','drawing',
    'enter to win','chance to win','no purchase necessary',
]

CATEGORY_MAP = {
    'automotive': ['car','truck','suv','vehicle','motorcycle','auto','tesla','ford','chevy','dodge','jeep','ram','toyota','honda','bmw','harley','e-bike','boat','rv','polaris'],
    'travel': ['vacation','trip','flight','hotel','resort','cruise','airfare','travel','getaway','beach','island','caribbean','hawaii','disney'],
    'technology': ['iphone','samsung','laptop','tablet','ipad','tv','television','gaming','playstation','xbox','nintendo','airpods','headphones','camera','drone','gopro'],
    'outdoor': ['north face','patagonia','rei','columbia','camping','hiking','outdoor','adventure','yeti','gear','kayak','ski','snowboard','fishing','hunting','cooler'],
    'home': ['furniture','ikea','west elm','kitchen','appliance','renovation','home','decor','makeover','mattress','backyard','patio','grill','garden'],
    'cash': ['cash','gift card','amazon','visa','mastercard','prepaid','paypal','money','dollar','$'],
    'fitness': ['peloton','gym','fitness','workout','bike','treadmill','health','wellness','spa'],
    'clothing': ['apparel','clothing','shoes','boots','jacket','hoodie','sneakers','fashion'],
    'food_bev': ['food','restaurant','dining','beverage','coffee','beer','wine','grocery'],
    'casino': ['casino','resort','slots','poker','gaming'],
    'experience': ['concert','tickets','event','show','festival','vip','backstage','sports'],
}

SEEN_FILE = '../data/seen_contests.json'

def fingerprint(url, title):
    raw = f"{url.strip().lower()}||{title.strip().lower()}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]

def sleep_politely():
    time.sleep(random.uniform(*REQUEST_DELAY))

def fetch(url, timeout=15):
    try:
        r = SESSION.get(url, timeout=timeout, allow_redirects=True)
        r.raise_for_status()
        return BeautifulSoup(r.text, 'html.parser')
    except Exception as e:
        log.warning(f"Failed {url}: {e}")
        return None

def extract_prize_value(text):
    matches = re.findall(r'\$\s*([\d,]+)', text)
    values = []
    for m in matches:
        try:
            values.append(int(m.replace(',','')))
        except:
            pass
    return max(values) if values else 0

def categorize(title, description=''):
    combined = (title + ' ' + description).lower()
    for cat, keywords in CATEGORY_MAP.items():
        for kw in keywords:
            if kw in combined:
                return cat
    return 'other'

def is_ca_eligible(text):
    text_lower = text.lower()
    for pat in CA_EXCLUDE:
        if re.search(pat, text_lower):
            return False
    return True

def is_social_required(text):
    text_lower = text.lower()
    for pat in SOCIAL_EXCLUDE:
        if re.search(pat, text_lower):
            return True
    return False

def is_contest_related(title, description=''):
    combined = (title + ' ' + description).lower()
    return any(kw in combined for kw in CONTEST_KEYWORDS)

def parse_date(text):
    month_map = {
        'january':1,'february':2,'march':3,'april':4,'may':5,'june':6,
        'july':7,'august':8,'september':9,'october':10,'november':11,'december':12
    }
    patterns = [
        r'(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2}),?\s+(\d{4})',
        r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})',
        r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',
    ]
    text_lower = text.lower()
    for pat in patterns:
        m = re.search(pat, text_lower)
        if m:
            try:
                g = m.groups()
                if g[0] in month_map:
                    return datetime(int(g[2]), month_map[g[0]], int(g[1]))
                nums = [int(x) for x in g]
                if nums[0] > 31:
                    return datetime(nums[0], nums[1], nums[2])
                y = nums[2] if nums[2] > 100 else 2000 + nums[2]
                return datetime(y, nums[0], nums[1])
            except:
                pass
    return None

def is_fresh(date, title='', url=''):
    if date is None:
        stale = re.findall(r'20(2[0123])', title + url)
        if stale:
            return False
        return True
    return date >= datetime.now() - timedelta(days=MAX_AGE_DAYS)

def scrape_contestbee(source):
    contests = []
    soup = fetch(source['url'])
    if not soup:
        return contests
    for card in soup.select('article, .contest-item, .giveaway-item, [class*="contest"], [class*="giveaway"]'):
        a = card.find('a', href=True)
        if not a:
            continue
        title = a.get_text(strip=True)
        if not title:
            continue
        url = a['href']
        if not url.startswith('http'):
            url = urljoin(source['url'], url)
        desc = card.get_text(' ', strip=True)
        contests.append({'title': title, 'url': url, 'description': desc[:300],
            'source': source['name'], 'date': parse_date(desc),
            'category': categorize(title, desc), 'prize_value': extract_prize_value(desc)})
    return contests

def scrape_contestgirl(source):
    contests = []
    soup = fetch(source['url'])
    if not soup:
        return contests
    for card in soup.select('article, .post, .entry, [class*="contest"], [class*="sweep"]'):
        a = card.find('a', href=True)
        if not a:
            continue
        title = a.get_text(strip=True)
        if not title or len(title) < 5:
            continue
        url = a['href']
        if not url.startswith('http'):
            url = urljoin(source['url'], url)
        desc = card.get_text(' ', strip=True)
        contests.append({'title': title, 'url': url, 'description': desc[:300],
            'source': source['name'], 'date': parse_date(desc),
            'category': categorize(title, desc), 'prize_value': extract_prize_value(desc)})
    return contests

def scrape_rss(source):
    contests = []
    try:
        feed = feedparser.parse(source['url'])
        for entry in feed.entries[:30]:
            title = entry.get('title', '')
            url = entry.get('link', '')
            desc = entry.get('summary', '')
            published = entry.get('published_parsed')
            date = None
            if published:
                try:
                    date = datetime(*published[:6])
                except:
                    pass
            if not is_contest_related(title, desc):
                continue
            contests.append({'title': title, 'url': url, 'description': desc[:300],
                'source': source['name'], 'date': date,
                'category': categorize(title, desc), 'prize_value': extract_prize_value(desc)})
    except Exception as e:
        log.warning(f"RSS error {source['url']}: {e}")
    return contests

def scrape_generic_list(source):
    contests = []
    soup = fetch(source['url'])
    if not soup:
        return contests
    for a in soup.select(source.get('link_selector', 'h2 a, h3 a')):
        title = a.get_text(strip=True)
        if not title or len(title) < 5:
            continue
        url = a.get('href', '')
        if not url:
            continue
        if not url.startswith('http'):
            url = urljoin(source['url'], url)
        parent_text = a.parent.get_text(' ', strip=True) if a.parent else ''
        contests.append({'title': title, 'url': url, 'description': parent_text[:300],
            'source': source['name'], 'date': parse_date(parent_text),
            'category': categorize(title, parent_text), 'prize_value': extract_prize_value(parent_text)})
    return contests

def scrape_brand_page(source):
    contests = []
    soup = fetch(source['url'])
    if not soup:
        return contests
    page_text = soup.get_text(' ', strip=True)
    if not is_contest_related(page_text):
        return contests
    for a in soup.find_all('a', href=True):
        title = a.get_text(strip=True)
        href = a['href']
        if not title or len(title) < 8:
            continue
        if not is_contest_related(title):
            continue
        if not href.startswith('http'):
            href = urljoin(source['url'], href)
        if href == source['url']:
            continue
        parent_text = a.parent.get_text(' ', strip=True) if a.parent else ''
        contests.append({'title': f"{source['name']}: {title}", 'url': href,
            'description': parent_text[:300], 'source': source['name'],
            'date': parse_date(parent_text), 'category': categorize(title, parent_text),
            'prize_value': extract_prize_value(parent_text)})
    if not contests and is_contest_related(page_text[:500]):
        contests.append({'title': f"{source['name']} Promotion", 'url': source['url'],
            'description': page_text[:300], 'source': source['name'],
            'date': parse_date(page_text[:1000]), 'category': categorize(source['name'], page_text[:500]),
            'prize_value': extract_prize_value(page_text[:1000])})
    return contests

SCRAPER_MAP = {
    'contestbee': scrape_contestbee,
    'contestgirl': scrape_contestgirl,
    'rss': scrape_rss,
    'generic_list': scrape_generic_list,
    'brand_generic': scrape_brand_page,
}

def load_seen():
    try:
        with open(SEEN_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_seen(seen):
    import os
    os.makedirs('../data', exist_ok=True)
    cutoff = (datetime.now() - timedelta(days=60)).isoformat()
    seen = {k: v for k, v in seen.items() if v >= cutoff}
    with open(SEEN_FILE, 'w') as f:
        json.dump(seen, f, indent=2)

def run():
    log.info("=== CONTEST HULK STARTING ===")
    seen = load_seen()
    log.info(f"Loaded {len(seen)} previously seen contests")
    all_contests = []
    total = len(ALL_SOURCES)
    for i, source in enumerate(ALL_SOURCES, 1):
        log.info(f"[{i}/{total}] {source['name']}")
        scraper = SCRAPER_MAP.get(source['type'])
        if not scraper:
            continue
        try:
            results = scraper(source)
            log.info(f"  -> {len(results)} raw results")
            all_contests.extend(results)
        except Exception as e:
            log.error(f"  -> ERROR: {e}")
        sleep_politely()
    log.info(f"Total raw: {len(all_contests)}")
    today = datetime.now().isoformat()
    new_seen = dict(seen)
    kept = []
    for c in all_contests:
        title = c.get('title','').strip()
        url = c.get('url','').strip()
        if not title or not url:
            continue
        fp = fingerprint(url, title)
        if fp in seen:
            continue
        if not is_fresh(c.get('date'), title, url):
            continue
        combined = f"{title} {c.get('description','')}"
        if not is_ca_eligible(combined):
            continue
        if is_social_required(combined):
            continue
        if not is_contest_related(title, c.get('description','')):
            continue
        new_seen[fp] = today
        kept.append(c)
    seen_fps = set()
    deduped = []
    for c in kept:
        fp = fingerprint(c['url'], c['title'])
        if fp not in seen_fps:
            seen_fps.add(fp)
            deduped.append(c)
    def score(c):
        s = min(c.get('prize_value',0)//100, 50)
        if c.get('category') in ['automotive','travel','technology']:
            s += 20
        if 'california' in (c.get('description','') + c.get('title','')).lower():
            s += 15
        if c.get('date'):
            s += max(0, 30 - (datetime.now() - c['date']).days)
        return s
    deduped.sort(key=score, reverse=True)
    save_seen(new_seen)
    log.info(f"Final contests to send: {len(deduped)}")
    return deduped
