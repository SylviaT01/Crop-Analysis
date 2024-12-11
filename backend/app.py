from flask import Flask, request, jsonify, Response
from flask_cors import CORS 
import ee
import os
import time


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
    nir_band = image.select('B8') 
    red_band = image.select('B4')  
    blue_band = image.select('B2')  
    
    # Normalize by dividing by 10000 (if Sentinel-2 data)
    nir_band = nir_band.divide(10000)
    red_band = red_band.divide(10000)
    blue_band = blue_band.divide(10000)
    
    # Constants for EVI
    # Gain factor
    G = 2.5 
    # Red band coefficient 
    C1 = 6 
    # Blue band coefficient 
    C2 = 7.5 
    # Canopy background adjustment value 
    L = 10000  

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

# Function to calculate Soil-Adjusted Vegetation Index (SAVI)
def calculate_savi(image, L=0.5):
    nir_band = image.select('B8')
    red_band = image.select('B4')
    savi = nir_band.subtract(red_band).multiply(1 + L).divide(nir_band.add(red_band).add(L)).rename('SAVI')
    return savi

# Function to calculate NDMI (Normalized Difference Moisture Index)
def calculate_ndmi(image):
    nir_band = image.select('B8')
    swir_band = image.select('B11')
    ndmi = nir_band.subtract(swir_band).divide(nir_band.add(swir_band)).rename('NDMI')
    return ndmi

# #Chlorophyll index
# def calculate_ci(image):
#     nir_band = image.select('B8')
#     red_band = image.select('B4')
#     ci = nir_band.divide(red_band).subtract(1).rename('CI')
#     return ci

def calculate_ci(image):
    nir_band = image.select('B8').divide(10000)  
    red_band = image.select('B4').divide(10000)  
    ci = nir_band.divide(red_band).subtract(1).rename('CI')
    
    # Clamp the CI values to a range of 0 to 10
    ci = ci.clamp(0, 10) 
    
    return ci

def calculate_lai_from_ndvi(ndvi, a=3.5, b=-0.5):
    """
    Calculate LAI from the given NDVI image using a linear relationship.
    Parameters:
    - ndvi: NDVI image.
    - a: Coefficient for LAI calculation (default 3.5).
    - b: Intercept for LAI calculation (default -0.5).
    Returns:
    - LAI image.
    """
    lai = ndvi.multiply(a).add(b).rename('LAI')
    return lai

def calculate_lai(image):
    """
    Calculate LAI directly from the input image by chaining NDVI and LAI calculations.
    Parameters:
    - image: Input image with necessary bands (e.g., B8 for NIR, B4 for Red).
    Returns:
    - LAI image.
    """
    # Step 1: Calculate NDVI
    ndvi = calculate_ndvi(image)
    
    # Step 2: Calculate LAI from NDVI
    lai = calculate_lai_from_ndvi(ndvi)
    
    return lai


def export_image_to_drive(vegetation_index, aoi, index_type):
 
    # Export the image to Google Drive
    task = ee.batch.Export.image.toDrive(
        image=vegetation_index,
        description=f"Vegetation_Index_{index_type}",
        region=aoi,
        scale=30,
        fileFormat='GeoTIFF'
    )
    task.start()

    # Monitor the export task status
    while task.status()['state'] not in ['COMPLETED', 'FAILED']:
        time.sleep(5)  
    if task.status()['state'] == 'COMPLETED':
        download_url = task.status()['destination_uris'][0]
        print(f"Export successful. Download URL: {download_url}")
        return download_url
    else:
        print(f"Export failed with status: {task.status()}")
        return None


