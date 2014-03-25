var map;
$(document).ready(function(){
  map = new GMaps({
    el: '#map',
    lat: {{ plattrs[0][8] }},
    lng: {{ plattrs[0][9] }},
    zoom: 4,
    zoomControl : true,
    zoomControlOpt: {
        style : 'SMALL',
        position: 'TOP_LEFT'
    },
    panControl : false,
    streetViewControl : false,
    mapTypeControl: false,
    overviewMapControl: false
  });
  map.addMarker({
  lat: {{ plattrs[0][8] }},
  lng: {{ plattrs[0][9] }},
  title: "{{ title }}"
  });
});