"""
Script tạo file PDF Báo cáo Sơ lược Hệ thống GreenMind AI
"""
import os
from fpdf import FPDF

OUTPUT_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "BaoCao_SoLuoc_HeThong_GreenMind.pdf")

class GreenMindPDF(FPDF):
    def __init__(self):
        super().__init__(orientation='P', unit='mm', format='A4')
        # Tải font NotoSans Unicode hỗ trợ tiếng Việt
        font_url = "https://github.com/google/fonts/raw/main/ofl/notosans/NotoSans%5Bwdth%2Cwght%5D.ttf"
        font_bold_url = "https://github.com/google/fonts/raw/main/ofl/notosans/NotoSans-Italic%5Bwdth%2Cwght%5D.ttf"
        
        regular = r"C:\Windows\Fonts\arial.ttf"
        bold = r"C:\Windows\Fonts\arialbd.ttf"
        
        if os.path.exists(regular):
            self.add_font("ArialVN", "", regular, uni=True)
            self.has_arial = True
        else:
            self.has_arial = False
            
        if os.path.exists(bold):
            self.add_font("ArialVN", "B", bold, uni=True)
            
    def _font(self, style="", size=10):
        if self.has_arial:
            self.set_font("ArialVN", style, size)
        else:
            self.set_font("Helvetica", style, size)
            
    def header(self):
        self.set_fill_color(11, 15, 25)
        self.rect(0, 0, 210, 20, 'F')
        self._font("B", 9)
        self.set_text_color(16, 185, 129)
        self.set_y(6)
        self.cell(0, 8, "GREENMIND AI CORE PLATFORM", align='L')
        self._font("", 7)
        self.set_text_color(156, 163, 175)
        self.cell(0, 8, "Enterprise Edition v2.0 | 2026", align='R')
        self.ln(14)
        
    def footer(self):
        self.set_y(-15)
        self.set_fill_color(11, 15, 25)
        self.rect(0, self.get_y(), 210, 15, 'F')
        self._font("", 7)
        self.set_text_color(107, 114, 128)
        self.cell(0, 10, f"Trang {self.page_no()}/{{nb}}", align='C')
        
    def section_title(self, num, title):
        self.ln(4)
        self.set_fill_color(5, 150, 105)
        self.rect(10, self.get_y(), 3, 8, 'F')
        self._font("B", 13)
        self.set_text_color(17, 24, 39)
        self.set_x(16)
        self.cell(0, 8, f"{num}. {title}")
        self.ln(10)
        
    def sub_title(self, title):
        self._font("B", 10)
        self.set_text_color(55, 65, 81)
        self.cell(0, 7, title)
        self.ln(8)
        
    def body(self, txt):
        self._font("", 9)
        self.set_text_color(55, 65, 81)
        self.multi_cell(0, 5, txt)
        self.ln(2)
        
    def body_bold(self, txt):
        self._font("B", 9)
        self.set_text_color(55, 65, 81)
        self.multi_cell(0, 5, txt)
        self.ln(2)
        
    def bullet(self, txt, indent=15):
        self._font("", 9)
        self.set_text_color(55, 65, 81)
        x = self.get_x()
        self.set_x(indent)
        self.cell(5, 5, chr(8226))
        self.multi_cell(0, 5, txt)
        self.ln(1)
        
    def table_header(self, cols, widths):
        self.set_fill_color(17, 24, 39)
        self._font("B", 8)
        self.set_text_color(209, 213, 219)
        for i, col in enumerate(cols):
            self.cell(widths[i], 7, col, border=1, fill=True, align='C')
        self.ln()
        
    def table_row(self, cols, widths, fill=False):
        if fill:
            self.set_fill_color(243, 244, 246)
        else:
            self.set_fill_color(255, 255, 255)
        self._font("", 8)
        self.set_text_color(55, 65, 81)
        for i, col in enumerate(cols):
            self.cell(widths[i], 6, col, border=1, fill=True, align='C' if i == 0 else 'L')
        self.ln()
        
    def key_value(self, key, value):
        self._font("B", 9)
        self.set_text_color(17, 24, 39)
        self.cell(55, 6, key)
        self._font("", 9)
        self.set_text_color(75, 85, 99)
        self.cell(0, 6, value)
        self.ln(7)

