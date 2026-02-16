from deep_translator import GoogleTranslator

translated = GoogleTranslator(source='auto', target='hi').translate("Hello")
print(translated)
