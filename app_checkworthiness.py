import streamlit as st
import pandas as pd
import gspread
import datetime
import os
import threading
from google.oauth2.service_account import Credentials
from streamlit_text_label import label_select
import random

# Force Light Mode 
st.markdown(
    """
    <style>
        body {
            background-color: white !important;
            color: black !important;
        }
        .stApp {
            background-color: white !important;
        }
    </style>
    """,
    unsafe_allow_html=True
)


# --- GOOGLE SHEETS SETUP ---
GOOGLE_CREDENTIALS = st.secrets["GOOGLE_CREDENTIALS"]
SHEET_ID = st.secrets["SHEET_ID"]

# Authenticate Google Sheets
creds = Credentials.from_service_account_info(GOOGLE_CREDENTIALS, scopes=["https://www.googleapis.com/auth/spreadsheets"])
gc = gspread.authorize(creds)

# --- GOOGLE SHEETS FUNCTIONS ---
def fetch_allowed_users():
    """Fetch allowed users and from the 'allowed_users' tab in the connected Google Sheet."""
    spreadsheet = gc.open_by_key(SHEET_ID)
    worksheet = spreadsheet.worksheet("allowed_users_Checkworthiness")  # changing to another sheet for admin control
    
    # Get users
    allowed_users = worksheet.col_values(1)  
    return set(allowed_users)

def get_user_worksheet(user_id):
    """ Ensure each user has a personal worksheet. Create one if it doesn’t exist. """
    spreadsheet = gc.open_by_key(SHEET_ID)
    try:
        return spreadsheet.worksheet(user_id)
    except gspread.exceptions.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title=user_id, rows="1000", cols="12")
        worksheet.insert_row(
            ["user_id", 
             "text_index", 
             "full_text", 
             "debate_unit_id",

             # Labels
             "check_worthy",
             "other",

             "comment_field",
             "timestamp"],
            index=1
        )
        return worksheet

def get_annotated_texts(user_id):
    """ Fetch already annotated texts for the user. """
    worksheet = get_user_worksheet(user_id)
    data = worksheet.get_all_values()
    if len(data) > 1:
        df_annotations = pd.DataFrame(data[1:], columns=["user_id", 
                                                         "text_index", 
                                                         "full_text", 
                                                         "debate_unit_id",

                                                         "check_worthy",
                                                         "other",

                                                         "comment_field",
                                                         "timestamp"])
        return set(df_annotations["full_text"].tolist())
    return set()

def save_annotations(user_id, annotations):
    """ Save annotations asynchronously to Google Sheets. """
    worksheet = get_user_worksheet(user_id)
    worksheet.append_rows(annotations)

# --- STREAMLIT APP SETUP ---
st.sidebar.title("Brugerlogin")

# ✅ Load allowed users only once per session
if "ALLOWED_USERS" not in st.session_state:
    st.session_state.ALLOWED_USERS = fetch_allowed_users()

# ✅ Check if user is logged in
if "user_id" not in st.session_state:
    user_id = st.sidebar.text_input("Indtast dit bruger-ID:")
    if st.sidebar.button("Log in") and user_id.strip():
        if user_id.strip() in st.session_state.ALLOWED_USERS:
            st.session_state.user_id = user_id.strip()
            st.session_state.text_index = -1
            st.session_state.annotations = []
            st.session_state.annotated_texts = get_annotated_texts(user_id)
            st.session_state.worksheet_ready = False
            st.session_state.finished = False
            st.rerun()
        else:
            st.sidebar.error("❌ Adgang nægtet: Dit bruger-ID er ikke autoriseret.")
else:
    user_id = st.session_state.user_id
    st.sidebar.success(f"✅ Du er logget ind som: **{user_id}**")

    if st.sidebar.button("Log ud"):
        if st.session_state.annotations:
            threading.Thread(target=save_annotations, args=(user_id, st.session_state.annotations), daemon=True).start()
            st.session_state.annotations = []
        st.session_state.clear()
        st.rerun()

# 🚨 Block annotation until user logs in
if "user_id" not in st.session_state:
    st.warning("Indtast dit bruger-ID ude til venstre for at begynde at annotere.")
    st.stop()

# ✅ Ensure each user has their personal worksheet (but do not block UI)
if not st.session_state.get("worksheet_ready", False):
    threading.Thread(target=get_user_worksheet, args=(user_id,), daemon=True).start()
    st.session_state.worksheet_ready = True

# --- LOAD TEXTS FROM LOCAL FILE ---
BASE_DIR = os.getcwd()

# ✅ Dynamically assign each user to their personal data folder
DATA_FOLDER = os.path.join(BASE_DIR, "data", "clean", st.session_state.user_id)
DATA_FILE = os.path.join(DATA_FOLDER, "processed_texts_test_check_worthy.txt")

# ✅ Check if the personal folder exists
if not os.path.exists(DATA_FILE):
    st.error(f"🚨 Data file missing for user: `{st.session_state.user_id}`! Ensure `{DATA_FILE}` exists.")
    st.stop()

#if not os.path.exists(DATA_FILE):
#    st.error("Text file missing! Run `preprocess.py` first.")
#    st.stop()

