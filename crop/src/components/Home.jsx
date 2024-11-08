import React from 'react';
import { Link } from 'react-router-dom';
import backgroundVideo from '../assets/backgroundVideo.mp4'

function Home() {
  return (
    <div className="relative flex flex-col items-center justify-center min-h-screen bg-gray-100">
      <video
        autoPlay
        loop
        muted
        className="absolute inset-0 w-full h-full object-cover"
      >
        <source src={backgroundVideo} type="video/mp4" />
        Your browser does not support the video tag.
      </video>
      <div className="relative z-10 text-center text-white">
        <h2 className="text-3xl font-bold text-green-600 mb-4">Welcome to the NDVI Analysis Tool</h2>
        <p className="text-lg text-gray-200 mb-6">Analyze vegetation health and conditions using NDVI data.</p>
        <Link to="/ndvi-map">
          <button className="bg-green-600 text-white py-2 px-6 rounded-lg hover:bg-green-700 transition duration-300">
            Start NDVI Analysis
          </button>
        </Link>
      </div>
    </div>
  );
}

export default Home;
