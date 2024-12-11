# Crop Analysis Platform
## Overview
The **Crop Analysis Platform** is designed to calculate various vegetation indices for crop monitoring and analysis. These indices, including **NDVI**, **EVI**, **NDWI**, **MNDWI**, **SAVI**, **NDMI**, **CI**, and **LAI**, help in assessing crop health, moisture levels, and vegetation cover. The platform integrates **Google Earth Engine (GEE)** for fetching satellite imagery, specifically **Sentinel-2 (COPERNICUS/S2_SR_HARMONIZED)** data, to provide accurate and up-to-date information for analysis.

## Key Features
- **Vegetation Index Calculations**: Compute multiple indices, such as:
  - NDVI (Normalized Difference Vegetation Index)
  - EVI (Enhanced Vegetation Index)
  - NDWI (Normalized Difference Water Index)
  - MNDWI (Modified Normalized Difference Water Index)
  - SAVI (Soil-Adjusted Vegetation Index)
  - NDMI (Normalized Difference Moisture Index)
  - CI (Chlorophyll Index)
  - LAI (Leaf Area Index)

- **Interactive Frontend**: Built using **React** and **Leaflet** for seamless map visualization and user interaction.
- **Satellite Imagery Integration**: Fetch satellite imagery from **Google Earth Engine** using **Sentinel-2** data, processed through a **Python Flask** backend.
- **Date and Index Selection**: Users can select a date range and index type to fetch relevant satellite data for crop analysis.
- **Download Imagery**: Users can download satellite imagery for offline use and further analysis.

## Technologies Used

- **Frontend**: 
  - React
  - Leaflet (for map visualization)
- **Backend**: 
  - Python
  - Flask
  - Google Earth Engine API (GEE)
- **Satellite Data**: 
  - Sentinel-2 (COPERNICUS/S2_SR_HARMONIZED)

## Getting Started

### Frontend Setup
1. Clone the repository.
```bash
git@github.com:SylviaT01/Crop-Analysis.git
```
2. Install the required frontend dependencies:
```bash
npm install
```
3. Run the React development server:
```bash
npm start
```
### Backend Setup
1. Install the required Python dependencies:
```bash
pip install -r requirements.txt
```
2. Set up your Google Earth Engine credentials by following the instructions on the official [GEE documentation](https://developers.google.com/earth-engine/guides/auth)
3. Start the Flask server:
```bash
python app.py
```
### Configuration
- **Google Earth Engine API**: Ensure you have access to Google Earth Engine and have set up the appropriate credentials for the API.


## Usage
1. Open the frontend application in your web browser.
2. Select a date range and index type to fetch relevant satellite data.
3. The map will display the satellite imagery for the selected date range and index type.
4. Users can download the satellite imagery for offline use and further analysis.

## Contributions
Contributions are welcome! If you'd like to contribute to this project, please fork the repository and submit a pull request.

## Author
[Sylvia Chebet](https://github.com/SylviaT01)

## License
This project is licensed under the MIT License.

