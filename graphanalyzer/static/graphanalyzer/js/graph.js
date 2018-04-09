var self = this,

svg = d3.select("svg")
        .call(d3.zoom().on("zoom", function () {
                          svg.attr("transform", d3.event.transform)
                  })),

width = +svg.attr("width"),

height = +svg.attr("height"),

radius = 6,

color = d3.scaleOrdinal(d3.schemeCategory20),

linkGroup = svg.append("g")
          .attr("class", "links"),

nodeGroup = svg.append("g")
          .attr("class", "nodes");

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
            node = nodeGroup
                .selectAll("g")
                .data(graph.nodes);

            // Enter any new nodes
            nodeEnter = node.enter().append("g")
                       .call(d3.drag()
                            .on("start", dragstarted)
                            .on("drag", dragged)
                            .on("end", dragended));



            node = nodeEnter.merge(node);

            node.append("image")
                  .attr("xlink:href", "https://twitter.com/favicon.ico")
                  .attr("width", 16)
                  .attr("height", 16);

            node.append("text")
                .attr("dx", 12)
                .attr("dy", ".35em")
                .text(function(d) { return d.n.name });


            // Exit any old nodes
            node.exit().remove();


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