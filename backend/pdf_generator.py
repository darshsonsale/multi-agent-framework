

"""
eFIR PDF Generator
==================
Generates an official NCRB I.I.F.-I (First Information Report) PDF
from a structured JSON file, matching the government form layout exactly.

Usage:
    python efir_generator.py input.json output.pdf

Dependencies:
    pip install reportlab
"""

import json
import sys
import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


# ─────────────────────────────────────────────
# Constants & Layout
# ─────────────────────────────────────────────
PAGE_W, PAGE_H = A4          # 595.28 x 841.89 pts
MARGIN_L = 20 * mm
MARGIN_R = 20 * mm
MARGIN_T = 15 * mm
MARGIN_B = 15 * mm
CONTENT_W = PAGE_W - MARGIN_L - MARGIN_R

HEADER_FONT = "Helvetica-Bold"
BODY_FONT   = "Helvetica"
SMALL       = 9
NORMAL      = 10
MEDIUM      = 11
LARGE       = 12
XLARGE      = 14
TITLE_SIZE  = 16

LINE_COLOR  = colors.black
BOX_COLOR   = colors.white

def pt(mm_val):
    return mm_val * mm


def safe(val, default="---"):
    """Return val if truthy, else default placeholder."""
    if val is None:
        return default
    s = str(val).strip()
    return s if s else default


# ─────────────────────────────────────────────
# Canvas helpers
# ─────────────────────────────────────────────
class FIRCanvas:
    def __init__(self, path):
        self.c = canvas.Canvas(path, pagesize=A4)
        self.c.setTitle("First Information Report - NCRB I.I.F.-I")
        self.c.setAuthor("eFIR System")
        self.page = 1
        self._y = PAGE_H - MARGIN_T  # current Y cursor (top-down)

    # ── drawing primitives ──────────────────
    def line(self, x1, y1, x2, y2, width=0.5):
        self.c.setLineWidth(width)
        self.c.line(x1, y1, x2, y2)

    def rect(self, x, y, w, h, fill=0, stroke=1):
        self.c.setLineWidth(0.5)
        self.c.rect(x, y, w, h, fill=fill, stroke=stroke)

    def bold(self, x, y, text, size=NORMAL, align="left"):
        self.c.setFont(HEADER_FONT, size)
        if align == "center":
            self.c.drawCentredString(x, y, text)
        elif align == "right":
            self.c.drawRightString(x, y, text)
        else:
            self.c.drawString(x, y, text)

    def text(self, x, y, txt, size=NORMAL, align="left"):
        self.c.setFont(BODY_FONT, size)
        if align == "center":
            self.c.drawCentredString(x, y, txt)
        elif align == "right":
            self.c.drawRightString(x, y, txt)
        else:
            self.c.drawString(x, y, txt)

    def label_value(self, x, y, label, value, label_size=SMALL, value_size=NORMAL, gap=2*mm):
        """Draw 'Label: Value' pair."""
        self.c.setFont(HEADER_FONT, label_size)
        self.c.drawString(x, y, label)
        lw = self.c.stringWidth(label, HEADER_FONT, label_size)
        self.c.setFont(BODY_FONT, value_size)
        self.c.drawString(x + lw + gap, y, value)

    def hline(self, y, x1=None, x2=None, width=0.5):
        x1 = x1 or MARGIN_L
        x2 = x2 or (PAGE_W - MARGIN_R)
        self.line(x1, y, x2, y, width)

    def wrapped_text(self, x, y, txt, max_width, size=NORMAL, leading=11):
        """Draw text with word-wrap; returns final y after drawing."""
        self.c.setFont(BODY_FONT, size)
        
        # Split into explicit lines first to handle '\n'
        raw_lines = txt.splitlines()
        if not raw_lines:
            return y
            
        cur_y = y
        for raw_line in raw_lines:
            words = raw_line.split()
            if not words:
                # Empty line preservations
                cur_y -= leading
                continue
                
            line_words = []
            for word in words:
                test_str = " ".join(line_words + [word])
                if self.c.stringWidth(test_str, BODY_FONT, size) <= max_width:
                    line_words.append(word)
                else:
                    if line_words:
                        self.c.drawString(x, cur_y, " ".join(line_words))
                        cur_y -= leading
                        line_words = [word]
                    else:
                        # Single word too long for max_width - force it
                        self.c.drawString(x, cur_y, word)
                        cur_y -= leading
                        line_words = []
            
            if line_words:
                self.c.drawString(x, cur_y, " ".join(line_words))
                cur_y -= leading
                
        return cur_y

    def calc_text_lines(self, txt, max_width, size=NORMAL):
        """Estimate number of lines needed for wrapping."""
        self.c.setFont(BODY_FONT, size)
        raw_lines = txt.splitlines()
        total_lines = 0
        
        for raw_line in raw_lines:
            words = raw_line.split()
            if not words:
                total_lines += 1
                continue
                
            line_words = []
            line_count = 1
            for word in words:
                test_str = " ".join(line_words + [word])
                if self.c.stringWidth(test_str, BODY_FONT, size) <= max_width:
                    line_words.append(word)
                else:
                    line_count += 1
                    line_words = [word]
            total_lines += line_count
            
        return max(1, total_lines)

    def new_page(self):
        self.c.showPage()
        self.page += 1
        # Draw NCRB header on every page
        self._draw_page_header()

    def save(self):
        self.c.save()

    # ── page header (appears on every page) ─
    def _draw_page_header(self):
        y = PAGE_H - 10*mm
        self.bold(PAGE_W - MARGIN_R, y, "N.C.R.B ", SMALL, "right")
        y -= 4*mm
        self.bold(PAGE_W - MARGIN_R, y, "I.I.F.-I ", SMALL, "right")


