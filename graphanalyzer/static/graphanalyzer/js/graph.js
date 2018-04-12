var self = this,

svg = d3.select("svg")
        /*.call(d3.zoom().on("zoom", function () {
                          svg.attr("transform", d3.event.transform)
                  }))*/,

width = +svg.attr("width"),

height = +svg.attr("height"),

radius = 6,

color = d3.scaleOrdinal(d3.schemeCategory20),

linkGroup = svg.append("g")
          .attr("class", "links"),

nodeGroup = svg.append("g")
          .attr("id", "container")
          .attr("class", "nodes")
          .attr("transform", "translate(0,0)scale(1,1)");;

/*var scale = 1.0;
var zoom = d3.zoom()
    .scaleExtent([1, 5])
    .on("zoom", zoomed);
var clickScale = 2.0;
var bbox, viewBox, vx, vy, vw, vh, defaultView;*/

function updateGraph() {
    d3.json("tweets.json", function(targetElement, graph) {
        if (targetElement) throw targetElement;

        svg.selectAll("line").remove();
        svg.selectAll("circle").remove();

        simulation = d3.forceSimulation()
                .force("link", d3.forceLink().id(function(d) { return d.id; }))
                .force("charge", d3.forceManyBody())
                .force("center", d3.forceCenter(width / 2, height / 2));

        update = function() {

            // Redefine and restart simulation
            simulation.nodes(graph.nodes)
                      .on("tick", ticked);

            simulation.force("link")
                      .links(graph.links);

            // Update links
            link = linkGroup
                .selectAll("line")
                .data(graph.links);

            // Enter links
            linkEnter = link
                .enter().append("line");

            link = linkEnter
                .merge(link);

            // Exit any old links
            link.exit().remove();

            // Update the nodes
            node = nodeGroup/*.append("g")
                .attr("id", "circles")*/
                .selectAll("g")
                .data(graph.nodes);

            // Enter any new nodes
            nodeEnter = node.enter().append("g")
                        .attr("class", "point")
                        .call(d3.drag()
                            .on("start", dragstarted)
                            .on("drag", dragged)
                            .on("end", dragended));


            node = nodeEnter.merge(node);

            node.html("");

            node.append("circle")
                        .attr("r", radius - .75)
                        .style("fill", function(d) { return color(d.group); })
                        .style("stroke", function(d) { return d3.rgb(color(d.group)).darker(); })
                        .on("click", showDetail);;

            node.append("text")
                .attr("dx", -20)
                //.attr("dy", ".35em")
                .text(function(d) { return d.n.name });


            // Exit any old nodes
            node.exit().remove();


            /*bbox = nodeEnter.node().getBBox();
            vx = bbox.x;		// container x co-ordinate
            vy = bbox.y;		// container y co-ordinate
            vw = bbox.width;	// container width
            vh = bbox.height;	// container height
            defaultView = "" + vx + " " + vy + " " + vw + " " + vh;
            svg
                .attr("viewBox", defaultView)
                .attr("preserveAspectRatio", "xMidYMid meet");*/


            function ticked() {
                link
                    .attr("x1", function(d) { return d.source.x; })
                    .attr("y1", function(d) { return d.source.y; })
                    .attr("x2", function(d) { return d.target.x; })
                    .attr("y2", function(d) { return d.target.y; });

                node.attr("transform", function(d) { return "translate(" + Math.max(radius, Math.min(width - radius, d.x)) + "," + Math.max(radius, Math.min(height - radius, d.y)) + ")"; });
            }
        },

        dragstarted = function(d) {
            if (!d3.event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
        },

        dragged = function(d) {
            d.fx = d3.event.x;
            d.fy = d3.event.y;
        },

        dragended = function(d) {
            if (!d3.event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
        },

        update();
    });
}
updateGraph();


function showDetail(d, i) {
    var tweetText;
    tweetText = "<h6 style=\"color:white;font-weight:bold\">" + d.n.name + "</h6>";
    tweetText = tweetText + "<h6 style=\"color:white\">" + "@" + d.n.username + "</h6>";
    tweetText = tweetText + "<h6 style=\"color:white\">" + d.n.tweet + "</h6>";
    tweetText = tweetText + "<img style=\"float: left;\" src=\"/static/graphanalyzer/images/location.png\"/ height=\"15\" width=\"15\">"
        +  "<h6 style=\"color:white;\">" + d.n.location + "</h6>";
    var tweetDate = new Date(d.n.time);
    var timestamp = new Date();
    var difference = (timestamp - tweetDate)/ 1000;
    var showingTime;
    if (difference <= 60) {
        showingTime = Math.round(difference) + "seg ago";
    } else if (difference <= 3600) {
        showingTime = Math.round(difference/60) + "min ago";
    } else if (difference <= 216000) {
        showingTime = Math.round(difference/3600) + "h ago";
    } else {
        showingTime = tweetDate.getDate() + ' ' + tweetDate.getMonth() + ' ' + tweetDate.getFullYear();
    }
    tweetText = tweetText + "<h6 style=\"color:white\">" + showingTime + "</h6>";
    document.getElementById("tweetDetail").innerHTML=tweetText;
    console.log(tweetText);
}


/*function clicked(d, i) {
  if (d3.event.defaultPrevented) {
    return; // panning, not clicking
  }
  node = d3.select(this);
  var transform = getTransform(node, clickScale);
  nodeEnter.transition().duration(1000)
     .attr("transform", "translate(" + transform.translate + ")scale(" + transform.scale + ")");
  zoom
      .translate(transform.translate);
  scale = transform.scale;
}

function getTransform(node, xScale) {
  bbox = node.node().getBBox();
  var bx = bbox.x;
  var by = bbox.y;
  var bw = bbox.width;
  var bh = bbox.height;
  var tx = -bx*xScale + vx + vw/2 - bw*xScale/2;
  var ty = -by*xScale + vy + vh/2 - bh*xScale/2;
  return {translate: [tx, ty], scale: xScale}
}

function zoomed() {
  var translateX = d3.event.translate[0];
  var translateY = d3.event.translate[1];
  var xScale = d3.event.scale;
  container.attr("transform", "translate(" + translateX + "," + translateY + ")scale(" + xScale + ")");
}

d3.select(self.frameElement).attr("margin", 10);*/