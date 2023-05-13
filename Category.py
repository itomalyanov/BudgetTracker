import json
import pandas as pd


class Category:
    """
    Separate class for categories. Still not sure why it has been created.

    On a new instance it's reading the categories.csv files and loads the existing categories to a list.
    New categories must be loaded for each new file with expenses.
    """

    def __init__(self):
        with open('categories.csv', 'r') as file:
            self.categories = pd.DataFrame(data=file, header=True)

        self.new_categories = []

    def compare_existing(self, from_import, auto_import = 0):
        """
        Function to compare the existing categories (already in categories.csv file) with the ones used in the imported file.
        If there are new categories found add them to a series object to append to the file.
        :param auto_import:
        :param from_import:
        :return:
        """
        set_import = set(from_import)
        set_existing = set(self.categories['name'])

        if set_import.issubset(set_existing):
            print("it's fine")
        else:
            self.new_categories = (set_import - set_existing)
            print("new categories has to be added")
            if auto_import == 1:
                for category in self.new_categories:
                    print(f"Import new category {category}")

        pass

    def add_category(self, name: str, description: str = None, parent: int = None):
        """
        Accept pandas dataframe row.
        Validate if the minimum required data is present.
        Check for duplicates, and add the new category to the file
        :param description:
        :type name: object
        :param parent:
        :param name:
        :return:
        """
        pass

    def edit_category(self):
        pass

    def save_category(self):
        pass

    def delete_category(self):
        pass


def create_spend_chart():
    pass
