import streamlit as st
import requests

API_BASE = "http://127.0.0.1:8000"

st.set_page_config(page_title="Contract Assistant", layout="wide")

# ----------------------------
# i18n (UI translations)
# ----------------------------
UI = {
    "en": {
        "app_title": "Contract Assistant (Saudi Employment)",
        "ui_lang": "Interface language",
        "tabs": ["Upload Contract", "Contract Q&A", "Contract Summary", "General Chatbot"],
        "upload_title": "Upload a contract (PDF/DOCX)",
        "upload_help": "Upload an employment contract. The system will split it into clauses and index it for Q&A and summaries.",
        "upload_btn": "Upload",
        "uploaded_ok": "Uploaded successfully!",
        "contract_id": "Contract ID",
        "contract_lang": "Contract language",
        "num_clauses": "Number of clauses",
        "qa_title": "Ask about the uploaded contract",
        "question": "Your question",
        "ask_btn": "Ask",
        "need_upload": "Please upload a contract first (Upload tab).",
        "summary_title": "Generate contract summary",
        "summary_mode": "Summary mode",
        "full": "Full summary",
        "focused": "Focused summary",
        "topics": "Select topics",
        "gen_btn": "Generate summary",
        "general_title": "General chatbot (no upload required)",
        "general_help": "Ask questions about Saudi employment contracts & labor law in general.",
        "send_btn": "Send",
        "output_lang": "Output language",
        "error": "Error",
    },
    "ar": {
        "app_title": "مساعد العقود (عقود العمل السعودية)",
        "ui_lang": "لغة الواجهة",
        "tabs": ["رفع عقد", "سؤال وجواب عن العقد", "ملخص العقد", "شات عام بدون عقد"],
        "upload_title": "ارفع عقد (PDF/DOCX)",
        "upload_help": "ارفع عقد عمل وسيتم تقسيمه إلى بنود وفهرسته للاستخدام في الأسئلة والملخصات.",
        "upload_btn": "رفع",
        "uploaded_ok": "تم الرفع بنجاح!",
        "contract_id": "معرّف العقد",
        "contract_lang": "لغة العقد",
        "num_clauses": "عدد البنود",
        "qa_title": "اسأل عن العقد المرفوع",
        "question": "سؤالك",
        "ask_btn": "اسأل",
        "need_upload": "رجاءً ارفع عقد أولاً من تبويب (رفع عقد).",
        "summary_title": "إنشاء ملخص للعقد",
        "summary_mode": "نوع الملخص",
        "full": "ملخص كامل",
        "focused": "ملخص مركّز",
        "topics": "اختر المواضيع",
        "gen_btn": "إنشاء الملخص",
        "general_title": "شات عام (بدون رفع عقد)",
        "general_help": "اسأل أسئلة عامة عن عقود العمل ونظام العمل السعودي.",
        "send_btn": "إرسال",
        "output_lang": "لغة الإخراج",
        "error": "خطأ",
    },
    # UI language only (simple labels). The actual answer language is controlled by output_lang below.
    "ur": {
        "app_title": "سعودی ملازمت کنٹریکٹ اسسٹنٹ",
        "ui_lang": "انٹرفیس زبان",
        "tabs": ["کنٹریکٹ اپلوڈ", "کنٹریکٹ سوال و جواب", "کنٹریکٹ سمری", "جنرل چیٹ بوٹ"],
        "upload_title": "کنٹریکٹ اپلوڈ کریں (PDF/DOCX)",
        "upload_help": "ملازمت کا کنٹریکٹ اپلوڈ کریں تاکہ سوال و جواب اور سمری بن سکے۔",
        "upload_btn": "اپلوڈ",
        "uploaded_ok": "کامیابی سے اپلوڈ ہوگیا!",
        "contract_id": "کنٹریکٹ آئی ڈی",
        "contract_lang": "کنٹریکٹ زبان",
        "num_clauses": "شقوں کی تعداد",
        "qa_title": "اپلوڈ شدہ کنٹریکٹ کے بارے میں پوچھیں",
        "question": "آپ کا سوال",
        "ask_btn": "پوچھیں",
        "need_upload": "براہ کرم پہلے کنٹریکٹ اپلوڈ کریں۔",
        "summary_title": "کنٹریکٹ سمری بنائیں",
        "summary_mode": "سمری موڈ",
        "full": "فل سمری",
        "focused": "فوکسڈ سمری",
        "topics": "موضوعات منتخب کریں",
        "gen_btn": "سمری بنائیں",
        "general_title": "جنرل چیٹ بوٹ (اپلوڈ ضروری نہیں)",
        "general_help": "سعودی لیبر لاء/کنٹریکٹس سے متعلق عمومی سوالات کریں۔",
        "send_btn": "بھیجیں",
        "output_lang": "آؤٹ پٹ زبان",
        "error": "خرابی",
    },
    "hi": {
        "app_title": "सऊदी रोजगार अनुबंध सहायक",
        "ui_lang": "इंटरफ़ेस भाषा",
        "tabs": ["अनुबंध अपलोड", "अनुबंध Q&A", "अनुबंध सारांश", "जनरल चैटबॉट"],
        "upload_title": "अनुबंध अपलोड करें (PDF/DOCX)",
        "upload_help": "रोजगार अनुबंध अपलोड करें ताकि Q&A और सारांश बन सके।",
        "upload_btn": "अपलोड",
        "uploaded_ok": "सफलतापूर्वक अपलोड!",
        "contract_id": "अनुबंध ID",
        "contract_lang": "अनुबंध भाषा",
        "num_clauses": "क्लॉज़ की संख्या",
        "qa_title": "अपलोड किए गए अनुबंध के बारे में पूछें",
        "question": "आपका प्रश्न",
        "ask_btn": "पूछें",
        "need_upload": "कृपया पहले अनुबंध अपलोड करें।",
        "summary_title": "अनुबंध सारांश बनाएं",
        "summary_mode": "सारांश मोड",
        "full": "पूर्ण सारांश",
        "focused": "फोकस्ड सारांश",
        "topics": "विषय चुनें",
        "gen_btn": "सारांश बनाएं",
        "general_title": "जनरल चैटबॉट (अपलोड जरूरी नहीं)",
        "general_help": "सऊदी श्रम कानून/अनुबंधों पर सामान्य प्रश्न पूछें।",
        "send_btn": "भेजें",
        "output_lang": "आउटपुट भाषा",
        "error": "त्रुटि",
    },
    "tl": {
        "app_title": "Saudi Employment Contract Assistant",
        "ui_lang": "Wika ng interface",
        "tabs": ["Mag-upload ng Kontrata", "Q&A sa Kontrata", "Buod ng Kontrata", "General Chatbot"],
        "upload_title": "Mag-upload ng kontrata (PDF/DOCX)",
        "upload_help": "Mag-upload ng employment contract para sa Q&A at buod.",
        "upload_btn": "Upload",
        "uploaded_ok": "Matagumpay na na-upload!",
        "contract_id": "Contract ID",
        "contract_lang": "Wika ng kontrata",
        "num_clauses": "Bilang ng clauses",
        "qa_title": "Magtanong tungkol sa na-upload na kontrata",
        "question": "Tanong mo",
        "ask_btn": "Itanong",
        "need_upload": "Mag-upload muna ng kontrata.",
        "summary_title": "Gumawa ng buod ng kontrata",
        "summary_mode": "Uri ng buod",
        "full": "Buong buod",
        "focused": "Piling buod",
        "topics": "Pumili ng topics",
        "gen_btn": "Gumawa ng buod",
        "general_title": "General chatbot (hindi kailangan ng upload)",
        "general_help": "Magtanong ng pangkalahatan tungkol sa Saudi labor law/contract terms.",
        "send_btn": "Ipadala",
        "output_lang": "Wika ng output",
        "error": "Error",
    }
}

