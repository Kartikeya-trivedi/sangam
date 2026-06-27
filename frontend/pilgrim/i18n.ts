// SETU multilingual strings — the heart of the cross-language UX.
// Every screen pulls BOTH its visible text and its spoken (TTS) text from here,
// so picking a language switches the entire app + the voice, not just a label.

export type Lang =
  | "hi-IN"
  | "ta-IN"
  | "bn-IN"
  | "mr-IN"
  | "te-IN"
  | "gu-IN"
  | "kn-IN"
  | "ml-IN"
  | "en-IN";

export interface LangMeta {
  code: Lang;
  label: string; // language name in its OWN script
  english: string; // English name (small, secondary)
}

// Shown on the language grid. Each name is in its own script (§2.12).
export const LANGUAGES: LangMeta[] = [
  { code: "hi-IN", label: "हिन्दी", english: "Hindi" },
  { code: "mr-IN", label: "मराठी", english: "Marathi" },
  { code: "ta-IN", label: "தமிழ்", english: "Tamil" },
  { code: "te-IN", label: "తెలుగు", english: "Telugu" },
  { code: "bn-IN", label: "বাংলা", english: "Bengali" },
  { code: "gu-IN", label: "ગુજરાતી", english: "Gujarati" },
  { code: "kn-IN", label: "ಕನ್ನಡ", english: "Kannada" },
  { code: "ml-IN", label: "മലയാളം", english: "Malayalam" },
  { code: "en-IN", label: "English", english: "English" },
];

export interface Strings {
  chooseLanguage: string;
  whoLookingFor: string;
  speak: string;
  listening: string;
  typeInstead: string;
  typeHere: string;
  continue: string;
  back: string;
  havePhoto: string;
  takePhoto: string;
  noPhoto: string;
  searching: string;
  isThisCorrect: string;
  youAreLooking: (summary: string) => string;
  yes: string;
  no: string;
  didntCatch: string;
  speakAgain: string;
  weFound: string;
  weRegistered: string;
  whyMatched: string;
  staffWillHelp: string;
  connect: string;
  startOver: string;
  listenAgain: string;
  announced: string;
  somethingWrong: string;
}

