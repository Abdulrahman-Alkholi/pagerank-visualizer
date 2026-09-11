
import sqlite3
import urllib.request
import urllib.error
import ssl
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

# Deal with SSL certificate anomalies
scontext = None

conn = sqlite3.connect("spider.sqlite")
cur = conn.cursor()

# Create tables
cur.execute("""
CREATE TABLE IF NOT EXISTS Pages
    (id INTEGER PRIMARY KEY, url TEXT UNIQUE, html TEXT,
     error INTEGER, old_rank REAL, new_rank REAL)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS Links
    (from_id INTEGER, to_id INTEGER)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS Webs
    (url TEXT UNIQUE)
""")

# Check to see if we are already in progress
cur.execute("""
SELECT id, url
FROM Pages
WHERE html IS NULL AND error IS NULL
ORDER BY RANDOM()
LIMIT 1
""")

row = cur.fetchone()

if row is not None:
    print("Restarting existing crawl. Remove spider.sqlite to start a fresh crawl.")

else:
    starturl = input("Enter web url or enter: ").strip()

    if len(starturl) < 1:
        starturl = "https://en.wikipedia.org/wiki/Palestine"

    if starturl.endswith("/"):
        starturl = starturl[:-1]

    web = starturl

    if starturl.endswith(".htm") or starturl.endswith(".html"):
        pos = starturl.rfind("/")
        web = starturl[:pos]

    if len(web) > 1:
        cur.execute(
            "INSERT OR IGNORE INTO Webs (url) VALUES (?)",
            (web,)
        )

        cur.execute(
            """
            INSERT OR IGNORE INTO Pages
            (url, html, new_rank)
            VALUES (?, NULL, 1.0)
            """,
            (starturl,)
        )

        conn.commit()


# Get the current webs
cur.execute("SELECT url FROM Webs")

webs = []

for row in cur:
    webs.append(str(row[0]))

print("Allowed websites:")
print(webs)


many = 0

while True:

    if many < 1:
        sval = input("How many pages: ").strip()

        if len(sval) < 1:
            break

        many = int(sval)

    many -= 1

    cur.execute("""
    SELECT id, url
    FROM Pages
    WHERE html IS NULL AND error IS NULL
    ORDER BY RANDOM()
    LIMIT 1
    """)

    row = cur.fetchone()

    if row is None:
        print("No unretrieved HTML pages found")
        many = 0
        break

    fromid = row[0]
    url = row[1]

    print(fromid, url)

    # If we are retrieving this page,
    # there should be no links from it yet.
    cur.execute(
        "DELETE FROM Links WHERE from_id=?",
        (fromid,)
    )

    try:

        # Request the page
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        )

        if scontext is not None:
            document = urllib.request.urlopen(
                request,
                context=scontext
            )
        else:
            document = urllib.request.urlopen(request)

        html = document.read()

        status_code = document.getcode()

        if status_code != 200:
            print("Error on page:", status_code)

            cur.execute(
                "UPDATE Pages SET error=? WHERE url=?",
                (status_code, url)
            )

            conn.commit()
            continue

        content_type = document.headers.get_content_type()

        if content_type != "text/html":
            print("Ignore non text/html page")

            cur.execute(
                "UPDATE Pages SET error=-1 WHERE url=?",
                (url,)
            )

            conn.commit()
            continue

        print("(" + str(len(html)) + " bytes)", end=" ")

        # Decode HTML
        html_text = html.decode("utf-8", errors="replace")

        soup = BeautifulSoup(html_text, "html.parser")

    except KeyboardInterrupt:
        print("\nProgram interrupted by user...")
        break

    except Exception as e:
        print("Unable to retrieve or parse page:", e)

        cur.execute(
            "UPDATE Pages SET error=-1 WHERE url=?",
            (url,)
        )

        conn.commit()
        continue

    # Save HTML
    cur.execute(
        """
        INSERT OR IGNORE INTO Pages
        (url, html, new_rank)
        VALUES (?, NULL, 1.0)
        """,
        (url,)
    )

    cur.execute(
        "UPDATE Pages SET html=? WHERE url=?",
        (html_text, url)
    )

    conn.commit()

    # Retrieve all anchor tags
    tags = soup.find_all("a")

    count = 0

    for tag in tags:

        href = tag.get("href")

        if href is None:
            continue

        href = href.strip()

        # Resolve relative references such as:
        # href="/contact"
        up = urlparse(href)

        if len(up.scheme) < 1:
            href = urljoin(url, href)

        # Remove fragments
        ipos = href.find("#")

        if ipos > 0:
            href = href[:ipos]

        # Ignore images
        lower_href = href.lower()

        if (
            lower_href.endswith(".png")
            or lower_href.endswith(".jpg")
            or lower_href.endswith(".jpeg")
            or lower_href.endswith(".gif")
            or lower_href.endswith(".svg")
            or lower_href.endswith(".webp")
        ):
            continue

        if href.endswith("/"):
            href = href[:-1]

        if len(href) < 1:
            continue

        # Check if the URL belongs to one of our allowed websites
        found = False

        for web in webs:

            if href.startswith(web):
                found = True
                break

        if not found:
            continue

        # Add page if it doesn't already exist
        cur.execute(
            """
            INSERT OR IGNORE INTO Pages
            (url, html, new_rank)
            VALUES (?, NULL, 1.0)
            """,
            (href,)
        )

        count += 1

        # Get the page ID
        cur.execute(
            "SELECT id FROM Pages WHERE url=? LIMIT 1",
            (href,)
        )

        row = cur.fetchone()

        if row is None:
            print("Could not retrieve id")
            continue

        toid = row[0]

        # Create the link
        cur.execute(
            """
            INSERT OR IGNORE INTO Links
            (from_id, to_id)
            VALUES (?, ?)
            """,
            (fromid, toid)
        )

    conn.commit()

    print("links:", count)

cur.close()
conn.close()

