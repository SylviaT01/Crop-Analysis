from flask import Flask, request, jsonify
from flask_cors import CORS 
import ee
import os

app = Flask(__name__)
CORS(app)

# Initialize Earth Engine (assuming authentication is set up)
ee.Authenticate()
ee.Initialize(project='ee-cropanalysisgee')


# Function to calculate NDVI
def calculate_ndvi(image):
    nir_band = image.select('B8')
    red_band = image.select('B4')
    ndvi = nir_band.subtract(red_band).divide(nir_band.add(red_band)).rename('NDVI')
    return ndvi


def calculate_evi(image):
    nir_band = image.select('B8')  # NIR band
    red_band = image.select('B4')  # Red band
    blue_band = image.select('B2')  # Blue band
    
    # Normalize by dividing by 10000 (if Sentinel-2 data)
    nir_band = nir_band.divide(10000)
    red_band = red_band.divide(10000)
    blue_band = blue_band.divide(10000)
    
    # Constants for EVI
    G = 2.5  # Gain factor
    C1 = 6  # Red band coefficient
    C2 = 7.5  # Blue band coefficient
    L = 10000  # Canopy background adjustment value

    # EVI formula
    evi = nir_band.subtract(red_band).multiply(G).divide(
        nir_band.add(red_band.multiply(C1)).subtract(blue_band.multiply(C2)).add(L)
    ).rename('EVI')
    
    return evi



# Function to calculate NDWI (Normalized Difference Water Index)
def calculate_ndwi(image):
    nir_band = image.select('B8')
    green_band = image.select('B3')
    ndwi = green_band.subtract(nir_band).divide(green_band.add(nir_band)).rename('NDWI')
    return ndwi

# Function to calculate MNDWI (Modified NDWI using SWIR)
def calculate_mndwi(image):
    green_band = image.select('B3') 
    swir_band = image.select('B11')  
    mndwi = green_band.subtract(swir_band).divide(green_band.add(swir_band)).rename('MNDWI')
    return mndwi

