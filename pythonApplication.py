# -------------------------------- HIERARCHY -------------------------------- #

# MealAPI - API
# CardUI - Widget
# HeaderUI - Widget
# MainUI - Widget
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
applicationVersion = 4.0

smallPadding = 10
bigPadding = 20

smallFont = ('JetBrains Mono', 16)
mediumFont = ('JetBrains Mono', 20)
bigFont = ('JetBrains Mono', 24, 'bold')

imageSmall = (300, 300)
imageBig = (450, 450)

accentCol = "#0080FF"
backGroundCol = "#000000"
foreGroundCol = "#101010"

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
            'id' : 'lookup.php?i',
            'name' : 'search.php?s',
            'category' : 'filter.php?c',
            'ingredient' : 'filter.php?i',
            'area' : 'filter.php?a'
        }

        try :
            response = requests.get(f'{self.url}/{routes[mode]}={prompt}')
            if response.status_code == 200 : return response.json()
        except Exception as exception :
            print('API error:', exception)

        return None

    def searchMeals(self, mode, prompt) :
        data = self.request(mode, prompt)

        if not (data and data.get('meals')) : return []
        return data['meals']
    
    def truncate(self, text, maxChars = 40):
        if not text : return ""
        return text if len(text) <= maxChars else text[:maxChars - 3] + "..."

    def processMeals(self, meals) :
        processed = []

        for meal in meals :
            # Build a clean meal object with only the fields the UI needs
            cleanMeal = {
                'idMeal' : meal.get('idMeal'),
                'strMeal' : meal.get('strMeal'),
                'strMealShort': self.truncate(meal.get('strMeal')),
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

    def listOptions(self, mode) :
        routes = {
            'category': 'list.php?c=list',
            'ingredient': 'list.php?i=list',
            'area': 'list.php?a=list'
        }

        if mode not in routes:
            print(f'Invalid list mode: {mode}')
            return []

        try :
            response = requests.get(f'{self.url}/{routes[mode]}')

            if response.status_code == 200 :
                data = response.json()

                # All three endpoints return a list under "meals"
                items = data.get('meals', [])

                # Normalize output to a simple list of strings
                if mode == 'category' : return [item['strCategory'] for item in items]
                if mode == 'ingredient' : return [item['strIngredient'] for item in items]
                if mode == 'area' : return [item['strArea'] for item in items]
        except Exception as exception :
            print('API error:', exception)

        return []

# -------------------------------- CARD UI -------------------------------- #

class CardUI(ctk.CTkFrame) :
    def __init__(self, parent, mealData, placeHolder, api : MealAPI) :
        super().__init__(parent, fg_color = foreGroundCol, width = 300, height = 400, cursor = "hand2")
        self.pack_propagate(False)

        self.api = api
        self.mealData = mealData

        # Image label
        self.imgLabel = ctk.CTkLabel(self, image = placeHolder, text = '', cursor = "hand2")
        self.imgLabel.pack()

        # ID label
        ctk.CTkLabel(
            self,
            text = f'Meal ID: {mealData['idMeal']}',
            font = smallFont,
            wraplength = 300
        ).pack()

        # Title
        ctk.CTkLabel(
            self,
            text = mealData['strMealShort'],
            font = bigFont,
            wraplength = 300
        ).pack()

        # Bind click to open recipe popup
        self.bind('<Button-1>', lambda event : self.openFullRecipe())
        self.imgLabel.bind('<Button-1>', lambda event : self.openFullRecipe())

        mealThumbUrl = mealData.get('previewThumb')

        if mealThumbUrl :
            threading.Thread(
                target = lambda : self.loadImageAsync(mealThumbUrl),
                daemon = True
            ).start()
    
    def openFullRecipe(self) :
        # Fetch full recipe details
        full = self.api.searchMeals('id', self.mealData['idMeal'])
        full = self.api.processMeals(full)

        if full : RecipeUI(full[0])

    # Replaces placeholder image with the actual image as it loads in the background
    def loadImageAsync(self, url) :
        try :
            response = requests.get(url)
            imgPIL = Image.open(BytesIO(response.content))
            imgTK = ctk.CTkImage(imgPIL, size = imageSmall)

            # Update image
            self.imgLabel.configure(image = imgTK)
        except Exception as exception :
            print('Failed to load image:', url, exception)

# -------------------------------- CARD GRID UI -------------------------------- #

class MainUI(ctk.CTkScrollableFrame) :
    def __init__(self, parent, maxColumns = 4, indexOffset = 0) :
        super().__init__(parent, fg_color = "transparent")

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
        row = (index // self.maxColumns) + 1 # +1 because row 0 is the label
        col = index % self.maxColumns

        card.grid(row = row, column = col, padx = smallPadding, pady = smallPadding)
        self.cards.append(card)

# -------------------------------- RECIPE UI -------------------------------- #

class RecipeUI(ctk.CTkToplevel) :
    def __init__(self, meal) :
        super().__init__(fg_color = backGroundCol)

        self.title(meal['strMeal'])
        self.geometry('1100x800')

        # Focuses all the input into this window
        self.grab_set()

        # Configure layout (two-column layout)
        self.grid_rowconfigure(0, weight = 1)
        self.grid_columnconfigure(0, weight = 1)
        self.grid_columnconfigure(1, weight = 1)

        # ---------------- MAIN FRAME (image + ingredients) ---------------- #

        mainFrame = ctk.CTkScrollableFrame(self, fg_color = foreGroundCol)
        mainFrame.grid(row = 0, column = 0, sticky = 'nsew', padx = bigPadding, pady = bigPadding)
        mainFrame.grid_columnconfigure(0, weight = 1)

        # Placeholder image
        self.tempImg = ctk.CTkImage(Image.new('RGB', imageBig, 'gray'), size = imageBig)

        # ID
        ctk.CTkLabel(
            mainFrame,
            text = f'Meal ID: {meal['idMeal']}',
            font = mediumFont,
            wraplength = 400
        ).grid(row = 0, column = 0, pady = smallPadding)

        # Meal Name
        ctk.CTkLabel(
            mainFrame,
            text = meal['strMeal'],
            font = bigFont,
            wraplength = 400
        ).grid(row = 1, column = 0, pady = smallPadding)

        # Image placeholder
        self.imgLabel = ctk.CTkLabel(mainFrame, image = self.tempImg, text = '')
        self.imgLabel.grid(row = 2, column = 0, pady = smallPadding)

        # Load image asynchronously
        if meal.get('strMealThumb') :
            threading.Thread(
                target = lambda : self.loadImageAsync(meal['strMealThumb']),
                daemon = True
            ).start()

        # ---------------- INGREDIENTS ---------------- #

        ingredients = meal.get('ingredients', [])

        if ingredients :
            ctk.CTkLabel(
                mainFrame,
                text = 'Ingredients',
                font = mediumFont
            ).grid(row = 3, column = 0, pady = smallPadding)

            for index, item in enumerate(ingredients) :
                ctk.CTkLabel(
                    mainFrame,
                    text = item,
                    font = smallFont,
                    anchor = 'w',
                    justify = 'left'
                ).grid(row = 4 + index, column = 0, sticky = 'w', padx = smallPadding)

        # ---------------- INSTRUCTIONS FRAME ---------------- #

        instructionFrame = ctk.CTkScrollableFrame(self, fg_color = foreGroundCol)
        instructionFrame.grid(row = 0, column = 1, sticky = 'nswe', padx = bigPadding, pady = bigPadding)

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
                text = 'Watch YouTube Tutorial',
                font = mediumFont,
                fg_color = accentCol,
                hover_color = accentCol,
                command = lambda : webbrowser.open(meal['strYoutube'])
            ).grid(row = 1, column = 0, padx = bigPadding, pady = bigPadding)

        # ---------------- CLOSE BUTTON ---------------- #

        ctk.CTkButton(
            self,
            text = 'Close Popup Window',
            font = mediumFont,
            fg_color = accentCol,
            hover_color = accentCol,
            command = self.destroy
        ).grid(row = 1, column = 1, padx = bigPadding, pady = bigPadding)

    # ---------------- Async loaders ---------------- #

    def loadImageAsync(self, url) :
        try :
            response = requests.get(url)

            imgPIL = Image.open(BytesIO(response.content))
            imgTK = ctk.CTkImage(imgPIL, size = imageBig)

            self.imgLabel.configure(image = imgTK, text = '')
        except Exception as exception :
            print('Failed to load recipe image :', exception)

# -------------------------------- HEADER UI -------------------------------- #

class HeaderUI(ctk.CTkFrame) :
    def __init__(self, parent, getSuggestions, runSearch) :
        super().__init__(parent, fg_color = "transparent")

        self.fullSuggestions = []
        self.runSearch = runSearch
        self.getSuggestions = getSuggestions

        self.grid_columnconfigure(0, weight = 1)

        # Track last typed text to avoid race conditions
        self.lastQuery = ""

        # ---------------- TITLE ---------------- #

        ctk.CTkLabel(
            self,
            text = applicationName,
            font = bigFont
        ).grid(row = 0, column = 0, padx = bigPadding, pady = bigPadding, sticky = 'nsw')

        # ---------------- MODE MENU ---------------- #

        self.modeMenu = ctk.CTkOptionMenu(
            self,
            values = ['Name', 'Category', 'Ingredient', 'Area', 'ID'],
            font = mediumFont,
            dropdown_font = mediumFont,
            fg_color = accentCol,
            button_color = accentCol,
            button_hover_color = accentCol
        )

        self.modeMenu.grid(row = 0, column = 2, padx = bigPadding, pady = bigPadding, sticky = 'nse')
        self.modeMenu.configure(command = self.onModeChange)

        # ---------------- SEARCH BUTTON ---------------- #

        self.searchButton = ctk.CTkButton(
            self,
            text = '🔍',
            font = bigFont,
            fg_color = accentCol,
            hover_color = accentCol
        )

        self.searchButton.grid(row = 0, column = 3, padx = bigPadding, pady = bigPadding, sticky = 'nse')

        # ---------------- SEARCH BAR ---------------- #

        self.searchBar = ctk.CTkEntry(
            self,
            placeholder_text = 'Search...',
            font = mediumFont,
            fg_color = foreGroundCol
        )

        self.searchBar.grid(row = 0, column = 4, ipadx = bigPadding * 8, padx = bigPadding, pady = bigPadding, sticky = 'nswe')

        # Bind typing event
        self.searchBar.bind('<KeyRelease>', self.updateAutocomplete)

        # ---------------- AUTOCOMPLETE FRAME ---------------- #

        self.autoFrame = ctk.CTkFrame(self, fg_color = foreGroundCol)
        self.autoFrame.grid(row = 1, column = 0, columnspan = 5, sticky = 'nwe', padx = bigPadding)
        self.autoFrame.grid_columnconfigure((0, 1, 2, 3), weight = 1)
        self.autoFrame.grid_remove() # Hidden at startup

        # Suggested label
        self.suggestLabel = ctk.CTkLabel(
            self.autoFrame,
            text = 'Suggested',
            font = bigFont
        )

        self.suggestLabel.grid(row = 0, column = 0, columnspan = 4, pady = (smallPadding, 0))

        # Pre-create 4 suggestion buttons
        self.autoButtons = []

        for index in range(4) :
            btn = ctk.CTkButton(
                self.autoFrame,
                text = '',
                font = mediumFont,
                fg_color = accentCol,
                hover_color = accentCol,
                command = lambda i = index : self.selectSuggestion(i)
            )

            btn.grid(row = 1, column = index, padx = bigPadding, pady = bigPadding, sticky = 'we')
            self.autoButtons.append(btn)

    # ---------------- AUTOCOMPLETE LOGIC ---------------- #

    def updateAutocomplete(self, event = None) :
        text = self.searchBar.get().strip()
        self.lastQuery = text

        # Hide immediately if empty
        if not text :
            self.hideAutocomplete()
            return

        # Threaded suggestion fetch
        threading.Thread(
            target = lambda : self.fetchSuggestions(text, self.modeMenu.get()),
            daemon = True
        ).start()

    def fetchSuggestions(self, text, mode) :
        # Ignore outdated threads
        if text != self.lastQuery : return

        # Ask the injected function for suggestions
        suggestions = self.getSuggestions(text, mode)

        # Push UI update to main thread
        self.after(0, lambda : self.showSuggestions(suggestions))

    def showSuggestions(self, suggestions) :
        self.fullSuggestions = suggestions

        if not (self.lastQuery and suggestions) :
            self.hideAutocomplete()
            return

        self.autoFrame.grid()

        for index, btn in enumerate(self.autoButtons) :
            if index < len(suggestions) :
                options = suggestions[index]
                # CASE 2 : Category / Ingredient / Area → item is a string
                buttonText = options
                # CASE 1 : Name mode → item is a meal object
                if isinstance(options, dict) : buttonText = options['strMealShort']

                btn.configure(text = buttonText)
                btn.grid()
            else:
                btn.grid_remove()
    
    def onModeChange(self, newMode):
        text = self.searchBar.get().strip()

        if not text:
            self.hideAutocomplete()
            return

        suggestions = self.getSuggestions(text, newMode)
        self.showSuggestions(suggestions)

    def selectSuggestion(self, index) :
        options = self.fullSuggestions[index]

        # CASE 2 : Category / Ingredient / Area → item is a string
        buttonText = options
        # CASE 1 : Name mode → item is a meal object
        if isinstance(options, dict) : buttonText = options['strMeal']

        self.searchBar.delete(0, 'end')
        self.searchBar.insert(0, buttonText)
        self.hideAutocomplete()

        self.runSearch(buttonText, self.modeMenu.get())
    
    def hideAutocomplete(self) :
        self.autoFrame.grid_remove()

# -------------------------------- MAIN APPLICATION -------------------------------- #

class Application(ctk.CTk) :
    def __init__(self) :
        super().__init__(fg_color = backGroundCol)

        self.geometry('360x360')
        self.after(0, self.wm_state, 'zoomed')
        self.title(f'{applicationName} v{applicationVersion}')

        # Grid config to adapt to layout
        self.grid_rowconfigure(0, weight = 0)
        self.grid_rowconfigure(1, weight = 1)
        self.grid_columnconfigure(0, weight = 1)

        self.api = MealAPI()

        # ---------------- MAIN UI ---------------- #

        header = HeaderUI(self, self.getAutocomplete, self.runSearch)
        header.grid(row = 0, column = 0, sticky = 'nwe')

        header.searchButton.configure(command = lambda : self.runSearch(header.searchBar.get(), header.modeMenu.get()))
        header.searchBar.bind('<Return>', lambda event : self.runSearch(header.searchBar.get(), header.modeMenu.get()))

        self.cardGrid = MainUI(self, 4, 0)
        self.cardGrid.grid(row = 1, column = 0, sticky = 'nsew')

    # ---------------- SEARCH LOGIC ---------------- #

    def runSearch(self, prompt, mode) :
        # Clear grid
        self.cardGrid.clear()
        # Change to loading while waiting
        self.cardGrid.loadLabel.configure(text = f'Loading "{prompt}" by {mode}…')

        threading.Thread(
            target = lambda : self.searchThread(prompt, mode),
            daemon = True
        ).start()

    def searchThread(self, prompt, mode) :
        # Process Raw API prompt
        raw = self.api.searchMeals(mode.lower(), prompt.lower())
        meals = self.api.processMeals(raw)

        # Temp image for all the cards as it loads
        tempImg = ctk.CTkImage(Image.new('RGB', imageSmall, 'gray'), size = imageSmall)

        # Update loading label if none found
        if not meals :
            self.after(0, lambda: self.cardGrid.loadLabel.configure(text = "No results found"))
            return

        # Update loading label if results found
        self.cardGrid.loadLabel.configure(text = f'Recipes for "{prompt}" by {mode}')

        # Add in the cards
        for meal in meals :
            card = CardUI(self.cardGrid, meal, tempImg, self.api)
            self.cardGrid.addCard(card)

    def getAutocomplete(self, text, mode):
        mode = mode.lower()

        if mode in ['category', 'ingredient', 'area'] :
            options = self.api.listOptions(mode)
            return [item for item in options if text.lower() in item.lower()][:4]

        if mode == 'name' :
            raw = self.api.searchMeals('name', text)
            meals = self.api.processMeals(raw)
            return meals[:4]

        return []

Application().mainloop()