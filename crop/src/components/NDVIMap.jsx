import React, { useState } from 'react';
import axios from 'axios';
import L from 'leaflet';
import { MapContainer, TileLayer, useMap, Popup, FeatureGroup } from 'react-leaflet';
import { EditControl } from 'react-leaflet-draw';
import 'leaflet/dist/leaflet.css';
import 'leaflet-draw/dist/leaflet.draw.css';
import backgroundVideo from '../assets/backgroundVideo.mp4';
import { Line } from 'react-chartjs-2';
// import { useMap } from 'react-leaflet';
import {
  Chart as ChartJS,
  LineElement,
  PointElement,
  LinearScale,
  Title,
  Tooltip,
  Legend,
  CategoryScale,
} from 'chart.js';

// Register the components
ChartJS.register(LineElement, PointElement, LinearScale, Title, Tooltip, Legend, CategoryScale);


function NDVIMap() {
  const [place, setPlace] = useState('');
  const [coordinates, setCoordinates] = useState({ lonMin: '', latMin: '', lonMax: '', latMax: '' });
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [tileUrl, setTileUrl] = useState(null);
  const [legend, setLegend] = useState(null);
  const [ndviValue, setNdviValue] = useState(null);
  const [popupPosition, setPopupPosition] = useState(null);
  const [selectedArea, setSelectedArea] = useState(null);
  const [showDateModal, setShowDateModal] = useState(false);
  // const map = useMap();
  const [ndviData, setNdviData] = useState({});


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
      const response = await axios.post('http://127.0.0.1:5000/get-ndvi', {
        coordinates: [coordinates.lonMin, coordinates.latMin, coordinates.lonMax, coordinates.latMax],
        start_date: startDate,
        end_date: endDate,
      });

      setTileUrl(response.data.tile_url);
      setLegend(response.data.legend);
    } catch (error) {
      console.error('Error fetching NDVI data:', error);
    }
  };

  const handleMapClick = async (event) => {
    const { lat, lng } = event.latlng;
    try {
      const response = await axios.post('http://127.0.0.1:5000/get-ndvi-value', {
        latitude: lat,
        longitude: lng,
        start_date: startDate,
        end_date: endDate,
      });
      setNdviValue(response.data.ndvi_value);
      setPopupPosition({ lat, lng });
    } catch (error) {
      console.error('Error fetching NDVI value:', error);
    }
  };

  const handlePolygonCreate = (e) => {
    const layer = e.layer;

    // Check if the created layer is a polygon and handle it
    if (layer instanceof L.Polygon || layer instanceof L.Polyline) {
      const latLngs = layer.getLatLngs()[0].map(latLng => [latLng.lat, latLng.lng]);
      console.log('Selected Area Coordinates (Polygon):', latLngs);
      setSelectedArea(latLngs);
      setShowDateModal(true);
    }
    // Check if it's a marker or circle marker and handle it
    else if (layer instanceof L.Marker || layer instanceof L.CircleMarker) {
      const latLng = layer.getLatLng();
      console.log('Selected Location Coordinates (Marker/CircleMarker):', [latLng.lat, latLng.lng]);
      setSelectedArea([[latLng.lat, latLng.lng]]); // You can modify this based on how you want to store the data
      setShowDateModal(true);
    } else {
      console.error("Unrecognized layer type.");
    }
  };


  const handleDateSubmit = async () => {
    if (!startDate || !endDate) {
      alert('Please select both start and end dates.');
      return;
    }
    setShowDateModal(false);

    const confirmView = window.confirm('Do you want to view NDVI for the selected area?');
    if (confirmView) {

      const coordinates = selectedArea.map(([lat, lng]) => [lng, lat]);
      console.log('Sending coordinates:', coordinates);

      try {
        const response = await axios.post('http://127.0.0.1:5000/get-ndvi-for-area', {
          coordinates: coordinates,
          start_date: startDate,
          end_date: endDate,
        });

        if (response.data.tile_url) {
          setTileUrl(response.data.tile_url);
          setLegend(response.data.legend);
        } else {
          alert('No NDVI data available for the selected area and date range.');
        }
      } catch (error) {
        console.error('Error fetching NDVI data for area:', error);
        alert('There was an error fetching NDVI data. Please try again later.');
      }
    }
  };
  const fetchNDVIForYearRange = async () => {
    if (!startDate || !endDate) {
      alert('Please select both start and end dates.');
      return;
    }

    const coordinates = selectedArea.map(([lat, lng]) => [lng, lat]);
    console.log('Sending coordinates for year range:', coordinates);

    try {
      const response = await axios.post('http://127.0.0.1:5000/get-ndvi-for-year-range', {
        coordinates: coordinates,
        start_date: startDate,
        end_date: endDate,
      });

      console.log('NDVI Data Response:', response.data);
      if (response.data.ndvi_data) {
        setNdviData(response.data.ndvi_data);
      } else {
        alert('No NDVI data available for the selected area and date range.');
      }
    } catch (error) {
      console.error('Error fetching NDVI data for year range:', error);
      alert('There was an error fetching NDVI data. Please try again later.');
    }
  };


  const chartData = {
    labels: Object.keys(ndviData), // Years
    datasets: [
      {
        label: 'Mean NDVI',
        data: Object.values(ndviData), // NDVI values
        borderColor: 'rgba(75, 192, 192, 1)', // Solid color for the line
        backgroundColor: 'rgba(75, 192, 192, 0.5)', // Adjust opacity here (0.5 is semi-transparent)
        borderWidth: 1,
      },
    ],
  };

  
  console.log('NDVI Data:', ndviData);
  console.log('Chart Data:', chartData); // Log the chart data

  function NDVILayer() {
    const map = useMap();
    if (tileUrl) {
      const ndviLayer = L.tileLayer(tileUrl, {
        attribution: 'Google Earth Engine',
      });
      ndviLayer.addTo(map);
      map.on('click', handleMapClick);
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
      <video autoPlay loop muted className="absolute inset-0 w-full h-full object-cover">
        <source src={backgroundVideo} type="video/mp4" />
        Your browser does not support the video tag.
      </video>

      <div className="relative z-10 p-6 max-w-4xl mx-auto bg-s late-200/20 shadow-md rounded-lg">
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
        {showDateModal && (
          <div className="fixed inset-0 bg-gray-600/50 flex justify-center items-center z-50">
            <div className="bg-white p-6 rounded-lg shadow-lg w-96 z-50">
              <h3 className="text-xl font-semibold">Select Date Range</h3>
              <div className="space-y-4 mt-4">
                <div className="flex flex-col">
                  <label className="font-semibold">Start Date:</label>
                  <input
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    className="p-2 border border-gray-300 rounded-lg"
                  />
                </div>
                <div className="flex flex-col">
                  <label className="font-semibold">End Date:</label>
                  <input
                    type="date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    className="p-2 border border-gray-300 rounded-lg"
                  />
                </div>
              </div>
              <div className="mt-4 flex justify-between">
                <button
                  onClick={handleDateSubmit}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg"
                >
                  Submit
                </button>
                <button onClick={fetchNDVIForYearRange}>Fetch NDVI for Year Range</button>
                <button
                  onClick={() => setShowDateModal(false)}
                  className="px-4 py-2 bg-gray-300 text-gray-700 rounded-lg"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}

        <MapContainer center={[-1.0, 37.0]} zoom={10} style={{ height: '500px', width: '100%', zIndex: 1 }} className="mt-6">
          <TileLayer
            url="https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}"
            attribution="&copy; Google Maps"
          />
          <FeatureGroup>
            <EditControl position="topright" onCreated={handlePolygonCreate} draw={{
              polyline: false,
              polygon: true,
              rectangle: false,
              circle: false,
              marker: false,
            }} />
          </FeatureGroup>
          <ZoomToArea />
          {tileUrl && <NDVILayer />}
          {popupPosition && ndviValue && (
            <Popup
              position={popupPosition}
              onClose={() => {
                setPopupPosition(null);
                setNdviValue(null);
              }}
            >
              NDVI value at this location: <strong>{ndviValue}</strong>
            </Popup>
          )}
        </MapContainer>
        {Object.keys(ndviData).length > 0 && (
          <div style={{ width: '100%', height: '400px', backgroundColor: 'white', padding: '10px', borderRadius: '5px', boxShadow: '0 2px 10px rgba(0, 0, 0, 0.1)' }}>
          <h2>NDVI Over Time</h2>
          <Line data={chartData} options={{
            scales: {
              y: {
                beginAtZero: true,
                title: {
                  display: true,
                  text: 'NDVI',
                },
              },
              x: {
                title: {
                  display: true,
                  text: 'Year',
                },
              },
            },
          }} />
        </div>
        )}
      </div>

    </div>
  );
}

export default NDVIMap;
