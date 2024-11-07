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

  return (
    <div>
      <form onSubmit={handleSubmit}>
        <div>
          <label>Place Name:</label>
          <input type="text" value={place} onChange={(e) => setPlace(e.target.value)} required />
          <button type="button" onClick={getCoordinatesFromPlace}>Get Coordinates</button>
        </div>
        <div>
          <label>Lon Min:</label>
          <input type="text" value={coordinates.lonMin} readOnly />
        </div>
        <div>
          <label>Lat Min:</label>
          <input type="text" value={coordinates.latMin} readOnly />
        </div>
        <div>
          <label>Lon Max:</label>
          <input type="text" value={coordinates.lonMax} readOnly />
        </div>
        <div>
          <label>Lat Max:</label>
          <input type="text" value={coordinates.latMax} readOnly />
        </div>
        <div>
          <label>Start Date:</label>
          <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} required />
        </div>
        <div>
          <label>End Date:</label>
          <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} required />
        </div>
        <button type="submit">Get NDVI Data</button>
      </form>

      <MapContainer center={[-1.0, 37.0]} zoom={10} style={{ height: '500px', width: '100%' }}>
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution="&copy; OpenStreetMap contributors"
        />
        {tileUrl && <NDVILayer />}
      </MapContainer>
    </div>
  );
}

export default NDVIMap;
