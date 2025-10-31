# def get_institution_code_from_name(institution_name):
#     """Maps a full institution name to its code."""
#     institution_mapping = {
#         "Jharkhand State University": "JHAR",
#         "Ranchi Tech Institute": "RANC",
#         "Jharkhand Business School": "JHAR_BS"
#     }
#     # Simple direct mapping - you might want to make this more robust
#     # with fuzzy matching if OCR results are imperfect
#     return institution_mapping.get(institution_name)

def get_institution_code_from_name(institution_name):
    """Maps a full institution name to its code."""
    institution_mapping = {
        "Jharkhand State University": "JHAR",
        "Ranchi Tech Institute": "RANC",
        "Jharkhand Business School": "JHAR_BS"
    }
    # Simple direct mapping - you might want to make this more robust
    # with fuzzy matching if OCR results are imperfect
    return institution_mapping.get(institution_name)