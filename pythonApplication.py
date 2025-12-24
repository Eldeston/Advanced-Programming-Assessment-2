# -------------------------------- HIERARCHY -------------------------------- #

# MealAPI - API
# CardUI - Widget
# CardGridUI - Widget
# RecipeUI - Top Level
# Application - Main Window

# -------------------------------- IMPORTS -------------------------------- #

# Imports requests for getting API data
import requests
# Imports threading to load application early while downloading data
import threading
# To open browser links
import webbrowser

# Imports pillow for images
from PIL import Image
# Imports BytesIO for conversion
from io import BytesIO

# Install customtkinter
# python -m pip install customtkinter
import customtkinter as ctk

# -------------------------------- STYLING -------------------------------- #

applicationName = 'MEALY DISPLAYINATOR 3000'
applicationVersion = 3.0

smallPadding = 10
bigPadding = 20

smallFont = ('JetBrains Mono', 16)
mediumFont = ('JetBrains Mono', 20)
bigFont = ('JetBrains Mono', 24)

# -------------------------------- CORE API -------------------------------- #

class MealAPI :
    def __init__(self) :
        self.url = 'https://www.themealdb.com/api/json/v1/1'

        print(
f'''
The Meal DB : Free Recipe API
The API and site will always remain free at point of access.

URL: {self.url}
'''
        )

    # Raw API request
    def request(self, mode, prompt) :
        routes = {
            'name' : 'search.php?s',
            'category' : 'filter.php?c',
            'ingredient' : 'filter.php?i',
            'area' : 'filter.php?a',
            'id' : 'lookup.php?i'
        }

        try :
            response = requests.get(f'{self.url}/{routes[mode]}={prompt}')
            if response.status_code == 200 :
                return response.json()
        except Exception as exception :
            print('API error :', exception)

        return None

    def searchMeals(self, mode, prompt) :
        data = self.request(mode, prompt)

        if not (data and data.get('meals')) :
            return []

        return data['meals']

    def processMeals(self, meals) :
        processed = []

        for meal in meals :
            # Build a clean meal object with only the fields the UI needs
            cleanMeal = {
                'idMeal' : meal.get('idMeal'),
                'strMeal' : meal.get('strMeal'),
                'strMealThumb' : meal.get('strMealThumb'),
                'previewThumb' : f'{meal.get('strMealThumb')}/preview' if meal.get('strMealThumb') else None,
                'strInstructions' : meal.get('strInstructions'),
                'strYoutube' : meal.get('strYoutube'),
                'ingredients' : []
            }

            # Extract ingredients
            for index in range(1, 21) :
                ingredient = meal.get(f'strIngredient{index}')
                measure = meal.get(f'strMeasure{index}')

                if ingredient and ingredient.strip() : cleanMeal['ingredients'].append(f'{ingredient} - {measure}')

            processed.append(cleanMeal)

        return processed

# -------------------------------- CARD UI -------------------------------- #

class CardUI(ctk.CTkFrame) :
    def __init__(self, parent, mealData, placeHolder, api : MealAPI) :
        super().__init__(parent)

        self.api = api
        self.mealData = mealData

        # Image label
        self.imgLabel = ctk.CTkLabel(self, image = placeHolder, text = '')
        self.imgLabel.pack(pady = smallPadding)

        # Title
        ctk.CTkLabel(
            self,
            text = mealData['strMeal'],
            font = bigFont,
            wraplength = 250
        ).pack()

        # ID label
        ctk.CTkLabel(
            self,
            text = f'Meal ID: {mealData['idMeal']}',
            font = smallFont,
            wraplength = 250
        ).pack()

        # Bind click to open recipe popup
        self.bind('<Button-1>', lambda event : self.openFullRecipe())
        self.imgLabel.bind('<Button-1>', lambda event : self.openFullRecipe())

        # v2-style preview thumbnail handling
        mealThumbUrl = mealData.get('previewThumb')
        if mealThumbUrl : self.loadImageAsync(mealThumbUrl)
    
    def openFullRecipe(self) :
        # Fetch full recipe details
        full = self.api.searchMeals('id', self.mealData['idMeal'])
        full = self.api.processMeals(full)

        if full : RecipeUI(full[0])

    # Replaces placeholder image with the actual image as it loads in the background
    def loadImageAsync(self, url) :
        def task() :
            try :
                response = requests.get(url)
                imgPIL = Image.open(BytesIO(response.content))
                imgTK = ctk.CTkImage(imgPIL, size = (250, 250))

                # Update image
                self.imgLabel.configure(image = imgTK)
            except Exception as exception :
                print('Failed to load image:', url, exception)

        threading.Thread(target = task, daemon = True).start()

