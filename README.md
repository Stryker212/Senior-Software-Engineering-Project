# Will-Landslide-Come-After-Wildfire

## Goal:
This application is an analytical tool that assesses the effects of forest fires on landslide susceptibility in Oregon. The intended audience includes academics, planners, and policymakers involved in studying the interaction between natural hazards and landscape stability.

Wildfires can destabilize the landscape by burning off plant cover, weakening soil integrity, and increasing runoff. Recognizing where these risks are greatest is essential for:

- Emergency planning  
- Protecting infrastructure  
- Environmental management  
- Public safety  

This study offers an evidence-based approach to pinpointing risk hot spots and visualizing how the effects of wildfires increase landslide risk.

- Pinpoints locations susceptible to landslides considering topographic and soil factors  
- Utilizes long-term wildfire history records (2020–2024) for evaluating environmental impacts  
- Identifies regions prone to repeated wildfires that affect stability  
- Employs geospatial techniques to analyze slope, soil, and hydrology data  
- Develops an easily interpretable risk map  

---

## Wildfire-Adjusted Landslide Risk Map

<img width="246" height="196" alt="image" src="https://github.com/user-attachments/assets/0626f748-45c8-4f34-9143-cc888a3de0a4" />

The figure above represents the landslide risk model using the slope, soil type, and forest fire variables. The dark areas depict high potential for landslides, whereas the repeated fire zones represent higher risks for landslides because of vegetation instability and erosion.

---

## Model Explanation

The equation considers factors that affect the landslide hazard as follows:

- **Slope** – High slopes enhance instability  
- **Content of clay** – More clay content weakens the soil when wet  
- **Bulk Density** – Soils with high bulk density increase the likelihood of slope failure  
- **Permeability (Ksat)** – Soils with low permeability retain more water  

The above factors are standardized and used in the weighted equation to determine the likelihood of landslides occurring.  

Data on previous wildland fires is introduced by locating areas that have experienced repeated burning and applying a multiplier to the landslide hazard in those areas.

---

## How to Access

**View on GitHub:**  

- Home Page:  
  https://github.com/Stryker212/Senior-Software-Engineering-Project  

- README:  
  https://github.com/Stryker212/Senior-Software-Engineering-Project/blob/main/README.md  

- Final Analytical Report:  
  https://docs.google.com/document/d/1nJzGfkT1cZTCUHmnIKcMGhW4X0LI2VPyk89pesMLLCs/edit?tab=t.0

---

## Requirements

- Requires Python (3.x)  
- QGIS for geospatial processing  
- Required datasets included in the repository  

---

## Webpage Setup

1. Clone or download the repository  
2. Navigate to the folder:  
   `262_maping data`  
3. Open the `README.md` file in that folder  
4. Follow the setup and execution instructions provided  

---

## Contributions

- John Stryker (strykerj@oregonstate.edu)  
  – Geospatial modeling, wildfire integration, data processing  

- Umna Khawaja (khawajau@oregonstate.edu)  
  – Landslide/vegetation modelling, statistical visualizations, data processing, statistical analysis  

- Evia Liang (liangev@oregonstate.edu)  
  – Wildfire and soil data processing, visualizations, modeling, and research  
