from docling.document_converter import DocumentConverter

# Change this to a local path or another URL if desired.
# Note: using the default URL requires network access; if offline, provide a
# local file path (e.g., Path("/path/to/file.pdf")).
source = "Alone_Against_Fear_EBOOK.pdf"

converter = DocumentConverter()
result = converter.convert(source)

# Write Markdown to file.
output_file = "output.md"
with open(output_file, "w", encoding="utf-8") as f:
    f.write(result.document.export_to_markdown())
print(f"Markdown exported to {output_file}")

# ============================================================================
# OFFLINE MODE (no network requests, disables OCR)
# Uncomment this version if you want to avoid HuggingFace model downloads
# ============================================================================
# import os
# from docling.datamodel.base_models import InputFormat
# from docling.datamodel.pipeline_options import PdfPipelineOptions
# 
# # Suppress HuggingFace warnings by setting offline mode
# os.environ["HF_HUB_OFFLINE"] = "1"
# 
# # Configure pipeline to use local models only
# pipeline_options = PdfPipelineOptions()
# pipeline_options.do_ocr = False  # Disable OCR to avoid model downloads
# pipeline_options.do_table_structure = True
# 
# converter = DocumentConverter(
#     format_options={
#         InputFormat.PDF: pipeline_options,
#     }
# )
# result = converter.convert(source)