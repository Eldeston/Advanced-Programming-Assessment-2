# Advanced Programming - Assessment 2

# Abstract
This project is a recipe viewer application using “TheMealDB” API. My application fetches user search queries from TheMealDB’s database to be used to display the recipes the user wants to view.

# Project Planning
The project plan goes as follows in their respective order:
- Make an API class with necessary functions/methods to fetch data
- Make a base user interface in web application style:
    - A header widget to contain the application name & search widgets
    - A main widget to contain all the clickable recipe cards
    - A separate window to display the recipe’s ingredients & instructions
- Make a backend for the application’s features and connect it to the API

The application should also run with optimizations in mind by running the API and backend code in the background. This will be explained further in later sections.
# Evidence of Design

## Application Wireframe


## UML Data Structure

```mermaid
classDiagram
    class MealAPI {
        - url: str
        + request(mode, prompt)
        + searchMeals(mode, prompt)
        + truncate(text, maxChars)
        + processMeals(meals)
        + listOptions(mode)
    }

    class CardUI {
        - api: MealAPI
        - mealData: dict
        - imgLabel
        + openFullRecipe()
        + loadImageAsync(url)
    }

    class MainUI {
        - maxColumns: int
        - indexOffset: int
        - cards: list
        - loadLabel
        + clear()
        + addCard(card)
    }

    class RecipeUI {
        - tempImg
        - imgLabel
        - instructions_label
        + loadImageAsync(url)
    }

    class HeaderUI {
        - fullSuggestions: list
        - lastQuery: str
        - getSuggestions: fn
        - runSearch: fn
        - autoButtons: list
        + updateAutocomplete()
        + fetchSuggestions(text, mode)
        + showSuggestions(list)
        + onModeChange(mode)
        + selectSuggestion(index)
        + hideAutocomplete()
    }

    class Application {
        - api: MealAPI
        - cardGrid: MainUI
        + runSearch(prompt, mode)
        + searchThread(prompt, mode)
        + getAutocomplete(text, mode)
    }

    %% Relationships
    Application --> MealAPI : uses
    Application --> HeaderUI : contains
    Application --> MainUI : contains

    MainUI --> CardUI : aggregates
    CardUI --> MealAPI : uses
    CardUI --> RecipeUI : creates
```

# Technical Description & Walkthrough