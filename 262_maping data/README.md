# Senior Software Engineering Project  
## Wildfire–Landslide Multi-Hazard Risk Dashboard

This project visualizes wildfire and landslide hazards across Oregon using geospatial datasets and an interactive Dash/Plotly interface.

Because the geospatial datasets are very large (many GB), they are **not stored in this GitHub repository**. Instead, they are hosted on **OneDrive**.

---

# Downloading the Required Data

After cloning the repository, you must download the project datasets.

### Step 1 — Download the data
Download the data package from OneDrive:

https://oregonstateuniversity-my.sharepoint.com/:f:/g/personal/strykerj_oregonstate_edu/IgBsb_GnW0iJS6lXDgn2xT7qAWl4TeCtFXlsnOJEmugQ0-U?e=ZtyfuL

Download and extract the folder.

---

### Step 2 — Place the data in the project folder

After extraction, place the **Data folder** in the project root so the structure looks like this:

262_maping data/
│
├── Data/
│ ├── Raster/
│ │ ├── slope_2992.tif
│ │ ├── nlcd_2016_2992.tif
│ │
│ ├── Vegetation/
│ ├── Base/
│ ├── Events/
│ │
│ └── other datasets...
│
├── outputs/
├── scripts/
├── themes/
├── README.md


# To run Webpage
1) run: python scripts/build_web_map_fast.py
2) run: python -m http.server 8000
3) In web browser: http://localhost:8000/outputs/web/index.html



If the program cannot find data, check that the folder structure matches the example above.

---

# Why the data is not in GitHub

Some datasets exceed GitHub's file size limits:

| Dataset | Size |
|-------|------|
| slope_2992.tif | ~13 GB |
| soil_muaggatt.gpkg | ~963 MB |
| nlcd_2016_2992.tif | ~798 MB |

GitHub limits files to **100 MB normally** and **2 GB with Git LFS**, so large datasets are stored externally.