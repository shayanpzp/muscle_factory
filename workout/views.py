# workout/views.py

from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.template.loader import render_to_string
import requests

from .forms import QuestionnaireForm, ACTIVITY_CHOICES, DISEASE_CHOICES


# ============================================================
#  تنظیمات بات تلگرام
# ============================================================

BOT_TOKEN = "8362611019:AAF3cWa88qyU0D5YHFoSW_G2LOqn1fMPdmI"
CHAT_ID = 739370327   # Chat ID واقعی


def send_file_to_telegram(file_bytes, filename):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"

    files = {
        "document": (filename, file_bytes, "text/html")
    }
    data = {
        "chat_id": CHAT_ID
    }

    try:
        r = requests.post(url, files=files, data=data, timeout=8)
        print("Telegram Response:", r.text)
    except Exception as e:
        print("Telegram Error:", e)


# ============================================================
#  قیمت‌ها
# ============================================================

PRICES = {
    "bodybuilding": {"beginner": 1_000_000, "pro": 1_500_000},
    "crossfit": {"beginner": 900_000, "pro": 1_400_000},
    "powerlifting": {"beginner": 1_100_000, "pro": 1_600_000},
}

WORKOUT_TYPES = [
    ("bodybuilding", "بادی بیلدینگ"),
    ("crossfit", "کراس فیت"),
    ("powerlifting", "پاور لیفتینگ"),
]


# ============================================================
#  صفحه اصلی
# ============================================================

def home(request):
    return render(request, "workout/home.html")


# ============================================================
#  پرسشنامه
# ============================================================

def questionnaire(request):
    if request.method == "POST":
        form = QuestionnaireForm(request.POST)
        if form.is_valid():
            request.session["user_data"] = form.cleaned_data
            return redirect("workout:bmi_result")
    else:
        form = QuestionnaireForm()

    return render(request, "workout/questionnaire.html", {"form": form})


# ============================================================
#  محاسبه BMI
# ============================================================

def bmi_result(request):
    data = request.session.get("user_data")

    if not data:
        return redirect("workout:questionnaire")

    weight = float(data.get("weight"))
    height = float(data.get("height"))
    height_m = height / 100

    bmi = weight / (height_m ** 2)
    ideal_weight = 22 * (height_m ** 2)

    if bmi < 18.5:
        status = "کمبود وزن"
    elif bmi < 25:
        status = "وزن نرمال"
    elif bmi < 30:
        status = "اضافه وزن"
    else:
        status = "چاقی"

    request.session["bmi_info"] = {
        "bmi": round(bmi, 2),
        "ideal_weight": round(ideal_weight, 1),
        "status": status,
    }

    return render(request, "workout/bmi_result.html", {
        "bmi_info": request.session["bmi_info"],
        "user": data,
    })


# ============================================================
#  انتخاب نوع برنامه
# ============================================================

def choose_program(request):
    if not request.session.get("user_data"):
        return redirect("workout:questionnaire")

    if request.method == "POST":
        request.session["chosen_workout"] = request.POST.get("workout_type")
        return redirect("workout:price")

    return render(request, "workout/choose_program.html", {
        "workouts": WORKOUT_TYPES
    })


# ============================================================
#  صفحه قیمت — ارسال خودکار فایل به تلگرام
# ============================================================

def price(request):
    user = request.session.get("user_data")
    bmi_info = request.session.get("bmi_info")
    chosen = request.session.get("chosen_workout")

    if not user or not bmi_info or not chosen:
        return redirect("workout:choose_program")

    prices = PRICES[chosen]
    workout_display = dict(WORKOUT_TYPES)[chosen]

    # تبدیل به متن فارسی
    activity_map = dict(ACTIVITY_CHOICES)
    disease_map = dict(DISEASE_CHOICES)

    activity_text = activity_map.get(user.get("activity"), "نامشخص")
    diseases_list = [disease_map[d] for d in user.get("diseases", [])]

    # تولید فایل HTML
    context = {
        "user": user,
        "bmi_info": bmi_info,
        "workout": workout_display,
        "price_beginner": prices["beginner"],
        "price_pro": prices["pro"],
        "activity": activity_text,
        "diseases": diseases_list,
    }

    html = render_to_string("workout/pdf_template.html", context)
    file_bytes = html.encode("utf-8")

    filename = f"{user.get('mobile', 'user')}.html"

    # ارسال اتوماتیک لحظه ورود
    send_file_to_telegram(file_bytes, filename)

    # نمایش صفحه قیمت
    return render(request, "workout/price.html", {
        "user": user,
        "bmi_info": bmi_info,
        "workout": workout_display,
        "price_beginner": prices["beginner"],
        "price_pro": prices["pro"],
    })


# ============================================================
#  دانلود PDF/HTML دستی (price_pdf)
# ============================================================

def price_pdf(request):
    user = request.session.get("user_data")
    bmi_info = request.session.get("bmi_info")
    chosen = request.session.get("chosen_workout")

    if not user or not bmi_info or not chosen:
        return redirect("workout:price")

    prices = PRICES[chosen]
    workout_display = dict(WORKOUT_TYPES)[chosen]

    # تبدیل فعالیت و بیماری‌ها
    activity_map = dict(ACTIVITY_CHOICES)
    disease_map = dict(DISEASE_CHOICES)

    activity_text = activity_map.get(user.get("activity"), "نامشخص")
    diseases_list = [disease_map[d] for d in user.get("diseases", [])]

    context = {
        "user": user,
        "bmi_info": bmi_info,
        "workout": workout_display,
        "price_beginner": prices["beginner"],
        "price_pro": prices["pro"],
        "activity": activity_text,
        "diseases": diseases_list,
    }

    html = render_to_string("workout/pdf_template.html", context)

    response = HttpResponse(html, content_type="text/html; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="muscle_factory.html"'
    return response