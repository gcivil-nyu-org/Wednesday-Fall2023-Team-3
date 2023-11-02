
async function initMap() {
    map = new google.maps.Map(document.getElementById("map"), {
      center: { lat: 40.71159438471519, lng: -73.97424027294727 },
      zoom: 11,
      mapId: '9a7e26117f10196d'
    });
        const responseEvent = await fetch('../get_data/');
        const responseLocation = await fetch('../get_locations/');
        const event_data = await responseEvent.json();
        const location_objects = await responseLocation.json();
        const location_data = event_data.location_data;
        const locations = location_objects.locations;
        const locationmap = new Map();
        for(let i =0; i<locations.length;i++){
            locationmap.set(locations[i].pk,[locations[i].fields.latitude,locations[i].fields.longitude])
        }
        for(let i =0; i<location_data.length;i++){
            
            if(location_data[i].fields.is_active == true){
                let lat = -1, lng = -1;
                if(locationmap.get(location_data[i].fields.event_location)!=null){
                    lat = locationmap.get(location_data[i].fields.event_location)[0];
                    lng = locationmap.get(location_data[i].fields.event_location)[1];
                }
            const marker = new google.maps.Marker({
                position: {lat: lat, lng:lng},
                map,
                title: location_data[i].fields.event_name,
                icon: {
                    url: "https://upload.wikimedia.org/wikipedia/commons/e/ed/Map_pin_icon.svg",
                    scaledSize: new google.maps.Size(25,30)
                },
                animation: google.maps.Animation.DROP
              });
              
              marker.addListener("click", () => {
                dynamicUrl = `http://127.0.0.1:8000/events/${location_data[i].pk}/`;
                window.location.href = dynamicUrl;
              });  
            }
    }
    
  }

//   40.71159438471519, -73.97424027294727
// 40.62285306937179, -74.00230260474844