# -------------------------------- CARD GRID UI -------------------------------- #

class CardGridUI(ctk.CTkScrollableFrame) :
    def __init__(self, parent, maxColumns = 4, indexOffset = 0) :
        super().__init__(parent)

        self.maxColumns = maxColumns
        self.indexOffset = indexOffset
        self.cards = []

        # Loading/Recipe label
        self.loadLabel = ctk.CTkLabel(
            self,
            text = 'Start Searching a Recipe',
            font = bigFont
        )
        
        self.loadLabel.grid(row = 0, column = 0, columnspan = maxColumns, padx = smallPadding, pady = smallPadding)

        # Configure responsive columns
        for col in range(maxColumns) :
            self.grid_columnconfigure(col, weight = 1)

    # Clears all cards
    def clear(self) :
        for card in self.cards : card.destroy()
        self.cards.clear()

    # Adds a CardUI widget and places it in the grid
    def addCard(self, card) :
        index = len(self.cards) + self.indexOffset
        row = (index // self.maxColumns) + 1   # +1 because row 0 is the label
        col = index % self.maxColumns

        card.grid(row = row, column = col, padx = smallPadding, pady = smallPadding)
        self.cards.append(card)

# -------------------------------- RECIPE UI -------------------------------- #

class RecipeUI(ctk.CTkToplevel) :
    def __init__(self, meal) :
        super().__init__()

        self.title(meal['strMeal'])
        self.geometry('1100x800')
        self.grab_set()

        # Configure layout (two-column layout)
        self.grid_rowconfigure(0, weight = 1)
        self.grid_columnconfigure(0, weight = 1)
        self.grid_columnconfigure(1, weight = 1)

        # ---------------- MAIN FRAME (image + ingredients) ---------------- #

        mainFrame = ctk.CTkScrollableFrame(self)
        mainFrame.grid(row = 0, column = 0, sticky = 'nsew', padx = bigPadding, pady = bigPadding)
        mainFrame.grid_columnconfigure(0, weight = 1)

        # Placeholder image
        self.tempImg = ctk.CTkImage(Image.new('RGB', (450, 450), 'gray'), size = (450, 450))

        # Title
        ctk.CTkLabel(
            mainFrame,
            text = meal['strMeal'],
            font = bigFont,
            wraplength = 400
        ).grid(row = 0, column = 0, pady = smallPadding)

        # Image placeholder
        self.imgLabel = ctk.CTkLabel(mainFrame, image = self.tempImg, text = '')
        self.imgLabel.grid(row = 1, column = 0, pady = smallPadding)

        # Load image asynchronously
        if meal.get('strMealThumb') :
            threading.Thread(
                target = self.loadImageAsync,
                args = (meal['strMealThumb'],),
                daemon = True
            ).start()

        # ---------------- INGREDIENTS ---------------- #

        ingredients = meal.get('ingredients', [])

        if ingredients :
            ctk.CTkLabel(
                mainFrame,
                text = 'Ingredients',
                font = mediumFont
            ).grid(row = 2, column = 0, pady = smallPadding)

            for index, item in enumerate(ingredients) :
                ctk.CTkLabel(
                    mainFrame,
                    text = item,
                    font = smallFont,
                    anchor = 'w',
                    justify = 'left'
                ).grid(row = 3 + index, column = 0, sticky = 'w', padx = smallPadding)

        # ---------------- INSTRUCTIONS FRAME ---------------- #

        instructionFrame = ctk.CTkScrollableFrame(self, width = 500)
        instructionFrame.grid(row = 0, column = 1, sticky = 'nsew', padx = bigPadding, pady = bigPadding)
        instructionFrame.grid_columnconfigure(0, weight = 1)

        ctk.CTkLabel(
            instructionFrame,
            text = 'Instructions',
            font = mediumFont
        ).grid(row = 0, column = 0, pady = smallPadding)

        self.instructions_label = ctk.CTkLabel(
            instructionFrame,
            text = meal.get('strInstructions', 'No instructions available.'),
            font = smallFont,
            wraplength = 500,
            justify = 'left'
        )

        self.instructions_label.grid(row = 1, column = 0, pady = smallPadding, sticky = 'nw')

        # ---------------- YOUTUBE BUTTON ---------------- #

        if meal.get('strYoutube') :
            ctk.CTkButton(
                self,
                text = 'Watch Tutorial on YouTube',
                font = mediumFont,
                command = lambda : webbrowser.open(meal['strYoutube'])
            ).grid(row = 1, column = 0, pady = bigPadding)

        # ---------------- CLOSE BUTTON ---------------- #

        ctk.CTkButton(
            self,
            text = 'Close',
            font = mediumFont,
            command = self.destroy
        ).grid(row = 1, column = 1, pady = bigPadding)

    # ---------------- Async loaders ---------------- #

    def loadImageAsync(self, url) :
        try :
            response = requests.get(url)

            imgPIL = Image.open(BytesIO(response.content))
            imgTK = ctk.CTkImage(imgPIL, size = (450, 450))

            self.updateImage(imgTK)
        except Exception as exception :
            print('Failed to load recipe image :', exception)

    def updateImage(self, imgTK) :
        self.imgRef = imgTK
        self.imgLabel.configure(image = imgTK, text = '')

# -------------------------------- MAIN APPLICATION -------------------------------- #

class Application(ctk.CTk) :
    def __init__(self) :
        super().__init__()

        self.geometry('360x360')
        self.after(1, self.wm_state, 'zoomed')

        self.grid_rowconfigure(0, weight = 0)
        self.grid_rowconfigure(1, weight = 1)
        self.grid_columnconfigure(0, weight = 1)
        self.title(f'{applicationName} v{applicationVersion}')

        self.api = MealAPI()

        self.buildUI()

    # ---------------- UI ---------------- #

    def buildUI(self) :
        header = ctk.CTkFrame(self)
        header.grid(row = 0, column = 0, sticky = 'nwe')
        header.grid_columnconfigure(0, weight = 1)

        ctk.CTkLabel(
            header,
            text = applicationName,
            font = bigFont
        ).grid(row = 0, column = 0, padx = bigPadding, pady = bigPadding, sticky = 'nsw')

        modeMenu = ctk.CTkOptionMenu(
            header,
            values = ['Name', 'Category', 'Ingredient', 'Area', 'ID'],
            font = mediumFont,
            dropdown_font = mediumFont
        )

        modeMenu.grid(row = 0, column = 2, padx = bigPadding, pady = bigPadding, sticky = 'nse')

        searchBar = ctk.CTkEntry(
            header,
            placeholder_text = 'Search...',
            font = bigFont
        )

        searchBar.grid(row = 0, column = 4, padx = bigPadding, pady = bigPadding, sticky = 'nse')

        searchPrompt = lambda : self.runSearch(searchBar.get(), modeMenu.get())
        searchBar.bind('<Return>', lambda event : searchPrompt())

        ctk.CTkButton(
            header,
            text = '🔍',
            font = bigFont,
            command = searchPrompt
        ).grid(row = 0, column = 3, padx = bigPadding, pady = bigPadding, sticky = 'nse')

        self.cardGrid = CardGridUI(self, 4, 0)
        self.cardGrid.grid(row = 1, column = 0, sticky = 'nsew')

    # ---------------- SEARCH LOGIC ---------------- #

    def runSearch(self, prompt, mode) :
        # Clear grid
        self.cardGrid.clear()
        # Change to loading while waiting
        self.cardGrid.loadLabel.configure(text = f'Loading "{prompt}" by {mode}…')

        threading.Thread(
            target = self.searchThread,
            args = (prompt, mode),
            daemon = True
        ).start()

    def searchThread(self, prompt, mode):
        # Process Raw API prompt
        raw = self.api.searchMeals(mode.lower(), prompt.lower())
        meals = self.api.processMeals(raw)

        # Temp image for all the cards as it loads
        tempImg = ctk.CTkImage(Image.new('RGB', (250, 250), 'gray'), size = (250, 250))

        # Update loading label if none found
        if not meals:
            self.after(0, lambda: self.cardGrid.loadLabel.configure(text="No results found"))
            return

        # Update loading label if results found
        self.cardGrid.loadLabel.configure(text = f'Recipes for "{prompt}" by {mode}')

        # Add in the cards
        for meal in meals :
            card = CardUI(self.cardGrid, meal, tempImg, self.api)
            self.cardGrid.addCard(card)

Application().mainloop()