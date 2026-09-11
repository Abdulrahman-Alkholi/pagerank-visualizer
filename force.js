/* PageRank Explorer — force-directed visualization (D3 v2) */

var container = document.getElementById("chart");
var width = Math.max(container.clientWidth || 640, 320);
var height = Math.round(Math.min(Math.max(width * 0.68, 420), 720));

/* Drop self-loop links: they carry no layout information and destabilize the
   force simulation (zero-length link -> divide-by-zero). */
spiderJson.links = spiderJson.links.filter(function (l) {
  return l.source !== l.target;
});

var ranks = spiderJson.nodes.map(function (d) {
  return d.rank;
});
var minRank = d3.min(ranks);
var maxRank = d3.max(ranks);
var midRank = (minRank + maxRank) / 2;

/* Node radius scales with PageRank */
var radiusScale = d3.scale.linear().domain([minRank, maxRank]).range([7, 30]);

/* Color is meaningful: cool (low rank) -> warm (high rank) */
var colorScale = d3.scale
  .linear()
  .domain([minRank, midRank, maxRank])
  .range(["#3b82f6", "#a855f7", "#ef4444"]);

function getrank(rval) {
  return radiusScale(rval);
}

function getcolor(rval) {
  return colorScale(rval);
}

/* Incoming link counts + neighbor lookup (from raw indices) */
var incoming = {};
var neighbors = {};
spiderJson.nodes.forEach(function (n, i) {
  incoming[i] = 0;
  neighbors[i] = {};
});
spiderJson.links.forEach(function (l) {
  if (l.source === l.target) return;
  incoming[l.target] = (incoming[l.target] || 0) + 1;
  neighbors[l.source][l.target] = true;
  neighbors[l.target][l.source] = true;
});

var force = d3.layout
  .force()
  .charge(-220)
  .linkDistance(110)
  .gravity(0.25)
  .friction(0.9)
  .size([width, height]);

var svg = d3
  .select("#chart")
  .append("svg")
  .attr("viewBox", "0 0 " + width + " " + height)
  .attr("preserveAspectRatio", "xMidYMid meet");

/* Soft glow filter for hovered nodes */
var defs = svg.append("defs");
var glow = defs
  .append("filter")
  .attr("id", "glow")
  .attr("x", "-50%")
  .attr("y", "-50%")
  .attr("width", "200%")
  .attr("height", "200%");
glow
  .append("feGaussianBlur")
  .attr("stdDeviation", "3.5")
  .attr("result", "blur");
var merge = glow.append("feMerge");
merge.append("feMergeNode").attr("in", "blur");
merge.append("feMergeNode").attr("in", "SourceGraphic");

var linkLayer = svg.append("g").attr("class", "links");
var nodeLayer = svg.append("g").attr("class", "nodes");

var tooltip = d3.select("#tooltip");
var link, node, halo;

function loadData(json) {
  /* Seed positions on a centered ring so the simulation starts stable
     (this D3 v2 build diverges from a wide random layout). */
  json.nodes.forEach(function (n, i) {
    var a = (i / json.nodes.length) * 2 * Math.PI;
    n.x = width / 2 + Math.cos(a) * 90;
    n.y = height / 2 + Math.sin(a) * 90;
    n.px = n.x;
    n.py = n.y;
  });

  force.nodes(json.nodes).links(json.links);

  force.start();

  link = linkLayer
    .selectAll("line.link")
    .data(json.links)
    .enter()
    .append("line")
    .attr("class", "link")
    .style("stroke-width", function (d) {
      return Math.sqrt(d.value);
    });

  halo = nodeLayer
    .selectAll("circle.node-halo")
    .data(json.nodes)
    .enter()
    .append("circle")
    .attr("class", "node-halo")
    .attr("r", function (d) {
      return getrank(d.rank) + 6;
    });

  node = nodeLayer
    .selectAll("circle.node")
    .data(json.nodes)
    .enter()
    .append("circle")
    .attr("class", "node")
    .attr("r", function (d) {
      return getrank(d.rank);
    })
    .style("fill", function (d) {
      return getcolor(d.rank);
    })
    .on("mouseover", function (d, i) {
      highlight(i);
      showTooltip(d, i);
    })
    .on("mousemove", moveTooltip)
    .on("mouseout", function () {
      clearHighlight();
      hideTooltip();
    })
    .on("dblclick", function (d) {
      if (confirm("Do you want to open " + d.url))
        window.open(d.url, "_new", "");
      d3.event.stopPropagation();
    })
    .call(force.drag);

  /* keep native title as an accessible fallback */
  node.append("title").text(function (d) {
    return d.url;
  });

  /* entrance animation */
  node
    .style("opacity", 0)
    .attr("r", 0)
    .transition()
    .duration(600)
    .delay(function (d, i) {
      return i * 20;
    })
    .style("opacity", 1)
    .attr("r", function (d) {
      return getrank(d.rank);
    });

  force.on("tick", function () {
    link
      .attr("x1", function (d) {
        return d.source.x;
      })
      .attr("y1", function (d) {
        return d.source.y;
      })
      .attr("x2", function (d) {
        return d.target.x;
      })
      .attr("y2", function (d) {
        return d.target.y;
      });

    node
      .attr("cx", function (d) {
        return d.x;
      })
      .attr("cy", function (d) {
        return d.y;
      });

    halo
      .attr("cx", function (d) {
        return d.x;
      })
      .attr("cy", function (d) {
        return d.y;
      });
  });
}

