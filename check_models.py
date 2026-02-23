import google.generativeai as genai

# আপনার API Key টি এখানে বসান
api_key = "AIzaSyDwlFseSSanidoiooTLV_375MgUhWpq-90"

try:
    genai.configure(api_key=api_key)
    print("✅ API Key Configured. Fetching available models...\n")

    print("--- আপনার জন্য বব্যহারযোগ্য মডেলসমূহ ---")
    available_models = []
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"- {m.name}")
            available_models.append(m.name)

    if not available_models:
        print("\n❌ কোনো মডেল পাওয়া যায়নি! লাইব্রেরি আপডেট বা API Key চেক করুন।")
    else:
        print(f"\n✅ মোট {len(available_models)} টি মডেল পাওয়া গেছে।")

except Exception as e:
    print(f"\n❌ Error: {e}")
