var wkt_map = function () {
    "use strict";
    var features = [];
    var gmap = null;
    var clearMap = function () {
        var i;
        for (i in features) {
            if (features.hasOwnProperty(i)) {
                features[i].setMap(null);
            }
        }
        features.length = 0;
    };

    var mapIt = function () {
        var el, obj, wkt;
        el = 'MULTIPOLYGON (((40 40, 20 45, 45 30, 40 40)), ((20 35, 10 30, 10 10, 30 5, 45 20, 20 35), (30 20, 20 15, 20 25, 30 20)))';
        wkt = new Wkt.Wkt();

        // if (el.last === el.value) { // Remember the last string
        //     return; // Do nothing if the WKT string hasn't changed
        // } else {
        //     el.last = el.value;
        // }

        try { // Catch any malformed WKT strings
            wkt.read(el);
        } catch (e1) {
            try {
                wkt.read(el.replace('\n', '').replace('\r', '').replace('\t', ''));
            } catch (e2) {
                if (e2.name === 'WKTError') {
                    alert('Wicket could not understand the WKT string you entered. Check that you have parentheses balanced, and try removing tabs and newline characters.');
                    return;
                }
            }
        }


        // console.log(gmap.defaults);
        
        obj = wkt.toObject(gmap.defaults); // Make an object

        // Add listeners for overlay editing events
        if (!Wkt.isArray(obj) && wkt.type !== 'point') {
            // New vertex is inserted
            google.maps.event.addListener(obj.getPath(), 'insert_at', function (n) {
                app.updateText();
            });
            // Existing vertex is removed (insertion is undone)
            google.maps.event.addListener(obj.getPath(), 'remove_at', function (n) {
                app.updateText();
            });
            // Existing vertex is moved (set elsewhere)
            google.maps.event.addListener(obj.getPath(), 'set_at', function (n) {
                app.updateText();
            });
        } else {
            if (obj.setEditable) {obj.setEditable(false);}
        }

        var bounds = new google.maps.LatLngBounds();
        var i;
        if (Wkt.isArray(obj)) { // Distinguish multigeometries (Arrays) from objects
            for (i in obj) {
                if (obj.hasOwnProperty(i) && !Wkt.isArray(obj[i])) {
                    obj[i].setMap(gmap);
                    features.push(obj[i]);

                    if(wkt.type === 'point' || wkt.type === 'multipoint')
                        bounds.extend(obj[i].getPosition());
                    else
                        obj[i].getPath().forEach(function(element,index){bounds.extend(element)});
                }
            }

            features = features.concat(obj);
        } else {
            obj.setMap(gmap); // Add it to the map
            features.push(obj);

            if(wkt.type === 'point' || wkt.type === 'multipoint')
                bounds.extend(obj.getPosition());
            else
                obj.getPath().forEach(function(element,index){bounds.extend(element)});
        }

        // Pan the map to the feature
        gmap.fitBounds(bounds);

        return obj;
    };

    var init = function () {
        // var gmap;

        gmap = new google.maps.Map(document.getElementById('google-map-canvas'), {
            center: new google.maps.LatLng(30, 10),
            defaults: {
                icon: 'red_dot.png',
                shadow: 'dot_shadow.png',
                editable: true,
                strokeColor: '#990000',
                fillColor: '#EEFFCC',
                fillOpacity: 0.6
            },
            disableDefaultUI: true,
            mapTypeControl: true,
            mapTypeId: google.maps.MapTypeId.ROADMAP,
            mapTypeControlOptions: {
                position: google.maps.ControlPosition.TOP_LEFT,
                style: google.maps.MapTypeControlStyle.DROPDOWN_MENU
            },
            panControl: false,
            streetViewControl: false,
            zoom: 2,
            zoomControl: true,
            zoomControlOptions: {
                position: google.maps.ControlPosition.LEFT_TOP,
                style: google.maps.ZoomControlStyle.SMALL
            }
        });

        google.maps.event.addListener(gmap, 'tilesloaded', function () {
            if (!this.loaded) {
                this.loaded = true;
                // NOTE: We start with a MULTIPOLYGON; these aren't easily deconstructed, so we won't set this object to be editable in this example
                // document.getElementById('wkt').value = 'MULTIPOLYGON (((40 40, 20 45, 45 30, 40 40)), ((20 35, 10 30, 10 10, 30 5, 45 20, 20 35), (30 20, 20 15, 20 25, 30 20)))';
                // mapIt();
            }
        });

        gmap.drawingManager = new google.maps.drawing.DrawingManager({
            drawingControlOptions: {
                position: google.maps.ControlPosition.TOP_CENTER,
                drawingModes: [
                    google.maps.drawing.OverlayType.MARKER,
                    google.maps.drawing.OverlayType.POLYLINE,
                    google.maps.drawing.OverlayType.POLYGON,
                    google.maps.drawing.OverlayType.RECTANGLE
                ]
            },
            markerOptions: gmap.defaults,
            polygonOptions: gmap.defaults,
            polylineOptions: gmap.defaults,
            rectangleOptions: gmap.defaults
        });
        gmap.drawingManager.setMap(gmap);

        google.maps.event.addListener(gmap.drawingManager, 'overlaycomplete', function (event) {
            var wkt;

            clearText();
            clearMap();

            // Set the drawing mode to "pan" (the hand) so users can immediately edit
            this.setDrawingMode(null);

            // Polygon drawn
            if (event.type === google.maps.drawing.OverlayType.POLYGON || event.type === google.maps.drawing.OverlayType.POLYLINE) {
                // New vertex is inserted
                google.maps.event.addListener(event.overlay.getPath(), 'insert_at', function (n) {
                    app.updateText();
                });

                // Existing vertex is removed (insertion is undone)
                google.maps.event.addListener(event.overlay.getPath(), 'remove_at', function (n) {
                    app.updateText();
                });

                // Existing vertex is moved (set elsewhere)
                google.maps.event.addListener(event.overlay.getPath(), 'set_at', function (n) {
                    app.updateText();
                });
            } else if (event.type === google.maps.drawing.OverlayType.RECTANGLE) { // Rectangle drawn
                // Listen for the 'bounds_changed' event and update the geometry
                google.maps.event.addListener(event.overlay, 'bounds_changed', function () {
                    app.updateText();
                });
            }

            app.features.push(event.overlay);
            wkt = new Wkt.Wkt();
            wkt.fromObject(event.overlay);
            // document.getElementById('wkt').value = wkt.write();
            });
        // this.gmap = gmap;
        // return gmap;
    };

    var updateText = function () {
        var wkt = new Wkt.Wkt();
        wkt.fromObject(features[0]);
        document.getElementById('wkt').value = wkt.write();
    };
    var updateTextPart = function () {
        var i, w, v;

        w = new Wkt.Wkt(features[0]);

        i = 1;
        while (i < features.length) {
            v = new Wkt.Wkt(features[i]);
            w.merge(v);
            i += 1;
        }

        document.getElementById('wkt').value = w.write();
    };
    /**
     * Formats the textarea contents for a URL.
     * @param   checked {Boolean}   The check state of the associated checkbox
     */
    var urlify = function (checked) {
        var wkt = new Wkt.Wkt();
        wkt.read(document.getElementById('wkt').value);
        wkt.delimiter = (checked) ? '+' : ' ';
        document.getElementById('wkt').value = wkt.write();
        return wkt;
    };

    var wktCallback = function(data, status, jqXHR){
        var obj,wkt;
        // console.log(data);
        clearMap();
        data.results.bindings.forEach(function(e){
            if (e.wkt){
                wkt = new Wkt.Wkt();
                try { // Catch any malformed WKT strings
                    wkt.read(e.wkt.value);
                } catch (e1) {
                    try {
                        wkt.read(e.wkt.value.replace('\n', '').replace('\r', '').replace('\t', ''));
                    } catch (e2) {
                        if (e2.name === 'WKTError') {
                            alert('Wicket could not understand the WKT string you entered. Check that you have parentheses balanced, and try removing tabs and newline characters.');
                            return;
                        }
                    }
                }
                obj = wkt.toObject(gmap.defaults);
                if (obj.setEditable) {obj.setEditable(false);}

                var bounds = new google.maps.LatLngBounds();
                var i;
                if (Wkt.isArray(obj)) { // Distinguish multigeometries (Arrays) from objects
                    for (i in obj) {
                        if (obj.hasOwnProperty(i) && !Wkt.isArray(obj[i])) {
                            obj[i].setMap(gmap);
                            features.push(obj[i]);

                            if(wkt.type === 'point' || wkt.type === 'multipoint')
                                bounds.extend(obj[i].getPosition());
                            else
                                obj[i].getPath().forEach(function(element,index){bounds.extend(element)});
                        }
                    }

                    features = features.concat(obj);
                } else {
                    obj.setMap(gmap); // Add it to the map
                    features.push(obj);

                    if(wkt.type === 'point' || wkt.type === 'multipoint')
                        bounds.extend(obj.getPosition());
                    else
                        obj.getPath().forEach(function(element,index){bounds.extend(element)});
                }

                // Pan the map to the feature
                gmap.fitBounds(bounds);


            }
        });
    };


    return {
        gmap: gmap,
        clearMap: clearMap,
        mapIt: mapIt,
        init: init,
        wktCallback: wktCallback
    };
}();