class Category:
    """
    Separate class for categories. Still not sure why it has been created.
    """

    def __init__(self):
        self.category = None

    def set_category(self, category):
        self.category = category

    def check_existing_category(self):
        """
        Check if provided category already exist! If the category does not exist in the list It's calling
        the set_category method of the Category class.
        :return:  Does not return anything
        """
        pass


def create_spend_chart():
    pass