import openpyxl
import logging

class ExcelParser:
    @staticmethod
    def load_dataframe(file_path):
        """Reads Excel and returns a list of rows (dicts) and list of columns."""
        try:
            wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
            ws = wb.active

            rows = list(ws.iter_rows(values_only=True))
            if not rows:
                return None, []

            columns = [str(c) if c is not None else "" for c in rows[0]]
            data = [dict(zip(columns, row)) for row in rows[1:]]

            wb.close()
            return data, columns
        except Exception as e:
            logging.error(f"Error reading Excel file: {e}")
            raise e

    @staticmethod
    def extract_names_from_column(data, column_name):
        """Extracts and cleans names from a specific column."""
        if not data or column_name not in data[0]:
            return []
        names = []
        for row in data:
            val = row.get(column_name)
            if val is not None:
                s = str(val).strip()
                if s:
                    names.append(s)
        return names