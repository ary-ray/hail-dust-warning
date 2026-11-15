import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta
from sklearn.model_selection import TimeSeriesSplit
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import classification_report, roc_auc_score, f1_score
import joblib

# 1. تحديد إحداثيات حائل ونطاق السنوات التاريخية للطقس
LATITUDE = 27.5219
LONGITUDE = 41.7492
START_DATE = "2015-01-01"
END_DATE = datetime.now().strftime("%Y-%m-%d")

print(f"[*] جاري سحب بيانات الطقس والأرشيف لإحداثيات حائل من Open-Meteo...")

# رابط واجهة أرشيف الطقس المجاني (Weather Archive API)
url = "https://archive-api.open-meteo.com/v1/archive"
params = {
    "latitude": LATITUDE,
    "longitude": LONGITUDE,
    "start_date": START_DATE,
    "end_date": END_DATE,
    "daily": [
        "temperature_2m_max",
        "temperature_2m_min",
        "precipitation_sum",
        "wind_speed_10m_max",
        "wind_gusts_10m_max",
        "surface_pressure_mean"
    ],
    "timezone": "auto"
}

response = requests.get(url, params=params)
if response.status_code == 200:
    data = response.json()
    daily_data = data.get("daily", {})
    df = pd.DataFrame(daily_data)
    df['time'] = pd.to_datetime(df['time'])
    print(f"[+] تم سحب بنجاح عدد {len(df)} يوم من سجلات الطقس التاريخية.")
else:
    raise Exception(f"خطأ في الاتصال بالـ API: {response.status_code} - {response.text}")

# 2. هندسة الميزات (Feature Engineering) وحساب مؤشرات عواصف الغبار
df['wind_gust_ratio'] = df['wind_gusts_10m_max'] / (df['wind_speed_10m_max'] + 1e-5)

# تعريف المتغير المستهدف (Target): يوم غبار عالي (1) إذا كانت هبات الرياح أعلى بيرسنتيل 90
dust_threshold = df['wind_gusts_10m_max'].quantile(0.90)
df['is_dust_day'] = (df['wind_gusts_10m_max'] >= dust_threshold).astype(int)

# إنشاء متأخرات زمنية (Lag Features) لتوقع الحدث قبل 1 إلى 3 أيام
for lag in [1, 2, 3]:
    df[f'wind_speed_lag_{lag}'] = df['wind_speed_10m_max'].shift(lag)
    df[f'pressure_lag_{lag}'] = df['surface_pressure_mean'].shift(lag)
    df[f'dust_lag_{lag}'] = df['is_dust_day'].shift(lag)

# تنظيف القيم الفارغة الناتجة عن الـ Lag
df = df.dropna().reset_index(drop=True)

# 3. إعداد مصفوفة الميزات (X) والمتغير المستهدف (y)
features = [
    'temperature_2m_max', 'temperature_2m_min', 'precipitation_sum',
    'wind_speed_10m_max', 'wind_gusts_10m_max', 'surface_pressure_mean',
    'wind_gust_ratio', 'wind_speed_lag_1', 'wind_speed_lag_2', 'wind_speed_lag_3',
    'pressure_lag_1', 'pressure_lag_2', 'pressure_lag_3',
    'dust_lag_1', 'dust_lag_2', 'dust_lag_3'
]

X = df[features]
y = df['is_dust_day']

print(f"[*] حجم البيانات النهائي للتدريب: {X.shape[0]} صف، وعدد الميزات: {X.shape[1]}")
print(f"[*] نسبة الأيام التي تصنف كأيام غبار: {y.mean()*100:.2f}%")

# 4. تقسيم زمني للبيانات (TimeSeriesSplit) وتقييم نموذج Gradient Boosting
tscv = TimeSeriesSplit(n_splits=5)
model = GradientBoostingClassifier(n_estimators=100, learning_rate=0.1, random_state=42)

fold = 1
for train_index, test_index in tscv.split(X):
    X_train, X_test = X.iloc[train_index], X.iloc[test_index]
    y_train, y_test = y.iloc[train_index], y.iloc[test_index]
    
    model.fit(X_train, y_train)
    preds = model.predict(X_test)
    probs = model.predict_proba(X_test)[:, 1]
    
    f1 = f1_score(y_test, preds)
    try:
        roc_auc = roc_auc_score(y_test, probs)
    except:
        roc_auc = 0.0
        
    print(f"--- Fold {fold} --- F1-Score: {f1:.4f} | ROC-AUC: {roc_auc:.4f}")
    fold += 1

print("\n[+] تم تدريب النموذج وتقييمه بنجاح عبر التسلسل الزمني!")

# 5. حفظ النموذج المدرب
model_filename = "hail_dust_model.pkl"
joblib.dump(model, model_filename)
print(f"[+] تم حفظ النموذج بنجاح في ملف: {model_filename}")

# 6. حفظ النتائج والبيانات المتوقعة كملف CSV
df['predicted_dust'] = model.predict(X)
df['predicted_probability'] = model.predict_proba(X)[:, 1]
df.to_csv("hail_dust_predictions.csv", index=False, encoding="utf-8-sig")
print("[+] تم حفظ جدول التنبؤات والبيانات في ملف 'hail_dust_predictions.csv'.")