def calculate_rgb(image):
    """Generates an RGB composite from Sentinel-2 bands."""
    return image.select(['B4', 'B3', 'B2']).rename(['red', 'green', 'blue'])


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
            'Green': 'Dense vegetation (healthy plant growth)(High values)',
            'Yellow': 'Moderate vegetation (sparse or stressed plants)',
            'Cyan': 'Low vegetation or bare soil (minimal plant cover)',
            'Blue': 'Water bodies (Low NDVI values)'
        }
    elif index_type == 'EVI':
        vegetation_index = calculate_evi(image)
        legend = {
            '#006400': 'Dense vegetation (High EVI values)',
            '#ADFF2F': 'Moderate vegetation (Less dense plant cover)',
            '#D2B48C': 'Bare soil or minimal vegetation',
            '#0000FF': 'Water bodies or non-vegetated areas (Low EVI values)'
        }
    elif index_type == 'NDWI':
        vegetation_index = calculate_ndwi(image)
        legend = {
            '#0000FF': 'Water bodies (High values)',
            '#87CEEB': 'Moderate water content (e.g., wetland, marshland)',
            '#D3D3D3': 'Low water content (e.g., dry land, bare soil)',
            '#8B4513': 'Bare soil or dry land (Low water content)'
        }
    elif index_type == 'MNDWI':  
        vegetation_index = calculate_mndwi(image)
        legend = {
            '#0000FF': 'Water bodies - High water content (High values)',
            '#87CEEB': 'Moderate water content',
            '#D3D3D3': 'Low water content or exposed land',
            '#8B4513': 'Dry land or bare soil (Very low values)'
        }
    elif index_type == 'SAVI':
        vegetation_index = calculate_savi(image)
        legend = {
            '#006400': 'Dense vegetation (High SAVI values)',
            '#ADFF2F': 'Moderate vegetation (Sparse or less dense vegetation)',
            '#D2B48C': 'Bare soil or minimal vegetation',
            '#FFA500': 'Dry areas or exposed soil (Low SAVI values)'
        }
    elif index_type == 'NDMI':
        vegetation_index = calculate_ndmi(image)
        legend = {
            '#0000FF': 'High moisture content (e.g., water bodies, wet vegetation)',
            '#87CEEB': 'Moderate moisture (e.g., healthy vegetation)',
            '#D3D3D3': 'Low moisture content (e.g., stressed vegetation)',
            '#8B4513': 'Dry or barren areas (Low NDMI values)'
        }
    elif index_type == 'CI':
        vegetation_index = calculate_ci(image)
        legend = {
            '#006400': 'High chlorophyll content (Healthy plants)',
            '#FFD700': 'Moderate chlorophyll content (Stressed vegetation)',
            '#FF8C00': 'Low chlorophyll content (Unhealthy or sparse vegetation)',
            '#FF0000': 'Minimal or no chlorophyll (Dead vegetation or bare soil)'
        }
    elif index_type == 'LAI':
        vegetation_index = calculate_lai(image)
        legend = {
            '#004D00': 'Dense vegetation canopy (High LAI values)',
            '#66FF66': 'Moderate vegetation canopy',
            '#FFFF99': 'Sparse vegetation',
            '#8B4513': 'Minimal vegetation or bare soil'
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
        maxPixels=1e9
    ).getInfo()
    print(f"Stats for {index_type}: {stats}")

    # Print the range for the vegetation index
    print(f"Vegetation Index Range for ROI: {stats}")

    # Define the color palette based on the index type
    if index_type == 'NDVI':
        palette = ['blue', 'cyan', 'yellow', 'green']
    elif index_type == 'NDWI':
        palette = ['#8B4513', '#D3D3D3', '#87CEEB', '#0000FF']
    elif index_type == 'EVI':
        palette = ['#0000FF', '#D2B48C', '#ADFF2F', '#006400']
    elif index_type == 'SAVI':
        palette = ['#FFA500', '#D2B48C', '#ADFF2F', '#006400']
    elif index_type == 'NDMI':
        palette = ['#8B4513', '#D3D3D3', '#87CEEB', '#0000FF'] 
    elif index_type == 'CI':
        palette = ["#FF0000", "#FF8C00", "#FFD700", "#006400"]
    elif index_type == 'LAI':
        palette = ["#8B4513", "#FFFF99", "#66FF66", "#004D00"] 
    else:  
        palette = ['#8B4513', '#D3D3D3', '#87CEEB', '#0000FF']

    # Generate map URL with correct color palette and value range
    min_value = stats.get(f'{index_type}_min', None)
    max_value = stats.get(f'{index_type}_max', None)

    if min_value is None or max_value is None:
        return jsonify({
            'error': f'Missing min/max values for {index_type}.'
        }), 500

    ndvi_params = vegetation_index.getMapId({
        'min': min_value,
        'max': max_value,
        'palette': palette  
    })
    print(f"Stats for {index_type}: {stats}")

    
    download_url = export_image_to_drive(vegetation_index, aoi, index_type)
    if download_url:
   
        return jsonify({
            'tile_url': ndvi_params['tile_fetcher'].url_format,
            'attribution': 'Google Earth Engine',
            'legend': legend,
            'index_range': stats,
            'palette': palette, 
            'download_url': download_url,
            'message': 'The vegetation index map is ready for viewing. You can download the imagery now from the provided link.'
        })
    else:
        return jsonify({'error': 'Export failed, please try again later.'}), 500

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
    savi = calculate_savi(image)
    ndmi = calculate_ndmi(image)
    ci = calculate_ci(image)
    lai = calculate_lai(image)

    # Combine all indices into a single image
    combined_image = ndvi.addBands([evi, ndwi, mndwi, savi, ndmi, ci, lai])

    # Sample the values of all indices at the point
    sampled_values = combined_image.sample(point, 10).first().getInfo()

    # Extract values from the sampled feature
    if sampled_values:
        properties = sampled_values['properties']
        ndvi_value = properties.get('NDVI')
        evi_value = properties.get('EVI')
        ndwi_value = properties.get('NDWI')
        mndwi_value = properties.get('MNDWI')
        savi_value = properties.get('SAVI')
        ndmi_value = properties.get('NDMI')
        ci_value = properties.get('CI')
        lai_value = properties.get('LAI')
    else:
        return jsonify({
            'error': 'Failed to retrieve values at the given location.'
        }), 500

    # Return all index values
    return jsonify({
        'ndvi_value': ndvi_value,
        'evi_value': evi_value,
        'ndwi_value': ndwi_value,
        'mndwi_value': mndwi_value,
        'savi_value': savi_value,
        'ndmi_value': ndmi_value,
        'ci_value': ci_value,
        'lai_value': lai_value,
    })


