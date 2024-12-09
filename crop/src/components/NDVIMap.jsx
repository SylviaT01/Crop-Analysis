import React, { useState, useRef } from 'react';
import axios from 'axios';
import L from 'leaflet';
import { MapContainer, TileLayer, useMap, Popup, FeatureGroup } from 'react-leaflet';
import { Circles } from 'react-loader-spinner';
import { EditControl } from 'react-leaflet-draw';
import 'leaflet/dist/leaflet.css';
import 'leaflet-draw/dist/leaflet.draw.css';
import backgroundVideo from '../assets/backgroundVideo.mp4';
import { IoMdHome } from "react-icons/io";
import { FaRedoAlt } from 'react-icons/fa';
import { Line } from 'react-chartjs-2';
import { toast } from 'react-toastify';
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
  const [startDate, setStartDate] = useState(null);
  const [endDate, setEndDate] = useState('');
  const [tileUrl, setTileUrl] = useState(null);
  const [ndviTileUrl, setNdviTileUrl] = useState(null);
  const [eviTileUrl, setEviTileUrl] = useState(null);
  const [ndwiTileUrl, setNdwiTileUrl] = useState(null);
  const [mndwiTileUrl, setMndwiTileUrl] = useState(null);
  const [legend, setLegend] = useState(null);
  const [indexValue, setIndexValue] = useState(null);
  const [popupPosition, setPopupPosition] = useState(null);
  const [selectedArea, setSelectedArea] = useState(null);
  const [showDateModal, setShowDateModal] = useState(false);
  const [ndviData] = useState({});
  const [indexType, setIndexType] = useState('NDVI');
  const startDateRef = useRef(startDate);
  const endDateRef = useRef(endDate);
  const [loading, setLoading] = useState(true);
  const [tilesLoaded, setTilesLoaded] = useState(false);
  const [indexRange, setIndexRange] = useState(null);
  const [palette, setPalette] = useState([]);

  React.useEffect(() => {
    startDateRef.current = startDate;
    endDateRef.current = endDate;
  }, [startDate, endDate]);

  const handleTileLoadStart = () => {
    if (!tilesLoaded) {
      setLoading(true);
    }
  };

  const handleTileLoadEnd = () => {
    setLoading(false);
    setTilesLoaded(true);
  };



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
    setLoading(true);
    toast.info('Preparing to view indices for the selected area...', {
      position: "top-right",
      autoClose: 3000,
      closeOnClick: true,
      draggable: true,
      pauseOnHover: true,
    });
    try {
      const response = await axios.post('http://127.0.0.1:5000/get-ndvi', {
        coordinates: [coordinates.lonMin, coordinates.latMin, coordinates.lonMax, coordinates.latMax],
        start_date: startDateRef.current,
        end_date: endDateRef.current,
        index: indexType,
      });

      if (response.status === 200) {
        toast.success('Data retrieved successfully!', {
          position: "top-right",
          autoClose: 3000,
          closeOnClick: true,
          draggable: true,
          pauseOnHover: true,
        });
        setTileUrl(response.data.tile_url);
        setLegend(response.data.legend);
        setIndexRange(response.data.index_range);
        setPalette(response.data.palette);
        setTimeout(() => setLoading(false), 3000);
      }
    } catch (error) {
      setLoading(false);
      if (error.response && error.response.status === 404) {
        // Show error notification
        toast.error('No imagery found for the selected date range.', {
          position: "top-right",
          autoClose: 5000,
          hideProgressBar: false,
          closeOnClick: true,
          pauseOnHover: true,
          draggable: true,
          progress: undefined,
        });
      } else {
        console.error('Error fetching vegetation index data:', error);
      }
    }
  };


  const handlePolygonCreate = (e) => {
    const layer = e.layer;
    layer.setStyle({
      fillOpacity: 0,
      color: '#3388ff',
      weight: 2
    });

    layer.on('click', (event) => {
      console.log('Polygon clicked:', event.latlng);
      console.log("Start Date:", startDateRef.current, "End Date:", endDateRef.current);
      handleMapClick(event);
    });



    // Check if the created layer is a polygon and handle it
    if (layer instanceof L.Polygon || layer instanceof L.Polyline) {
      const latLngs = layer.getLatLngs()[0].map(latLng => [latLng.lat, latLng.lng]);
      console.log('Selected Area Coordinates (Polygon):', latLngs);
      setSelectedArea(latLngs);
      setShowDateModal(true);
    }
    else {
      console.error("Unrecognized layer type.");
    }
  };

  const handleDateSubmit = async () => {
    console.log("Start Date in Submit:", startDate);
    console.log("End Date in Submit:", endDate);

    console.log("Start Date:", startDate, "End Date:", endDate);
    setShowDateModal(false);
    setLoading(true);


    toast.info('Preparing to view indices for the selected area...', {
      position: "top-right",
      autoClose: 3000,
      closeOnClick: true,
      draggable: true,
      pauseOnHover: true,
    });


    const confirmView = window.confirm('Do you want to view the indices for the selected area?');
    if (confirmView) {
      const coordinates = selectedArea.map(([lng, lat]) => [lat, lng]);
      console.log('Sending coordinates:', coordinates);

      try {
        const response = await axios.post('http://127.0.0.1:5000/get-ndvi-for-area', {
          coordinates: coordinates,
          start_date: startDateRef.current,
          end_date: endDateRef.current,
          index: indexType,
        });


        if (response.data) {

          toast.success('Data retrieved successfully!', {
            position: "top-right",
            autoClose: 3000,
            closeOnClick: true,
            draggable: true,
            pauseOnHover: true,
          });

          if (indexType === 'NDVI') {
            setNdviTileUrl(response.data.ndvi_tile_url || null);
          } else if (indexType === 'EVI') {
            setEviTileUrl(response.data.evi_tile_url || null);
          } else if (indexType === 'NDWI') {
            setNdwiTileUrl(response.data.ndwi_tile_url || null);
          } else if (indexType === 'MNDWI') {
            setMndwiTileUrl(response.data.mndwi_tile_url || null);
          }
          setLegend(response.data.legend[indexType] || null);
          setIndexRange(response.data.index_range[indexType] || null);
          setTimeout(() => setLoading(false), 3000);
        }
      } catch (error) {
        setLoading(false)
        toast.error('No imagery found for the selected date range.', {
          position: "top-right",
          autoClose: 5000,
          closeOnClick: true,
          draggable: true,
          pauseOnHover: true,
        });
      }
    }
  };
  const handleMapClick = async (event) => {
    const { lat, lng } = event.latlng;

    console.log("Map clicked at:", { lat, lng });
    console.log("start_date:", startDateRef.current, "end_date:", endDateRef.current);

    if (!startDateRef.current || !endDateRef.current) {
      console.error("Missing start_date or end_date");
      alert('Please select both start and end dates before clicking on the map.');
      return;
    }
    setPopupPosition({ lat, lng });
    setIndexValue(null);

    try {
      const response = await axios.post('http://127.0.0.1:5000/get-index-values', {
        latitude: lat,
        longitude: lng,
        start_date: startDateRef.current,
        end_date: endDateRef.current,
      });

      const data = response.data;
      const indexKey = indexType.toLowerCase() + '_value';
      console.log('Response data:', response.data);
      setIndexValue(data[indexKey]);
      setPopupPosition({ lat, lng });
      console.log(`${indexType} Value at ${lat}, ${lng}:`, data[indexKey]);
      console.log('Index Value:', data[indexKey]);
      console.log('Popup Position:', { lat, lng });
      console.log('Map clicked at:', { lat, lng });

    } catch (error) {
      console.error('Error fetching index value:', error);
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
    labels: Object.keys(ndviData),
    datasets: [
      {
        label: 'Mean NDVI',
        data: Object.values(ndviData),
        borderColor: 'rgba(75, 192, 192, 1)',
        backgroundColor: 'rgba(75, 192, 192, 0.5)',
        borderWidth: 1,
      },
    ],
  };



  function NDVILayer() {
    const map = useMap();

    React.useEffect(() => {
      if (tileUrl) {
        const ndviLayer = L.tileLayer(tileUrl, {
          attribution: 'Google Earth Engine',
          interactive: true,
        });
        ndviLayer.addTo(map);

        const handleClick = (event) => {
          handleMapClick(event);
        };
        map.on('click', handleClick);
        return () => {
          map.off('click', handleClick);
          map.removeLayer(ndviLayer);
        };
      }
    }, [map]);

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


  const handleClearMap = () => {
    setTileUrl(null);
    setNdviTileUrl(null);
    setEviTileUrl(null);
    setNdwiTileUrl(null);
    setMndwiTileUrl(null);
    setLegend(null);
    setIndexRange(null);
    setIndexValue(null);
    setPopupPosition(null);
    setSelectedArea(null);

    const map = document.querySelector('.leaflet-container')?.leafletElement;
    if (map) {
      map.eachLayer((layer) => {
        if (layer instanceof L.TileLayer && !layer.options.attribution.includes('Google Maps')) {
          map.removeLayer(layer);
        }
      });
    }
  };



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
          <div className="bg-yellow-200 p-4 rounded-lg text-black">
            <h2 className="text-lg font-semibold">Sentinel-2 Data Availability:</h2>
            <p>
              Sentinel-2 data in the COPERNICUS/S2_SR_HARMONIZED collection is available from <strong>2018 onwards</strong>.
              This includes Level-2A Surface Reflectance (SR) imagery with <strong>10-meter resolution</strong> and a revisit time of <strong>5 days</strong>.
              Fetch images from <strong>2018 to the present</strong> for your selected location and index.
            </p>
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
                min="2018-01-01"
                max={new Date().toISOString().split('T')[0]}
                className="p-2 border border-gray-300 rounded-lg"
              />
            </div>
            <div className="flex flex-col">
              <label className="text-white/70 font-semibold">End Date:</label>
              <input
                type="date"
                value={endDate}
                onChange={(e) => {
                  const selectedEndDate = e.target.value;
                  if (new Date(selectedEndDate) <= new Date(startDate)) {
                    toast.error("End date must be later than the start date.");
                  } else {
                    setEndDate(selectedEndDate);
                  }
                }}
                required
                min="2018-01-01"
                max={new Date().toISOString().split('T')[0]}
                className="p-2 border border-gray-300 rounded-lg"
              />
            </div>
          </div>

          <button
            type="submit"
            className="w-full mt-4 p-3 bg-green-600/50 text-white rounded-lg hover:bg-green-700/50 transition duration-300"
          >
            Get {indexType} Data
          </button>
        </form>
        {loading && (
          <div className="fixed inset-0 flex items-center justify-center bg-gray-900 bg-opacity-75"
            style={{ zIndex: 9999 }}>

            <Circles
              height="80"
              width="80"
              color="#4fa94d"
              ariaLabel="loading"
              wrapperStyle={{}}
              wrapperClass=""
              visible={true}
            />
          </div>
        )}
        {indexRange && indexRange[indexType + '_min'] !== undefined && indexRange[indexType + '_max'] !== undefined && (
          <div className="mt-6 p-4 bg-gray-100 rounded-lg shadow-md">
            <h3 className="text-xl font-semibold">Index Range for {indexType}</h3>
            <p className="text-gray-700">Min: {(indexRange[indexType + '_min']).toFixed(4)}</p>
            <p className="text-gray-700">Max: {(indexRange[indexType + '_max']).toFixed(4)}</p>
          </div>
        )}

        {legend && (
          <div className="mt-6 p-4 bg-gray-100 rounded-lg shadow-md">
            <h3 className="text-xl font-semibold">Legend for {indexType}</h3>
            <div style={{ width: '100%', height: '20px', background: `linear-gradient(to right, ${palette.join(', ')})` }}></div>
            <ul className="space-y-2 mt-4 flex flex-row justify-around">
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
                <div className="flex flex-col">
                  <label className="font-semibold">Start Date:</label>
                  <input
                    type="date"
                    value={startDate}
                    onChange={(e) => { setStartDate(e.target.value); console.log("Start Date Changed:", e.target.value); }}
                    required
                    min="2018-01-01"
                    max={new Date().toISOString().split('T')[0]}
                    className="p-2 border border-gray-300 rounded-lg"
                  />
                </div>
                <div className="flex flex-col">
                  <label className="font-semibold">End Date:</label>
                  <input
                    type="date"
                    value={endDate}
                    onChange={(e) => {
                      const selectedEndDate = e.target.value;
                      if (new Date(selectedEndDate) <= new Date(startDate)) {
                        toast.error("End date must be later than the start date.");
                      } else {
                        setEndDate(selectedEndDate);
                      }
                    }}
                    required
                    className="p-2 border border-gray-300 rounded-lg"
                  />
                </div>
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
                          checked={indexType === index}
                          onChange={(e) => setIndexType(e.target.value)}
                          className="mr-2"
                        />
                        <label htmlFor={index} className="text-gray-700">{index}</label>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
              <div className="mt-4 flex justify-between">
                <button
                  onClick={handleDateSubmit}
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
        <div className="map-container relative">
          <MapContainer center={[-1.0, 37.0]} zoom={10} style={{ height: '500px', width: '100%', zIndex: 1 }} className="mt-6" zoomControl={true}  >
            <TileLayer
              url="https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}"
              attribution="&copy; Google Maps"
              eventHandlers={{
                loading: handleTileLoadStart,
                load: handleTileLoadEnd,
              }}

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
            {popupPosition && indexValue && (
              <Popup
                position={popupPosition}
                onClose={() => {
                  setPopupPosition(null);
                  setIndexValue(null);
                }}
              >
                {indexValue !== null ? (
                  <>
                    {indexType} value at this location: <strong>{indexValue.toFixed(2)}</strong>
                  </>
                ) : (
                  <span>Loading...</span>
                )}
              </Popup>
            )}
          </MapContainer>
          <button
            onClick={handleClearMap}
            className="absolute top-4 left-1/2 transform -translate-x-1/2 bg-white text-gray-600 hover:bg-gray-100 shadow-md rounded-full p-2 z-[1000]"
            title="Clear Map"
          >
            <FaRedoAlt size={14} />
          </button>
        </div>


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