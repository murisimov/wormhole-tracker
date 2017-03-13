function track() {
    $('#status').html('Tracking enabled');
    $('#status').removeClass('btn-warning');
    $('#status').addClass('btn-success');
}

function untrack() {
    $('#status').html('Tracking disabled');
    $('#status').removeClass('btn-success');
    $('#status').addClass('btn-warning');
    warning();
}

function warning(text) {
    if (text) {
        $('#warning').html(
            '<a class="btn btn-warning">' +
              text +
            '</a>'
        );
    }
    else {
        $('#warning').html('');
    }
}

$(document).ready(function() {
    if ("MozWebSocket" in window) {
        WebSocket = MozWebSocket;
    }
    if (WebSocket) {
        var ws = new WebSocket("ws://" + window.location.host + "/poll");
        var send = function(message) {
            ws.send(JSON.stringify(message))
        }
        ws.onopen = function() {
            console.warn("WS connection established");
        };
        ws.onmessage = function(evt) {
            //console.debug(evt.data);
            var message = $.parseJSON(evt.data);
            //console.log(data);
            var type = message[0],
                data = message[1];

            if (type === 'treant') {
                warning();

                //$('#tree-simple').height($(window).height());
                var chart_config = {
                    chart: {
                        container: "#tree-simple"
                    },
                    nodeStructure: data,
                }
                var chart = new Treant(chart_config, function() {}, $);
            }
            else if (type === 'warning') {
                warning(data);
            }
        }
        ws.onclose = function() {
            console.warn("WS connection closed");
            untrack();
        };

        $('#track').on('click', (function() {
            send("track");
            track();
        }));
        $('#stop').on('click', (function() {
            send("stop");
            untrack();
        }));
    } else {
        alert("WebSocket not supported");
    }
});