# ─────────────────────────────────────────────
# Address formatter
# ─────────────────────────────────────────────
def format_address(addr: dict) -> str:
    parts = [
        safe(addr.get("houseNo")),
        safe(addr.get("streetName")),
        safe(addr.get("colony")),
        safe(addr.get("village")),
        safe(addr.get("tehsil")),
        safe(addr.get("district")),
        safe(addr.get("state")),
        safe(addr.get("country")),
        safe(addr.get("policeStation")),
        safe(addr.get("pincode")),
    ]
    return ", ".join(p for p in parts if p)


# ─────────────────────────────────────────────
# PAGE 1 builder
# ─────────────────────────────────────────────
def build_page1(fc: FIRCanvas, data: dict):
    c = fc.c

    # ── NCRB top-right header ───────────────
    y_top = PAGE_H - 10*mm
    fc.bold(PAGE_W - MARGIN_R, y_top, "N.C.R.B ", SMALL, "right")
    fc.bold(PAGE_W - MARGIN_R, y_top - 4*mm, "I.I.F.-I ", SMALL, "right")

    # ── Title block ─────────────────────────
    ty = PAGE_H - 22*mm
    fc.bold(PAGE_W / 2, ty, "FIRST INFORMATION REPORT", XLARGE, "center")
    ty -= 5*mm
    fc.text(PAGE_W / 2, ty, "(Under Section 173 B.N.S.S)", SMALL, "center")

    # ── Row 1: District | FIR No | Year | Date & Time of FIR ────
    meta = data.get("complaintSubmissionDetails", {})
    complaint = data.get("complaintDetail", {})
    incident = data.get("incidentDetail", {})

    row1_y = ty - 8*mm
    fc.hline(row1_y + 5*mm)

    district = safe(meta.get("district"), "___________")
    ps       = safe(meta.get("policeStation"), "___________")
    fir_date = safe(complaint.get("dateOfComplaint"), datetime.today().strftime("%d/%m/%Y %H:%M"))

    fc.bold(MARGIN_L, row1_y, "1. District :", SMALL)
    fc.text(MARGIN_L + 38*mm, row1_y, district, NORMAL)
    fc.bold(PAGE_W/2, row1_y, "P.S. :", SMALL)
    fc.text(PAGE_W/2 + 22*mm, row1_y, ps, NORMAL)

    row1_y -= 5*mm
    fc.bold(MARGIN_L, row1_y, "FIR No. :", SMALL)
    fc.bold(PAGE_W/2, row1_y, "Year :", SMALL)
    fc.text(PAGE_W/2 + 22*mm, row1_y, datetime.today().strftime("%Y"), NORMAL)

    row1_y -= 5*mm
    fc.bold(MARGIN_L, row1_y, "Date and Time of FIR :", SMALL)
    fc.text(MARGIN_L + 70*mm, row1_y, fir_date, NORMAL)

    fc.hline(row1_y - 2*mm)

    # ── Section 2: Acts & Sections ──────────
    s2_y = row1_y - 8*mm
    fc.bold(MARGIN_L, s2_y, "2.", NORMAL)
    col_sno  = MARGIN_L + 6*mm
    col_acts = MARGIN_L + 18*mm
    col_sec  = MARGIN_L + 100*mm

    fc.bold(col_sno,  s2_y, "S.No. ", SMALL)
    fc.bold(col_acts, s2_y, "Acts ", SMALL)
    fc.bold(col_sec,  s2_y, "Sections ", SMALL)
    s2_y -= 4*mm
    fc.hline(s2_y + 3*mm, MARGIN_L, PAGE_W - MARGIN_R)
    
    act_str = safe(incident.get("typeOfIncident"), "")
    act_w = col_sec - col_acts - 2*mm
    lines_act = fc.calc_text_lines(act_str, act_w, NORMAL)
    act_row_h = max(8*mm, lines_act * 11 + 4*mm)
    
    # Draw a sample row border
    fc.rect(MARGIN_L, s2_y - act_row_h + 2*mm, CONTENT_W, act_row_h)
    fc.text(col_sno,  s2_y - 3*mm, "1", NORMAL)
    fc.wrapped_text(col_acts, s2_y - 3*mm, act_str, act_w, NORMAL, leading=11)
    s2_y -= act_row_h
    fc.hline(s2_y)

    # ── Section 3: Occurrence of offence ────
    s3_y = s2_y - 6*mm
    date_from = safe(incident.get("incidentDate"), "")
    date_to   = safe(incident.get("incidentDate"), "")
    time_of   = safe(incident.get("incidentTime"), "")

    fc.bold(MARGIN_L, s3_y, "3. (a) Occurrence of offence :", SMALL)
    s3_y -= 5*mm

    # Two-column: left = day/period, right = dates
    fc.bold(MARGIN_L + 4*mm, s3_y, "1. Day :", SMALL)
    fc.bold(PAGE_W/2, s3_y, "Date From :", SMALL)
    fc.text(PAGE_W/2 + 48*mm, s3_y, date_from, NORMAL)

    s3_y -= 5*mm
    fc.bold(MARGIN_L + 4*mm, s3_y, "Time Period:", SMALL)
    fc.bold(PAGE_W/2, s3_y, "Date To :", SMALL)
    fc.text(PAGE_W/2 + 48*mm, s3_y, date_to, NORMAL)

    s3_y -= 5*mm
    fc.bold(PAGE_W/2, s3_y, "Time From :", SMALL)
    fc.text(PAGE_W/2 + 48*mm, s3_y, time_of, NORMAL)

    s3_y -= 5*mm
    fc.bold(PAGE_W/2, s3_y, "Time To :", SMALL)

    s3_y -= 5*mm
    fc.bold(MARGIN_L, s3_y, "(b) Information received at P.S. :", SMALL)
    s3_y -= 5*mm
    fc.bold(MARGIN_L + 4*mm, s3_y, "Date :", SMALL)
    fc.bold(PAGE_W/2, s3_y, "Time :", SMALL)

    s3_y -= 5*mm
    fc.bold(MARGIN_L, s3_y, "(c) General Diary Reference :", SMALL)
    s3_y -= 5*mm
    fc.bold(MARGIN_L + 4*mm, s3_y, "Entry No. :", SMALL)
    s3_y -= 5*mm
    fc.bold(MARGIN_L + 4*mm, s3_y, "Date & Time :", SMALL)

    fc.hline(s3_y - 3*mm)

    # ── Section 4: Type of Information ──────
    s4_y = s3_y - 8*mm
    fc.bold(MARGIN_L, s4_y, "4. Type of Information : ", SMALL)
    fc.hline(s4_y - 3*mm)

    # ── Section 5: Place of Occurrence ──────
    s5_y = s4_y - 8*mm
    place = safe(incident.get("placeOfIncident"), "")
    fc.bold(MARGIN_L, s5_y, "5. Place of Occurrence:", SMALL)
    s5_y -= 5*mm
    fc.bold(MARGIN_L + 4*mm, s5_y, "1.(a) Direction and distance from P.S. :", SMALL)
    fc.bold(PAGE_W/2 + 20*mm, s5_y, "Beat No. :", SMALL)
    s5_y -= 5*mm
    fc.bold(MARGIN_L + 4*mm, s5_y, "(b) Address :", SMALL)
    s5_y = fc.wrapped_text(MARGIN_L + 35*mm, s5_y, place, CONTENT_W - 39*mm, NORMAL, leading=11)

    s5_y -= 2*mm
    fc.bold(MARGIN_L, s5_y, "(c) In case, outside the limit of this Police Station, then", SMALL)
    s5_y -= 4*mm
    fc.bold(MARGIN_L + 4*mm, s5_y, "Name of P.S. :", SMALL)
    s5_y -= 4*mm
    fc.bold(MARGIN_L + 4*mm, s5_y, "District (State):", SMALL)

    # ── Page number ─────────────────────────
    fc.text(PAGE_W / 2, MARGIN_B, "1", NORMAL, "center")
    fc.hline(MARGIN_B + 5*mm)


