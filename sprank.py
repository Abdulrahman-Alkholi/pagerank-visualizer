import sqlite3

conn = sqlite3.connect("spider.sqlite")
cur = conn.cursor()

# Find the IDs that send out PageRank.
# We are only interested in pages in the SCC
# that have both incoming and outgoing links.

cur.execute("SELECT DISTINCT from_id FROM Links")

from_ids = []

for row in cur:
    from_ids.append(row[0])

# Find the IDs that receive PageRank.

to_ids = []
links = []

cur.execute("SELECT DISTINCT from_id, to_id FROM Links")

for row in cur:
    from_id = row[0]
    to_id = row[1]

    if from_id == to_id:
        continue

    if from_id not in from_ids:
        continue

    if to_id not in from_ids:
        continue

    links.append(row)

    if to_id not in to_ids:
        to_ids.append(to_id)

# Get the latest PageRank values for the strongly connected component.

prev_ranks = {}

for node in from_ids:
    cur.execute(
        "SELECT new_rank FROM Pages WHERE id = ?",
        (node,)
    )

    row = cur.fetchone()

    if row is not None:
        prev_ranks[node] = row[0]

# Ask how many iterations to perform.

sval = input("How many iterations: ")

many = 1

if len(sval) > 0:
    many = int(sval)

# Sanity check

if len(prev_ranks) < 1:
    print("Nothing to page rank. Check data.")
    conn.close()
    quit()

# Do PageRank in memory so it is fast.

for i in range(many):

    next_ranks = {}
    total = 0.0

    # Calculate total current PageRank
    # and initialize the next ranks.

    for node, old_rank in prev_ranks.items():
        total += old_rank
        next_ranks[node] = 0.0

    # Find the number of outbound links
    # and distribute the PageRank among them.

    for node, old_rank in prev_ranks.items():

        give_ids = []

        for from_id, to_id in links:

            if from_id != node:
                continue

            if to_id not in to_ids:
                continue

            give_ids.append(to_id)

        if len(give_ids) < 1:
            continue

        amount = old_rank / len(give_ids)

        for link_id in give_ids:
            next_ranks[link_id] += amount

    # Calculate the total PageRank after distributing it.

    newtot = 0.0

    for node, next_rank in next_ranks.items():
        newtot += next_rank

    # Redistribute the lost PageRank (evaporation).

    evap = (total - newtot) / len(next_ranks)

    for node in next_ranks:
        next_ranks[node] += evap

    # Calculate the new total.

    newtot = 0.0

    for node, next_rank in next_ranks.items():
        newtot += next_rank

    # Calculate the average change from old rank to new rank.
    # This indicates convergence.

    totdiff = 0.0

    for node, old_rank in prev_ranks.items():
        new_rank = next_ranks[node]
        diff = abs(old_rank - new_rank)
        totdiff += diff

    avediff = totdiff / len(prev_ranks)

    print(i + 1, avediff)

    # Move to the next iteration.

    prev_ranks = next_ranks

# Put the final ranks back into the database.

print(list(next_ranks.items())[:5])

cur.execute("UPDATE Pages SET old_rank = new_rank")

for page_id, new_rank in next_ranks.items():
    cur.execute(
        "UPDATE Pages SET new_rank = ? WHERE id = ?",
        (new_rank, page_id)
    )

conn.commit()

cur.close()
conn.close()