with open(DATA_FILE, "r", encoding="utf-8") as file:
    texts = [line.strip() for line in file if line.strip()]

df_texts = pd.DataFrame(texts, columns=["text"])

# ✅ Remove already annotated texts # herhen
unannotated_texts = df_texts[~df_texts["text"].isin(st.session_state.annotated_texts)]["text"].tolist() # was text before

# ✅ Ensure `text_index` is initialized correctly
if "text_index" not in st.session_state or st.session_state.text_index == -1:
    st.session_state.text_index = 0

# ✅ If all texts are annotated, trigger completion message immediately
if len(unannotated_texts) == 0 or st.session_state.get("finished", False):
    st.session_state.finished = True
    st.success("🎉 Du har annoteret alle tekster!")
    st.info("✅ Du kan nu logge ud via knappen i sidebaren.")
    
    if st.session_state.annotations:
        threading.Thread(target=save_annotations, args=(user_id, st.session_state.annotations), daemon=True).start()
        st.session_state.annotations = []
    
    st.stop()

# ✅ If user has finished all texts, show completion message
if st.session_state.text_index >= len(unannotated_texts):
    st.session_state.finished = True
    st.success("🎉 Du har annoteret alle tekster!")
    st.info("✅ Du kan nu logge ud via knappen i sidebaren.")

    if st.session_state.annotations:
        threading.Thread(target=save_annotations, args=(user_id, st.session_state.annotations.copy()), daemon=True).start()
        st.session_state.annotations = []

    st.stop()

# ✅ Get the next text properly
current_text = unannotated_texts[st.session_state.text_index]

# --- TEXT HIGHLIGHTING ---
st.markdown("## Hvilke udsagn bør faktatjekkes? 🔍🧑‍💻📚")
st.markdown("##### Sådan bruges siden:")
st.markdown("1) **Markér de udsagn, der bør faktatjekkes**, dvs. udsagn som den generelle offentlighed kunne have interesse i at få verificeret.")
st.markdown("2) Når du ikke kan finde flere sætninger, du synes bør faktatjekkes, så tryk på **den blå update-knap** for at opdatere siden.")
st.markdown("3) Tryk til sidst på **Gem annotation**-knappen i bunden af siden for at gemme dine markeringer og gå videre til næste debat.")
st.markdown("______")

st.markdown("## 🔍 Hvordan ved jeg, hvad der bør faktatjekkes?")
st.markdown("""
**Spørg dig selv:**  
*"Vil den brede offentlighed være interesseret i at vide, om sætningen er sand eller falsk?"*  

👉 **Bør faktatjekkes (Checkworthy):**  
- Udsagn, der præsenteres som fakta, og som kan verificeres med data eller ekspertkilder.  
- Kvantitative påstande (*"Danmark har det højeste skattetryk i Europa."*).  
- Historiske påstande (*"Den tidligere regering skar 20% af sundhedsbudgettet."*).  
- Påstande om lovgivning eller internationale aftaler (*"EU kræver, at vi reducerer CO2 med 50% inden 2030."*).  
- Referencer til videnskabelige undersøgelser (*"Forskning viser, at elbiler er 70% mere bæredygtige end dieselbiler."*).  

🚫 **Bør ikke faktatjekkes:**  
- Personlige holdninger og værdiladede udsagn (*"Jeg synes, vi har den bedste klimapolitik."*).  
- Spekulationer og hypotetiske scenarier (*"Hvis vi ikke handler nu, vil økonomien kollapse."*).  
- Meget vage eller generelle udsagn (*"Vi gør det bedre end før."*).  
""")
st.markdown("**⚡️ Tips ⚡️ :**")
st.markdown("""
- Hvis du fortryder en annotation, kan du klikke på markeringen og trykke **slet** / **delete** på dit tastatur.  
- Hvis du vil have en pause, kan du logge ud på log-ud knappen til venstre og vende tilbage senere og starte, hvor du slap.  
- Du optjener flere lod i lotteriet per færdiggjort annotations-runde.
    
*Har du nogle spørgsmål? Skriv til mig (Pernille) på au650502@cas.au.dk* 🌞
""")

# with st.expander("🔍 Klik her for at se lidt eksempler på, hvordan stategierne ser ud 🔍 "):
#     st.markdown("""
#     ### **📌 Label forklaringer & eksempler**

#     🔍 **Bør faktatjekkes (Checkworthy)**  
#     _Definition_: En påstand, der indeholder faktuelle oplysninger, som offentligheden kunne have interesse i at få verificeret.  
#     _Eksempel_:  
#     **Spørger**: *"Er det rigtigt, at Danmark har det højeste skattetryk i verden?"*  
#     **Ordfører**: *"Ja, Danmark har det højeste skattetryk i OECD-landene."*  
#     🔹 **Inkluderer**:
#     - Kvantitative udsagn om økonomi, kriminalitet, sundhed osv.
#     - Historiske eller videnskabelige påstande.
#     - Referencer til konkrete statistikker eller data.

