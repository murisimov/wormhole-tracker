// This file is part of wormhole-tracker package released under
// the GNU GPLv3 license. See the LICENSE file for more information.


var width = 960,
    height = 500;

var color = d3.scale.category20();

var force = d3.layout.force()
    .charge(-120)
    .linkDistance(30)
    .size([width, height]);

var svg = d3.select("#path").append("svg")
    .attr("width", width)
    .attr("height", height);

var current_system;
var star_systems = { nodes: [], links: [] };
var link, node;

function draw(graph) {
    console.log(graph);
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
        .style("fill", function(d) { return color(0); });

    node.append("text")
        .attr("dx", 12)
        .attr("dy", ".35em")
        .text(function(d) { return d.name; });

    force.on("tick", function() {
        link.attr("x1", function(d) { return d.source.x; })
            .attr("y1", function(d) { return d.source.y; })
            .attr("x2", function(d) { return d.target.x; })
            .attr("y2", function(d) { return d.target.y; });
        node.attr("transform", function(d) {
            return "translate(" + d.x + "," + d.y + ")";
        });
    });

    function dragstart(d) {
        d.x = d3.event.x;
        d.y = d3.event.y;
        d3.select(this).classed("fixed", d.fixed = true);
    }
}

draw(star_systems); // Initial graph drawing

function clear_svg() {
    svg.selectAll("*").remove();
}

function clear_path() {
    star_systems.nodes = [];
    star_systems.links = [];
}

function track_reset() {
    clear_svg();
    clear_path();
    console.warn("Tracking reset");
}

function bind_link(l) {
    for (var i in star_systems.nodes) {
        var n = star_systems.nodes[i];
        if (l.source == n.name) {
            l.source = n;
        }
        else if (l.target == n.name) {
            l.target = n;
        }
    }
}

function save_graph() {
    star_systems.nodes = node.data();
    star_systems.links = link.data();
}

function redraw(data) {
    // Redraw only if we got at least something
    if (data.node || data.link) {
        if (data.node) {
            star_systems.nodes.push(data.node);
        }
        if (data.link) {
            bind_link(data.link);
            star_systems.links.push(data.link);
        }
        clear_svg();
        draw(star_systems);
        save_graph();
    }
}

