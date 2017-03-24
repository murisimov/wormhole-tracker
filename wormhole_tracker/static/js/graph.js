



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

draw(data);

var link, node;
function draw(graph) {
    force.nodes(d3.values(graph.nodes))
         .links(graph.links)
         .start();
    link = svg.selectAll(".link")
        .data(graph.links)
      .enter().append("line")
        .attr("class", "link")
        .style("stroke-width", function(d) { return Math.sqrt(d.value); });

    var drag = force.drag()
        .on("dragstart", dragstart);

    node = svg.selectAll(".node")
        .data(d3.values(graph.nodes))
      .enter().append("circle")
        .attr("class", "node")
        .attr("r", 5)
        .style("fill", function(d) { return color(0); })
        .call(drag);

    node.append("title")
        .text(function(d) { return d.name; });

    force.on("tick", function() {
        link.attr("x1", function(d) { return d.source.x; })
            .attr("y1", function(d) { return d.source.y; })
            .attr("x2", function(d) { return d.target.x; })
            .attr("y2", function(d) { return d.target.y; });

        node.attr("cx", function(d) { return d.x; })
            .attr("cy", function(d) { return d.y; });
    });

    function dragstart(d) {
        d.x = d3.event.x;
        d.y = d3.event.y;
        d3.select(this).classed("fixed", d.fixed = true);
    }
}
var savedGraph = { nodes: {}, links: [] };
d3.select("#saveBtn").on('click',function() {
    savedGraph.nodes = node.data();
    savedGraph.links = link.data();
    svg.selectAll("*").remove();
});
d3.select("#loadBtn").on('click',function(){
    console.log(savedGraph);
    draw(savedGraph);
});
d3.select("#addBtn").on('click',function(){
    savedGraph.nodes['Dodixie'] = {name: 'Dodixie', fixed: 2};
    //savedGraph.links.push({})
    svg.selectAll("*").remove();
    draw(savedGraph);
});
