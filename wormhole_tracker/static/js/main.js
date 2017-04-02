// This file is part of wormhole-tracker package released under
// the GNU GPLv3 license. See the LICENSE file for more information.


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



$(document).ready(function() {
    if ("MozWebSocket" in window) {
        WebSocket = MozWebSocket;
    }
    if (WebSocket) {
        var ws = new WebSocket("ws://" + window.location.host + "/poll");

        var send = function(message) {
            ws.send(JSON.stringify(message))
        };

        ws.onopen = function() {
            console.warn("WS connection established");
        };
        ws.onmessage = function(evt) {
            //console.debug(evt.data);
            var message = $.parseJSON(evt.data);
            //console.log(data);
            var type = message[0],
                data = message[1];

            if (type === 'update') {
                warning();
                if (data) {
                    console.log(data);
                    redraw(data);
                }
            }
            else if (type === 'recover') {
                clear_svg();
                data = recover(data);
                draw(data);
                save_graph();
            }
            else if (type === 'warning') {
                warning(data);
            }
        };
        ws.onclose = function() {
            console.warn("WS connection closed");
            untrack();
        };

        function send_backup() {
            var backup = clone(star_systems);
            send(['backup', star_systems]);
        }

        setInterval(send_backup, 3000);


        // Button event handlers

        $('#track').on('click', (function() {
            send("track");
            track();
        }));
        $('#stop').on('click', (function() {
            send("stop");
            untrack();
        }));
        $('#reset').on('click', (function() {
            send("reset");
            untrack();
            track_reset();
        }));
    } else {
        alert("WebSocket not supported");
    }
});
