class Course:
    """Active Courses in the academic year

        Args:
            name
            href
    """
    def __init__(self, name, href):
        self.name = name
        self.href = href

    def __str__(self):
        return self.name