# ─────────────────────────────────────────────
# PAGE 2 builder
# ─────────────────────────────────────────────
def build_page2(fc: FIRCanvas, data: dict):
    c = fc.c
    comp = data.get("complainantDetail", {})
    pi   = comp.get("personalInformation", {})
    addr = comp.get("address", {})
    ident= comp.get("identification", {})
    accused_list = data.get("accusedDetail", [])

    y = PAGE_H - 18*mm

    # ── Section 6: Complainant ───────────────
    fc.bold(MARGIN_L, y, "6. Complainant / Informant :", MEDIUM)
    y -= 6*mm

    name_parts = " ".join(filter(None, [
        safe(pi.get("firstName")),
        safe(pi.get("middleName")),
        safe(pi.get("lastName")),
    ]))
    fc.label_value(MARGIN_L + 4*mm, y, "(a) Name :", name_parts)
    y -= 5*mm

    relative = safe(pi.get("relative_name"), "")
    rel_type = safe(pi.get("relation_type"), "")
    rel_str  = f"{relative} ({rel_type})" if rel_type else relative
    fc.label_value(MARGIN_L + 4*mm, y, "(b) Father's/Husband's Name :", rel_str)
    y -= 5*mm

    dob = safe(pi.get("dateOfBirth"), "")
    fc.label_value(MARGIN_L + 4*mm, y, "(c) Date/Year of Birth :", dob)
    y -= 5*mm

    nationality = safe(ident.get("countryOfNationality"), "")
    fc.label_value(MARGIN_L + 4*mm, y, "(d) Nationality :", nationality)
    y -= 5*mm

    uid = safe(pi.get("uid"), "")
    fc.label_value(MARGIN_L + 4*mm, y, "(e) UID No. (:", uid)
    y -= 5*mm

    fc.bold(MARGIN_L + 4*mm, y, "(f) Passport No. :", SMALL)
    y -= 4*mm
    fc.bold(MARGIN_L + 8*mm, y, "Date of Issue :", SMALL)
    y -= 4*mm
    fc.bold(MARGIN_L + 8*mm, y, "Place of Issue :", SMALL)
    y -= 6*mm

    records = ident.get("records", [])
    if records:
        id_type = safe(records[0].get("type"), "")
        id_num  = safe(records[0].get("number"), "")
    else:
        id_type = ""
        id_num  = ""
    fc.bold(MARGIN_L + 4*mm, y, "(g) ID details (Ration Card, Voter ID Card, Passport, UID No., Driving License, PAN)", SMALL)
    y -= 5*mm
    # ID table header
    col1 = MARGIN_L + 4*mm
    col2 = MARGIN_L + 30*mm
    col3 = MARGIN_L + 90*mm
    fc.rect(col1, y - 5*mm, 26*mm, 8*mm)
    fc.rect(col2, y - 5*mm, 60*mm, 8*mm)
    fc.rect(col3, y - 5*mm, 70*mm, 8*mm)
    fc.bold(col1 + 1*mm, y - 2*mm, "S.No. ", SMALL)
    fc.bold(col2 + 1*mm, y - 2*mm, "ID Type ", SMALL)
    fc.bold(col3 + 1*mm, y - 2*mm, "ID Number ", SMALL)
    y -= 8*mm
    
    lines_id = fc.calc_text_lines(id_type, 58*mm, NORMAL)
    lines_no = fc.calc_text_lines(id_num, 68*mm, NORMAL)
    id_row_h = max(8*mm, max(lines_id, lines_no) * 11 + 4*mm)
    
    fc.rect(col1, y - id_row_h + 3*mm, 26*mm, id_row_h)
    fc.rect(col2, y - id_row_h + 3*mm, 60*mm, id_row_h)
    fc.rect(col3, y - id_row_h + 3*mm, 70*mm, id_row_h)
    fc.text(col1 + 1*mm, y - 2*mm, "1", NORMAL)
    fc.wrapped_text(col2 + 1*mm, y - 2*mm, id_type, 58*mm, NORMAL, leading=11)
    fc.wrapped_text(col3 + 1*mm, y - 2*mm, id_num, 68*mm, NORMAL, leading=11)
    y -= id_row_h + 2*mm

    # Address table
    fc.bold(MARGIN_L + 4*mm, y, "(h) Address :", SMALL)
    y -= 5*mm
    pres_addr  = format_address(addr)
    perm_str = pres_addr

    col_a = MARGIN_L + 4*mm
    col_b = MARGIN_L + 28*mm
    col_c = MARGIN_L + 55*mm
    addr_w = CONTENT_W - 55*mm - 2*mm
    # headers
    fc.rect(col_a, y - 5*mm, 24*mm, 8*mm)
    fc.rect(col_b, y - 5*mm, 27*mm, 8*mm)
    fc.rect(col_c, y - 5*mm, CONTENT_W - 55*mm, 8*mm)
    fc.bold(col_a + 1*mm, y - 2*mm, "S.No.", SMALL)
    fc.bold(col_b + 1*mm, y - 2*mm, "Address Type", SMALL)
    fc.bold(col_c + 1*mm, y - 2*mm, "Address ", SMALL)
    y -= 8*mm
    
    # Present row
    pres_lines = fc.calc_text_lines(pres_addr, addr_w, SMALL)
    pres_row_h = max(8*mm, pres_lines * 10 + 4*mm)
    fc.rect(col_a, y - pres_row_h + 3*mm, 24*mm, pres_row_h)
    fc.rect(col_b, y - pres_row_h + 3*mm, 27*mm, pres_row_h)
    fc.rect(col_c, y - pres_row_h + 3*mm, CONTENT_W - 55*mm, pres_row_h)
    fc.text(col_a + 1*mm, y - 2*mm, "1", NORMAL)
    fc.text(col_b + 1*mm, y - 2*mm, " ", NORMAL)
    fc.wrapped_text(col_c + 1*mm, y - 2*mm, pres_addr, addr_w, SMALL, 10)
    y -= pres_row_h
    
    # Permanent row
    perm_lines = fc.calc_text_lines(perm_str, addr_w, SMALL)
    perm_row_h = max(8*mm, perm_lines * 10 + 4*mm)
    fc.rect(col_a, y - perm_row_h + 3*mm, 24*mm, perm_row_h)
    fc.rect(col_b, y - perm_row_h + 3*mm, 27*mm, perm_row_h)
    fc.rect(col_c, y - perm_row_h + 3*mm, CONTENT_W - 55*mm, perm_row_h)
    fc.text(col_a + 1*mm, y - 2*mm, "2", NORMAL)
    fc.text(col_b + 1*mm, y - 2*mm, "", NORMAL)
    fc.wrapped_text(col_c + 1*mm, y - 2*mm, perm_str, addr_w, SMALL, 10)
    y -= perm_row_h + 2*mm

    fc.label_value(MARGIN_L + 4*mm, y, "(i) Occupation :", "")
    y -= 5*mm
    mobile = safe(pi.get("mobileNo"), "")
    fc.bold(MARGIN_L + 4*mm, y, "(j) Phone number :", SMALL)
    y -= 4*mm
    fc.label_value(MARGIN_L + 8*mm, y, "Mobile :", mobile)
    y -= 8*mm
    fc.hline(y)

    # ── Section 7: Accused ───────────────────
    y -= 6*mm
    fc.bold(MARGIN_L, y, "7. Details of known/suspected/unknown accused with full particulars :", SMALL)
    y -= 5*mm

    # Table header
    col_sno  = MARGIN_L
    col_name = MARGIN_L + 10*mm
    col_alias= MARGIN_L + 50*mm
    col_rel  = MARGIN_L + 80*mm
    col_addr2= MARGIN_L + 115*mm

    fc.rect(col_sno,  y - 5*mm, 10*mm, 8*mm)
    fc.rect(col_name, y - 5*mm, 40*mm, 8*mm)
    fc.rect(col_alias,y - 5*mm, 30*mm, 8*mm)
    fc.rect(col_rel,  y - 5*mm, 35*mm, 8*mm)
    fc.rect(col_addr2,y - 5*mm, PAGE_W - MARGIN_R - col_addr2, 8*mm)
    fc.bold(col_sno  + 1*mm, y - 2*mm, "S.No.", SMALL)
    fc.bold(col_name + 1*mm, y - 2*mm, "Name ", SMALL)
    fc.bold(col_alias+ 1*mm, y - 2*mm, "Alias ", SMALL)
    fc.bold(col_rel  + 1*mm, y - 2*mm, "Relative's Name", SMALL)
    fc.bold(col_addr2+ 1*mm, y - 2*mm, "Present Address ", SMALL)
    y -= 8*mm

    for i, acc in enumerate(accused_list):
        aname = safe(acc.get("name"), "")
        aaddr_str = safe(acc.get("address"), "")
        
        name_w = 40*mm - 2*mm
        addr2_w = PAGE_W - MARGIN_R - col_addr2 - 2*mm
        lines_name = fc.calc_text_lines(aname, name_w, SMALL)
        lines_addr = fc.calc_text_lines(aaddr_str, addr2_w, SMALL)
        row_h = max(10*mm, max(lines_name, lines_addr) * 10 + 4*mm)
        
        fc.rect(col_sno,  y - row_h + 3*mm, 10*mm, row_h)
        fc.rect(col_name, y - row_h + 3*mm, 40*mm, row_h)
        fc.rect(col_alias,y - row_h + 3*mm, 30*mm, row_h)
        fc.rect(col_rel,  y - row_h + 3*mm, 35*mm, row_h)
        fc.rect(col_addr2,y - row_h + 3*mm, PAGE_W - MARGIN_R - col_addr2, row_h)
        
        fc.text(col_sno  + 1*mm, y, str(i + 1), SMALL)
        fc.wrapped_text(col_name + 1*mm, y, aname, name_w, SMALL, leading=10)
        fc.wrapped_text(col_addr2+ 1*mm, y, aaddr_str, addr2_w, SMALL, leading=10)
        y -= row_h + 1*mm

    y -= 5*mm
    fc.hline(y)

    # ── Section 8 & 9 ────────────────────────
    y -= 5*mm
    fc.bold(MARGIN_L, y, "8. Reasons for delay in reporting by the complainant/informant :", SMALL)
    y -= 10*mm
    fc.hline(y)

    y -= 5*mm
    fc.bold(MARGIN_L, y, "9. Particulars of properties of interest :", SMALL)
    y -= 5*mm
    # Property table header
    fc.rect(MARGIN_L, y - 6*mm, 10*mm, 8*mm)
    fc.rect(MARGIN_L + 10*mm, y - 6*mm, 45*mm, 8*mm)
    fc.rect(MARGIN_L + 55*mm, y - 6*mm, 45*mm, 8*mm)
    fc.rect(MARGIN_L + 100*mm, y - 6*mm, 50*mm, 8*mm)
    fc.rect(MARGIN_L + 150*mm, y - 6*mm, CONTENT_W - 150*mm, 8*mm)
    fc.bold(MARGIN_L + 1*mm, y - 3*mm, "S.No.", SMALL)
    fc.bold(MARGIN_L + 11*mm, y - 3*mm, "Property Category", SMALL)
    fc.bold(MARGIN_L + 56*mm, y - 3*mm, "Property Type", SMALL)
    fc.bold(MARGIN_L + 101*mm, y - 3*mm, "Description", SMALL)
    fc.bold(MARGIN_L + 151*mm, y - 3*mm, "Value (Rs/-)", SMALL)
    y -= 14*mm

    # Page number
    fc.text(PAGE_W / 2, MARGIN_B, "2", NORMAL, "center")
    fc.hline(MARGIN_B + 5*mm)


