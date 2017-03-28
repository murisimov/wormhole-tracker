// This file is part of wormhole-tracker package released under
// the GNU GPLv3 license. See the LICENSE file for more information.


/* Type stuff */

function typeOf(value) {
    var s = typeof value;
    if (s === 'object') {
        if (value) {
            if (Object.prototype.toString.call(value) == '[object Array]') {
                s = 'array';
            }
        } else {
            s = 'null';
        }
    }
    return s;
}

function int(number) {
    return parseInt(number);
}

function float(number) {
    return parseFloat(number);
}

function str(value) {
    return String(value);
}

/* Arrays stuff */

function remove(array, element) {
    var i = array.indexOf(element);
    if (i != -1) array.splice(i, 1);
    return i;
}

function range(num) {
    var result = [];
    for (var i=0; i < Math.ceil(num); i++) {
        result.push(i);
    }
    return result;
}

/* Objects stuff */

function clone(obj) {
    return jQuery.extend(true, {}, obj);
}

function merge(source, obj) {
    jQuery.extend(true, source, obj);
}