// English is always shown as a small secondary line, so these stay terse.
const STRINGS: Record<Lang, Strings> = {
  "hi-IN": {
    chooseLanguage: "अपनी भाषा चुनिए",
    whoLookingFor: "किसे ढूंढ रहे हैं?",
    speak: "बोलिए",
    listening: "सुन रहे हैं… रोकने के लिए दबाएँ",
    typeInstead: "टाइप करें",
    typeHere: "यहाँ लिखिए…",
    continue: "आगे बढ़िए",
    back: "वापस",
    havePhoto: "फोटो है?",
    takePhoto: "फोटो दिखाइए",
    noPhoto: "फोटो नहीं है, आगे बढ़िए",
    searching: "ढूंढ रहे हैं…",
    isThisCorrect: "सही है?",
    youAreLooking: (s) => `आप ढूंढ रहे हैं: ${s} — सही है?`,
    yes: "हाँ",
    no: "नहीं",
    didntCatch: "समझ नहीं आया",
    speakAgain: "फिर से बोलिए",
    weFound: "हमें ये लोग मिले",
    weRegistered: "जानकारी दर्ज हो गई, मिलते ही बताएंगे",
    whyMatched: "क्यों match हुआ",
    staffWillHelp: "स्टाफ़ मदद करेगा",
    connect: "इनसे मिलिए",
    startOver: "फिर से शुरू करें",
    listenAgain: "सुनिए",
    announced: "घोषणा कर दी गई है",
    somethingWrong: "कुछ गड़बड़ हुई, स्टाफ़ से संपर्क करें",
  },
  "mr-IN": {
    chooseLanguage: "तुमची भाषा निवडा",
    whoLookingFor: "तुम्ही कोणाला शोधत आहात?",
    speak: "बोला",
    listening: "ऐकत आहोत… थांबवण्यासाठी दाबा",
    typeInstead: "टाइप करा",
    typeHere: "इथे लिहा…",
    continue: "पुढे चला",
    back: "मागे",
    havePhoto: "फोटो आहे का?",
    takePhoto: "फोटो दाखवा",
    noPhoto: "फोटो नाही, पुढे चला",
    searching: "शोधत आहोत…",
    isThisCorrect: "बरोबर आहे का?",
    youAreLooking: (s) => `तुम्ही शोधत आहात: ${s} — बरोबर आहे का?`,
    yes: "होय",
    no: "नाही",
    didntCatch: "समजले नाही",
    speakAgain: "पुन्हा बोला",
    weFound: "आम्हाला हे लोक सापडले",
    weRegistered: "माहिती नोंदवली, सापडताच कळवू",
    whyMatched: "का जुळले",
    staffWillHelp: "कर्मचारी मदत करतील",
    connect: "यांना भेटा",
    startOver: "पुन्हा सुरू करा",
    listenAgain: "ऐका",
    announced: "घोषणा केली आहे",
    somethingWrong: "काहीतरी चूक झाली, कर्मचाऱ्यांशी संपर्क करा",
  },
  "ta-IN": {
    chooseLanguage: "உங்கள் மொழியைத் தேர்வுசெய்க",
    whoLookingFor: "யாரைத் தேடுகிறீர்கள்?",
    speak: "பேசுங்கள்",
    listening: "கேட்கிறோம்… நிறுத்த அழுத்தவும்",
    typeInstead: "தட்டச்சு செய்க",
    typeHere: "இங்கே எழுதுங்கள்…",
    continue: "தொடரவும்",
    back: "பின்செல்",
    havePhoto: "புகைப்படம் உள்ளதா?",
    takePhoto: "புகைப்படம் காட்டவும்",
    noPhoto: "புகைப்படம் இல்லை, தொடரவும்",
    searching: "தேடுகிறோம்…",
    isThisCorrect: "சரியா?",
    youAreLooking: (s) => `நீங்கள் தேடுவது: ${s} — சரியா?`,
    yes: "ஆம்",
    no: "இல்லை",
    didntCatch: "புரியவில்லை",
    speakAgain: "மீண்டும் பேசுங்கள்",
    weFound: "இவர்களைக் கண்டுபிடித்தோம்",
    weRegistered: "தகவல் பதிவாகியது, கிடைத்ததும் தெரிவிப்போம்",
    whyMatched: "ஏன் பொருந்தியது",
    staffWillHelp: "பணியாளர் உதவுவார்",
    connect: "இவரைச் சந்திக்கவும்",
    startOver: "மீண்டும் தொடங்கு",
    listenAgain: "கேளுங்கள்",
    announced: "அறிவிப்பு செய்யப்பட்டது",
    somethingWrong: "ஏதோ தவறு, பணியாளரைத் தொடர்பு கொள்ளவும்",
  },
  "te-IN": {
    chooseLanguage: "మీ భాషను ఎంచుకోండి",
    whoLookingFor: "మీరు ఎవరిని వెతుకుతున్నారు?",
    speak: "మాట్లాడండి",
    listening: "వింటున్నాం… ఆపడానికి నొక్కండి",
    typeInstead: "టైప్ చేయండి",
    typeHere: "ఇక్కడ రాయండి…",
    continue: "కొనసాగించండి",
    back: "వెనుకకు",
    havePhoto: "ఫోటో ఉందా?",
    takePhoto: "ఫోటో చూపించండి",
    noPhoto: "ఫోటో లేదు, కొనసాగించండి",
    searching: "వెతుకుతున్నాం…",
    isThisCorrect: "సరైనదేనా?",
    youAreLooking: (s) => `మీరు వెతుకుతున్నది: ${s} — సరైనదేనా?`,
    yes: "అవును",
    no: "కాదు",
    didntCatch: "అర్థం కాలేదు",
    speakAgain: "మళ్ళీ మాట్లాడండి",
    weFound: "మాకు వీరు దొరికారు",
    weRegistered: "సమాచారం నమోదైంది, దొరికిన వెంటనే తెలియజేస్తాం",
    whyMatched: "ఎందుకు సరిపోలింది",
    staffWillHelp: "సిబ్బంది సహాయం చేస్తారు",
    connect: "వీరిని కలవండి",
    startOver: "మళ్ళీ మొదలుపెట్టండి",
    listenAgain: "వినండి",
    announced: "ప్రకటన చేయబడింది",
    somethingWrong: "ఏదో తప్పు జరిగింది, సిబ్బందిని సంప్రదించండి",
  },
  "bn-IN": {
    chooseLanguage: "আপনার ভাষা বেছে নিন",
    whoLookingFor: "আপনি কাকে খুঁজছেন?",
    speak: "বলুন",
    listening: "শুনছি… থামাতে চাপুন",
    typeInstead: "টাইপ করুন",
    typeHere: "এখানে লিখুন…",
    continue: "এগিয়ে যান",
    back: "পিছনে",
    havePhoto: "ছবি আছে?",
    takePhoto: "ছবি দেখান",
    noPhoto: "ছবি নেই, এগিয়ে যান",
    searching: "খুঁজছি…",
    isThisCorrect: "ঠিক আছে?",
    youAreLooking: (s) => `আপনি খুঁজছেন: ${s} — ঠিক আছে?`,
    yes: "হ্যাঁ",
    no: "না",
    didntCatch: "বুঝতে পারিনি",
    speakAgain: "আবার বলুন",
    weFound: "আমরা এদের পেয়েছি",
    weRegistered: "তথ্য নথিভুক্ত হয়েছে, পেলেই জানাব",
    whyMatched: "কেন মিলল",
    staffWillHelp: "কর্মীরা সাহায্য করবেন",
    connect: "এদের সাথে দেখা করুন",
    startOver: "আবার শুরু করুন",
    listenAgain: "শুনুন",
    announced: "ঘোষণা করা হয়েছে",
    somethingWrong: "কিছু সমস্যা হয়েছে, কর্মীদের সাথে যোগাযোগ করুন",
  },
  "gu-IN": {
    chooseLanguage: "તમારી ભાષા પસંદ કરો",
    whoLookingFor: "તમે કોને શોધી રહ્યા છો?",
    speak: "બોલો",
    listening: "સાંભળી રહ્યા છીએ… રોકવા દબાવો",
    typeInstead: "ટાઇપ કરો",
    typeHere: "અહીં લખો…",
    continue: "આગળ વધો",
    back: "પાછળ",
    havePhoto: "ફોટો છે?",
    takePhoto: "ફોટો બતાવો",
    noPhoto: "ફોટો નથી, આગળ વધો",
    searching: "શોધી રહ્યા છીએ…",
    isThisCorrect: "બરાબર છે?",
    youAreLooking: (s) => `તમે શોધી રહ્યા છો: ${s} — બરાબર છે?`,
    yes: "હા",
    no: "ના",
    didntCatch: "સમજાયું નહીં",
    speakAgain: "ફરી બોલો",
    weFound: "અમને આ લોકો મળ્યા",
    weRegistered: "માહિતી નોંધાઈ, મળતાં જ જણાવીશું",
    whyMatched: "કેમ મેળ ખાધો",
    staffWillHelp: "સ્ટાફ મદદ કરશે",
    connect: "આમને મળો",
    startOver: "ફરી શરૂ કરો",
    listenAgain: "સાંભળો",
    announced: "જાહેરાત કરી દીધી છે",
    somethingWrong: "કંઈક ભૂલ થઈ, સ્ટાફનો સંપર્ક કરો",
  },
  "kn-IN": {
    chooseLanguage: "ನಿಮ್ಮ ಭಾಷೆಯನ್ನು ಆರಿಸಿ",
    whoLookingFor: "ನೀವು ಯಾರನ್ನು ಹುಡುಕುತ್ತಿದ್ದೀರಿ?",
    speak: "ಮಾತನಾಡಿ",
    listening: "ಕೇಳುತ್ತಿದ್ದೇವೆ… ನಿಲ್ಲಿಸಲು ಒತ್ತಿ",
    typeInstead: "ಟೈಪ್ ಮಾಡಿ",
    typeHere: "ಇಲ್ಲಿ ಬರೆಯಿರಿ…",
    continue: "ಮುಂದುವರಿಯಿರಿ",
    back: "ಹಿಂದೆ",
    havePhoto: "ಫೋಟೋ ಇದೆಯೇ?",
    takePhoto: "ಫೋಟೋ ತೋರಿಸಿ",
    noPhoto: "ಫೋಟೋ ಇಲ್ಲ, ಮುಂದುವರಿಯಿರಿ",
    searching: "ಹುಡುಕುತ್ತಿದ್ದೇವೆ…",
    isThisCorrect: "ಸರಿಯೇ?",
    youAreLooking: (s) => `ನೀವು ಹುಡುಕುತ್ತಿರುವುದು: ${s} — ಸರಿಯೇ?`,
    yes: "ಹೌದು",
    no: "ಇಲ್ಲ",
    didntCatch: "ಅರ್ಥವಾಗಲಿಲ್ಲ",
    speakAgain: "ಮತ್ತೆ ಮಾತನಾಡಿ",
    weFound: "ನಮಗೆ ಇವರು ಸಿಕ್ಕರು",
    weRegistered: "ಮಾಹಿತಿ ದಾಖಲಾಗಿದೆ, ಸಿಕ್ಕ ಕೂಡಲೇ ತಿಳಿಸುತ್ತೇವೆ",
    whyMatched: "ಏಕೆ ಹೊಂದಿಕೆಯಾಯಿತು",
    staffWillHelp: "ಸಿಬ್ಬಂದಿ ಸಹಾಯ ಮಾಡುತ್ತಾರೆ",
    connect: "ಇವರನ್ನು ಭೇಟಿಯಾಗಿ",
    startOver: "ಮತ್ತೆ ಪ್ರಾರಂಭಿಸಿ",
    listenAgain: "ಕೇಳಿ",
    announced: "ಘೋಷಣೆ ಮಾಡಲಾಗಿದೆ",
    somethingWrong: "ಏನೋ ತಪ್ಪಾಗಿದೆ, ಸಿಬ್ಬಂದಿಯನ್ನು ಸಂಪರ್ಕಿಸಿ",
  },
  "ml-IN": {
    chooseLanguage: "നിങ്ങളുടെ ഭാഷ തിരഞ്ഞെടുക്കുക",
    whoLookingFor: "നിങ്ങൾ ആരെയാണ് തിരയുന്നത്?",
    speak: "സംസാരിക്കൂ",
    listening: "കേൾക്കുന്നു… നിർത്താൻ അമർത്തുക",
    typeInstead: "ടൈപ്പ് ചെയ്യുക",
    typeHere: "ഇവിടെ എഴുതുക…",
    continue: "തുടരുക",
    back: "പുറകോട്ട്",
    havePhoto: "ഫോട്ടോ ഉണ്ടോ?",
    takePhoto: "ഫോട്ടോ കാണിക്കുക",
    noPhoto: "ഫോട്ടോ ഇല്ല, തുടരുക",
    searching: "തിരയുന്നു…",
    isThisCorrect: "ശരിയാണോ?",
    youAreLooking: (s) => `നിങ്ങൾ തിരയുന്നത്: ${s} — ശരിയാണോ?`,
    yes: "അതെ",
    no: "അല്ല",
    didntCatch: "മനസ്സിലായില്ല",
    speakAgain: "വീണ്ടും പറയൂ",
    weFound: "ഞങ്ങൾ ഇവരെ കണ്ടെത്തി",
    weRegistered: "വിവരം രേഖപ്പെടുത്തി, കിട്ടിയാൽ അറിയിക്കും",
    whyMatched: "എന്തുകൊണ്ട് യോജിച്ചു",
    staffWillHelp: "ജീവനക്കാർ സഹായിക്കും",
    connect: "ഇവരെ കാണുക",
    startOver: "വീണ്ടും തുടങ്ങുക",
    listenAgain: "കേൾക്കൂ",
    announced: "അറിയിപ്പ് നൽകി",
    somethingWrong: "എന്തോ തെറ്റ് സംഭവിച്ചു, ജീവനക്കാരെ ബന്ധപ്പെടുക",
  },
  "en-IN": {
    chooseLanguage: "Choose your language",
    whoLookingFor: "Who are you looking for?",
    speak: "Speak",
    listening: "Listening… tap to stop",
    typeInstead: "Type instead",
    typeHere: "Write here…",
    continue: "Continue",
    back: "Back",
    havePhoto: "Have a photo?",
    takePhoto: "Take / choose photo",
    noPhoto: "No photo, continue",
    searching: "Searching…",
    isThisCorrect: "Is this correct?",
    youAreLooking: (s) => `You are looking for: ${s} — correct?`,
    yes: "Yes",
    no: "No",
    didntCatch: "Didn't catch that",
    speakAgain: "Speak again",
    weFound: "We found these people",
    weRegistered: "Your report is registered, we'll tell you when we find them",
    whyMatched: "Why it matched",
    staffWillHelp: "Staff will help you",
    connect: "Connect",
    startOver: "Start over",
    listenAgain: "Listen again",
    announced: "Announcement made",
    somethingWrong: "Something went wrong, please contact staff",
  },
};

