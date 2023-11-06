async function initMap() {
    map = new google.maps.Map(document.getElementById("map"), {
      center: { lat: 40.71159438471519, lng: -73.97424027294727 },
      zoom: 12,
      mapId: '9a7e26117f10196d'
    });
        const responseEvent = await fetch('events/');
        const responseLocation = await fetch('locations/');
        const event_data = await responseEvent.json();
        const location_objects = await responseLocation.json();
        const location_data = event_data.location_data;
        const locations = location_objects.locations;
        const locationmap = new Map();
        for(let i =0; i<locations.length;i++){
            locationmap.set(locations[i].pk,[locations[i].fields.latitude,locations[i].fields.longitude])
        }
        let duplicateLocationsMap = {};
        for(let i=0; i<location_data.length;i++){
            let loc = location_data[i].fields;
            if(!duplicateLocationsMap[loc.event_location]){
                    duplicateLocationsMap[loc.event_location] = [];
                }
                duplicateLocationsMap[loc.event_location].push({name:loc.event_name,id:event_data.location_data[i].pk});
        }
        for(let i =0; i<location_data.length;i++){
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
                    url: "https://www.svgviewer.dev/static-svgs/490211/marker.svg",
                    scaledSize: new google.maps.Size(30,35)
                },
                animation: google.maps.Animation.DROP
              });
              const popupContent = document.createElement('div');
            const locEvents = duplicateLocationsMap[location_data[i].fields.event_location];
            locEvents.forEach((locEvent) => { 
                var eventNameDiv = document.createElement('div');
                eventNameDiv.className = "eventnameDiv";
                eventNameDiv.addEventListener("click", function(e){
                    window.location.href += `${locEvent.id}`;
                });
                eventNameDiv.innerHTML = `${locEvent.name}`+"\n";
                
                popupContent.appendChild(eventNameDiv);
                
            }); 
              
            const infoWindow = new google.maps.InfoWindow({
            content: popupContent,
            });
                
              marker.addListener("click", () => {
                infoWindow.open(map, marker);
              }); 
    }
    
  }

 