# ─────────────────────────────────────────────
# PAGE 3 builder  (FIR narrative)
# ─────────────────────────────────────────────
def build_page3(fc: FIRCanvas, data: dict):
    c = fc.c
    complaint = data.get("complaintDetail", {})
    incident  = data.get("incidentDetail", {})
    comp      = data.get("complainantDetail", {})
    pi        = comp.get("personalInformation", {})
    addr      = comp.get("address", {})
    meta_sub  = data.get("complaintSubmissionDetails", {})

    y = PAGE_H - 18*mm

    fc.bold(MARGIN_L, y, "10. Total value of property (In Rs/-)", SMALL)
    fc.bold(MARGIN_L + 4*mm, y - 4*mm, " ", SMALL)
    y -= 14*mm
    fc.hline(y)

    y -= 6*mm
    fc.bold(MARGIN_L, y, "11. Inquest Report / U.D. case No., if any", SMALL)
    fc.bold(MARGIN_L + 4*mm, y - 4*mm, " ",SMALL)
    y -= 8*mm
    fc.rect(MARGIN_L, y - 5*mm, 25*mm, 8*mm)
    fc.rect(MARGIN_L + 25*mm, y - 5*mm, 75*mm, 8*mm)
    fc.bold(MARGIN_L + 1*mm, y - 2*mm, "S.No.", SMALL)
    fc.bold(MARGIN_L + 26*mm, y - 2*mm, "UIDB Number ", SMALL)
    y -= 14*mm
    fc.hline(y)

    # ── Section 12: FIR Narrative ────────────
    y -= 6*mm
    fc.bold(MARGIN_L, y, "12. First Information contents :", MEDIUM)
    y -= 5*mm
    fc.bold(MARGIN_L + 4*mm, y, " " ,SMALL)
    y -= 6*mm

    # Jurisdiction header inside complaint
    district = safe(meta_sub.get("district"), "")
    ps       = safe(meta_sub.get("police_station"), "")
    date_c   = safe(complaint.get("dateOfComplaint"), "")
    fc.text(MARGIN_L + 20*mm, y, f"{district}, {district}", NORMAL)
    y -= 5*mm
    fc.text(MARGIN_L + 20*mm, y, f"{date_c}", NORMAL)
    y -= 6*mm

    # Complainant intro line
    name_full = " ".join(filter(None, [
        safe(pi.get("firstName")), safe(pi.get("middleName")), safe(pi.get("lastName"))
    ]))
    dob      = safe(pi.get("dateOfBirth"), "")
    mobile   = safe(pi.get("mobileNo"), "")
    city     = safe(addr.get("village"), "")
    state    = safe(addr.get("state"), "")
    nat      = safe(comp.get("identification", {}).get("countryOfNationality"), "")

    intro = (
        f" {name_full}, {dob},  {mobile} "
        f" {city}, {state}. "
    )
    y = fc.wrapped_text(MARGIN_L + 4*mm, y, intro, CONTENT_W - 8*mm, NORMAL, 12)
    y -= 3*mm

    # Main complaint description
    description = safe(complaint.get("description"), "")
    if description:
        y = fc.wrapped_text(MARGIN_L + 4*mm, y, description, CONTENT_W - 8*mm, NORMAL, 12)
    else:
        # Draw blank lines for manual filling
        for _ in range(8):
            fc.hline(y, MARGIN_L + 4*mm, PAGE_W - MARGIN_R - 4*mm, 0.3)
            y -= 8*mm

    y -= 5*mm
    fc.hline(y)

    # Page number
    fc.text(PAGE_W / 2, MARGIN_B, "3", NORMAL, "center")
    fc.hline(MARGIN_B + 5*mm)


