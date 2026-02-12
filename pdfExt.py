
from fpdf import FPDF
from PIL import Image
import os
from typing import Tuple, Optional


class PDF(FPDF):
    """
    Improved PDF helper for 'Bærekraftsrapportering'.
    - Auto-centers the title using page width.
    - Uses margins from FPDF (no hard-coded 210mm).
    - Robust image scaling with aspect-ratio preserved.
    - Returns actual drawn image height for layout chaining.
    - Safer color handling and consistent units.
    - Optional Unicode TTF font registration for full glyph support.
    """

    def __init__(self, title: str = "Bærekraftsrapportering", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title_text = title

        # Set default metadata & margins
        self.set_auto_page_break(auto=True, margin=15)

        # Core font with ISO-Latin-1 (works for most Norwegian text)
        self.set_font("helvetica", size=12)

        # If you want full Unicode support, register a TTF once:
        # self.add_font("DejaVu", "", "DejaVuSans.ttf", uni=True)
        # self.add_font("DejaVu", "B", "DejaVuSans-Bold.ttf", uni=True)
        # self.set_font("DejaVu", size=12)

    # ---------------------------
    # Header / Footer
    # ---------------------------
    def header(self):
        # Logo (if available)
        logo_path = "fhf_logo2024_finansiert_positiv.png"
        if os.path.exists(logo_path):
            # fixed width; height auto-calculated
            self.image(logo_path, x=self.l_margin, y=8, w=33)

        # Title
        self.set_font("helvetica", "B", 15)
        title_w = self.get_string_width(self.title_text) + 6
        # Center using page width and margins (self.w is total width)
        page_w = self.w
        self.set_x((page_w - title_w) / 2)
        self.set_draw_color(0, 0, 0)
        self.set_line_width(0.5)
        self.cell(title_w, 9, self.title_text, border=0, ln=1, align="C")

        # Divider line (from left margin to right margin)
        y = self.get_y() + 1
        self.line(self.l_margin, y, page_w - self.r_margin, y)
        self.ln(10)

    def footer(self):
        # Position at 1.5 cm from bottom
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.set_text_color(128)
        self.cell(0, 10, f"Side {self.page_no()}", 0, 0, "C")

    # ---------------------------
    # Image Helpers
    # ---------------------------
    def _scaled_image_height(self, img_path: str, target_w_mm: float) -> Optional[float]:
        """
        Compute the height (mm) after scaling to target width while maintaining aspect ratio.
        Returns None if image not found or cannot be open.
        """
        try:
            with Image.open(img_path) as im:
                width_px, height_px = im.size
                # DPI-independent ratio via pixels:height/width * target width
                return target_w_mm * (height_px / float(width_px))
        except Exception:
            return None

    def _place_image(self, img_path: str, x: float, y: float, w: float) -> Optional[float]:
        """
        Place an image at (x, y) with width w (mm).
        Height is auto-calculated; returns the drawn height or None on failure.
        """
        h = self._scaled_image_height(img_path, w)
        if h is None:
            # Draw a placeholder box with a warning
            self.set_xy(x, y)
            self.set_draw_color(200, 0, 0)
            self.set_line_width(0.2)
            self.set_font("helvetica", "", 9)
            placeholder = f"[Mangler bilde: {os.path.basename(img_path)}]"
            # Draw a 40mm tall box as placeholder
            self.multi_cell(w, 5, placeholder, border=1, align="C")
            return None

        self.image(img_path, x=x, y=y, w=w, h=0)  # h=0 keeps aspect ratio
        return h

    # ---------------------------
    # Public Image Blocks
    # ---------------------------
    def printImage(self, orgIm: str) -> float:
        """
        Add a page and draw a single large image under the header.
        Returns the drawn height in mm (or an estimated 40mm if missing).
        """
        self.add_page()
        content_w = self.w - self.l_margin - self.r_margin
        top_y = 25  # below header baseline

        h = self._place_image(orgIm, x=self.l_margin, y=top_y, w=content_w)
        return h if h is not None else 40.0

    def printImage2(self, orgIm: str, boxIm: str) -> float:
        """
        Add a page and draw two images side-by-side (equal width).
        Returns the max drawn height of the two images (or 40mm if both missing).
        """
        self.add_page()
        content_w = self.w - self.l_margin - self.r_margin
        col_w = (content_w - 5) / 2.0  # 5mm gap between columns
        top_y = 25

        h1 = self._place_image(orgIm, x=self.l_margin, y=top_y, w=col_w)
        h2 = self._place_image(boxIm, x=self.l_margin + col_w + 5, y=top_y, w=col_w)

        heights = [h for h in (h1, h2) if h is not None]
        return max(heights) if heights else 40.0

    def printImage3(self, orgIm: str, boxIm: str, segIm: str) -> float:
        """
        Add a page and draw two images side-by-side plus a third centered below them.
        Returns total height used (top block height + third image height), or a fallback.
        """
        self.add_page()
        content_w = self.w - self.l_margin - self.r_margin
        col_w = (content_w - 5) / 2.0
        top_y = 25

        h1 = self._place_image(orgIm, x=self.l_margin, y=top_y, w=col_w)
        h2 = self._place_image(boxIm, x=self.l_margin + col_w + 5, y=top_y, w=col_w)
        top_block_h = max([h for h in (h1, h2) if h is not None] or [40.0])

        # Third image, centered under the two
        third_top = top_y + top_block_h + 5
        third_w = content_w / 2.0
        third_x = self.l_margin + (content_w - third_w) / 2.0
        h3 = self._place_image(segIm, x=third_x, y=third_top, w=third_w)

        return top_block_h + (h3 if h3 is not None else 40.0)

    # ---------------------------
    # Table-like Headline & Rows
    # ---------------------------
    def printHeadLine(self, h1: str, h2: str, h3: str, h4: str, h5: str, h6: str):
        """
        Prints a 6-column headline with a line beneath it.
        Column widths adapt to margins/page width.
        """
        self.set_font("helvetica", "B", 10)
        content_w = self.w - self.l_margin - self.r_margin
        col_w = content_w / 6.0

        self.set_x(self.l_margin)
        for i, text in enumerate((h1, h2, h3, h4, h5, h6)):
            align = "L" if i == 0 else "C"
            self.cell(col_w, 0, text, border=0, ln=0, align=align)

        # Baseline + divider line
        y = self.get_y() + 3
        self.line(self.l_margin, y, self.w - self.r_margin, y)
        self.ln(6)

    def printObjectLine(self, o1: str, o2: str, o3: str, o4: str, o5: str, o6: str,
                        color: Tuple[int, int, int]):
        """
        Prints a 6-column row and a small colored rectangle next to the first column.
        'color' must be (r, g, b) in 0..255.
        """
        self.ln(1)
        self.set_font("helvetica", "", 8)
        r, g, b = color
        content_w = self.w - self.l_margin - self.r_margin
        col_w = content_w / 6.0
        row_h = 5

        # column bg
        self.set_fill_color(230, 230, 230)
        self.set_draw_color(0, 0, 0)
        self.set_line_width(0.3)

        # place first column
        self.set_x(self.l_margin)
        self.cell(col_w, row_h, o1, border=0, ln=0, align="L", fill=True)

        # draw a small color swatch rectangle next to first col text
        swatch_x = self.l_margin + 10  # small offset inside first col
        swatch_y = self.get_y() + 1
        self.set_fill_color(r, g, b)
        self.rect(swatch_x, swatch_y, 7, row_h - 2, style="F")

        # reset grey fill for remaining columns
        self.set_fill_color(230, 230, 230)
        for val in (o2, o3, o4, o5, o6):
            self.cell(col_w, row_h, val, border=0, ln=0, align="C", fill=True)
        self.ln(row_h)
