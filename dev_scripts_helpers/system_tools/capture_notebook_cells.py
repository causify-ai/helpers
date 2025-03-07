# pip install nbconvert nbformat selenium pillow

import os
import time

import nbformat
from PIL import Image
from selenium import webdriver


#def extract_cells(notebook_path, cell_numbers, temp_notebook="temp_subset.ipynb"):
#    """
#    Extracts specific cells from a Jupyter Notebook and saves them as a new
#    temporary notebook.
#
#    Args:
#        notebook_path (str): Path to the original .ipynb notebook.
#        cell_numbers (list): List of cell indices to extract.
#        temp_notebook (str): Name of the temporary notebook file.
#    """
#    # Load the notebook
#    with open(notebook_path, "r", encoding="utf-8") as f:
#        nb = nbformat.read(f, as_version=4)
#
#    # Keep only the selected cells
#    nb["cells"] = [nb["cells"][i] for i in cell_numbers if i < len(nb["cells"])]
#
#    # Save to a new temporary notebook
#    with open(temp_notebook, "w", encoding="utf-8") as f:
#        nbformat.write(nb, f)
#
#
#def save_cells_as_png(notebook_path, cell_numbers, output_path="output.png"):
#    """
#    Extracts specific cells, renders them as HTML, and captures a screenshot.
#
#    Args:
#        notebook_path (str): Path to the original .ipynb notebook.
#        cell_numbers (list): List of cell indices to extract.
#        output_path (str): Output image file name.
#    """
#    temp_notebook = "temp_subset.ipynb"
#    extract_cells(notebook_path, cell_numbers, temp_notebook)
#
#    # Convert to HTML
#    html_path = temp_notebook.replace(".ipynb", ".html")
#    os.system(f"jupyter nbconvert --to html {temp_notebook} --output temp_subset")
#
#    # Start headless browser
#    options = webdriver.ChromeOptions()
#    options.add_argument("--headless")
#    driver = webdriver.Chrome(options=options)
#
#    # Open HTML file
#    driver.get(f"file://{os.path.abspath(html_path)}")
#    time.sleep(2)  # Wait for rendering
#
#    # Take a full-page screenshot
#    screenshot_path = "temp_screenshot.png"
#    driver.save_screenshot(screenshot_path)
#    driver.quit()
#
#    # Crop to only show the extracted cells
#    img = Image.open(screenshot_path)
#    width, height = img.size
#
#    # Assume each cell has a fixed height (adjust as needed)
#    cell_height = 180
#    top = 0
#    bottom = min(len(cell_numbers) * cell_height, height)
#
#    cropped_img = img.crop((0, top, width, bottom))
#    cropped_img.save(output_path)
#    cropped_img.show()
#
#
## Example: Capture cells 1, 3, and 5 from notebook
#save_cells_as_png(
#    "example_notebook.ipynb",
#    cell_numbers=[1, 3, 5],
#    output_path="selected_cells.png",
#)