/* ---------- Highlight ---------- */
function highlight(i) {
  node.classed("is-dim", function (d, j) {
    return j !== i && !neighbors[i][j];
  });
  node.classed("is-hi", function (d, j) {
    return j === i;
  });
  halo.style("opacity", function (d, j) {
    return j === i ? 1 : 0;
  });
  link.classed("is-hi", function (d) {
    return d.source.index === i || d.target.index === i;
  });
  link.classed("is-dim", function (d) {
    return d.source.index !== i && d.target.index !== i;
  });
}

function clearHighlight() {
  node.classed("is-dim", false).classed("is-hi", false);
  halo.style("opacity", 0);
  link.classed("is-hi", false).classed("is-dim", false);
}

/* ---------- Tooltip ---------- */
function showTooltip(d, i) {
  tooltip
    .html(
      '<div class="tooltip__url">' +
        escapeHtml(d.url) +
        "</div>" +
        '<div class="tooltip__row"><span>PageRank</span><span>' +
        d.rank.toFixed(3) +
        "</span></div>" +
        '<div class="tooltip__row"><span>Incoming links</span><span>' +
        (incoming[i] || 0) +
        "</span></div>",
    )
    .attr("aria-hidden", "false")
    .classed("is-visible", true);
  moveTooltip(d);
}

function moveTooltip() {
  var e = d3.event;
  if (!e) return;
  var pad = 16;
  var tw = tooltip.node().offsetWidth;
  var th = tooltip.node().offsetHeight;
  var x = e.clientX + pad;
  var y = e.clientY + pad;
  if (x + tw > window.innerWidth) x = e.clientX - tw - pad;
  if (y + th > window.innerHeight) y = e.clientY - th - pad;
  tooltip.style("left", x + "px").style("top", y + "px");
}

function hideTooltip() {
  tooltip.classed("is-visible", false).attr("aria-hidden", "true");
}

function escapeHtml(s) {
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

/* ---------- Chrome: stats, legend, top list, buttons ---------- */
function buildChrome() {
  var totalLinks = spiderJson.links.filter(function (l) {
    return l.source !== l.target;
  }).length;

  var stats = [
    { value: spiderJson.nodes.length, label: "Pages" },
    { value: totalLinks, label: "Links" },
    { value: maxRank.toFixed(2), label: "Max rank" },
  ];
  d3.select("#stats")
    .selectAll("div.stat")
    .data(stats)
    .enter()
    .append("div")
    .attr("class", "stat")
    .html(function (s) {
      return (
        '<div class="stat__value">' +
        s.value +
        '</div><div class="stat__label">' +
        s.label +
        "</div>"
      );
    });

  var startUrl = spiderJson.nodes[0].url;
  d3.select("#start-url").attr("href", startUrl).text(startUrl);

  d3.select("#legend-scale").style(
    "background",
    "linear-gradient(90deg, " +
      colorScale(minRank) +
      ", " +
      colorScale(midRank) +
      ", " +
      colorScale(maxRank) +
      ")",
  );

  var top = spiderJson.nodes
    .map(function (d, i) {
      return { d: d, i: i };
    })
    .sort(function (a, b) {
      return b.d.rank - a.d.rank;
    })
    .slice(0, 5);

  d3.select("#toplist")
    .selectAll("li")
    .data(top)
    .enter()
    .append("li")
    .html(function (t) {
      var name = t.d.url.replace(/^https?:\/\/[^/]+\//, "");
      return (
        '<button type="button" data-i="' +
        t.i +
        '">' +
        escapeHtml(decodeURIComponent(name)) +
        '</button> <span class="rank">' +
        t.d.rank.toFixed(2) +
        "</span>"
      );
    });

  d3.selectAll("#toplist button").on("click", function () {
    var i = +this.getAttribute("data-i");
    highlight(i);
    setTimeout(clearHighlight, 1600);
  });

  d3.select("#btn-restart").on("click", function () {
    force.resume();
  });

  var frozen = false;
  d3.select("#btn-freeze").on("click", function () {
    frozen = !frozen;
    if (frozen) {
      force.stop();
      this.textContent = "Resume";
    } else {
      force.resume();
      this.textContent = "Freeze";
    }
  });
}

/* ---------- Responsive ---------- */
var resizeTimer;
window.addEventListener("resize", function () {
  clearTimeout(resizeTimer);
  resizeTimer = setTimeout(function () {
    var w = Math.max(container.clientWidth || 640, 320);
    if (Math.abs(w - width) < 40) return;
    width = w;
    height = Math.round(Math.min(Math.max(width * 0.68, 420), 720));
    svg.attr("viewBox", "0 0 " + width + " " + height);
    force.size([width, height]).resume();
  }, 200);
});

buildChrome();
loadData(spiderJson);
