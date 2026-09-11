
import sqlite3

conn = sqlite3.connect("spider.sqlite")
cur = conn.cursor()

print("Creating JSON output on spider.js...")

howmany = int(input("How many nodes? "))

cur.execute("""
    SELECT COUNT(from_id) AS inbound,
           old_rank,
           new_rank,
           id,
           url
    FROM Pages
    JOIN Links ON Pages.id = Links.to_id
    WHERE html IS NOT NULL AND error IS NULL
    GROUP BY id
    ORDER BY id, inbound
""")

fhand = open("spider.js", "w", encoding="utf-8")

nodes = []

maxrank = None
minrank = None

for row in cur:

    nodes.append(row)

    rank = row[2]

    if maxrank is None or maxrank < rank:
        maxrank = rank

    if minrank is None or minrank > rank:
        minrank = rank

    if len(nodes) >= howmany:
        break

# Check whether PageRank has been calculated.

if maxrank == minrank or maxrank is None or minrank is None:
    print("Error - please run sprank.py to compute page rank")
    fhand.close()
    cur.close()
    conn.close()
    quit()

# Start the JSON output.

fhand.write('spiderJson = {"nodes":[\n')

count = 0

node_map = {}
ranks = {}

for row in nodes:

    if count > 0:
        fhand.write(",\n")

    rank = row[2]

    # Scale PageRank to a value between 0 and 19.
    scaled_rank = 19 * (
        (rank - minrank) / (maxrank - minrank)
    )

    fhand.write(
        '{"weight":' + str(row[0]) +
        ',"rank":' + str(scaled_rank) +
        ',"id":' + str(row[3]) +
        ',"url":"' + row[4] + '"}'
    )

    node_map[row[3]] = count
    ranks[row[3]] = scaled_rank

    count += 1

fhand.write("],\n")

# Create the links section.

cur.execute("SELECT DISTINCT from_id, to_id FROM Links")

fhand.write('"links":[\n')

count = 0

for row in cur:

    from_id = row[0]
    to_id = row[1]

    # Only include links where both nodes
    # are part of our selected nodes.

    if from_id not in node_map or to_id not in node_map:
        continue

    if count > 0:
        fhand.write(",\n")

    fhand.write(
        '{"source":' + str(node_map[from_id]) +
        ',"target":' + str(node_map[to_id]) +
        ',"value":3}'
    )

    count += 1

fhand.write("]};")

fhand.close()
cur.close()
conn.close()

print("Open force.html in a browser to view the visualization")