SUPPORTED_OUTPUT_LANGS = ["en", "ar", "ur", "hi", "tl"]


# ----------------------------
# Session State
# ----------------------------
if "contract_id" not in st.session_state:
    st.session_state.contract_id = None
if "contract_lang" not in st.session_state:
    st.session_state.contract_lang = None


# ----------------------------
# Top Bar
# ----------------------------
ui_lang = st.sidebar.selectbox("🌐 Interface language / لغة الواجهة", ["en", "ar", "ur", "hi", "tl"], index=0)
T = UI[ui_lang]

st.title(T["app_title"])

output_lang = st.sidebar.selectbox(T["output_lang"], SUPPORTED_OUTPUT_LANGS, index=0)

st.sidebar.markdown("---")
if st.session_state.contract_id:
    st.sidebar.success(f"{T['contract_id']}: {st.session_state.contract_id}")
    if st.session_state.contract_lang:
        st.sidebar.info(f"{T['contract_lang']}: {st.session_state.contract_lang}")
else:
    st.sidebar.warning(T["need_upload"])


# ----------------------------
# Tabs
# ----------------------------
tab1, tab2, tab3, tab4 = st.tabs(T["tabs"])

# ----------------------------
# TAB 1: Upload
# ----------------------------
with tab1:
    st.subheader(T["upload_title"])
    st.caption(T["upload_help"])

    file = st.file_uploader("", type=["pdf", "docx"])

    if st.button(T["upload_btn"], use_container_width=True):
        if not file:
            st.warning("Please select a file.")
        else:
            try:
                files = {"file": (file.name, file.getvalue())}
                r = requests.post(f"{API_BASE}/upload_contract", files=files, timeout=120)
                if r.status_code != 200:
                    st.error(f"{T['error']}: {r.text}")
                else:
                    data = r.json()
                    st.success(T["uploaded_ok"])
                    st.session_state.contract_id = data.get("contract_id")
                    st.session_state.contract_lang = data.get("language")

                    st.write(f"**{T['contract_id']}**: {data.get('contract_id')}")
                    st.write(f"**{T['contract_lang']}**: {data.get('language')}")
                    st.write(f"**{T['num_clauses']}**: {data.get('num_clauses')}")
            except Exception as e:
                st.error(f"{T['error']}: {e}")

