// This file is part of wormhole-tracker package released under
// the GNU GPLv3 license. See the LICENSE file for more information.

var ForceLayout = function (svg, force) {
    /*
        Class represents state container for D3.js force layout.
        Arguments:
            svg:       Predefined and selected SVG container.
            force:     Predefined D3.js force layout object.

        Attributes:
            current:   Character's current location.
            nodes:     List with objects used for drawing D3.js nodes.
            links:     List with objects used for drawing D3.js links.

            svg_node:  D3.js node object. Replaces on every redraw.
            svg_link:  D3.js link object. Replaces on every redraw.
     */

    var self = this;

    self.svg       = svg;
    self.force     = force;

    self.current   = '';
    self.nodes     = [];
    self.links     = [];

    self.svg_link = self.svg.selectAll(".link");
    self.svg_node = self.svg.selectAll(".node");

    self.bind_links = function(links) {
        /*
            Bind links to existing nodes.

            Arguments:
                links: A list of links like this:
                    [{'source': {'name': 'Tama'}, 'target': {'name': 'Kedama'}]
         */
        for (var i in links) {
            var link = links[i];
            for (var n in self.nodes) {
                var node = self.nodes[n];
                if (link.source.name === node.name) {
                link.source = node;
                }
                else if (link.target.name === node.name) {
                    link.target = node;
                }
            }
        }
    };

    self.clear_svg = function () {
        self.svg.selectAll("*").remove();
    };

    self.draw = function () {
        console.log(self);

        self.force.nodes(self.nodes)
             .links(self.links)
             .start();

        self.svg_link = self.svg.selectAll(".link")
            .data(self.links)
          .enter().append("line")
            .attr("class", "link")
            .style("stroke-width", function(d) { return 4; });

        var drag = self.force.drag()
            .on("dragstart", function (d) {
                d.x = d3.event.x;
                d.y = d3.event.y;
                d3.select(this).classed("fixed", d.fixed = true);
            });

        self.svg_node = self.svg.selectAll(".node")
            .data(self.nodes)
            .enter().append('g')
            .attr("class", "node")
            .call(drag);

        self.svg_node.append("circle")
            .attr("r", 5)
            .style("fill", function(d) {
                if (d.name === self.current) {
                    return 'tomato';
                }
                return 'beige';
            });

        self.svg_node.append("text")
            .attr("dx", 12)
            .attr("dy", ".35em")
            .attr("fill", "aliceblue")
            .text(function (d) {
                if (d.name === self.current) {
                    return '[ ' + d.name + ' ]';
                }
                return d.name;
            });

        self.force.on("tick", function () {
            self.svg_link.attr("x1", function (d) { return d.source.x; })
                .attr("y1", function (d) { return d.source.y; })
                .attr("x2", function (d) { return d.target.x; })
                .attr("y2", function (d) { return d.target.y; });
            self.svg_node.attr("transform", function (d) {
                return "translate(" + d.x + "," + d.y + ")";
            });
        });
    };

    self.save = function () {
        self.nodes = self.svg_node.data();
        self.links = self.svg_link.data();
    };


    self.update = function (data) {
        if (data.current) {
            self.current = data.current;
        }
        if (data.nodes) {
            self.nodes = self.nodes.concat(data.nodes);
        }
        if (data.links) {
            self.bind_links(data.links);
            self.links = self.links.concat(data.links);
        }
        self.clear_svg();
        self.draw();
        self.save();
    };

    /*
    self.redraw = function () {
        self.clear_svg();
        self.draw();
        self.save();
    };
    */

    self.backup = function () {
        self.save();
        return {
            'current': self.current,
            'nodes'  : self.nodes,
            'links'  : self.links
        }
    };

    self.clear = function () {
        self.current = '';
        self.nodes   = [];
        self.links   = [];
    };

    self.reset = function () {
        self.clear();
        self.clear_svg();
    }

};


var width  = document.body.clientWidth,
    height = document.body.clientHeight;

//var color = d3.scale.category20();

var force = d3.layout.force()
    .charge(-120)
    .linkDistance(30)
    .size([width, height]);

var svg = d3.select("#path")
    .append("svg")
    .attr("width", width)
    .attr("height", height);

var graph = new ForceLayout(svg, force);