@app.route('/get-ndvi-for-area', methods=['POST'])
def get_ndvi_for_area():
    # Extract the user input from the request
    data = request.json
    print("Received data:", data) 
    coordinates = data.get('coordinates') 
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    index_type = data.get('index')

    # Define area of interest (from user-provided polygon coordinates)
    aoi = ee.Geometry.Polygon(coordinates)

    # Load and filter Sentinel-2 image collection
    image_collection = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
        .filterBounds(aoi) \
        .filterDate(start_date, end_date) \
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 10)) \
        .limit(10)

    # Check if the image collection has any images after filtering
    # image_count = image_collection.size().getInfo()
    image_count = image_collection.sort('system:time_start').first().getInfo
    # print(f"Number of images found: {image_count}") 
    if image_count == 0:
        return jsonify({
            'error': 'No images available for the given date range and area with acceptable cloud cover.'
        }), 404


    index_mosaic = None
    if index_type == 'NDVI':
        index_mosaic = image_collection.map(calculate_ndvi).mean().clip(aoi)
    elif index_type == 'EVI':
        index_mosaic = image_collection.map(calculate_evi).mean().clip(aoi)
    elif index_type == 'NDWI':
        index_mosaic = image_collection.map(calculate_ndwi).mean().clip(aoi)
    elif index_type == 'MNDWI':
        index_mosaic = image_collection.map(calculate_mndwi).mean().clip(aoi)
    elif index_type == 'SAVI':
        index_mosaic = image_collection.map(calculate_savi).mean().clip(aoi)
    elif index_type == 'NDMI':
        index_mosaic = image_collection.map(calculate_ndmi).mean().clip(aoi)
    elif index_type == 'CI':
        index_mosaic = image_collection.map(calculate_ci).mean().clip(aoi)
    elif index_type == 'LAI':
        index_mosaic = image_collection.map(calculate_lai).mean().clip(aoi)


    stats = index_mosaic.reduceRegion(
        reducer=ee.Reducer.minMax().combine(ee.Reducer.mean(), sharedInputs=True),
        geometry=aoi,
        scale=30,
        maxPixels=1e9,
        bestEffort=True
    ).getInfo()

    index_params = index_mosaic.getMapId({'min': stats[f'{index_type}_min'], 'max': stats[f'{index_type}_max'], 'palette': get_palette(index_type)})

    download_url = export_image_to_drive(index_mosaic, aoi, index_type)

    return jsonify({
        f'{index_type}_tile_url': index_params['tile_fetcher'].url_format,
        'legend': get_legend(index_type),
        'palette': get_palette(index_type),
        'index_range': {
            f'{index_type}_min': stats[f'{index_type}_min'],
            f'{index_type}_max': stats[f'{index_type}_max'],
        },
        f'{index_type}_download_url': download_url,
    })


