from flask import Flask, request, jsonify
from flask_cors import CORS 
import ee

app = Flask(__name__)
CORS(app)

# Initialize Earth Engine (assuming authentication is set up)
ee.Authenticate()

# Initialize the Earth Engine library with the specified project.
ee.Initialize(project='ee-cropanalysisgee')


@app.route('/get-ndvi', methods=['POST'])
def get_ndvi():
    # Extract the user input from the request
    data = request.json
    coordinates = data.get('coordinates')  # [lon_min, lat_min, lon_max, lat_max]
    start_date = data.get('start_date')
    end_date = data.get('end_date')

    # Define area of interest (from user-provided coordinates)
    aoi = ee.Geometry.Rectangle(coordinates)

    # Load and filter Sentinel-2 image collection
    image = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
        .filterBounds(aoi) \
        .filterDate(start_date, end_date) \
        .sort('system:time_start') \
        .first()  # Use the first image in the collection

    # Select Red and NIR bands for NDVI calculation
    nir_band = image.select('B8')
    red_band = image.select('B4')
    ndvi = nir_band.subtract(red_band).divide(nir_band.add(red_band)).rename('NDVI')

    # Get the NDVI map parameters
    ndvi_params = ndvi.getMapId({'min': -1, 'max': 1, 'palette': ['blue', 'white', 'green']})

    # Return the URL for the tile layer to the frontend
    return jsonify({
        'tile_url': ndvi_params['tile_fetcher'].url_format,
        'attribution': 'Google Earth Engine'
    })

if __name__ == '__main__':
    app.run(debug=True)