# ─────────────────────────────────────────────
# PAGE 4 – continuation of narrative
# ─────────────────────────────────────────────
def build_page4(fc: FIRCanvas, data: dict):
    c    = fc.c
    comp = data.get("complainantDetail", {})
    pi   = comp.get("personalInformation", {})
    addr = comp.get("address", {})
    complaint = data.get("complaintDetail", {})
    incident  = data.get("incidentDetail", {})
    accused_list = data.get("accusedDetail", [])

    y = PAGE_H - 18*mm

    # Continuation / overflow text area
    remarks = safe(complaint.get("remarks"), "")
    if remarks:
        y = fc.wrapped_text(MARGIN_L + 4*mm, y, remarks, CONTENT_W - 8*mm, NORMAL, 12)
    else:
        for _ in range(6):
            fc.hline(y, MARGIN_L + 4*mm, PAGE_W - MARGIN_R - 4*mm, 0.3)
            y -= 8*mm

    y -= 5*mm
    fc.hline(y)

    # Accused detail summary
    y -= 6*mm
    for i, acc in enumerate(accused_list):
        aname = safe(acc.get("name"), "")
        aaddr = safe(acc.get("address"), "")
        line  = f"{aname}, N/A — {aaddr}"
        y = fc.wrapped_text(MARGIN_L + 4*mm, y, line, CONTENT_W - 8*mm, NORMAL, 12)
        y -= 4*mm

    y -= 5*mm
    fc.hline(y)

    fc.text(PAGE_W / 2, MARGIN_B, "4", NORMAL, "center")
    fc.hline(MARGIN_B + 5*mm)