// --- Tap-first option labels (panic-friendly: choose, don't type) ---
export interface OptStrings {
  detailsTitle: string;
  genderQ: string;
  male: string;
  female: string;
  notSure: string;
  ageQ: string;
  locationQ: string;
  skip: string;
  addDetails: string;
}

const OPTS: Record<Lang, OptStrings> = {
  "hi-IN": { detailsTitle: "जानकारी चुनिए", genderQ: "पुरुष या महिला?", male: "पुरुष", female: "महिला", notSure: "पता नहीं", ageQ: "उम्र?", locationQ: "कहाँ खोया?", skip: "छोड़ें", addDetails: "या टैप करके बताइए" },
  "mr-IN": { detailsTitle: "माहिती निवडा", genderQ: "पुरुष की स्त्री?", male: "पुरुष", female: "स्त्री", notSure: "माहीत नाही", ageQ: "वय?", locationQ: "कुठे हरवले?", skip: "वगळा", addDetails: "किंवा टॅप करून सांगा" },
  "ta-IN": { detailsTitle: "விவரம் தேர்வு", genderQ: "ஆணா பெண்ணா?", male: "ஆண்", female: "பெண்", notSure: "தெரியாது", ageQ: "வயது?", locationQ: "எங்கே தொலைந்தது?", skip: "தவிர்", addDetails: "அல்லது தட்டிச் சொல்லுங்கள்" },
  "te-IN": { detailsTitle: "వివరాలు ఎంచుకోండి", genderQ: "పురుషుడా స్త్రీనా?", male: "పురుషుడు", female: "స్త్రీ", notSure: "తెలియదు", ageQ: "వయసు?", locationQ: "ఎక్కడ తప్పిపోయారు?", skip: "దాటవేయి", addDetails: "లేదా నొక్కి చెప్పండి" },
  "bn-IN": { detailsTitle: "তথ্য বেছে নিন", genderQ: "পুরুষ না মহিলা?", male: "পুরুষ", female: "মহিলা", notSure: "জানি না", ageQ: "বয়স?", locationQ: "কোথায় হারিয়েছে?", skip: "এড়িয়ে যান", addDetails: "অথবা ট্যাপ করে বলুন" },
  "gu-IN": { detailsTitle: "માહિતી પસંદ કરો", genderQ: "પુરુષ કે સ્ત્રી?", male: "પુરુષ", female: "સ્ત્રી", notSure: "ખબર નથી", ageQ: "ઉંમર?", locationQ: "ક્યાં ખોવાયા?", skip: "છોડો", addDetails: "અથવા ટેપ કરીને કહો" },
  "kn-IN": { detailsTitle: "ವಿವರ ಆಯ್ಕೆಮಾಡಿ", genderQ: "ಪುರುಷ ಅಥವಾ ಮಹಿಳೆ?", male: "ಪುರುಷ", female: "ಮಹಿಳೆ", notSure: "ಗೊತ್ತಿಲ್ಲ", ageQ: "ವಯಸ್ಸು?", locationQ: "ಎಲ್ಲಿ ಕಳೆದುಹೋದರು?", skip: "ಬಿಟ್ಟುಬಿಡಿ", addDetails: "ಅಥವಾ ಒತ್ತಿ ಹೇಳಿ" },
  "ml-IN": { detailsTitle: "വിവരം തിരഞ്ഞെടുക്കുക", genderQ: "പുരുഷനോ സ്ത്രീയോ?", male: "പുരുഷൻ", female: "സ്ത്രീ", notSure: "അറിയില്ല", ageQ: "വയസ്സ്?", locationQ: "എവിടെ കാണാതായി?", skip: "ഒഴിവാക്കുക", addDetails: "അല്ലെങ്കിൽ ടാപ്പ് ചെയ്ത് പറയൂ" },
  "en-IN": { detailsTitle: "Add details", genderQ: "Man or woman?", male: "Man", female: "Woman", notSure: "Not sure", ageQ: "How old?", locationQ: "Last seen where?", skip: "Skip", addDetails: "Or tap to add details" },
};