@app.route('/get-ndvi', methods=['POST'])
def get_vegetation_index():
    data = request.json
    coordinates = data.get('coordinates') 
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    index_type = data.get('index', 'NDVI')  

    aoi = ee.Geometry.Rectangle(coordinates)

    image_collection = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
        .filterBounds(aoi) \
        .filterDate(start_date, end_date) \
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
    
    image_count = image_collection.size().getInfo()
    print(f"Number of images found: {image_count}") 
    if image_collection.size().getInfo() == 0:
        return jsonify({
            'error': f'No Sentinel-2 imagery available for the requested date range ({start_date} to {end_date}) and area of interest.'
        }), 404

    image = image_collection.sort('system:time_start').first()  
    if image.getInfo() is None:
        return jsonify({
            'error': 'No images available for the given date range and area with acceptable cloud cover.'

        }), 404

    # Calculate the requested vegetation index
    if index_type == 'NDVI':
        vegetation_index = calculate_ndvi(image)
        legend = {
            'Green': 'High vegetation (healthy plant growth) (High values)',
            'Yellow': 'Moderate vegetation (sparse or stressed plants)',
            'Cyan': 'Low vegetation or bare soil',
            'Blue': 'Water bodies (Low values)'
        }
    elif index_type == 'EVI':
        vegetation_index = calculate_evi(image)
        legend = {
            '#006400': 'High vegetation (High values)',
            '#ADFF2F': 'Moderate vegetation',
            '#D2B48C': 'Bare soil',
            '#0000FF': 'Non-vegetated/Water bodies (Low values)'
        }
    elif index_type == 'NDWI':
        vegetation_index = calculate_ndwi(image)
        legend = {
            '#0000FF': 'Water - High water content (High values)',
            '#87CEEB': 'Moderate water content',
            '#D3D3D3': 'Low water content or bare soil',
            '#8B4513': 'Dry/bare soil (Low values)'
        }
    elif index_type == 'MNDWI':  # New option for Modified NDWI
        vegetation_index = calculate_mndwi(image)
        legend = {
            '#0000FF': 'Water - High water content (High Values)',
            '#87CEEB': 'Moderate water content',
            '#D3D3D3': 'Low water content or bare soil',
            '#8B4513': 'Dry/bare soil (Low values)'
        }
    else:
        return jsonify({
            'error': 'Invalid vegetation index type. Choose from NDVI, EVI, NDWI, or MNDWI.'
        }), 400

    # Compute NDVI, EVI, or NDWI range for ROI
    stats = vegetation_index.reduceRegion(
        reducer=ee.Reducer.minMax(),
        geometry=aoi,
        scale=30,
        maxPixels=1e8
    ).getInfo()

    # Print the range for the vegetation index
    print(f"Vegetation Index Range for ROI: {stats}")

    # Generate map URL with correct color palette and value range
    # ndvi_params = vegetation_index.getMapId({
    #     'min': stats['NDWI_min'] if index_type == 'NDWI' else 
    #            stats['NDVI_min'] if index_type == 'NDVI' else 
    #            stats['EVI_min'] if index_type == 'EVI' else
    #            stats['MNDWI_min'],
    #     'max': stats['NDWI_max'] if index_type == 'NDWI' else 
    #            stats['NDVI_max'] if index_type == 'NDVI' else 
    #            stats['EVI_max'] if index_type == 'EVI' else
    #            stats['MNDWI_max'],
    #     'palette': ['blue', 'cyan', 'yellow', 'green'] if index_type == 'NDVI' else 
    #                ['#8B4513', '#D3D3D3', '#87CEEB', '#0000FF'] if index_type == 'NDWI' else
    #                ['#0000FF', '#D2B48C', '#ADFF2F', '#006400'] if index_type == 'EVI' else 
    #                ['#8B4513', '#D3D3D3', '#87CEEB', '#0000FF'] 
    # })

    # return jsonify({
    #     'tile_url': ndvi_params['tile_fetcher'].url_format,
    #     'attribution': 'Google Earth Engine',
    #     'legend': legend,
    #     'index_range': stats
    # })

    # Define the color palette based on the index type
    if index_type == 'NDVI':
        palette = ['blue', 'cyan', 'yellow', 'green']
    elif index_type == 'NDWI':
        palette = ['#8B4513', '#D3D3D3', '#87CEEB', '#0000FF']
    elif index_type == 'EVI':
        palette = ['#0000FF', '#D2B48C', '#ADFF2F', '#006400']
    else:  
        palette = ['#8B4513', '#D3D3D3', '#87CEEB', '#0000FF']

    # Generate map URL with correct color palette and value range
    ndvi_params = vegetation_index.getMapId({
        'min': stats['NDWI_min'] if index_type == 'NDWI' else 
            stats['NDVI_min'] if index_type == 'NDVI' else 
            stats['EVI_min'] if index_type == 'EVI' else
            stats['MNDWI_min'],
        'max': stats['NDWI_max'] if index_type == 'NDWI' else 
            stats['NDVI_max'] if index_type == 'NDVI' else 
            stats['EVI_max'] if index_type == 'EVI' else
            stats['MNDWI_max'],
        'palette': palette  
    })

    return jsonify({
        'tile_url': ndvi_params['tile_fetcher'].url_format,
        'attribution': 'Google Earth Engine',
        'legend': legend,
        'index_range': stats,
        'palette': palette,  # Return the palette
    })


@app.route('/get-index-values', methods=['POST'])
def get_index_values():
    # Extract the user input from the request
    data = request.json
    print(f"Received data: {data}")
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    start_date = data.get('start_date')
    end_date = data.get('end_date')

    if not start_date or not end_date:
        return jsonify({"error": "Invalid date range"}), 400
    print(f"Start date: {start_date}, End date: {end_date}")


    # Define the point of interest (user-provided latitude and longitude)
    point = ee.Geometry.Point([longitude, latitude])

    # Load and filter Sentinel-2 image collection
    image_collection = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
        .filterBounds(point) \
        .filterDate(start_date, end_date) \
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)) 
    print(image_collection.size().getInfo())
    # Get the first image in the filtered collection
    image = image_collection.sort('system:time_start').first()

    # Check if the image exists
    image_exists = image.getInfo() is not None

    if not image_exists:
        return jsonify({
            'error': 'No images available for the given date range and location with acceptable cloud cover.'
        }), 404

    # Calculate all indices
    ndvi = calculate_ndvi(image)
    evi = calculate_evi(image)
    ndwi = calculate_ndwi(image)
    mndwi = calculate_mndwi(image)

    # Combine all indices into a single image
    combined_image = ndvi.addBands([evi, ndwi, mndwi])

    # Sample the values of all indices at the point
    sampled_values = combined_image.sample(point, 10).first().getInfo()

    # Extract values from the sampled feature
    if sampled_values:
        properties = sampled_values['properties']
        ndvi_value = properties.get('NDVI')
        evi_value = properties.get('EVI')
        ndwi_value = properties.get('NDWI')
        mndwi_value = properties.get('MNDWI')
    else:
        return jsonify({
            'error': 'Failed to retrieve values at the given location.'
        }), 500

    # Return all index values
    return jsonify({
        'ndvi_value': ndvi_value,
        'evi_value': evi_value,
        'ndwi_value': ndwi_value,
        'mndwi_value': mndwi_value
    })



