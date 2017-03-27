// This file is part of wormhole-tracker package released under
// the GNU GPLv3 license. See the LICENSE file for more information.


var width = 960,
    height = 500;

var color = d3.scale.category20();

var force = d3.layout.force()
    .charge(-120)
    .linkDistance(30)
    .size([width, height]);

var svg = d3.select("body").append("svg")
    .attr("width", width)
    .attr("height", height);

var currentSystem;
var starSystems = { nodes: [], links: [] };
var link, node;

function draw(graph) {
    console.warn(graph);
    force.nodes(graph.nodes)
         .links(graph.links)
         .start();
    link = svg.selectAll(".link")
        .data(graph.links)
      .enter().append("line")
        .attr("class", "link")
        .style("stroke-width", function(d) { return 4; });

    var drag = force.drag()
        .on("dragstart", dragstart);

    node = svg.selectAll(".node")
        .data(graph.nodes)
        .enter().append('g')
        .attr("class", "node")
        .call(drag);

    node.append("circle")
        .attr("r", 5)
        .style("fill", function(d) { return color(0); })

    node.append("text")
        .attr("dx", 12)
        .attr("dy", ".35em")
        .text(function(d) { return d.name; });


    force.on("tick", function() {
        link.attr("x1", function(d) { return d.source.x; })
            .attr("y1", function(d) { return d.source.y; })
            .attr("x2", function(d) { return d.target.x; })
            .attr("y2", function(d) { return d.target.y; });

        //node.attr("cx", function(d) { return d.x; })
        //    .attr("cy", function(d) { return d.y; });
        node.attr("transform", function(d) { return "translate(" + d.x + "," + d.y + ")"; });
    });

    function dragstart(d) {
        d.x = d3.event.x;
        d.y = d3.event.y;
        d3.select(this).classed("fixed", d.fixed = true);
    }
}

draw(starSystems); // Initial graph drawing

function bindLink(l) {
    for (var i in starSystems.nodes) {
        var n = starSystems.nodes[i];
        if (l.source == n.name) {
            l.source = n;
        }
        else if (l.target == n.name) {
            l.target = n;
        }
    }
}

function saveGraph() {
    starSystems.nodes = node.data();
    starSystems.links = link.data();
}

function reDraw(data) {
    saveGraph();
    if (data.node) starSystems.nodes.push(data.node);
    if (data.link) {
        bindLink(data.link);
        starSystems.links.push(data.link);
    }
    svg.selectAll("*").remove();
    draw(starSystems);
}

