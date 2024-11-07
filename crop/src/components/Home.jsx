// Home.js
import React from 'react';
import { Link } from 'react-router-dom';

function Home() {
  return (
    <div>
      <h2>Welcome to the NDVI Analysis Tool</h2>
      <p>Analyze vegetation health and conditions using NDVI data.</p>
      <Link to="/ndvi-map">
        <button>Start NDVI Analysis</button>
      </Link>
    </div>
  );
}

export default Home;
