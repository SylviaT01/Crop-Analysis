// App.js
import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import Home from './components/Home';
import NDVIMap from './components/NDVIMap';
import './App.css';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

function App() {
  return (
    <Router>
      <div className="App">
      <ToastContainer />
        {/* <header>
          <h1>NDVI Analysis Tool</h1>
        </header> */}
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/indices-map" element={<NDVIMap />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