def get_legend(index_type):
    legends = {
        'NDVI': {
            'Green': 'Dense vegetation (healthy plant growth)(High values)',
            'Yellow': 'Moderate vegetation (sparse or stressed plants)',
            'Cyan': 'Low vegetation or bare soil (minimal plant cover)',
            'Blue': 'Water bodies (Low NDVI values)'
        },
        'EVI': {
            '#006400': 'Dense vegetation (High EVI values)',
            '#ADFF2F': 'Moderate vegetation (Less dense plant cover)',
            '#D2B48C': 'Bare soil or minimal vegetation',
            '#0000FF': 'Water bodies or non-vegetated areas (Low EVI values)'
        },
        'NDWI': {
            '#0000FF': 'Water bodies (High values)',
            '#87CEEB': 'Moderate water content (e.g., wetland, marshland)',
            '#D3D3D3': 'Low water content (e.g., dry land, bare soil)',
            '#8B4513': 'Bare soil or dry land (Low water content)'
        },
        'MNDWI': {
            '#0000FF': 'Water bodies - High water content (High values)',
            '#87CEEB': 'Moderate water content',
            '#D3D3D3': 'Low water content or exposed land',
            '#8B4513': 'Dry land or bare soil (Very low values)'
        },
        'SAVI': {
            '#006400': 'Dense vegetation (High SAVI values)',
            '#ADFF2F': 'Moderate vegetation (Sparse or less dense vegetation)',
            '#D2B48C': 'Bare soil or minimal vegetation',
            '#FFA500': 'Dry areas or exposed soil (Low SAVI values)'
        },
        'NDMI': {
            '#0000FF': 'High moisture content (e.g., water bodies, wet vegetation)',
            '#87CEEB': 'Moderate moisture (e.g., healthy vegetation)',
            '#D3D3D3': 'Low moisture content (e.g., stressed vegetation)',
            '#8B4513': 'Dry or barren areas (Low NDMI values)'
        },
        'CI': {
            '#006400': 'High chlorophyll content (Healthy plants)',
            '#FFD700': 'Moderate chlorophyll content (Stressed vegetation)',
            '#FF8C00': 'Low chlorophyll content (Unhealthy or sparse vegetation)',
            '#FF0000': 'Minimal or no chlorophyll (Dead vegetation or bare soil)'
        },
        'LAI': {
            '#004D00': 'Dense vegetation canopy (High LAI values)',
            '#66FF66': 'Moderate vegetation canopy',
            '#FFFF99': 'Sparse vegetation',
            '#8B4513': 'Minimal vegetation or bare soil'
        }
    }
    return legends.get(index_type, {})

def get_palette(index_type):
    palettes = {
        'NDVI': ['blue', 'cyan', 'yellow', 'green'],
        'EVI': ['#228B22', '#ADFF2F', '#FFFF00', '#8B4513'],
        'NDWI': ['#8B4513', '#D3D3D3', '#87CEEB', '#0000FF'],
        'MNDWI': ['#8B4513', '#D3D3D3', '#87CEEB', '#0000FF'],
        'SAVI': ['#FFA500', '#D2B48C', '#ADFF2F', '#006400'],
        'NDMI': ['#8B4513', '#D3D3D3', '#87CEEB', '#0000FF'],
        'CI': ["#FF0000", "#FF8C00", "#FFD700", "#006400"],
        'LAI': ["#8B4513", "#FFFF99", "#66FF66", "#004D00"],
    }
    return palettes.get(index_type, [])

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