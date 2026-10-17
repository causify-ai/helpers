

<!-- toc -->

- [Selenium](#selenium)
  * [What is Selenium](#what-is-selenium)
  * [Installation](#installation)
  * [Code Tutorial](#code-tutorial)

<!-- tocstop -->

# Selenium

## What is Selenium

- `Selenium` is an open-source automation tool primarily used for testing web
  applications. It allows developers to programmatically control web browsers,
  making it valuable for data crawling and web scraping when interacting with
  dynamic, `JavaScript` driven websites. With Selenium, you can simulate user
  actions like clicking buttons, filling forms, and navigating pages, which
  makes it particularly effective for extracting data from websites that do not
  provide a direct `API` or have content loaded dynamically via `JavaScript`

- Key Features for Data Crawling:
  - `Browser Automation`: `Selenium` supports multiple browsers (e.g., `Chrome`,
    `Firefox`, `Safari`), enabling you to simulate a real user's interaction
    with the webpage
  - `JavaScript Handling: `Selenium`can interact with`JavaScript` based
    elements, ensuring data loaded dynamically is accessible
  - `Customizable Waiting Strategies`: `Selenium` offers both explicit and
    implicit waits, allowing scripts to wait for specific elements or
    conditions, essential for dealing with varying page load times

## Installation

- The following installation is based on `Chrome browser` and `Linux OS` for a
  local machine environment and not our dev servrer. It can be used for any
  other OS and browsers
- Check your google chrome verion
  - Open Google Chrome, type `chrome://settings/help` and press Enter. You’ll
    see the Chrome version listed under "Google Chrome" (e.g.,
    `Version 118.0.5993.89`)

- There are 2 ways to install chrome driver
  - Using Web Browser
    - Check what `ChromeDriver` version in compatible with your chrome and
      download at
      [ChromeDriver Download](https://sites.google.com/chromium.org/driver/downloads)
  - Using Terminal
    - Check what `ChromeDriver` version in compatibility with chrome
      [ChromeDriver Link](https://sites.google.com/chromium.org/driver/downloads)

    ```bash
    > wget https://chromedriver.storage.googleapis.com/<version>/chromedriver_linux64.zip
    ```

    OR

    ```bash
    > curl -O https://chromedriver.storage.googleapis.com/<version>/chromedriver_linux64.zip
    ```
  - Unzip the file

    ```bash
    > unzip chromedriver_linux64.zip
    ```
  - Move the file to given path and extract from here when needed

    ```bash
    > mv chromedriver /<path to driver>/
    ```

- Install the following modules
  - Within terminal

    ```bash
    > pip install selenium
    > pip install webdriver-manager
    ```

## Code Tutorial

1. Go to the notebook:
   [Selenium tutorial](https://github.com/cryptokaizen/cmamp/blob/master/docs/work_tools/selenium.tutorial.ipynb)

2. High-Level Overview

   The uploaded notebook uses `Selenium WebDriver` to automate browser actions
   for web scraping and testing two websites:
   - Website 1: [Test site](https://the-internet.herokuapp.com/login) -
     Automates the process of logging in and out, ensuring the login
     functionality works as expected
   - Website 2:
     [Adidas shoes site](https://www.adidas.com/us/men-athletic_sneakers) -
     Focuses on extracting show data from multiple pages within a specific
     section of the site (Basketball)

3. Key functionalities include:
   - Setting up `ChromeDriver` with custom options for compatibility in
     restricted environments
   - Interacting with web elements like `buttons`, `input fields`, and
     `pagination` controls
   - Extracting and potentially saving scraped data using `pandas`
   - Employing explicit waits (`WebDriverWait`) to handle dynamic content
     loading effectively

4. How to Find Elements Using `Selenium`

   `Selenium` provides several ways to locate elements on a webpage. Below is an
   explanation of each method, an example, and placeholders for images you can
   insert:
   - By `ID`:
     - Description: Locates an element by its unique `id` attribute
     - Example:
       ```
       from selenium.webdriver.common.by import By

       # Example: Find the login field element by its ID.
       login_field = driver.find_element(By.ID, "username")
       login_field.send_keys("xyz")
       ```

       <img src="figs/selenium/image1.png">
   - By `Name`:
     - Description: Finds an element using its `Name` attribute.
     - Example:
       ```
       # Example: Find the password field by its name attribute.
       password_field = driver.find_element(By.NAME, "password")
       password_field.send_keys("xyz")
       ```

       <img src="figs/selenium/image2.png">
   - By `Class Name`
     - Description: Locates elements by their `class` attribute
     - Example:
       ```
       # Example: Find a show name by its class name.
       shoe = driver.find_element(By.CLASS_NAME, "product-card-description_name__xHvJ2")
       ```

       <img src="figs/selenium/image3.png">
   - By `Tag Name`:
     - Description: Targets elements based on their `HTML` tag (e.g., `div`,
       `button`)
     - Example:
       ```
       # Example: Find shoe type by tag and print their text
       type = driver.find_elements(By.TAG_NAME, "p")
       print(type.text)
       ```

       <img src="figs/selenium/image4.png">
   - By `CSS Selector`:
     - Description: Leverages `CSS selectors` for flexible element
       identification.
     - Consider the following `html`:
       ```
       <div class="product" id="item-1">
         <h2 class="product-title">Running Shoes</h2>
         <p class="product-price">$50</p>
         <button class="add-to-cart">Add to Cart</button>
       </div>
       ```
     - Key CSS Selectors with Examples
       - Select by `Class`:
         ```
         button = driver.find_element(By.CSS_SELECTOR, ".add-to-cart")
         button.click()
         ```
       - Select by `ID`:
         ```
         product = driver.find_element(By.CSS_SELECTOR, "#item-1")
         print(product.text)
         ```
       - Select by `Parent-Child`:
         ```
         price = driver.find_element(By.CSS_SELECTOR, "#item-1 > p")
         print(price.text)
         ```
       - Select by `Descendant`:
         ```
         button = driver.find_element(By.CSS_SELECTOR, ".product button")
         button.click()
         ```
       - Select by `Attribute`:
         ```
         title = driver.find_element(By.CSS_SELECTOR, "[class='product-title']")
         print(title.text)
         ```
   - By `XPath`:
     - Description: Uses `XML path` expressions to locate elements.
     - Example:
       ```
       # Example: Find a shoe block using an XPath query
       show_block = driver.find_element(By.XPATH, "/html/body/div[1]/div[2]/main/section[3]/article[2]/div")
       ```

       <img src="figs/selenium/image5.png">

5. The above tutorial describes how to set up `Selenium`, find elements on a
   webpage, and automate tasks like clicking, sending data and scraping data.
   With different locator methods like `ID`, `Name`, and `XPath`, you can handle
   most web pages. Just tweak the code to fit your target site, and you’re good
   to go!
