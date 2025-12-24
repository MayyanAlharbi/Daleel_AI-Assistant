# backend/api/constants.py

# ----------------------------
# Constants
# ----------------------------
DEFAULT_TOPICS = [
    "probation period",
    "salary and allowances",
    "working hours and overtime",
    "leave and holidays",
    "termination and notice",
    "end of service benefits",
    "penalties and disciplinary actions",
    "non-compete",
    "contract duration / renewal",
]

TOPIC_QUERIES = {
    "Salary": "salary basic wage allowances deductions benefits الراتب البدلات الاستقطاعات",
    "Probation": "probation period تجربة فسخ خلال التجربة",
    "Termination": "termination notice end of contract Article 80 إنهاء إشعار المادة 80",
    "Working Hours": "working hours overtime دوام ساعات عمل عمل إضافي",
    "Leave": "annual leave sick leave vacation إجازة سنوية إجازة مرضية",
    "Benefits": "benefits housing transportation medical insurance مزايا سكن نقل تأمين طبي",
    "Non-Compete": "non-compete confidentiality عدم منافسة سرية",
    "Penalties": "penalties disciplinary fine خصم جزاءات عقوبات",
    "Duration": "contract duration renewal fixed-term مدة العقد تجديد عقد محدد المدة",
}

SUPPORTED_UI_LANGS = {"ar", "en", "ur", "hi", "tl"}  # tl = Tagalog/Filipino

# =========================
# Summary JSON Schema
# =========================

SUMMARY_SCHEMA = {
    "name": "contract_summary_schema",
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "mode": {"type": "string", "enum": ["full", "focused"]},
            "language": {"type": "string"},
            "overview": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "text": {"type": "string"},
                        "sources": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "additionalProperties": False,
                                "properties": {
                                    "type": {"type": "string", "enum": ["contract", "law"]},
                                    "id": {"type": "string"}
                                },
                                "required": ["type", "id"]
                            }
                        }
                    },
                    "required": ["text", "sources"]
                }
            },
            "sections": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "key": {"type": "string"},
                        "title": {"type": "string"},
                        "bullets": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "additionalProperties": False,
                                "properties": {
                                    "text": {"type": "string"},
                                    "sources": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "additionalProperties": False,
                                            "properties": {
                                                "type": {"type": "string", "enum": ["contract", "law"]},
                                                "id": {"type": "string"}
                                            },
                                            "required": ["type", "id"]
                                        }
                                    }
                                },
                                "required": ["text", "sources"]
                            }
                        }
                    },
                    "required": ["key", "title", "bullets"]
                }
            }
        },
        "required": ["mode", "language", "overview", "sections"]
    }
}