# ----------------------------
# TAB 2: Contract Q&A
# ----------------------------
with tab2:
    st.subheader(T["qa_title"])

    if not st.session_state.contract_id:
        st.warning(T["need_upload"])
    else:
        q = st.text_area(T["question"], height=120)

        if st.button(T["ask_btn"], use_container_width=True):
            if not q.strip():
                st.warning("Please enter a question.")
            else:
                payload = {
                    "contract_id": st.session_state.contract_id,
                    "question": q
                }
                try:
                    r = requests.post(f"{API_BASE}/ask", json=payload, timeout=120)
                    if r.status_code != 200:
                        st.error(f"{T['error']}: {r.text}")
                    else:
                        ans = r.json().get("answer", "")
                        st.markdown(ans)
                except Exception as e:
                    st.error(f"{T['error']}: {e}")

# ----------------------------
# TAB 3: Summary
# ----------------------------
with tab3:
    st.subheader(T["summary_title"])

    if not st.session_state.contract_id:
        st.warning(T["need_upload"])
    else:
        mode = st.radio(T["summary_mode"], ["full", "focused"], horizontal=True)
        topics = []
        if mode == "focused":
            topics = st.multiselect(
                T["topics"],
                options=["Salary", "Probation", "Termination", "Working Hours", "Leave", "Benefits", "Non-Compete", "Penalties", "Duration"]
            )

        if st.button(T["gen_btn"], use_container_width=True):
            payload = {
                "contract_id": st.session_state.contract_id,
                "mode": mode,
                "topics": topics if mode == "focused" else None,
                "language": output_lang,
            }
            try:
                r = requests.post(f"{API_BASE}/summary", json=payload, timeout=180)
                if r.status_code != 200:
                    st.error(f"{T['error']}: {r.text}")
                else:
                    summ = r.json().get("summary", "")
                    st.markdown(summ)
            except Exception as e:
                st.error(f"{T['error']}: {e}")

# ----------------------------
# TAB 4: General Chatbot
# ----------------------------
with tab4:
    st.subheader(T["general_title"])
    st.caption(T["general_help"])

    if "general_chat" not in st.session_state:
        st.session_state.general_chat = []

    # display history
    for role, msg in st.session_state.general_chat:
        with st.chat_message(role):
            st.markdown(msg)

    prompt = st.chat_input(T["question"])
    if prompt:
        st.session_state.general_chat.append(("user", prompt))
        with st.chat_message("user"):
            st.markdown(prompt)

        payload = {"question": prompt, "language": output_lang}
        try:
            r = requests.post(f"{API_BASE}/ask_general", json=payload, timeout=120)
            if r.status_code != 200:
                answer = f"{T['error']}: {r.text}"
            else:
                answer = r.json().get("answer", "")

        except Exception as e:
            answer = f"{T['error']}: {e}"

        st.session_state.general_chat.append(("assistant", answer))
        with st.chat_message("assistant"):
            st.markdown(answer)
