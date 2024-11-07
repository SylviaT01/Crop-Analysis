import React, { useState } from 'react';
import axios from 'axios';
import L from 'leaflet';
import { MapContainer, TileLayer, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

function NDVIMap() {
  const [place, setPlace] = useState('');
  const [coordinates, setCoordinates] = useState({ lonMin: '', latMin: '', lonMax: '', latMax: '' });
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [tileUrl, setTileUrl] = useState(null);
  const [legend, setLegend] = useState(null);

  // Geocoding function to get coordinates from place name
  const getCoordinatesFromPlace = async () => {
    try {
      const geocodeResponse = await axios.get(
        `https://nominatim.openstreetmap.org/search?q=${place}&format=json&polygon_geojson=1`
      );
      if (geocodeResponse.data.length > 0) {
        const { boundingbox } = geocodeResponse.data[0];
        setCoordinates({
          latMin: parseFloat(boundingbox[0]),
          latMax: parseFloat(boundingbox[1]),
          lonMin: parseFloat(boundingbox[2]),
          lonMax: parseFloat(boundingbox[3]),
        });
      } else {
        alert('Place not found.');
      }
    } catch (error) {
      console.error('Error in geocoding:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    try {
      // Send a POST request to the backend
      const response = await axios.post('http://127.0.0.1:5000/get-ndvi', {
        coordinates: [coordinates.lonMin, coordinates.latMin, coordinates.lonMax, coordinates.latMax],
        start_date: startDate,
        end_date: endDate,
      });

      // Set the NDVI tile URL from the response
      setTileUrl(response.data.tile_url);
      setLegend(response.data.legend);
    } catch (error) {
      console.error('Error fetching NDVI data:', error);
    }
  };

  // Custom component for adding NDVI layer to the map when `tileUrl` changes
  function NDVILayer() {
    const map = useMap();

    if (tileUrl) {
      const ndviLayer = L.tileLayer(tileUrl, {
        attribution: 'Google Earth Engine',
      });
      ndviLayer.addTo(map);
      return () => map.removeLayer(ndviLayer);
    }
    return null;
  }

  function ZoomToArea() {
    const map = useMap();

    if (coordinates.lonMin && coordinates.latMin && coordinates.lonMax && coordinates.latMax) {
      const bounds = [
        [coordinates.latMin, coordinates.lonMin],
        [coordinates.latMax, coordinates.lonMax],
      ];
      map.fitBounds(bounds);
    }

    return null;
  }

  return (
    <div className="relative">
      <video
        autoPlay
        loop
        muted
        className="absolute inset-0 w-full h-full object-cover"
      >
        <source src="https://videocdn.cdnpk.net/videos/40acdff1-c51b-4d55-b13a-68950ef91166/horizontal/previews/clear/large.mp4?token=exp=1731018023~hmac=89c2ffbdfdd39a92693c514b0c812c0c2ab2a284b5300ddef2b62360a1180a4d" type="video/mp4" />
        Your browser does not support the video tag.
      </video>

      {/* Form and Map content */}
      <div className="relative z-10 p-6 max-w-4xl mx-auto bg-slate-200/20 shadow-md rounded-lg">
        <form onSubmit={handleSubmit} className="space-y-4 mb-10">
          <div className="flex flex-col">
            <label className="text-white/70 font-semibold">Place Name:</label>
            <input
              type="text"
              value={place}
              onChange={(e) => setPlace(e.target.value)}
              required
              className="p-2 border border-gray-300 rounded-lg"
            />
            <button
              type="button"
              onClick={getCoordinatesFromPlace}
              className="mt-2 p-2 bg-blue-600/50 text-white rounded-lg hover:bg-blue-700/50 transition duration-300"
            >
              Get Coordinates
            </button>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="flex flex-col">
              <label className="text-white/70 font-semibold">Lon Min:</label>
              <input
                type="text"
                value={coordinates.lonMin}
                readOnly
                className="p-2 border border-gray-300 rounded-lg bg-gray-100"
              />
            </div>
            <div className="flex flex-col">
              <label className="text-white/70 font-semibold">Lat Min:</label>
              <input
                type="text"
                value={coordinates.latMin}
                readOnly
                className="p-2 border border-gray-300 rounded-lg bg-gray-100"
              />
            </div>
            <div className="flex flex-col">
              <label className="text-white/70 font-semibold">Lon Max:</label>
              <input
                type="text"
                value={coordinates.lonMax}
                readOnly
                className="p-2 border border-gray-300 rounded-lg bg-gray-100"
              />
            </div>
            <div className="flex flex-col">
              <label className="text-white/70 font-semibold">Lat Max:</label>
              <input
                type="text"
                value={coordinates.latMax}
                readOnly
                className="p-2 border border-gray-300 rounded-lg bg-gray-100"
              />
            </div>
          </div>

          <h1 className="text-sm font-bold text-white/70 mb-6">Please select the date range:</h1>
          <div className="grid grid-cols-2 gap-4">
            <div className="flex flex-col">
              <label className="text-white/70 font-semibold">Start Date:</label>
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                required
                className="p-2 border border-gray-300 rounded-lg"
              />
            </div>
            <div className="flex flex-col">
              <label className="text-white/70 font-semibold">End Date:</label>
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                required
                className="p-2 border border-gray-300 rounded-lg"
              />
            </div>
          </div>

          <button
            type="submit"
            className="w-full mt-4 p-3 bg-green-600/50 text-white rounded-lg hover:bg-green-700/50 transition duration-300"
          >
            Get NDVI Data
          </button>
        </form>

        {legend && (
          <div className="mt-6 p-4 bg-gray-100 rounded-lg shadow-md">
            <h3 className="text-xl font-semibold">NDVI Legend</h3>
            <ul className="space-y-2 mt-4">
              {Object.entries(legend).map(([color, description]) => (
                <li key={color} className="flex items-center space-x-2">
                  <span
                    className="w-4 h-4 inline-block"
                    style={{ backgroundColor: color.toLowerCase() }}
                  ></span>
                  <span className="text-gray-700">{description}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
        <MapContainer center={[-1.0, 37.0]} zoom={10} style={{ height: '500px', width: '100%' }} className="mt-6">
          <TileLayer
            url="https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}"
            attribution="&copy; OpenStreetMap contributors"
          />
          <ZoomToArea />
          {tileUrl && <NDVILayer />}
        </MapContainer>
      </div>
    </div>
  );
}

export default NDVIMap;