def build_pdf():
    pdf = GreenMindPDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)
    
    # ===== COVER PAGE =====
    pdf.add_page()
    pdf.ln(30)
    pdf.set_fill_color(5, 150, 105)
    pdf.rect(10, pdf.get_y(), 190, 2, 'F')
    pdf.ln(8)
    
    pdf._font("B", 10)
    pdf.set_text_color(107, 114, 128)
    pdf.cell(0, 6, "CUOC THI SINH VIEN NGHIEN CUU KHOA HOC VA DOI MOI SANG TAO 2025-2026", align='C')
    pdf.ln(6)
    pdf._font("", 8)
    pdf.cell(0, 5, "Truong Dai hoc Giao thong Van tai TP. Ho Chi Minh", align='C')
    pdf.ln(5)
    pdf.cell(0, 5, "Vien Cong nghe Thong tin va Dien, Dien tu", align='C')
    pdf.ln(15)
    
    pdf._font("B", 22)
    pdf.set_text_color(17, 24, 39)
    pdf.cell(0, 12, "GREENMIND", align='C')
    pdf.ln(12)
    pdf._font("B", 11)
    pdf.set_text_color(5, 150, 105)
    txt = "He thong Du bao Thong minh Tu thich nghi"
    pdf.cell(0, 8, txt, align='C')
    pdf.ln(7)
    txt2 = "cho Quan ly Kho Logistics Xanh Viet Nam"
    pdf.cell(0, 8, txt2, align='C')
    pdf.ln(15)
    
    pdf.set_fill_color(5, 150, 105)
    pdf.rect(80, pdf.get_y(), 50, 1, 'F')
    pdf.ln(10)
    
    pdf._font("", 9)
    pdf.set_text_color(107, 114, 128)
    pdf.cell(0, 6, "Linh vuc: Tri tue nhan tao va Hoc may", align='C')
    pdf.ln(6)
    pdf.cell(0, 6, "Phien ban: Enterprise Edition v2.0", align='C')
    pdf.ln(6)
    pdf.cell(0, 6, "Nam: 2026", align='C')
    pdf.ln(20)

    # Team info on cover
    pdf._font("B", 10)
    pdf.set_text_color(17, 24, 39)
    pdf.cell(0, 7, "NHOM NGHIEN CUU", align='C')
    pdf.ln(8)
    
    team = [
        ["1", "046205006145", "Ha Nhat Nguyen Vu", "He thong Thong tin Quan ly", "Nhom truong"],
        ["2", "060205011928", "Nguyen Van Toi", "Khoa hoc Du lieu", "Data Scientist"],
        ["3", "068305006913", "Nguyen Dao Kieu Dung", "Logistics & Chuoi cung ung", "Logistics Expert"],
        ["4", "079205004676", "Le Huynh Quang Minh", "An toan & Moi truong", "Environment Spec."],
    ]
    w = [10, 30, 40, 50, 40]
    pdf.set_x(20)
    pdf.table_header(["STT", "MSSV", "Ho va ten", "Chuyen nganh", "Vai tro"], w)
    for i, row in enumerate(team):
        pdf.set_x(20)
        pdf.table_row(row, w, fill=(i % 2 == 0))
    
    # ===== PAGE 2: TONG QUAN =====
    pdf.add_page()
    pdf.section_title("1", "TONG QUAN DE TAI")
    
    pdf.sub_title("1.1. Boi canh & Tinh cap thiet")
    pdf.body(
        "Nganh logistics Viet Nam doi mat voi thach thuc kep: tang truong bung no tu thuong mai dien tu "
        "(chi phi logistics chiem ~18% GDP) va ap luc chuyen doi xanh tu cac cam ket quoc te "
        "(Net Zero 2050, CBAM cua EU). Hoat dong kho bai chiem khoang 11% tong phat thai logistics toan cau, "
        "trong khi 60-70% doanh nghiep Viet Nam van quan ly kho thu cong, dan den lang phi nang luong 15-20% "
        "va that thoat hang hoa khoang 2-2.5% doanh thu (kho FMCG)."
    )
    
    pdf.sub_title("1.2. Khoang trong nghien cuu")
    pdf.body(
        "Mac du cac mo hinh du bao don le (ARIMA, Prophet) da duoc ung dung rong rai, viec tich hop da mo hinh "
        "(SARIMAX, Prophet, XGBoost) ket hop co che tu chon mo hinh toi uu (Champion Selection) vao mot he thong "
        "quan ly kho xanh hoan chinh tai Viet Nam van con rat hiem. Dac biet, gan nhu chua co nghien cuu nao "
        "so sanh cac kich ban 'Green Scenario' dua tren sai so MAPE de quy doi sang tiet kiem phat thai CO2 "
        "theo chuan ISO 14064."
    )
    
    pdf.sub_title("1.3. Muc tieu")
    pdf.bullet("Du bao nhu cau (demand) bang AI da mo hinh tu thich nghi.")
    pdf.bullet("He thong ho tro ra quyet dinh (DSS) ve ton kho va diem tai dat hang.")
    pdf.bullet("Do luong va bao cao tac dong moi truong (Green Metrics / ESG) theo chuan quoc te.")
    
    # ===== PAGE 3: KIEN TRUC =====
    pdf.add_page()
    pdf.section_title("2", "KIEN TRUC HE THONG (3-TIER ARCHITECTURE)")
    
    pdf.body(
        "He thong GreenMind duoc thiet ke theo mo hinh phan lop 3 tang nham dam bao tinh mo rong, "
        "bao mat va tach biet trach nhiem ro rang giua cac thanh phan."
    )
    pdf.ln(3)
    
    # Tier 1
    pdf.sub_title("Tang 1: Data Layer - SQL Server")
    w2 = [45, 145]
    pdf.table_header(["Thanh phan", "Mo ta"], w2)
    rows_t1 = [
        ["Cong nghe", "Microsoft SQL Server (SQL Express), T-SQL"],
        ["Database", "GRW"],
        ["Bang Master", "Dim_Products (San pham, He so phat thai, Ke kho), Dim_Users"],
        ["Bang Fact", "Fact_Inventory_History, Fact_AI_Predictions"],
        ["Bang Logs", "Green_Impact_Logs, Inventory_CO2_Warnings, System_Health_Log"],
        ["Stored Proc", "sp_SellProduct (Transaction + Trigger)"],
        ["Bao ve", "SQL Transaction, Trigger tu dong ghi canh bao CO2"],
    ]
    for i, r in enumerate(rows_t1):
        pdf.table_row(r, w2, fill=(i%2==0))
    pdf.ln(5)
    
    # Tier 2
    pdf.sub_title("Tang 2: Intelligence Layer - Python AI")
    pdf.table_header(["Thanh phan", "Mo ta"], w2)
    rows_t2 = [
        ["Cong nghe", "Python 3.13, SQLAlchemy, Pandas, Scikit-learn"],
        ["Core Engine", "GreenMindEngine (greenmind_engine.py, ~470 LOC)"],
        ["Mo hinh AI", "SARIMAX, Prophet, XGBoost"],
        ["Chon Model", "Battle of Models - 3 model cung chay, MAE thap nhat = Champion"],
        ["Pipeline", "Du bao Demand (SoldQuantity/ngay), KHONG du bao Stock"],
        ["DSS Output", "Safety Stock = Z x sigma_demand x sqrt(lead_time)"],
        ["Green Metrics", "kWh = overstock x 0.002 x 365 -> kgCO2e = kWh x 0.4937"],
    ]
    for i, r in enumerate(rows_t2):
        pdf.table_row(r, w2, fill=(i%2==0))
    pdf.ln(5)
    
    # Tier 3
    pdf.sub_title("Tang 3: Presentation Layer - Django")
    pdf.table_header(["Thanh phan", "Mo ta"], w2)
    rows_t3 = [
        ["Cong nghe", "Django 5.x, Tailwind CSS (CDN), Plotly.js, Google Fonts"],
        ["Thiet ke", "Dark Mode Premium, Responsive, Enterprise Dashboard"],
        ["Xac thuc", "Django Authentication (Login / Register / Role-based)"],
        ["Phan quyen", "SuperUser (IT), Admin (Kho), Staff (Nhan vien)"],
    ]
    for i, r in enumerate(rows_t3):
        pdf.table_row(r, w2, fill=(i%2==0))
    
    # ===== PAGE 4: MODULES =====
    pdf.add_page()
    pdf.section_title("3", "CAC MODULE CHUC NANG CHINH")
    
    modules = [
        ("Module 1: Tong quan Du bao (Forecast Dashboard)", [
            "Hien thi bieu do chuoi thoi gian (Stock & Demand) cua tung SKU.",
            "Cho phep nguoi dung chon Ma SKU de phan tich.",
            "Hien thi ket qua Battle Models (SARIMAX vs Prophet vs XGBoost) cung Champion.",
            "Bieu dien duong du bao 30 ngay tiep theo."
        ]),
        ("Module 2: Danh muc San pham (Master Data Catalog)", [
            "Quan ly CRUD san pham trong bang Dim_Products.",
            "Ho tro nhap he so phat thai CO2 (EmissionFactor) va Safety Stock cho tung SKU.",
            "Phan quyen: Chi Admin duoc thao tac. Staff chi xem (ReadOnly)."
        ]),
        ("Module 3: Quan tri Nghiep vu Kho (Warehouse Simulator)", [
            "Mo phong giao dich Nhap/Xuat kho ghi thang vao Fact_Inventory_History.",
            "Su dung Stored Procedure sp_SellProduct dam bao toan ven.",
            "Du lieu phan chieu tuc thi, lam moi bo dem AI ngay lap tuc."
        ]),
        ("Module 4: He thong Du lieu (Monitoring)", [
            "Bang tong hop tinh trang ton kho theo SKU.",
            "Ban do nhiet kho (Warehouse Heatmap) theo vi tri ke.",
            "Nhat ky bien dong kho (Inventory Movement Log)."
        ]),
        ("Module 5: Bao cao ESG", [
            "Tong hop luong CO2 tiet kiem nho toi uu du bao AI.",
            "Quy doi ra cay xanh tuong duong (Trees Equivalent).",
            "Bieu do so sanh Phat thai co so vs Phat thai AI (sau toi uu).",
            "Huong den xuat bao cao tuan thu chuan ISO 14064."
        ]),
        ("Module 6: System Diagnostics (Health Check) - AN", [
            "Chi danh cho SuperUser (Admin Ky thuat / DevOps).",
            "KHONG hien thi tren menu. Truy cap bang URL /health-check/ hoac CLI.",
            "Kiem tra 3 chang: Bien moi truong -> CSDL -> AI Pipeline.",
            "Ket qua ghi vao bang System_Health_Log (Self-healing)."
        ]),
    ]
    
    for title, items in modules:
        pdf.sub_title(title)
        for item in items:
            pdf.bullet(item)
        pdf.ln(2)
    
    # ===== PAGE 5: LUONG VAN HANH & KET QUA =====
    pdf.add_page()
    pdf.section_title("4", "LUONG VAN HANH AI PIPELINE")
    
    steps = [
        "1. Du lieu bien dong kho duoc nap lien tuc vao Fact_Inventory_History.",
        "2. Feature Engineering: Tach chuoi Demand (= SoldQuantity moi ngay) tu du lieu tho.",
        "3. Battle of Models: 3 mo hinh AI cung chay du bao, mo hinh co MAE thap nhat duoc phong Champion.",
        "4. Champion Model thuc hien du bao demand 30 ngay tiep theo.",
        "5. DSS: Tinh toan Safety Stock va Reorder Point (ROP) theo cong thuc chuan nghiep vu.",
        "6. Ket qua duoc dua ra cho nguoi van hanh kho de ra quyet dinh nhap/xuat.",
        "7. Green Metrics: Luong CO2 tiet kiem duoc quy doi tu luong overstock giam thieu.",
        "8. ESG Report: Tong hop bao cao phat thai tuan thu chuan ISO 14064.",
        "9. Feedback Loop: Bao cao ESG phan hoi nguoc lai de dieu chinh chinh sach ton kho."
    ]
    for s in steps:
        pdf.bullet(s)
    
    pdf.ln(5)
    pdf.section_title("5", "KET QUA SO BO DAT DUOC")
    
    w3 = [80, 110]
    pdf.table_header(["Chi so", "Gia tri"], w3)
    results = [
        ["So SKU trong he thong", "13 san pham (Active)"],
        ["So ban ghi lich su kho", "36,304 dong"],
        ["Model Champion pho bien nhat", "XGBoost"],
        ["Sai so MAPE du kien", "6-18% (tuy SKU va mua vu)"],
        ["So bang CSDL", "8 bang (3 Dim + 3 Fact + 2 Log)"],
        ["So nguoi dung thu nghiem", "3 tai khoan (Admin, Manager, Staff)"],
    ]
    for i, r in enumerate(results):
        pdf.table_row(r, w3, fill=(i%2==0))
    
    # ===== PAGE 6: CONG NGHE, MO RONG, TLTK =====
    pdf.add_page()
    pdf.section_title("6", "CONG NGHE SU DUNG")
    
    w4 = [25, 35, 20, 110]
    pdf.table_header(["Tang", "Cong nghe", "Version", "Vai tro"], w4)
    tech = [
        ["Backend", "Python", "3.13", "Ngon ngu loi"],
        ["Framework", "Django", "5.x", "HTTP Server, Routing, Auth"],
        ["Database", "SQL Server", "Express", "Luu tru du lieu tap trung"],
        ["ORM", "SQLAlchemy", "-", "Ket noi Python <-> SQL Server"],
        ["AI/ML", "XGBoost", "-", "Mo hinh du bao phi tuyen"],
        ["AI/ML", "Prophet", "-", "Mo hinh du bao mua vu"],
        ["AI/ML", "Statsmodels", "-", "SARIMAX chuoi thoi gian"],
        ["Frontend", "Tailwind CSS", "CDN", "Giao dien Dark Mode Responsive"],
        ["Charting", "Plotly.js", "-", "Bieu do tuong tac"],
    ]
    for i, r in enumerate(tech):
        pdf.table_row(r, w4, fill=(i%2==0))
    
    pdf.ln(5)
    pdf.section_title("7", "KHA NANG MO RONG")
    pdf.bullet("Giai doan 1: Module GreenMind Forecasting - Giam ton kho du thua bang AI.")
    pdf.bullet("Giai doan 2: Bo sung IGA Slotting - Toi uu vi tri luu tru trong kho.")
    pdf.bullet("Giai doan 3: Tich hop IoT Sensor - Giam sat nhiet do, do am, dien nang.")
    pdf.bullet("Tam nhin 2030: Scale cho 50+ kho FMCG khu vuc phia Nam, tich hop Robot AMR va ket noi ERP/TMS.")
    pdf.ln(2)
    pdf.body(
        "Khi thi truong carbon Viet Nam chinh thuc van hanh (du kien 2026-2028), he thong co the tu dong tao "
        "bao cao phat thai CO2 theo chuan ISO 14064 phuc vu giao dich tin chi ETS - mang lai gia tri thuong mai "
        "truc tiep cho doanh nghiep."
    )
    
    pdf.ln(5)
    pdf.section_title("8", "TAI LIEU THAM KHAO")
    refs = [
        "[1] Cosimato, S. (2015). Green supply chain management. The TQM Journal, 27(2), 256-276.",
        "[2] McKinnon, A. (2015). Green logistics. Kogan Page Publishers.",
        "[3] Miklautsch, P. (2023). Industrial logistics decarbonization. Trans. Res. Interdisc. Perspectives, 21.",
        "[4] Perotti, S. (2023). Greening warehouses. Int. J. of Logistics Management, 34(7), 199-234.",
        "[5] Phan Dinh Quyet. Logistics xanh va chuyen doi so tai Viet Nam.",
        "[6] Ren, Q., et al. (2023). Green warehouse system design. J. of Cleaner Production, 388.",
        "[7] Smith, J.D. (1998). The warehouse management handbook. Tompkins Press.",
        "[8] Doan Thi Thu Trang, Nguyen Khanh Linh. (2024). Logistics xanh tai Viet Nam.",
        "[9] Van Vo, H., Nguyen, N.P. (2023). Greening the Vietnamese supply chain. Heliyon, 9(5).",
    ]
    for r in refs:
        pdf._font("", 8)
        pdf.set_text_color(55, 65, 81)
        pdf.multi_cell(0, 5, r)
        pdf.ln(1)
    
    # Footer info
    pdf.ln(10)
    pdf.set_fill_color(5, 150, 105)
    pdf.rect(10, pdf.get_y(), 190, 1, 'F')
    pdf.ln(5)
    pdf._font("B", 9)
    pdf.set_text_color(17, 24, 39)
    pdf.cell(0, 6, "GreenMind AI Core Platform | 2026", align='C')
    pdf.ln(6)
    pdf._font("", 8)
    pdf.set_text_color(107, 114, 128)
    pdf.cell(0, 5, "Truong Dai hoc Giao thong Van tai TP. Ho Chi Minh", align='C')
    
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    pdf.output(OUTPUT_PATH)
    print(f"PDF da duoc tao thanh cong tai: {OUTPUT_PATH}")

if __name__ == "__main__":
    build_pdf()
