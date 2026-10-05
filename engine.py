import os
import shutil
from concurrent.futures import ThreadPoolExecutor
from excel_parser import ExcelParser
from pdf_handler import PDFHandler

class Engine:
    def __init__(self):
        self.names = []
        self.df = None
        self.template_path = None
        self.output_dir = None
        self.text_config = {}

    def load_excel(self, file_path):
        self.df, columns = ExcelParser.load_dataframe(file_path)
        return columns

    def set_name_column(self, column_name):
        if self.df is not None:
            self.names = ExcelParser.extract_names_from_column(self.df, column_name)
            return len(self.names)
        return 0

    def set_template(self, file_path):
        self.template_path = file_path

    def set_output_dir(self, dir_path):
        self.output_dir = dir_path

    def set_text_config(self, config):
        self.text_config = config

    def validate_setup(self):
        if not self.template_path:
            return False, "Template image not loaded."
        if not self.names:
            return False, "No names found in the Excel file."
        if not self.output_dir:
            return False, "Output directory not selected."
        if 'box' not in self.text_config:
            return False, "Text box not drawn on the template."
        return True, ""

    def generate(self, merge=False, zip_output=False, progress_callback=None):
        valid, msg = self.validate_setup()
        if not valid:
            raise ValueError(msg)

        total = len(self.names)
        working_template = self.template_path
        
        try:
            if merge:
                merged_path = os.path.join(self.output_dir, "Mawaheb_Certificates.pdf")
                PDFHandler.generate_merged_certificates(working_template, self.names, self.text_config, merged_path, progress_callback)
                
                if zip_output:
                    if progress_callback:
                        progress_callback(total, total, "Zipping PDF...")
                    import zipfile
                    zip_path = os.path.join(self.output_dir, "Mawaheb_Certificates.zip")
                    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                        zipf.write(merged_path, os.path.basename(merged_path))
                    os.remove(merged_path)
            else:
                temp_dir = os.path.join(self.output_dir, "temp_certs")
                os.makedirs(temp_dir, exist_ok=True)
                try:
                    def worker(i, name):
                        safe_name = "".join([c for c in name if c.isalpha() or c.isdigit() or c==' ']).rstrip()
                        if not safe_name:
                            safe_name = f"Certificate_{i+1}"
                        out_path = os.path.join(temp_dir, f"{safe_name}.pdf")
                        PDFHandler.generate_certificate(working_template, name, self.text_config, out_path)
                        return out_path

                    pdf_paths = []
                    with ThreadPoolExecutor() as executor:
                        futures = []
                        for i, name in enumerate(self.names):
                            futures.append(executor.submit(worker, i, name))
                        
                        for i, future in enumerate(futures):
                            pdf_paths.append(future.result())
                            if progress_callback:
                                progress_callback(i + 1, total, "Generating")

                    if zip_output:
                        if progress_callback:
                            progress_callback(total, total, "Zipping PDFs...")
                        import zipfile
                        zip_path = os.path.join(self.output_dir, "Mawaheb_Certificates.zip")
                        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                            for path in pdf_paths:
                                zipf.write(path, os.path.basename(path))
                    else:
                        for path in pdf_paths:
                            shutil.move(path, os.path.join(self.output_dir, os.path.basename(path)))
                finally:
                    if os.path.exists(temp_dir):
                        shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception as e:
            raise e

        return True