@app.route('/get-ndvi-for-area', methods=['POST'])
def get_ndvi_for_area():
    # Extract the user input from the request
    data = request.json
    print("Received data:", data) 
    coordinates = data.get('coordinates') 
    start_date = data.get('start_date')
    end_date = data.get('end_date')

    # Define area of interest (from user-provided polygon coordinates)
    aoi = ee.Geometry.Polygon(coordinates)

    # Load and filter Sentinel-2 image collection
    image_collection = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
        .filterBounds(aoi) \
        .filterDate(start_date, end_date) \
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))  

    # Check if the image collection has any images after filtering
    image_count = image_collection.size().getInfo()
    
    if image_count == 0:
        return jsonify({
            'error': 'No images available for the given date range and area with acceptable cloud cover.'
        }), 404

    # Calculate indices for the image collection
    ndvi_collection = image_collection.map(calculate_ndvi)
    evi_collection = image_collection.map(calculate_evi)
    ndwi_collection = image_collection.map(calculate_ndwi)
    mndwi_collection = image_collection.map(calculate_mndwi)

    # Create a mosaic from the collections
    ndvi_mosaic = ndvi_collection.mean().clip(aoi)
    evi_mosaic = evi_collection.mean().clip(aoi)
    ndwi_mosaic = ndwi_collection.mean().clip(aoi)
    mndwi_mosaic = mndwi_collection.mean().clip(aoi)

    # Define visualization parameters for each index
    ndvi_params = ndvi_mosaic.getMapId({
        'min': -0.5,
        'max': 1,
        'palette': ['blue', 'cyan', 'yellow', 'green']
    })
    evi_params = evi_mosaic.getMapId({
        'min': -0.2,
        'max': 1,
        'palette': ['#228B22', '#ADFF2F', '#FFFF00', '#8B4513']
    })
    ndwi_params = ndwi_mosaic.getMapId({
        'min': -0.5,
        'max': 0.5,
        'palette': ['#8B4513', '#D3D3D3', '#87CEEB', '#0000FF']
    })
    mndwi_params = mndwi_mosaic.getMapId({
        'min': -0.5,
        'max': 0.5,
        'palette': ['#8B4513', '#D3D3D3', '#87CEEB', '#0000FF']
    })

    # Define legends for the indices
    legend = {
        'NDVI': {
            'Green': 'High vegetation (healthy plant growth)',
            'Yellow': 'Moderate vegetation (sparse or stressed plants)',
            'Cyan': 'Low vegetation or bare soil',
            'Blue': 'Water bodies'
        },
        'EVI': {
            '#228B22': 'High vegetation',
            '#ADFF2F': 'Moderate vegetation',
            '#FFFF00': 'Sparse vegetation',
            '#8B4513': 'Bare soil',
            '#0000FF': 'Water bodies'
        },
        'NDWI': {
            '#0000FF': 'Water - High water content',
            '#87CEEB': 'Moderate water content',
            '#D3D3D3': 'Low water content or bare soil',
            '#8B4513': 'Dry/bare soil'
        },
        'MNDWI': {
            '#0000FF': 'Water - High water content',
            '#87CEEB': 'Moderate water content',
            '#D3D3D3': 'Low water content or bare soil',
            '#8B4513': 'Dry/bare soil'
        }
    }

    # Return URLs for all indices and legends to the frontend
    return jsonify({
        'ndvi_tile_url': ndvi_params['tile_fetcher'].url_format,
        'evi_tile_url': evi_params['tile_fetcher'].url_format,
        'ndwi_tile_url': ndwi_params['tile_fetcher'].url_format,
        'mndwi_tile_url': mndwi_params['tile_fetcher'].url_format,
        'legend': legend
    })
    



    


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
    # app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))