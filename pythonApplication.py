# -------------------------------- Imports -------------------------------- #

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

# -------------------------------- Styling -------------------------------- #

applicationName = "MEALY DISPLAYINATOR 3000"
applicationVersion = 2.0

smallPadding = 8
bigPadding = 16

smallFont = ("JetBrains Mono", 16)
mediumFont = ("JetBrains Mono", 20)
bigFont = ("JetBrains Mono", 24)

# -------------------------------- API LAYER — Main API -------------------------------- #

class MealAPI :
    def __init__(self) :
        self.url = "https://www.themealdb.com/api/json/v1/1"

    def search(self, mode, prompt) :
        routes = {
            "name" : "search.php?s",
            "category" : "filter.php?c",
            "ingredient" : "filter.php?i",
            "area" : "filter.php?a",
            "id" : "lookup.php?i"
        }

        try :
            response = requests.get(f"{self.url}/{routes[mode]}={prompt}")
            if response.status_code == 200 : return response.json()
        except Exception as exception :
            print("API error :", exception)

        return None

# -------------------------------- REPOSITORY LAYER - Manages API data -------------------------------- #

class MealRepo :
    def __init__(self, api : MealAPI) :
        self.api = api

    def searchMeals(self, mode, prompt) :
        data = self.api.search(mode, prompt)

        if not (data and data.get("meals")) : return []

        meals = []

        for meal in data["meals"] :
            meal["previewThumb"] = meal["strMealThumb"] + "/preview" if meal["strMealThumb"] else None
            meals.append(meal)

        return meals

    def extractIngredients(self, meal) :
        ingredients = []

        for index in range(1, 21) :
            ingredient = meal.get(f"strIngredient{index}")
            measure = meal.get(f"strMeasure{index}")

            if ingredient and ingredient.strip() : ingredients.append(f"{ingredient} - {measure}")

        return ingredients

# -------------------------------- UI LAYER — Card Factory (creates card widgets only) -------------------------------- #

class CardUI :
    def __init__(self, app) :
        self.app = app
        self.images = []
        self.cache = {}  # Cache for downloaded images
        self.tempImg = ctk.CTkImage(Image.new("RGB", (250, 250), "gray"), size = (250, 250))

    def loadImageAsync(self, url, label) :
        # If cached, use immediately
        if url in self.cache :
            label.configure(image = self.cache[url])
            return

        def task() :
            try :
                response = requests.get(url)
                imgPIL = Image.open(BytesIO(response.content))
                imgTK = ctk.CTkImage(imgPIL, size = (250, 250))

                # Cache it
                self.cache[url] = imgTK
                self.images.append(imgTK)

                # Update UI safely
                label.after(0, lambda : label.configure(image = imgTK))

            except Exception as exception :
                print("Failed to load image :", url, exception)

        threading.Thread(target = task, daemon = True).start()

    def createCard(self, parent, meal) :
        card = ctk.CTkFrame(parent)

        imgLabel = ctk.CTkLabel(card, image = self.tempImg, text = "")
        imgLabel.pack(pady = smallPadding)

        # Async image loading
        if meal["previewThumb"] :
            self.loadImageAsync(meal["previewThumb"], imgLabel)

        ctk.CTkLabel(
            card,
            text = meal["strMeal"],
            font = bigFont,
            wraplength = 250
        ).pack()

        ctk.CTkLabel(
            card,
            text = f"Meal ID : {meal['idMeal']}",
            font = smallFont,
            wraplength = 250
        ).pack()

        card.bind("<Button-1>", lambda event : self.app.openRecipe(meal))
        imgLabel.bind("<Button-1>", lambda event : self.app.openRecipe(meal))

        return card

# -------------------------------- UI LAYER — Card Grid (layout only) -------------------------------- #

class CardGridUI :
    def __init__(self, parent, maxColumns = 4, indexOffset = 0) :
        self.parent = parent
        self.maxColumns = maxColumns
        self.indexOffset = indexOffset
        self.cards = []

        for col in range(maxColumns) : self.parent.grid_columnconfigure(col, weight = 1)

    def clear(self) :
        for card in self.cards : card.destroy()
        self.cards.clear()

    def addCard(self, card) :
        index = len(self.cards) + self.indexOffset
        row = index // self.maxColumns
        col = index % self.maxColumns

        card.grid(row = row, column = col, padx = smallPadding, pady = smallPadding)
        self.cards.append(card)

# -------------------------------- UI LAYER — Recipe Window -------------------------------- #

