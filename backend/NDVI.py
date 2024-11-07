import ee
import folium

# Authenticate the Earth Engine account
ee.Authenticate()

# Initialize the Earth Engine library with the specified project.
ee.Initialize(project='ee-cropanalysisgee')

# Use FAO/GAUL dataset to define Kenya's geometry and ensure the correct CRS
kenya = ee.FeatureCollection("FAO/GAUL/2015/level0") \
    .filter(ee.Filter.eq('ADM0_NAME', 'Kenya')) \
    .geometry() \
    .transform('EPSG:4326')  # Ensure it is in the EPSG:4326 (WGS84) coordinate system

# Load a Sentinel-2 image collection for the year 2022
image_collection = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
    .filterBounds(kenya) \
    .filterDate('2022-01-01', '2022-12-31') \
    .sort('system:time_start')

# Check the number of images returned
image_count = image_collection.size().getInfo()
print(f"Number of images in the collection: {image_count}")

# If no images are found, print an error message
if image_count == 0:
    print("No images found for the specified date range and area.")
else:
    # Function to apply cloud masking
    def mask_clouds(image):
        # Select the QA60 band to mask clouds
        cloud_mask = image.select('QA60').eq(0)  # 0 indicates clear pixels
        return image.updateMask(cloud_mask)

    # Apply the cloud masking function to the image collection
    cloud_masked_collection = image_collection.map(mask_clouds)

    # Function to calculate NDVI for each image
    def calculate_ndvi(image):
        nir_band = image.select('B8')  # NIR band
        red_band = image.select('B4')  # Red band
        ndvi = nir_band.subtract(red_band).divide(nir_band.add(red_band)).rename('NDVI')
        return ndvi

    # Calculate NDVI for each image in the masked collection
    ndvi_collection = cloud_masked_collection.map(calculate_ndvi)

    # Calculate the mean NDVI over the collection
    mean_ndvi = ndvi_collection.mean()

    # Create a map centered around Kenya (adjusting zoom level for clarity)
    my_map = folium.Map(location=[1.5, 38.5], zoom_start=6)  # Centered around Kenya

    # Add the geometry of Kenya to the map for visualization
    folium.GeoJson(kenya.getInfo()).add_to(my_map)

    # Retrieve the NDVI visualization parameters
    ndvi_params = mean_ndvi.getMapId({'min': -0.2, 'max': 0.8, 'palette': ['blue', 'white', 'green']})

    # Add the NDVI layer to the map with attribution
    folium.TileLayer(
        tiles=ndvi_params['tile_fetcher'].url_format,
        attr='Google Earth Engine',
        name="Mean NDVI",
        overlay=True,
        control=True
    ).add_to(my_map)

    # Add a legend for better understanding of NDVI values
    def add_ndvi_legend(map_object):
        legend_html = '''
         <div style="position: fixed; 
                     bottom: 50px; left: 50px; width: 150px; height: 90px; 
                     background-color: white; border:2px solid grey; z-index:9999; font-size:14px;">
         &nbsp; <strong>NDVI Legend</strong> <br>
         &nbsp; <span style="background-color:blue; width:20px; height:10px; display:inline-block;"></span> Low (e.g., water) <br>
         &nbsp; <span style="background-color:white; width: 20px; height:10px; display:inline-block;"></span> Moderate (e.g., bare soil) <br>
         &nbsp; <span style="background-color:green; width:20px; height:10px; display:inline-block;"></span> High (e.g., dense vegetation) <br>
         </div>
         '''
        map_object.get_root().html.add_child(folium.Element(legend_html))

    # Add the NDVI legend to the map
    add_ndvi_legend(my_map)

    # Display the map
    my_map.save('mean_ndvi_kenya.html')
    print("Map saved as 'mean_ndvi_kenya.html'.")