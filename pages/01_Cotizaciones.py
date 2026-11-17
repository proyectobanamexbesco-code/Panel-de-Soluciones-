def draw_table_row(pdf, concepto):
    # Genera las líneas envueltas
    lines = pdf_wrap_lines(pdf, concepto["Concepto"], TABLE_COLS["concepto"] - 4)
    
    # 1. FIX: Aumentamos el padding para asegurar que el texto no toque los bordes inferiores
    padding_inferior = 6
    row_height = max(TABLE_MIN_ROW_HEIGHT, len(lines) * TABLE_LINE_HEIGHT + padding_inferior)
    
    # 2. Control de salto de página si la fila no cabe
    if pdf.get_y() + row_height > 238:
        pdf.add_page()
        draw_table_header(pdf)
        
    x = pdf.get_x()
    y = pdf.get_y()
    
    # 3. Dibujar la caja principal de la fila (bordes)
    widths = [
        TABLE_COLS["codigo"], 
        TABLE_COLS["concepto"], 
        TABLE_COLS["unidad"], 
        TABLE_COLS["cantidad"], 
        TABLE_COLS["pu"], 
        TABLE_COLS["importe"]
    ]
    
    for width in widths:
        pdf.rect(x, y, width, row_height)
        x += width
        
    # 4. Imprimir contenido de las celdas
    
    # CÓDIGO
    x_codigo = pdf.l_margin
    pdf.set_xy(x_codigo, y + (row_height / 2) - 2)
    pdf.cell(TABLE_COLS["codigo"], 4, limpiar_texto_pdf(str(concepto.get("Item", ""))), 0, 0, "C")
    
    # CONCEPTO (Impresión multi-línea)
    x_concepto = pdf.l_margin + TABLE_COLS["codigo"] + 1.5
    y_text = y + 3.2 # Margen superior fijo para el texto del concepto
    for line in lines:
        pdf.set_xy(x_concepto, y_text)
        pdf.cell(TABLE_COLS["concepto"] - 3, 4, line, 0, 0, "L")
        y_text += TABLE_LINE_HEIGHT
        
    # UNIDAD
    x_unidad = pdf.l_margin + TABLE_COLS["codigo"] + TABLE_COLS["concepto"]
    pdf.set_xy(x_unidad, y + (row_height / 2) - 2)
    pdf.cell(TABLE_COLS["unidad"], 4, limpiar_texto_pdf(str(concepto.get("Unidad", ""))), 0, 0, "C")
    
    # CANTIDAD
    x_cantidad = x_unidad + TABLE_COLS["unidad"]
    pdf.set_xy(x_cantidad, y + (row_height / 2) - 2)
    pdf.cell(TABLE_COLS["cantidad"], 4, limpiar_texto_pdf(f"{float(concepto.get('Cantidad', 0)):,.2f}"), 0, 0, "C")
    
    # PRECIO UNITARIO
    x_pu = x_cantidad + TABLE_COLS["cantidad"]
    pdf.set_xy(x_pu, y + (row_height / 2) - 2)
    pdf.cell(TABLE_COLS["pu"] - 1.5, 4, limpiar_texto_pdf(f"$ {float(concepto.get('Precio Venta', 0)):,.2f}"), 0, 0, "R")
    
    # IMPORTE
    x_importe = x_pu + TABLE_COLS["pu"]
    pdf.set_xy(x_importe, y + (row_height / 2) - 2)
    pdf.cell(TABLE_COLS["importe"] - 1.5, 4, limpiar_texto_pdf(f"$ {float(concepto.get('Importe', 0)):,.2f}"), 0, 0, "R")
    
    # Bajar el cursor para la siguiente fila
    pdf.set_y(y + row_height)
