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
    image_collection = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
        .filterBounds(aoi) \
        .filterDate(start_date, end_date) \
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))  # Filter images with less than 20% cloud cover

    # Get the first image in the filtered collection
    image = image_collection.sort('system:time_start').first()  # Sort by time and take the first image

    # Check if the image exists (i.e., collection is not empty)
    image_exists = image.getInfo() is not None

    if not image_exists:
        return jsonify({
            'error': 'No images available for the given date range and area with acceptable cloud cover.'
        }), 404

    # Select Red and NIR bands for NDVI calculation
    nir_band = image.select('B8')
    red_band = image.select('B4')
    ndvi = nir_band.subtract(red_band).divide(nir_band.add(red_band)).rename('NDVI')

    # Get the NDVI map parameters
    ndvi_params = ndvi.getMapId({'min': -1, 'max': 1, 'palette': ['blue', 'white', 'green']})

    # Define the legend for NDVI
    legend = {
        'Green': 'High vegetation (healthy plant growth)',
        'White': 'Moderate vegetation (sparse or stressed plants)',
        'Blue': 'No vegetation or water bodies'
    }

    # Return the URL for the tile layer and the legend to the frontend
    return jsonify({
        'tile_url': ndvi_params['tile_fetcher'].url_format,
        'attribution': 'Google Earth Engine',
        'legend': legend
    })

@app.route('/get-ndvi-value', methods=['POST'])
def get_ndvi_value():
    # Extract the user input from the request
    data = request.json
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    start_date = data.get('start_date')
    end_date = data.get('end_date')

    # Define the point of interest (user-provided latitude and longitude)
    point = ee.Geometry.Point([longitude, latitude])

    # Load and filter Sentinel-2 image collection
    image_collection = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
        .filterBounds(point) \
        .filterDate(start_date, end_date) \
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))  # Filter images with less than 20% cloud cover

    # Get the first image in the filtered collection
    image = image_collection.sort('system:time_start').first()  # Sort by time and take the first image

    # Check if the image exists
    image_exists = image.getInfo() is not None

    if not image_exists:
        return jsonify({
            'error': 'No images available for the given date range and location with acceptable cloud cover.'
        }), 404

    # Select Red and NIR bands for NDVI calculation
    nir_band = image.select('B8')
    red_band = image.select('B4')
    ndvi = nir_band.subtract(red_band).divide(nir_band.add(red_band)).rename('NDVI')

    # Sample the NDVI value at the clicked point
    ndvi_value = ndvi.sample(point).first().get('NDVI').getInfo()

    return jsonify({'ndvi_value': ndvi_value})


if __name__ == '__main__':
    app.run(debug=True)
