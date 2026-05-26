# For Presidio
from presidio_analyzer import AnalyzerEngine, PatternRecognizer
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig, RecognizerResult

# For console output
# from pprint import pprint

# For extracting text
# from pdfminer.high_level import extract_text, extract_pages
# from pdfminer.layout import LTTextContainer, LTChar, LTTextLine

# # For updating the PDF
# from pikepdf import Pdf, AttachedFileSpec, Name, Dictionary, Array

analyzer = AnalyzerEngine()

anonymizer = AnonymizerEngine()

analyzed_character_sets = []

# for page_layout in extract_pages("./sample_data/sample.pdf"):
#     for text_container in page_layout:
#         if isinstance(text_container, LTTextContainer):

#             # The element is a LTTextContainer, containing a paragraph of text.
#             text_to_anonymize = text_container.get_text()

#             # Analyze the text using the analyzer engine
#             analyzer_results = analyzer.analyze(text=text_to_anonymize, language='en')
 
#             if text_to_anonymize.isspace() == False:
#                 print(text_to_anonymize)
#                 print(analyzer_results)

#             characters = list([])

#             # Grab the characters from the PDF
#             for text_line in filter(lambda t: isinstance(t, LTTextLine), text_container):
#                     for character in filter(lambda t: isinstance(t, LTChar), text_line):
#                             characters.append(character)


#             # Slice out the characters that match the analyzer results.
#             for result in analyzer_results:
#                 start = result.start
#                 end = result.end
#                 analyzed_character_sets.append({"characters": characters[start:end], "result": result})


chat_input = """Hi, I'm Charles. I live in Chennai. My order has not yet arrived.
I used my  visa card to pay for it. What is it's deliver status? Can I call you using my phone ?"""


results = analyzer.analyze(chat_input, language="en")
print(results)
print(anonymizer.anonymize(chat_input, results))