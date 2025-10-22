"""
Style definitions for BlueGenomics (placeholder for UI/display styling)
"""

# Color definitions used in notebooks
DARK_PURPLE = "#281741"
PURPLE = "#8D63CE"
MINT = "#51E5B4"
BLUE = "#5DCAD9"
YELLOW = "#FFC431"
ORANGE = "#F78E54"
RED = "#DC536C"
GREY_200 = "#ECEAEF"
GREY_300 = "#9A94A8"


class PlotColors:
    """Color maps and palettes for plotting"""

    def __init__(self):
        self.cmap = [
            ORANGE,
            PURPLE,
            RED,
            BLUE,
            DARK_PURPLE,
            MINT,
            YELLOW,
            "#1C5D99",
            "#639FAB",
            "#BBCDE5",
        ]

        self.dark_purple = DARK_PURPLE
        self.purple = PURPLE
        self.mint = MINT
        self.blue = BLUE
        self.yellow = YELLOW
        self.orange = ORANGE
        self.red = RED
        self.grey_200 = GREY_200
        self.grey_300 = GREY_300
