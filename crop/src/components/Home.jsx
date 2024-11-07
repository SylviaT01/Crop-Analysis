import React from 'react';
import { Link } from 'react-router-dom';

function Home() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-100">
      <h2 className="text-3xl font-bold text-center text-green-600 mb-4">Welcome to the NDVI Analysis Tool</h2>
      <p className="text-lg text-center text-gray-700 mb-6">Analyze vegetation health and conditions using NDVI data.</p>
      <Link to="/ndvi-map">
        <button className="bg-green-600 text-white py-2 px-6 rounded-lg hover:bg-green-700 transition duration-300">
          Start NDVI Analysis
        </button>
      </Link>
    </div>
  );
}

export default Home;
