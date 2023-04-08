import json
class Category:

    def __init__(self):
        self.category = None
        file = open('CategoriesList.json')
        cat_list = json.load(file)

    def set_category(self, category):
        self.category = category



def create_spend_chart():
    pass