# ─────────────────────────────────────────────
# PAGE 5 – Action taken & signatures
# ─────────────────────────────────────────────
def build_page5(fc: FIRCanvas, data: dict):
    c = fc.c
    meta_sub  = data.get("complaintSubmissionDetails", {})
    complaint = data.get("complaintDetail", {})
    comp      = data.get("complainantDetail", {})
    pi        = comp.get("personalInformation", {})

    accused_list = data.get("accusedDetail", [])

    y = PAGE_H - 18*mm

    # Accused last entry blurb (government boilerplate ending)
    if accused_list:
        last_acc = accused_list[-1]
        aname    = safe(last_acc.get("name"), "")
        aaddr    = safe(last_acc.get("address"), "")
        fc.text(MARGIN_L + 4*mm, y, f"{aname} — {aaddr}", SMALL)
    y -= 10*mm
    fc.hline(y)

    # ── Section 13: Action taken ─────────────
    y -= 6*mm
    fc.bold(MARGIN_L, y, "13. Action taken: Since the above information reveals commission of", SMALL)
    y -= 4*mm
    fc.bold(MARGIN_L + 4*mm, y, "offence(s) u/s as mentioned at Item No. 2.", SMALL)
    y -= 6*mm

    fc.bold(MARGIN_L, y, "(1) Registered the case and took up the investigation:", SMALL)
    y -= 5*mm
    fc.text(MARGIN_L + 4*mm, y, "___________________________ (Inspector) /", NORMAL)
    fc.bold(PAGE_W/2 + 20*mm, y, "or ", SMALL)
    y -= 6*mm
    fc.bold(MARGIN_L, y, "(2) Directed (Name of I.O.) :", SMALL)
    y -= 5*mm
    fc.bold(MARGIN_L + 4*mm, y, "Rank :", SMALL)
    fc.bold(PAGE_W/2, y, "No. :", SMALL)
    y -= 5*mm
    fc.bold(MARGIN_L + 4*mm, y, "to take up the Investigation or ", SMALL)
    y -= 5*mm
    fc.bold(MARGIN_L, y, "(3) Refused investigation due to :", SMALL)
    y -= 8*mm
    
    fc.bold(MARGIN_L, y, "(4) Transferred to P.S.", SMALL)
    y -= 5*mm
   
    fc.bold(MARGIN_L + 4*mm, y, "District :", SMALL)
    y -= 5*mm
    fc.bold(MARGIN_L + 4*mm, y, "on point of jurisdiction.", SMALL)
    y -= 8*mm

    fc.bold(MARGIN_L, y, "F.I.R. read over to the complainant / informant, admitted to be correctly", SMALL)
    y -= 4*mm
    fc.bold(MARGIN_L, y, "recorded and a copy given to the complainant / informant free of cost.", SMALL)
    y -= 5*mm
    fc.bold(MARGIN_L, y, "R.O.A.C. ", SMALL)
    y -= 10*mm
    fc.hline(y)

    # ── Section 14: Signatures ───────────────
    y -= 6*mm
    fc.bold(MARGIN_L, y, "14. Signature/Thumb impression of the", SMALL)
    y -= 4*mm
    fc.bold(MARGIN_L, y, "complainant / informant.", SMALL)
    y -= 4*mm
    
    # Signature box (left)
    fc.rect(MARGIN_L, y, 60*mm, 20*mm)
    # Right signature block
    fc.bold(PAGE_W - MARGIN_R - 60*mm, y + 8*mm, "Signature of Officer in charge, Police Station", SMALL)
    y -= 4*mm
    
    fc.bold(PAGE_W - MARGIN_R - 60*mm, y, "Name : ___________________________", SMALL)
    y -= 5*mm
    fc.bold(PAGE_W - MARGIN_R - 60*mm, y, "Rank :  ___________________________", SMALL)
    y -= 5*mm
    fc.bold(PAGE_W - MARGIN_R - 60*mm, y, "No. :  ___________________________", SMALL)
    y -= 10*mm
    fc.hline(y)

    # ── Section 15 ───────────────────────────
    y -= 6*mm
    fc.bold(MARGIN_L, y, "15. Date and time of dispatch to the court", SMALL)
    

    # Page number
    fc.text(PAGE_W / 2, MARGIN_B, "5", NORMAL, "center")
    fc.hline(MARGIN_B + 5*mm)


# ─────────────────────────────────────────────
# Main entry point
# ─────────────────────────────────────────────
def generate_efir_pdf(json_path: str, output_path: str):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    fc = FIRCanvas(output_path)

    # ── Page 1 ──────────────────────────────
    build_page1(fc, data)
    fc.new_page()

    # ── Page 2 ──────────────────────────────
    build_page2(fc, data)
    fc.new_page()

    # ── Page 3 ──────────────────────────────
    build_page3(fc, data)
    fc.new_page()

    # ── Page 4 ──────────────────────────────
    build_page4(fc, data)
    fc.new_page()

    # ── Page 5 ──────────────────────────────
    build_page5(fc, data)

    fc.save()
    print(f" eFIR PDF generated → {output_path}")


# ─────────────────────────────────────────────
if __name__ == "__main__":
    generate_efir_pdf("input.json", "output1.pdf")