// --- Single-screen report intake + submission states ---
export interface ReportStrings {
  reportTitle: string;
  reportSub: string;
  who: string;
  where: string;
  contact: string;
  optional: string;
  name: string;
  voiceNote: string;
  whenQ: string;
  justNow: string;
  lt1hr: string;
  today: string;
  earlier: string;
  mobileHelp: string;
  addPhoto: string;
  photoAdded: string;
  locationAuto: string;
  priorityMinor: string;
  priorityElderly: string;
  submit: string;
  showVolunteer: string;
  submitting: string;
  submittingSub: string;
  successTitle: string;
  caseId: string;
  whatNow: string;
  searchingCenters: string;
  matching: string;
  willCall: string;
  saveCaseId: string;
  reportAnother: string;
  failTitle: string;
  failSaved: string;
  tryAgain: string;
  saveOffline: string;
  offlineBanner: string;
}

const REPORTS: Record<Lang, ReportStrings> = {
  "hi-IN": { reportTitle: "गुमशुदा की रिपोर्ट दर्ज करें", reportSub: "रिपोर्ट देते ही हम खोजना शुरू कर देंगे।", who: "कौन गुम है", where: "कहाँ आख़िरी बार देखा", contact: "आपका संपर्क", optional: "और कुछ (वैकल्पिक)", name: "नाम (वैकल्पिक)", voiceNote: "🎤 हुलिया बोलकर बताइए", whenQ: "कब?", justNow: "अभी", lt1hr: "1 घंटे में", today: "आज", earlier: "पहले", mobileHelp: "मिलते ही हम इसी नंबर पर कॉल करेंगे", addPhoto: "📷 फोटो जोड़ें", photoAdded: "✓ फोटो जुड़ गई", locationAuto: "📍 जगह: अपने आप", priorityMinor: "⚠ बच्चा — स्टाफ़ को तुरंत सूचना", priorityElderly: "⚠ बुज़ुर्ग — प्राथमिकता पर", submit: "रिपोर्ट दें", showVolunteer: "मदद? किसी स्वयंसेवक को दिखाएँ", submitting: "भेज रहे हैं…", submittingSub: "आपकी रिपोर्ट सुरक्षित भेजी जा रही है", successTitle: "रिपोर्ट दर्ज हो गई", caseId: "केस नंबर", whatNow: "अब आगे:", searchingCenters: "सभी केंद्रों व CCTV में खोज", matching: "पूरे मेले में मिलान", willCall: "मिलते ही हम कॉल करेंगे", saveCaseId: "📋 केस नंबर सेव करें", reportAnother: "दूसरी रिपोर्ट दें", failTitle: "अभी नहीं भेज सके", failSaved: "आपकी रिपोर्ट इस डिवाइस पर सेव है", tryAgain: "↻ फिर कोशिश करें", saveOffline: "ऑफलाइन सेव करें — अपने आप भेजेंगे", offlineBanner: "⏳ ऑफलाइन सेव — ऑनलाइन होते ही भेजेंगे" },
  "mr-IN": { reportTitle: "हरवलेल्याची तक्रार नोंदवा", reportSub: "तक्रार देताच आम्ही शोध सुरू करू.", who: "कोण हरवले", where: "शेवटचे कुठे पाहिले", contact: "तुमचा संपर्क", optional: "आणखी काही (ऐच्छिक)", name: "नाव (ऐच्छिक)", voiceNote: "🎤 वर्णन बोलून सांगा", whenQ: "केव्हा?", justNow: "आत्ताच", lt1hr: "1 तासात", today: "आज", earlier: "आधी", mobileHelp: "सापडताच आम्ही याच नंबरवर कॉल करू", addPhoto: "📷 फोटो जोडा", photoAdded: "✓ फोटो जोडला", locationAuto: "📍 ठिकाण: आपोआप", priorityMinor: "⚠ लहान मूल — कर्मचाऱ्यांना त्वरित सूचना", priorityElderly: "⚠ वृद्ध — प्राधान्याने", submit: "तक्रार द्या", showVolunteer: "मदत? स्वयंसेवकाला दाखवा", submitting: "पाठवत आहोत…", submittingSub: "तुमची तक्रार सुरक्षित पाठवली जात आहे", successTitle: "तक्रार नोंदवली", caseId: "केस क्रमांक", whatNow: "आता पुढे:", searchingCenters: "सर्व केंद्रे व CCTV मध्ये शोध", matching: "संपूर्ण मेळ्यात जुळवणी", willCall: "सापडताच आम्ही कॉल करू", saveCaseId: "📋 केस क्रमांक सेव्ह करा", reportAnother: "दुसरी तक्रार द्या", failTitle: "आत्ता पाठवता आले नाही", failSaved: "तुमची तक्रार या डिव्हाइसवर सेव्ह आहे", tryAgain: "↻ पुन्हा प्रयत्न करा", saveOffline: "ऑफलाइन सेव्ह — आपोआप पाठवू", offlineBanner: "⏳ ऑफलाइन सेव्ह — ऑनलाइन होताच पाठवू" },
  "ta-IN": { reportTitle: "காணாமல் போனவர் புகார் பதிவு", reportSub: "புகார் தந்தவுடன் தேடத் தொடங்குவோம்.", who: "யார் காணவில்லை", where: "கடைசியாக எங்கே", contact: "உங்கள் தொடர்பு", optional: "மேலும் (விருப்பம்)", name: "பெயர் (விருப்பம்)", voiceNote: "🎤 தோற்றத்தைப் பேசுங்கள்", whenQ: "எப்போது?", justNow: "இப்போது", lt1hr: "1 மணி நேரத்தில்", today: "இன்று", earlier: "முன்பு", mobileHelp: "கண்டதும் இந்த எண்ணுக்கு அழைப்போம்", addPhoto: "📷 புகைப்படம் சேர்க்க", photoAdded: "✓ புகைப்படம் சேர்க்கப்பட்டது", locationAuto: "📍 இடம்: தானாக", priorityMinor: "⚠ குழந்தை — பணியாளருக்கு உடனடி தகவல்", priorityElderly: "⚠ முதியவர் — முன்னுரிமை", submit: "புகார் தர", showVolunteer: "உதவி? தொண்டருக்குக் காட்டுங்கள்", submitting: "அனுப்புகிறோம்…", submittingSub: "உங்கள் புகார் பாதுகாப்பாக அனுப்பப்படுகிறது", successTitle: "புகார் பதிவாகியது", caseId: "வழக்கு எண்", whatNow: "அடுத்து:", searchingCenters: "அனைத்து மையங்கள் & CCTV தேடல்", matching: "மேளா முழுவதும் பொருத்தம்", willCall: "கண்டதும் அழைப்போம்", saveCaseId: "📋 வழக்கு எண்ணை சேமி", reportAnother: "மற்றொரு புகார்", failTitle: "இப்போது அனுப்ப முடியவில்லை", failSaved: "உங்கள் புகார் இந்த சாதனத்தில் சேமிக்கப்பட்டது", tryAgain: "↻ மீண்டும் முயற்சி", saveOffline: "ஆஃப்லைனில் சேமி — தானாக அனுப்பும்", offlineBanner: "⏳ ஆஃப்லைனில் சேமிப்பு — ஆன்லைனானதும் அனுப்பும்" },
  "te-IN": { reportTitle: "తప్పిపోయిన వ్యక్తి ఫిర్యాదు", reportSub: "ఫిర్యాదు ఇవ్వగానే వెతకడం మొదలుపెడతాం.", who: "ఎవరు తప్పిపోయారు", where: "చివరిగా ఎక్కడ", contact: "మీ సంప్రదింపు", optional: "మరిన్ని (ఐచ్ఛికం)", name: "పేరు (ఐచ్ఛికం)", voiceNote: "🎤 రూపం చెప్పండి", whenQ: "ఎప్పుడు?", justNow: "ఇప్పుడే", lt1hr: "1 గంటలో", today: "ఈరోజు", earlier: "ముందు", mobileHelp: "దొరికిన వెంటనే ఈ నంబర్‌కు కాల్ చేస్తాం", addPhoto: "📷 ఫోటో జోడించండి", photoAdded: "✓ ఫోటో జోడించబడింది", locationAuto: "📍 స్థలం: ఆటోమేటిక్", priorityMinor: "⚠ పిల్లవాడు — సిబ్బందికి తక్షణ సమాచారం", priorityElderly: "⚠ వృద్ధులు — ప్రాధాన్యత", submit: "ఫిర్యాదు ఇవ్వండి", showVolunteer: "సహాయం? వాలంటీర్‌కు చూపండి", submitting: "పంపుతున్నాం…", submittingSub: "మీ ఫిర్యాదు సురక్షితంగా పంపబడుతోంది", successTitle: "ఫిర్యాదు నమోదైంది", caseId: "కేసు నంబర్", whatNow: "ఇప్పుడు:", searchingCenters: "అన్ని కేంద్రాలు & CCTV శోధన", matching: "మేళా అంతటా సరిపోల్చడం", willCall: "దొరికిన వెంటనే కాల్ చేస్తాం", saveCaseId: "📋 కేసు నంబర్ సేవ్ చేయండి", reportAnother: "మరో ఫిర్యాదు", failTitle: "ఇప్పుడు పంపలేకపోయాం", failSaved: "మీ ఫిర్యాదు ఈ పరికరంలో సేవ్ అయింది", tryAgain: "↻ మళ్ళీ ప్రయత్నించండి", saveOffline: "ఆఫ్‌లైన్ సేవ్ — ఆటోమేటిక్‌గా పంపుతాం", offlineBanner: "⏳ ఆఫ్‌లైన్ సేవ్ — ఆన్‌లైన్ కాగానే పంపుతాం" },
  "bn-IN": { reportTitle: "নিখোঁজ ব্যক্তির রিপোর্ট করুন", reportSub: "রিপোর্ট দিলেই আমরা খোঁজা শুরু করব।", who: "কে নিখোঁজ", where: "শেষ কোথায় দেখা", contact: "আপনার যোগাযোগ", optional: "আরও কিছু (ঐচ্ছিক)", name: "নাম (ঐচ্ছিক)", voiceNote: "🎤 চেহারা বলে দিন", whenQ: "কখন?", justNow: "এইমাত্র", lt1hr: "১ ঘণ্টায়", today: "আজ", earlier: "আগে", mobileHelp: "পেলেই আমরা এই নম্বরে কল করব", addPhoto: "📷 ছবি যোগ করুন", photoAdded: "✓ ছবি যোগ হয়েছে", locationAuto: "📍 স্থান: স্বয়ংক্রিয়", priorityMinor: "⚠ শিশু — কর্মীদের তাৎক্ষণিক জানানো", priorityElderly: "⚠ বয়স্ক — অগ্রাধিকার", submit: "রিপোর্ট দিন", showVolunteer: "সাহায্য? স্বেচ্ছাসেবককে দেখান", submitting: "পাঠানো হচ্ছে…", submittingSub: "আপনার রিপোর্ট নিরাপদে পাঠানো হচ্ছে", successTitle: "রিপোর্ট জমা হয়েছে", caseId: "কেস নম্বর", whatNow: "এখন:", searchingCenters: "সব কেন্দ্র ও CCTV খোঁজা", matching: "পুরো মেলায় মিলানো", willCall: "পেলেই আমরা কল করব", saveCaseId: "📋 কেস নম্বর সেভ করুন", reportAnother: "আরেকটি রিপোর্ট", failTitle: "এখন পাঠানো গেল না", failSaved: "আপনার রিপোর্ট এই ডিভাইসে সেভ আছে", tryAgain: "↻ আবার চেষ্টা করুন", saveOffline: "অফলাইন সেভ — স্বয়ংক্রিয়ভাবে পাঠাবে", offlineBanner: "⏳ অফলাইন সেভ — অনলাইন হলেই পাঠাবে" },
  "gu-IN": { reportTitle: "ગુમ થયેલ વ્યક્તિની ફરિયાદ", reportSub: "ફરિયાદ આપતાં જ અમે શોધ શરૂ કરીશું.", who: "કોણ ગુમ છે", where: "છેલ્લે ક્યાં જોયા", contact: "તમારો સંપર્ક", optional: "બીજું કંઈ (વૈકલ્પિક)", name: "નામ (વૈકલ્પિક)", voiceNote: "🎤 દેખાવ બોલીને કહો", whenQ: "ક્યારે?", justNow: "હમણાં જ", lt1hr: "1 કલાકમાં", today: "આજે", earlier: "પહેલાં", mobileHelp: "મળતાં જ અમે આ નંબર પર કૉલ કરીશું", addPhoto: "📷 ફોટો ઉમેરો", photoAdded: "✓ ફોટો ઉમેરાયો", locationAuto: "📍 સ્થળ: આપમેળે", priorityMinor: "⚠ બાળક — સ્ટાફને તાત્કાલિક જાણ", priorityElderly: "⚠ વૃદ્ધ — પ્રાથમિકતા", submit: "ફરિયાદ આપો", showVolunteer: "મદદ? સ્વયંસેવકને બતાવો", submitting: "મોકલી રહ્યા છીએ…", submittingSub: "તમારી ફરિયાદ સુરક્ષિત મોકલાઈ રહી છે", successTitle: "ફરિયાદ નોંધાઈ", caseId: "કેસ નંબર", whatNow: "હવે:", searchingCenters: "બધા કેન્દ્રો અને CCTV શોધ", matching: "આખા મેળામાં મેળ", willCall: "મળતાં જ અમે કૉલ કરીશું", saveCaseId: "📋 કેસ નંબર સેવ કરો", reportAnother: "બીજી ફરિયાદ", failTitle: "અત્યારે મોકલી શકાયું નહીં", failSaved: "તમારી ફરિયાદ આ ડિવાઇસ પર સેવ છે", tryAgain: "↻ ફરી પ્રયાસ કરો", saveOffline: "ઑફલાઇન સેવ — આપમેળે મોકલશે", offlineBanner: "⏳ ઑફલાઇન સેવ — ઑનલાઇન થતાં મોકલશે" },
  "kn-IN": { reportTitle: "ಕಾಣೆಯಾದ ವ್ಯಕ್ತಿಯ ದೂರು", reportSub: "ದೂರು ನೀಡಿದ ತಕ್ಷಣ ಹುಡುಕಲು ಪ್ರಾರಂಭಿಸುತ್ತೇವೆ.", who: "ಯಾರು ಕಾಣೆಯಾಗಿದ್ದಾರೆ", where: "ಕೊನೆಯದಾಗಿ ಎಲ್ಲಿ", contact: "ನಿಮ್ಮ ಸಂಪರ್ಕ", optional: "ಇನ್ನಷ್ಟು (ಐಚ್ಛಿಕ)", name: "ಹೆಸರು (ಐಚ್ಛಿಕ)", voiceNote: "🎤 ರೂಪವನ್ನು ಹೇಳಿ", whenQ: "ಯಾವಾಗ?", justNow: "ಈಗಷ್ಟೇ", lt1hr: "1 ಗಂಟೆಯಲ್ಲಿ", today: "ಇಂದು", earlier: "ಮೊದಲು", mobileHelp: "ಸಿಕ್ಕ ಕೂಡಲೇ ಈ ನಂಬರ್‌ಗೆ ಕರೆ ಮಾಡುತ್ತೇವೆ", addPhoto: "📷 ಫೋಟೋ ಸೇರಿಸಿ", photoAdded: "✓ ಫೋಟೋ ಸೇರಿಸಲಾಗಿದೆ", locationAuto: "📍 ಸ್ಥಳ: ಸ್ವಯಂ", priorityMinor: "⚠ ಮಗು — ಸಿಬ್ಬಂದಿಗೆ ತಕ್ಷಣ ಸೂಚನೆ", priorityElderly: "⚠ ಹಿರಿಯರು — ಆದ್ಯತೆ", submit: "ದೂರು ನೀಡಿ", showVolunteer: "ಸಹಾಯ? ಸ್ವಯಂಸೇವಕರಿಗೆ ತೋರಿಸಿ", submitting: "ಕಳುಹಿಸುತ್ತಿದ್ದೇವೆ…", submittingSub: "ನಿಮ್ಮ ದೂರು ಸುರಕ್ಷಿತವಾಗಿ ಕಳುಹಿಸಲಾಗುತ್ತಿದೆ", successTitle: "ದೂರು ದಾಖಲಾಗಿದೆ", caseId: "ಕೇಸ್ ಸಂಖ್ಯೆ", whatNow: "ಈಗ:", searchingCenters: "ಎಲ್ಲಾ ಕೇಂದ್ರಗಳು & CCTV ಹುಡುಕಾಟ", matching: "ಇಡೀ ಮೇಳದಲ್ಲಿ ಹೊಂದಾಣಿಕೆ", willCall: "ಸಿಕ್ಕ ಕೂಡಲೇ ಕರೆ ಮಾಡುತ್ತೇವೆ", saveCaseId: "📋 ಕೇಸ್ ಸಂಖ್ಯೆ ಉಳಿಸಿ", reportAnother: "ಇನ್ನೊಂದು ದೂರು", failTitle: "ಈಗ ಕಳುಹಿಸಲಾಗಲಿಲ್ಲ", failSaved: "ನಿಮ್ಮ ದೂರು ಈ ಸಾಧನದಲ್ಲಿ ಉಳಿಸಲಾಗಿದೆ", tryAgain: "↻ ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ", saveOffline: "ಆಫ್‌ಲೈನ್ ಉಳಿಸಿ — ಸ್ವಯಂ ಕಳುಹಿಸುತ್ತದೆ", offlineBanner: "⏳ ಆಫ್‌ಲೈನ್ ಉಳಿಸಲಾಗಿದೆ — ಆನ್‌ಲೈನ್ ಆದಾಗ ಕಳುಹಿಸುತ್ತದೆ" },
  "ml-IN": { reportTitle: "കാണാതായ ആളെക്കുറിച്ച് റിപ്പോർട്ട്", reportSub: "റിപ്പോർട്ട് നൽകിയാലുടൻ തിരച്ചിൽ തുടങ്ങും.", who: "ആരെ കാണാനില്ല", where: "അവസാനം എവിടെ", contact: "നിങ്ങളുടെ ബന്ധപ്പെടൽ", optional: "കൂടുതൽ (ഓപ്ഷണൽ)", name: "പേര് (ഓപ്ഷണൽ)", voiceNote: "🎤 രൂപം പറയൂ", whenQ: "എപ്പോൾ?", justNow: "ഇപ്പോൾ", lt1hr: "1 മണിക്കൂറിൽ", today: "ഇന്ന്", earlier: "നേരത്തെ", mobileHelp: "കണ്ടെത്തിയാലുടൻ ഈ നമ്പറിൽ വിളിക്കും", addPhoto: "📷 ഫോട്ടോ ചേർക്കുക", photoAdded: "✓ ഫോട്ടോ ചേർത്തു", locationAuto: "📍 സ്ഥലം: സ്വയം", priorityMinor: "⚠ കുട്ടി — ജീവനക്കാർക്ക് ഉടൻ അറിയിപ്പ്", priorityElderly: "⚠ വയോധികർ — മുൻഗണന", submit: "റിപ്പോർട്ട് നൽകൂ", showVolunteer: "സഹായം? വോളണ്ടിയറെ കാണിക്കൂ", submitting: "അയക്കുന്നു…", submittingSub: "നിങ്ങളുടെ റിപ്പോർട്ട് സുരക്ഷിതമായി അയക്കുന്നു", successTitle: "റിപ്പോർട്ട് രേഖപ്പെടുത്തി", caseId: "കേസ് നമ്പർ", whatNow: "ഇനി:", searchingCenters: "എല്ലാ കേന്ദ്രങ്ങളും CCTV യും തിരയുന്നു", matching: "മേള മുഴുവൻ പൊരുത്തപ്പെടുത്തൽ", willCall: "കണ്ടെത്തിയാലുടൻ വിളിക്കും", saveCaseId: "📋 കേസ് നമ്പർ സേവ് ചെയ്യൂ", reportAnother: "മറ്റൊരു റിപ്പോർട്ട്", failTitle: "ഇപ്പോൾ അയക്കാനായില്ല", failSaved: "നിങ്ങളുടെ റിപ്പോർട്ട് ഈ ഉപകരണത്തിൽ സേവ് ചെയ്തു", tryAgain: "↻ വീണ്ടും ശ്രമിക്കൂ", saveOffline: "ഓഫ്‌ലൈൻ സേവ് — സ്വയം അയക്കും", offlineBanner: "⏳ ഓഫ്‌ലൈൻ സേവ് — ഓൺലൈൻ ആകുമ്പോൾ അയക്കും" },
  "en-IN": { reportTitle: "Report a Missing Person", reportSub: "We start searching the moment you submit.", who: "Who is missing", where: "Where last seen", contact: "Your contact", optional: "Anything else (optional)", name: "Name (optional)", voiceNote: "🎤 Describe by voice", whenQ: "When?", justNow: "Just now", lt1hr: "< 1 hr", today: "Today", earlier: "Earlier", mobileHelp: "We'll call this number the moment we find them", addPhoto: "📷 Add photo", photoAdded: "✓ Photo added", locationAuto: "📍 Location: auto", priorityMinor: "⚠ Child — staff alerted immediately", priorityElderly: "⚠ Elderly — prioritised", submit: "Submit Report", showVolunteer: "Need help? Show a volunteer", submitting: "Submitting…", submittingSub: "Sending your report securely to all centers", successTitle: "Report submitted", caseId: "Case ID", whatNow: "What happens now:", searchingCenters: "Searching all centers + CCTV", matching: "Matching across the whole Mela", willCall: "We will call you the moment we find them", saveCaseId: "📋 Save Case ID", reportAnother: "Report another person", failTitle: "Couldn't send right now", failSaved: "Your report is saved on this device", tryAgain: "↻ Try again", saveOffline: "Save offline — send automatically", offlineBanner: "⏳ Saved offline — will send when online" },
};

// Always show an English subtitle under the native text — helps staff + mixed crowds.
export const EN = STRINGS["en-IN"];
export const ENOPT = OPTS["en-IN"];
export const ENREPORT = REPORTS["en-IN"];

export function t(lang: Lang): Strings {
  return STRINGS[lang] ?? STRINGS["hi-IN"];
}

export function opt(lang: Lang): OptStrings {
  return OPTS[lang] ?? OPTS["hi-IN"];
}

export function report(lang: Lang): ReportStrings {
  return REPORTS[lang] ?? REPORTS["hi-IN"];
}
