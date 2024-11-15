from flask import Flask, request, jsonify
from flask_cors import CORS 
import ee

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
    green_band = image.select('B3')  # Green Band (Band 3)
    swir_band = image.select('B11')  # SWIR Band (Band 11)
    mndwi = green_band.subtract(swir_band).divide(green_band.add(swir_band)).rename('MNDWI')
    return mndwi


@app.route('/get-ndvi', methods=['POST'])
def get_vegetation_index():
    data = request.json
    coordinates = data.get('coordinates') 
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    index_type = data.get('index', 'NDVI')  # Default to NDVI if not specified

    aoi = ee.Geometry.Rectangle(coordinates)
    image_collection = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
        .filterBounds(aoi) \
        .filterDate(start_date, end_date) \
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 10))

    image = image_collection.sort('system:time_start').first()  
    if image.getInfo() is None:
        return jsonify({
            'error': 'No images available for the given date range and area with acceptable cloud cover.'
        }), 404

    # Calculate the requested vegetation index
    if index_type == 'NDVI':
        vegetation_index = calculate_ndvi(image)
        legend = {
            'Green': 'High vegetation (healthy plant growth) - Index: 0.3 to 1.0',
            'Yellow': 'Moderate vegetation (sparse or stressed plants) - Index: 0.1 to 0.3',
            'Cyan': 'Low vegetation or bare soil - Index: -0.1 to 0.1',
            'Blue': 'Water bodies - Index: -1.0 to -0.1'
        }
    elif index_type == 'EVI':
        vegetation_index = calculate_evi(image)
        legend = {
            '#006400': 'High vegetation - Index: > 0.4',
            '#ADFF2F': 'Moderate vegetation - Index: 0.2 to 0.4',
            '#D2B48C': 'Bare soil - Index: 0 to 0.2',
            '#0000FF': 'Non-vegetated/Water bodies - Index: < 0'
        }
    elif index_type == 'NDWI':
        vegetation_index = calculate_ndwi(image)
        legend = {
            '#0000FF': 'Water - High water content - Index: > 0.3',
            '#87CEEB': 'Moderate water content - Index: 0.1 to 0.3',
            '#D3D3D3': 'Low water content or bare soil - Index: -0.1 to 0.1',
            '#8B4513': 'Dry/bare soil - Index: < -0.1'
        }
    elif index_type == 'MNDWI':  # New option for Modified NDWI
        vegetation_index = calculate_mndwi(image)
        legend = {
            '#0000FF': 'Water - High water content - Index: > 0.3',
            '#87CEEB': 'Moderate water content - Index: 0.1 to 0.3',
            '#D3D3D3': 'Low water content or bare soil - Index: -0.1 to 0.1',
            '#8B4513': 'Dry/bare soil - Index: < -0.1'
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
    ndvi_params = vegetation_index.getMapId({
        'min': stats['NDWI_min'] if index_type == 'NDWI' else 
               stats['NDVI_min'] if index_type == 'NDVI' else 
               stats['EVI_min'] if index_type == 'EVI' else
               stats['MNDWI_min'],
        'max': stats['NDWI_max'] if index_type == 'NDWI' else 
               stats['NDVI_max'] if index_type == 'NDVI' else 
               stats['EVI_max'] if index_type == 'EVI' else
               stats['MNDWI_max'],
        'palette': ['blue', 'cyan', 'yellow', 'green'] if index_type == 'NDVI' else 
                   ['#8B4513', '#D3D3D3', '#87CEEB', '#0000FF'] if index_type == 'NDWI' else
                   ['#0000FF', '#D2B48C', '#ADFF2F', '#006400'] if index_type == 'EVI' else 
                   ['#8B4513', '#D3D3D3', '#87CEEB', '#0000FF']  # Palette for MNDWI
    })

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
            'Green': 'High vegetation (healthy plant growth) - NDVI: 0.3 to 1.0',
            'Yellow': 'Moderate vegetation (sparse or stressed plants) - NDVI: 0.1 to 0.3',
            'Cyan': 'Low vegetation or bare soil - NDVI: -0.1 to 0.1',
            'Blue': 'Water bodies - NDVI: -1.0 to -0.1'
        },
        'EVI': {
            '#228B22': 'High vegetation - Index: > 0.4',
            '#ADFF2F': 'Moderate vegetation - Index: 0.2 to 0.4',
            '#FFFF00': 'Sparse vegetation - Index: 0 to 0.2',
            '#8B4513': 'Bare soil - Index: -0.2 to 0',
            '#0000FF': 'Water bodies - Index: < -0.2'
        },
        'NDWI': {
            '#0000FF': 'Water - High water content - Index: > 0.3',
            '#87CEEB': 'Moderate water content - Index: 0.1 to 0.3',
            '#D3D3D3': 'Low water content or bare soil - Index: -0.1 to 0.1',
            '#8B4513': 'Dry/bare soil - Index: < -0.1'
        },
        'MNDWI': {
            '#0000FF': 'Water - High water content - Index: > 0.3',
            '#87CEEB': 'Moderate water content - Index: 0.1 to 0.3',
            '#D3D3D3': 'Low water content or bare soil - Index: -0.1 to 0.1',
            '#8B4513': 'Dry/bare soil - Index: < -0.1'
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