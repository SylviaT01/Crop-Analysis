import React, { useState } from 'react';
import axios from 'axios';
import L from 'leaflet';
import { MapContainer, TileLayer, useMap, Popup, FeatureGroup } from 'react-leaflet';
import { EditControl } from 'react-leaflet-draw';
import 'leaflet/dist/leaflet.css';
import 'leaflet-draw/dist/leaflet.draw.css';
import backgroundVideo from '../assets/backgroundVideo.mp4';
import { IoMdHome } from "react-icons/io";
import { Line } from 'react-chartjs-2';
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
  const [ndviTileUrl, setNdviTileUrl] = useState(null);
  const [eviTileUrl, setEviTileUrl] = useState(null);
  const [ndwiTileUrl, setNdwiTileUrl] = useState(null);
  const [mndwiTileUrl, setMndwiTileUrl] = useState(null);
  const [legend, setLegend] = useState(null);
  const [ndviValue, setNdviValue] = useState(null);
  const [popupPosition, setPopupPosition] = useState(null);
  const [selectedArea, setSelectedArea] = useState(null);
  const [showDateModal, setShowDateModal] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(null);
  const [ndviData, setNdviData] = useState({});
  const [indexType, setIndexType] = useState('NDVI');

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
      const response = await axios.post('https://backend-crop-analysis-1.onrender.com/get-ndvi', {
        coordinates: [coordinates.lonMin, coordinates.latMin, coordinates.lonMax, coordinates.latMax],
        start_date: startDate,
        end_date: endDate,
        index: indexType,  // Include index type in request
      });

      setTileUrl(response.data.tile_url);
      setLegend(response.data.legend);
    } catch (error) {
      console.error('Error fetching vegetation index data:', error);
    }
  };


  const handleMapClick = async (event) => {
    const { lat, lng } = event.latlng;
    try {
      const response = await axios.post('https://backend-crop-analysis-1.onrender.com/get-ndvi-value', {
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

    const confirmView = window.confirm('Do you want to view the indices for the selected area?');
    if (confirmView) {
      const coordinates = selectedArea.map(([lat, lng]) => [lng, lat]);
      console.log('Sending coordinates:', coordinates);

      try {
        const response = await axios.post('https://backend-crop-analysis-1.onrender.com/get-ndvi-for-area', {
          coordinates: coordinates,
          start_date: startDate,
          end_date: endDate,
          index: selectedIndex,  // Pass selectedIndex here
        });

        if (response.data) {
          // Set the tile URL based on the selected index
          if (selectedIndex === 'NDVI') {
            setNdviTileUrl(response.data.ndvi_tile_url || null);
          } else if (selectedIndex === 'EVI') {
            setEviTileUrl(response.data.evi_tile_url || null);
          } else if (selectedIndex === 'NDWI') {
            setNdwiTileUrl(response.data.ndwi_tile_url || null);
          } else if (selectedIndex === 'MNDWI') {
            setMndwiTileUrl(response.data.mndwi_tile_url || null);
          }

          // Set the legend for the selected index (specific to the selected index)
          setLegend(response.data.legend[selectedIndex] || null);
        } else {
          alert('No data available for the selected area, date range, and index.');
        }
      } catch (error) {
        console.error('Error fetching data for area:', error);
        alert('There was an error fetching data. Please try again later.');
      }
    }
  };





  // const fetchNDVIForYearRange = async () => {
  //   if (!startDate || !endDate) {
  //     alert('Please select both start and end dates.');
  //     return;
  //   }

  //   const coordinates = selectedArea.map(([lat, lng]) => [lng, lat]);
  //   console.log('Sending coordinates for year range:', coordinates);

  //   try {
  //     const response = await axios.post('https://backend-crop-analysis-1.onrender.com/get-ndvi-for-year-range', {
  //       coordinates: coordinates,
  //       start_date: startDate,
  //       end_date: endDate,
  //     });

  //     console.log('NDVI Data Response:', response.data);
  //     if (response.data.ndvi_data) {
  //       setNdviData(response.data.ndvi_data);
  //     } else {
  //       alert('No NDVI data available for the selected area and date range.');
  //     }
  //   } catch (error) {
  //     console.error('Error fetching NDVI data for year range:', error);
  //     alert('There was an error fetching NDVI data. Please try again later.');
  //   }
  // };


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
        <div className="flex items-center space-x-2 mb-4">
          <a href="/" className="text-green-500 hover:text-green-700 flex items-center space-x-2">
            <IoMdHome className="text-xl" />
            <span className="text-lg">Home</span>
          </a>
          <span className="text-white/70">/</span>
          <span className="text-white/70">Form</span>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4 mb-10">
          <div className="flex flex-col">
            <label className="text-white/70 font-semibold mb-2">Place Name:</label>
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
          <div className="flex flex-col">
            <label className="text-white/70 font-semibold">Select Index:</label>
            <select value={indexType} onChange={(e) => setIndexType(e.target.value)} className="p-2 border border-gray-300 rounded-lg">
              <option value="NDVI">Normalized Difference Vegetation Index (NDVI)</option>
              <option value="EVI">Enhanced Vegetation Index (EVI)</option>
              <option value="NDWI">Normalized Difference Water Index (NDWI)</option>
              <option value="MNDWI">Modified Normalized Difference Water Index (MNDWI)</option>
            </select>
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
            Get {selectedIndex} Data
          </button>
        </form>


        {legend && (
          <div className="mt-6 p-4 bg-gray-100 rounded-lg shadow-md">
            <h3 className="text-xl font-semibold">Legend for {indexType}</h3>
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
              <h3 className="text-xl font-semibold">Select Date Range and Index</h3>
              <div className="space-y-4 mt-4">
                {/* Start Date Input */}
                <div className="flex flex-col">
                  <label className="font-semibold">Start Date:</label>
                  <input
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    className="p-2 border border-gray-300 rounded-lg"
                  />
                </div>

                {/* End Date Input */}
                <div className="flex flex-col">
                  <label className="font-semibold">End Date:</label>
                  <input
                    type="date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    className="p-2 border border-gray-300 rounded-lg"
                  />
                </div>

                {/* Index Selection */}
                <div className="flex flex-col">
                  <label className="font-semibold">Select Index:</label>
                  <div className="space-y-2">
                    {['NDVI', 'EVI', 'NDWI', 'MNDWI'].map((index) => (
                      <div key={index} className="flex items-center">
                        <input
                          type="radio"
                          id={index}
                          name="index"
                          value={index}
                          checked={selectedIndex === index}
                          onChange={(e) => setSelectedIndex(e.target.value)}
                          className="mr-2"
                        />
                        <label htmlFor={index} className="text-gray-700">{index}</label>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Buttons */}
              <div className="mt-4 flex justify-between">
                <button
                  onClick={handleDateSubmit}  // Ensure handleDateSubmit is aware of selectedIndex
                  className="px-4 py-2 bg-green-600 text-white rounded-lg"
                >
                  Submit
                </button>
                {/* <button
                  onClick={fetchNDVIForYearRange}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg"
                >
                  Fetch NDVI for Year Range
                </button> */}
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
          {ndviTileUrl && <TileLayer url={ndviTileUrl} />}
          {eviTileUrl && <TileLayer url={eviTileUrl} />}
          {ndwiTileUrl && <TileLayer url={ndwiTileUrl} />}
          {mndwiTileUrl && <TileLayer url={mndwiTileUrl} />}
          {popupPosition && ndviValue && (
            <Popup
              position={popupPosition}
              onClose={() => {
                setPopupPosition(null);
                setNdviValue(null);
              }}
            >
              {selectedIndex} value at this location: <strong>{ndviValue}</strong>
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
