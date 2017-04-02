// This file is part of wormhole-tracker package released under
// the GNU GPLv3 license. See the LICENSE file for more information.


var width  = document.getElementById('route_container').clientWidth,
    height = document.getElementById('route_container').clientHeight;

//var color = d3.scale.category20();

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
    if (graph.current) current_system = graph.current;

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
        .style("fill", function(d) {
            if (d.name === current_system) {
                return 'tomato';
            }
            return 'beige';
        });

    node.append("text")
        .attr("dx", 12)
        .attr("dy", ".35em")
        .attr("fill", "aliceblue")
        .text(function(d) {
            if (d.name === current_system) {
                return '[ ' + d.name + ' ]';
            }
            return d.name;
        });

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

//draw(star_systems); // Initial graph drawing

function clear_svg() {
    svg.selectAll("*").remove();
}

function clear_path() {
    star_systems.current = '';
    star_systems.nodes = [];
    star_systems.links = [];
}

function track_reset() {
    clear_svg();
    clear_path();
    console.warn("Tracking reset");
}

function bind_link(data, l) {
    for (var i in data.nodes) {
        var n = data.nodes[i];
        if (l.source === n.name) {
            l.source = n;
        }
        else if (l.target === n.name) {
            l.target = n;
        }
    }
}

function save_graph() {
    star_systems.current = current_system;
    star_systems.nodes   = node.data();
    star_systems.links   = link.data();
}

function redraw(data) {
    // Redraw only if we got at least something
    if (data.node || data.link || data.current) {
        if (data.current) {
            star_systems.current = data.current;
        }
        if (data.node) {
            star_systems.nodes.push(data.node);
        }
        if (data.link) {
            bind_link(star_systems, data.link);
            star_systems.links.push(data.link);
        }
        clear_svg();
        draw(star_systems);
        save_graph();
    }
}

function recover(data) {
    for (var l in data.links) {
        for (var n in data.nodes) {
            var _link = data.links[l],
                _node = data.nodes[n];
            if (_link.source.name === _node.name) {
                _link.source = _node;
            }
            else if (_link.target.name === _node.name) {
                _link.target = _node;
            }
        }
    }
    return data;
}

