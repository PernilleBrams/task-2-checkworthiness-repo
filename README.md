# Streamlit Annotation Tool for Checkworthiness 🗣️📝

This tool is **Task 2** in a multi-phase annotation project. It focuses on identifying **which statements are worth fact-checking** (“Bør faktatjekkes”) in political debates. **Task 1** (Rhetorical Strategies) is located in the **task-1-rhetorical-strategies-repo** repository.

## ✨ Key Features

1. **User Login & Individual Data** 🔐  
   - Users log in with their unique ID from the sidebar.  
   - Each user has a **personal worksheet** in a Google Sheet and a **personal data file** (e.g., `data/clean/<USER_ID>/processed_texts_test_check_worthy.txt`).  
   - The app checks for the user’s worksheet, creating one if it doesn’t exist.

2. **Checkworthiness Annotation** 🔍  
   - Highlight any snippet(s) of text that **should be fact-checked** (e.g., statistic-based claims, historical facts, references to laws).  
   - Select **“Bør faktatjekkes”** if the statement is verifiable and relevant to public interest, otherwise label it **“Andet”**.  
   - A **comment box** allows users to note any uncertainties or extra remarks.

3. **Google Sheets Integration** ☁️  
   - Annotations are appended automatically to a user-specific sheet, keeping everyone’s data separate.  
   - Annotations are **batched** in groups of 5 for efficient saving. Any leftover annotations are still saved upon finishing or logging out.

4. **Light Mode by Default** 🌞  
   - The tool enforces a white background to ensure readability. If your browser forcibly uses dark mode, you may need to switch to light mode in the Streamlit settings.

5. **Session Management** 🔄  
   - Once logged in, your progress is tracked by Streamlit’s session state.  
   - If you log out or close the browser, you can resume from where you left off next time you log in.

6. **Minimal Dependencies** 🛠️  
   - Uses **Streamlit**, **pandas**, **gspread**, and **streamlit_text_label**. No extra servers needed—just Google Sheets for backend storage.

---

## 🗂️ Project Structure

```
annotation-tool-checkworthiness/
├── app_checkworthiness.py       # Main Streamlit app for Task 2 (Checkworthiness)
├── requirements.txt             # Python dependencies
├── .streamlit/
│   └── secrets.toml             # Google Sheets API credentials
├── data/
│   └── clean/
│       └── <USER_ID>/
│           └── processed_texts_test_check_worthy.txt
├── .gitignore                   # Ignore tokens, credentials, etc.
└── README.md                    # This documentation file
```

> **Note**: The file `processed_texts_test_check_worthy.txt` is the input text for **checkworthiness** annotation. Each user folder can contain a separate file for them to annotate.

---

## 🚀 How to Use

1. **Run the Checkworthiness Script**  
   ```bash
   streamlit run app_checkworthiness.py
   ```
   This will launch the Streamlit app.

2. **Log In**  
   - Enter your **User ID** in the sidebar.  
   - Click **“Log in.”** If you’re authorized, you’ll see the annotation interface.

3. **Label Snippets**  
   - Each text is shown in a highlighting widget.  
   - **Highlight** any phrase/statement that “Bør faktatjekkes.”  
   - (Optional) Label other things as “Andet” if you think they have impact on the overall expressions in the text. Add a comment to elaborate on the marking if you wish.

4. **Comment (Optional)**  
   - If unsure or you want to note something, add remarks in the comment box below.

5. **Save & Proceed**  
   - Click **“Gem annotation”** to store your labels. You’ll then see the next text.  
   - Annotations save automatically in **batches of 5** for performance.

6. **Completion or Logout**  
   - Once all texts are annotated, you’ll see a **completion message**.  
   - You can also **log out** in the sidebar at any time-partial annotations will be saved before exiting.

---

## ⚙️ Tech Stack

- **Streamlit** for the front-end interface  
- **Python** libraries:
  - `pandas` for data manipulation  
  - `gspread` + `google.oauth2.service_account` for Google Sheets  
  - `streamlit_text_label` for text selection and labeling  
- **Google Sheets** for backend storage

---

## 📝 Notes & Tips

- **Batch Saving**  
  - Data is sent to the Google Sheet in increments of 5 annotations.  
  - If you have fewer than 5 unsaved annotations and you exit, the app will still save them.

- **Resuming Work**  
  - The app remembers which texts you’ve already annotated. When you log back in, you pick up where you left off.

- **Light Theme**  
  - By design, the app forces a white background. If your machine is locked to dark mode, open “Settings” in the Streamlit menu and switch to Light mode.

- **Customization**  
  - You can tweak the instructions, add more labels (if needed), or change any UI text by modifying `app_checkworthiness.py`.
