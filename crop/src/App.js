// App.js
import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import Home from './components/Home';
import NDVIMap from './components/NDVIMap';
import './App.css';

function App() {
  return (
    <Router>
      <div className="App">
        {/* <header>
          <h1>NDVI Analysis Tool</h1>
        </header> */}
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/ndvi-map" element={<NDVIMap />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
