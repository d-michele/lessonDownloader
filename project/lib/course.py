class Course:

    """Active Courses in the academic year

        Args:
            name
            href
            start_download
            end_download
    """
    def __init__(self, name, href=""):
        self.name = name
        self.href = href
        start_download = None
        end_download = None

    def __str__(self):
        return self.name

    @property
    def start_download(self):
        return self.start_download

    @start_download.setter
    def set_start_download(start):
        start_download = start

    @property
    def end_download(self):
        return self.end_download

    @start_download.setter
    def set_end_download(start):
        end_download = end

