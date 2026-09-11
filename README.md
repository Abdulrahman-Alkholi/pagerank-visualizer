# PageRank Explorer

A small web crawler, PageRank calculator, and interactive force-directed
visualizer, built in Python and D3.js. Point it at a starting URL, let it
crawl and rank pages, then explore the resulting link graph in your browser —
node size and color scale with PageRank, and hovering a node reveals its URL,
rank, and incoming-link count.

![Python](https://img.shields.io/badge/python-3.x-blue)
![License: MIT](https://img.shields.io/badge/license-MIT-green)

## Features

- **Web crawler** (`spider.py`) — crawls a site, follows links, and stores
  pages and link relationships in a local SQLite database.
- **PageRank engine** (`sprank.py`) — runs iterative PageRank over the
  crawled link graph until it converges.
- **JSON exporter** (`spjson.py`) — exports the top-ranked pages and their
  links for the visualizer.
- **Interactive visualization** (`force.html`) — a modern, dashboard-style
  force-directed graph (D3.js) with:
  - Node size and color mapped to PageRank
  - Hover tooltips showing URL, PageRank, and incoming links
  - Highlighting of a node's connections on hover
  - A live stats panel, gradient legend, and a "Top Pages" leaderboard
  - Responsive layout for different screen sizes

## Requirements

- Python 3.x
- [BeautifulSoup4](https://pypi.org/project/beautifulsoup4/)

```bash
pip install beautifulsoup4
```

No build step is required for the visualization — it's plain HTML/CSS/JS and
runs directly in a browser.

## How it works

The pipeline has four stages, each a standalone script:

```
spider.py  →  spider.sqlite  →  sprank.py  →  spjson.py  →  spider.js  →  force.html
 (crawl)        (storage)       (rank)        (export)      (data)      (visualize)
```

## Usage

### 1. Crawl a website

```bash
python spider.py
```

You'll be prompted for a starting URL and how many pages to crawl. The
crawler stores pages and links in `spider.sqlite`. Run it again (optionally
pointing at a different URL) to keep adding more pages — already-crawled
pages are never re-crawled.

```
Enter web url or enter: https://example.com/
How many pages: 10
```

### 2. Compute PageRank

```bash
python sprank.py
```

Enter the number of iterations to run. More iterations produce a more
converged (accurate) ranking. You can run this multiple times to keep
refining the ranks as you crawl more pages.

```
How many iterations: 50
```

To reset all ranks back to 1.0 and start over without re-crawling:

```bash
python spreset.py
```

### 3. Export the graph for visualization

```bash
python spjson.py
```

You'll be asked how many top-ranked nodes to include. This writes the graph
data (nodes + links) to `spider.js`.

```
How many nodes? 30
```

### 4. View the visualization

Open `force.html` directly in your browser, or serve it locally:

```bash
python -m http.server 8000
```

Then visit `http://localhost:8000/force.html`.

- **Hover** a node to see its URL, PageRank, and incoming-link count, and to
  highlight its connections.
- **Drag** a node to reposition it.
- **Double-click** a node to open its URL in a new tab.

Re-run `spjson.py` any time after crawling more pages or recomputing
PageRank, then refresh the browser to see updated data.

### Inspecting the raw data

```bash
python spdump.py
```

Prints each page's incoming link count, old/new PageRank, id, and URL
directly from the database.

## Project structure

```
spider.py       Crawls a site and stores pages/links in SQLite
spider.sqlite   Crawled data (pages, links, ranks)
sprank.py       Runs the PageRank algorithm
spreset.py      Resets all PageRank values to 1.0
spjson.py       Exports top pages/links to spider.js
spdump.py       Prints the database contents to the console
spider.js       Generated graph data (consumed by force.html)
force.html      Visualization page
force.css       Visualization styling
force.js        Visualization logic (D3.js force layout)
d3.v2.js        D3.js library (bundled locally)
```

## License

MIT — see [LICENSE](LICENSE).
