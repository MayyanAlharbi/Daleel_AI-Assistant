from ml.notebook_model import predict_label_tfidf

samples = [
    "The employee basic salary is 8000 SAR and housing allowance is 2000 SAR.",
    "يستحق الموظف إجازة سنوية مدفوعة الأجر وفقاً لنظام العمل السعودي.",
    "Either party may terminate this contract with written notice.",
    "ساعات العمل ثمان ساعات يومياً مع إمكانية العمل الإضافي.",
]

for s in samples:
    print(predict_label_tfidf(s), "|", s[:60])
