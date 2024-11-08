from flask import Flask, request, jsonify
from flask_cors import CORS 
import ee

app = Flask(__name__)
CORS(app)

# Initialize Earth Engine (assuming authentication is set up)
ee.Authenticate()
ee.Initialize(project='ee-cropanalysisgee')

@app.route('/get-ndvi', methods=['POST'])
def get_ndvi():
    # Extract the user input from the request
    data = request.json
    coordinates = data.get('coordinates') 
    start_date = data.get('start_date')
    end_date = data.get('end_date')

    # Define area of interest (from user-provided coordinates)
    aoi = ee.Geometry.Rectangle(coordinates)

    # Load and filter Sentinel-2 image collection
    image_collection = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
        .filterBounds(aoi) \
        .filterDate(start_date, end_date) \
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 10))  

    # Get the first image in the filtered collection
    image = image_collection.sort('system:time_start').first()  

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

    # Define a color palette that clearly distinguishes water bodies
    ndvi_params = ndvi.getMapId({
        'min': -0.5, 
        'max': 1, 
        'palette': ['blue', 'cyan', 'yellow', 'green'] 
    })

    # Define the legend for NDVI with ranges
    legend = {
        'Green': 'High vegetation (healthy plant growth) - NDVI: 0.3 to 1.0',
        'Yellow': 'Moderate vegetation (sparse or stressed plants) - NDVI: 0.1 to 0.3',
        'Cyan': 'Low vegetation or bare soil - NDVI: -0.1 to 0.1',
        'Blue': 'Water bodies - NDVI: -1.0 to -0.1'
    }

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
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)) 

    # Get the first image in the filtered collection
    image = image_collection.sort('system:time_start').first()  

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

@app.route('/get-ndvi-for-area', methods=['POST'])
def get_ndvi_for_area():
    # Extract the user input from the request
    data = request.json
    coordinates = data.get('coordinates') 
    start_date = data.get('start_date')
    end_date = data.get('end_date')

    # Define area of interest (from user-provided polygon coordinates)
    aoi = ee.Geometry.Polygon(coordinates)

    # Load and filter Sentinel-2 image collection
    image_collection = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
        .filterBounds(aoi) \
        .filterDate(start_date, end_date) \
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 5))  

    # Create a mosaic of the NDVI images
    ndvi_collection = image_collection.map(lambda image: 
        image.select('B8').subtract(image.select('B4')).divide(image.select('B8').add(image.select('B4'))).rename('NDVI')
    )

    # Create a mosaic from the NDVI collection
    ndvi_mosaic = ndvi_collection.mean().clip(aoi)

    # Check if the mosaic exists
    ndvi_mosaic_exists = ndvi_mosaic.getInfo() is not None

    if not ndvi_mosaic_exists:
        return jsonify({
            'error': 'No NDVI data available for the given date range and area with acceptable cloud cover.'
        }), 404

    # Define a color palette for NDVI visualization
    ndvi_params = ndvi_mosaic.getMapId({
        'min': -0.5,
        'max': 1,
        'palette': ['blue', 'cyan', 'yellow', 'green']
    })

    # Define the legend for NDVI with ranges
    legend = {
        'Green': 'High vegetation (healthy plant growth) - NDVI: 0.3 to 1.0',
        'Yellow': 'Moderate vegetation (sparse or stressed plants) - NDVI: 0.1 to 0.3',
        'Cyan': 'Low vegetation or bare soil - NDVI: -0.1 to 0.1',
        'Blue': 'Water bodies - NDVI: -1.0 to -0.1'
    }

    # Return the URL for the tile layer and the legend to the frontend
    return jsonify({
        'tile_url': ndvi_params['tile_fetcher'].url_format,
        'attribution': 'Google Earth Engine',
        'legend': legend
    })

# @app.route('/get-ndvi-for-year-range', methods=['POST'])
# def get_ndvi_for_year_range():
#     # Extract the user input from the request
#     data = request.json
#     coordinates = data.get('coordinates') 
#     start_date = data.get('start_date')
#     end_date = data.get('end_date')

#     # Define area of interest (from user-provided polygon coordinates)
#     aoi = ee.Geometry.Polygon(coordinates)

#     # Parse the start and end years
#     start_year = int(start_date.split('-')[0])
#     end_year = int(end_date.split('-')[0])

#     ndvi_data = {}

#     for year in range(start_year, end_year + 1):
#         year_start = f"{year}-01-01"
#         year_end = f"{year}-12-31"

#         # Load and filter Sentinel-2 image collection
#         image_collection = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
#             .filterBounds(aoi) \
#             .filterDate(year_start, year_end) \
#             .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 10))  

#         # Calculate the NDVI for the given year
#         ndvi_collection = image_collection.map(lambda image: 
#             image.select('B8').subtract(image.select('B4')).divide(image.select('B8').add(image.select('B4'))).rename('NDVI')
#         )

#         # Create a mosaic from the NDVI collection and calculate mean NDVI
#         ndvi_mosaic = ndvi_collection.mean().clip(aoi)

#         # Get the NDVI mean value for the year
#         mean_ndvi = ndvi_mosaic.reduceRegion(
#             reducer=ee.Reducer.mean(),
#             geometry=aoi,
#             scale=30,
#             maxPixels=1e8
#         ).get('NDVI').getInfo()

#         ndvi_data[year] = mean_ndvi

#     return jsonify({'ndvi_data': ndvi_data})

@app.route('/get-ndvi-for-year-range', methods=['POST'])
def get_ndvi_for_year_range():
    # Extract the user input from the request
    data = request.json
    coordinates = data.get('coordinates') 
    start_date = data.get('start_date')
    end_date = data.get('end_date')

    # Define area of interest (from user-provided polygon coordinates)
    aoi = ee.Geometry.Polygon(coordinates)

    # Parse the start and end years
    start_year = int(start_date.split('-')[0])
    end_year = int(end_date.split('-')[0])

    ndvi_data = {}

    for year in range(start_year, end_year + 1):
        year_start = f"{year}-01-01"
        year_end = f"{year}-12-31"

    # Load and filter Sentinel-2 image collection
        image_collection = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
            .filterBounds(aoi) \
            .filterDate(year_start, year_end) \
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 5))  

    # Calculate the NDVI for the given year
        ndvi_collection = image_collection.map(lambda image: 
            image.select('B8').subtract(image.select('B4')).divide(image.select('B8').add(image.select('B4'))).rename('NDVI')
        )

    # Create a mean NDVI for the year
        mean_ndvi = ndvi_collection.mean().reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=aoi,
            scale=30,
            maxPixels=1e8
        ).get('NDVI').getInfo()

    # Store the mean NDVI for the year
        ndvi_data[year] = mean_ndvi if mean_ndvi is not None else None

    print('Final NDVI Data:', ndvi_data)
    return jsonify({'ndvi_data': ndvi_data})

if __name__ == '__main__':
    app.run(debug=True)