#     👀 **Andet (Other)**  
#     _Definition_: Hvis en udtalelse ikke passer ind i de andre kategorier, men stadig er relevant.  
#     🔹 **Inkluderer**:
#     - Udtalelser, der ikke indeholder nogen af de ovenstående strategier.
#     - Tekniske forklaringer eller neutral information.
#     - Meget vage eller uklare svar.

#     """)

import re

def bold_unicode(text):
    """ Converts text to bold using Unicode Mathematical Bold Letters """
    normal = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    bold = "𝗔𝗕𝗖𝗗𝗘𝗙𝗚𝗛𝗜𝗝𝗞𝗟𝗠𝗡𝗢𝗣𝗤𝗥𝗦𝗧𝗨𝗩𝗪𝗫𝗬𝗭𝗮𝗯𝗰𝗱𝗲𝗳𝗴𝗵𝗶𝗷𝗸𝗹𝗺𝗻𝗼𝗽𝗾𝗿𝘀𝘁𝘂𝘃𝘄𝘅𝘆𝘇"
    trans = str.maketrans(normal, bold)
    return text.translate(trans)

def format_speaker_text(text):
    """ 
    Extracts DebateUnitID.
    Ensures speaker names are bold (Unicode) and a newline appears before bold parts (except the first one). 
    """
    # Step 1: Extract DebateUnitID from the text
    match = re.match(r"\[(\d+)\]\s*(.*)", text)
    if match:
        debate_unit_id = int(match.group(1))  # Extracted number
        text = match.group(2)  # Remove the ID from the text
    else:
        debate_unit_id = None  # No ID found

    # Step 2: Identify speaker names before the colon and bold them
    text = re.sub(r"\*\*(.*?):\*\*", lambda m: bold_unicode(m.group(1)) + ":", text)  
    
    # Step 3: Add a newline **after** the colon (keeping bold formatting intact)
    text = re.sub(r"(\S+): ", r"\1:\n", text)  

    # Step 4: Convert bold markdown **text** into Unicode bold
    text = re.sub(r"\*\*(.*?)\*\*", lambda m: "\n" + bold_unicode(m.group(1)), text, count=1)  # Don't add newline for the first match
    text = re.sub(r"\*\*(.*?)\*\*", lambda m: "\n" + bold_unicode(m.group(1)), text)  # Add newline for the rest

    return debate_unit_id, text  # Return extracted ID and formatted text

# Convert bold-marked text (**text**) into Unicode bold characters
debate_unit_id, formatted_text = format_speaker_text(current_text)

selections = label_select(
    body=formatted_text,
    #labels=["Stretch", "Dodge", "Omission", "Deflection", "Svar", "Andet"]
    labels=[#"Svar", 
            #"Overdrivelse", 
            #"Undvigelse/Udenomssnak", 
            #"Selv-promovering/Personlig anekdote",
            #"Angreb/Provokation", 
            "Bør faktatjekkes",
            "Andet"]
            #"Udeladelse", 
            #"Afledning", 
            #"Svar", "Andet"]
)

# Display a little msg
st.markdown("*Hvis du ikke ser en blå 'Update' knap under boksen med debat-tekst, så udvid dit browservindue lidt.*")

#selections = label_select(
#    body=formatted_text,
#    labels=["Stretch", "Dodge", "Omission", "Deflection"]
#)

# Convert selections to a list of dictionaries if needed
selection_data = selections if isinstance(selections, list) else []

# --- Format Selections nicely ---
formatted_selections = {}
for s in selection_data:
    for label in s.labels:
        formatted_selections.setdefault(label, []).append(s.text)

# Display formatted selections
st.markdown("#### Dine annotationer:")
for label, texts in formatted_selections.items():
    st.write(f"**{label}:** {' , '.join(texts)}")

# Automatically disable the button if no selections are made
submit_button_disabled = len(selection_data) == 0

# Add comment
# Ensure comment_text is initialized in session state
if "comment_text" not in st.session_state:
    st.session_state.comment_text = ""

# Store the user's input in a temporary variable
comment_input = st.text_area(
    "Tilføj en kommentar (hvis du f.eks. er usikker eller bare har en kommentar til din annotering):",
    value=st.session_state.comment_text,  # Ensure it's linked to session state
    key="comment_text"  # This ensures that Streamlit updates session state
)



# --- Submit button ---
submit_button = st.button("Gem annotation", disabled=submit_button_disabled)

if submit_button:
    # Extract text per label from recorded selections
    check_worthy_text = "; ".join([s.text for s in selection_data if 'Bør faktatjekkes' in s.labels])
    other_text = "; ".join([s.text for s in selection_data if 'Andet' in s.labels])
    
    annotation_data = [
        user_id,
        st.session_state.text_index,
        current_text,
        debate_unit_id,
        
        check_worthy_text,
        other_text,

        comment_input,
        datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ]

    st.session_state.annotations.append(annotation_data)

    # Save annotations in batches of 5
    if len(st.session_state.annotations) >= 5:
        threading.Thread(target=save_annotations, args=(user_id, st.session_state.annotations.copy()), daemon=True).start()
        st.session_state.annotations = []

    st.session_state.pop("comment_text", None)

    # Move to the next text
    st.session_state.text_index += 1
    st.rerun()
