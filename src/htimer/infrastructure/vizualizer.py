from typing import Any
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from application.reports import interfaces




class ReportVizualizer(interfaces.ReportVizualizer):

    def generete_table(self, content: interfaces.ContentType | list) -> list[list[Any]]:

        tables_data: list[list[Any]] = []

        if isinstance(content, list):
            pass
            

    async def vizualize(self, content: interfaces.ContentType) -> bytes:

        pdf = SimpleDocTemplate("table.pdf", pagesize=A4)



                
        # Создаём таблицу
        table = Table(data)

        # Настраиваем стиль таблицы
        style = TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.grey),      # цвет заголовка
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('GRID', (0,0), (-1,-1), 1, colors.black),      # сетка
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ])
        table.setStyle(style)

        # Добавляем в документ
        elements = [table]
        pdf.build(elements)