class RecipeUI(ctk.CTkToplevel) :
    def __init__(self, meal, repo : MealRepo) :
        super().__init__()

        self.title(meal["strMeal"])
        self.geometry("1100x800")
        self.grab_set()

        self.grid_rowconfigure(0, weight = 1)
        self.grid_columnconfigure(0, weight = 1)
        self.grid_columnconfigure(1, weight = 1)

        # Main frame
        mainFrame = ctk.CTkScrollableFrame(self)
        mainFrame.grid(row = 0, column = 0, sticky = "nsew", padx = bigPadding, pady = bigPadding)
        mainFrame.grid_columnconfigure(0, weight = 1)

        # Placeholder image
        self.tempImg = ctk.CTkImage(Image.new("RGB", (450, 450), "gray"), size = (450, 450))

        ctk.CTkLabel(
            mainFrame,
            text = meal["strMeal"],
            font = bigFont
        ).grid(row = 0, column = 0, pady = smallPadding)

        # Image placeholder
        self.img_label = ctk.CTkLabel(mainFrame, image = self.tempImg, text = "")
        self.img_label.grid(row = 1, column = 0, pady = smallPadding)

        # Load image asynchronously
        if meal["strMealThumb"] :
            threading.Thread(
                target = self.loadImageAsync,
                args = (meal["strMealThumb"],),
                daemon = True
            ).start()

        # Ingredients
        ingredients = repo.extractIngredients(meal)
        if ingredients :
            ctk.CTkLabel(
                mainFrame,
                text = "Ingredients",
                font = mediumFont
            ).grid(row = 2, column = 0, pady = smallPadding)

            for index, item in enumerate(ingredients) :
                ctk.CTkLabel(
                    mainFrame,
                    text = item,
                    font = smallFont,
                    anchor = "w",
                    justify = "left"
                ).grid(row = 3 + index, column = 0, sticky = "w", padx = smallPadding)

        # Instructions frame
        instructionFrame = ctk.CTkScrollableFrame(self, width = 400)
        instructionFrame.grid(row = 0, column = 1, sticky = "nsew", padx = bigPadding, pady = bigPadding)
        instructionFrame.grid_columnconfigure(0, weight = 1)

        ctk.CTkLabel(
            instructionFrame,
            text = "Instructions",
            font = mediumFont
        ).grid(row = 0, column = 0, pady = smallPadding)

        # Instructions placeholder
        self.instructions_label = ctk.CTkLabel(
            instructionFrame,
            text = meal["strInstructions"],
            font = smallFont,
            wraplength = 500,
            justify = "left"
        )

        self.instructions_label.grid(row = 1, column = 0, pady = smallPadding, sticky = "nw")

        # YouTube button
        if meal.get("strYoutube") :
            ctk.CTkButton(
                self,
                text = "Watch Tutorial on YouTube",
                font = mediumFont,
                command = lambda : webbrowser.open(meal["strYoutube"])
            ).grid(row = 1, column = 0, pady = bigPadding)

        # Close button
        ctk.CTkButton(
            self,
            text = "Close",
            font = mediumFont,
            command = self.destroy
        ).grid(row = 1, column = 1, pady = bigPadding)

    # ---------------- Async loaders ---------------- #

    def loadImageAsync(self, url) :
        try :
            response = requests.get(url)

            imgPIL = Image.open(BytesIO(response.content))
            imgTK = ctk.CTkImage(imgPIL, size = (450, 450))

            self.after(0, lambda : self.updateImage(imgTK))
        except Exception as exception :
            print("Failed to load recipe image :", exception)

    def updateImage(self, imgTK) :
        self.img_ref = imgTK
        self.img_label.configure(image = imgTK, text = "")

# -------------------------------- APPLICATION CONTROLLER - Main application -------------------------------- #

class Application(ctk.CTk) :
    def __init__(self) :
        super().__init__()

        self.geometry("360x360")
        self.after(1, self.wm_state, "zoomed")

        self.grid_rowconfigure(0, weight = 0)
        self.grid_rowconfigure(1, weight = 1)
        self.grid_columnconfigure(0, weight = 1)
        self.title(f"{applicationName} v{applicationVersion}")

        self.api = MealAPI()
        self.repo = MealRepo(self.api)
        self.factory = CardUI(self)

        self.buildUI()

        self.runSearch("Seafood", "name")

    # ---------------- UI ---------------- #

    def buildUI(self) :
        header = ctk.CTkFrame(self)
        header.grid(row = 0, column = 0, sticky = "nwe")
        header.grid_columnconfigure(0, weight = 1)

        ctk.CTkLabel(
            header,
            text = applicationName,
            font = bigFont
        ).grid(row = 0, column = 0, padx = bigPadding, pady = bigPadding, sticky = "nsw")

        modeMenu = ctk.CTkOptionMenu(
            header,
            values = ["name", "category", "ingredient", "area", "id"],
            font = mediumFont,
            dropdown_font = mediumFont
        )

        modeMenu.grid(row = 0, column = 2, padx = bigPadding, pady = bigPadding, sticky = "nse")

        searchBar = ctk.CTkEntry(
            header,
            placeholder_text = "Search...",
            font = bigFont
        )

        searchBar.grid(row = 0, column = 4, padx = bigPadding, pady = bigPadding, sticky = "nse")

        searchPrompt = lambda : self.runSearch(searchBar.get(), modeMenu.get())
        searchBar.bind("<Return>", lambda event : searchPrompt())

        ctk.CTkButton(
            header,
            text = "🔍",
            font = bigFont,
            command = searchPrompt
        ).grid(row = 0, column = 3, padx = bigPadding, pady = bigPadding, sticky = "e")

        main = ctk.CTkScrollableFrame(self)
        main.grid(row = 1, column = 0, sticky = "nsew")

        ctk.CTkLabel(
            main,
            text = "Recipes",
            font = bigFont
        ).grid(row = 0, column = 0, columnspan = 4, padx = smallPadding, pady = smallPadding)

        self.cardGrid = CardGridUI(main, 4, 4)

    # ---------------- Search Logic ---------------- #

    def runSearch(self, prompt, mode) :
        self.cardGrid.clear()
        threading.Thread(
            target = self._searchThread,
            args = (prompt, mode),
            daemon = True
        ).start()

    def _searchThread(self, prompt, mode) :
        meals = self.repo.searchMeals(mode, prompt)

        for meal in meals :
            card = self.factory.createCard(self.cardGrid.parent, meal)
            self.cardGrid.addCard(card)

    # ---------------- Recipe Window ---------------- #

    def openRecipe(self, meal) :
        full = self.api.search("id", meal["idMeal"])

        if full and full.get("meals") : meal = full["meals"][0]

        RecipeUI(meal, self.repo)

# Run Application
Application().mainloop()