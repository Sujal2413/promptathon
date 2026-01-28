from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods
import json

from .forms import PickupRequestForm
from .models import PickupRequest, WasteGuideItem

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


def home(request):
    # Keep home accessible; stats only to staff
    stats = None
    if request.user.is_authenticated and request.user.is_staff:
        stats = {
            "total": PickupRequest.objects.filter(created_by__isnull=False).count(),
            "wet": PickupRequest.objects.filter(created_by__isnull=False, waste_type="WET").count(),
            "dry": PickupRequest.objects.filter(created_by__isnull=False, waste_type="DRY").count(),
            "ewaste": PickupRequest.objects.filter(created_by__isnull=False, waste_type="EWASTE").count(),
            "hazard": PickupRequest.objects.filter(created_by__isnull=False, waste_type="HAZARD").count(),
        }
    return render(request, "core/home.html", {"stats": stats})


def request_new(request):
    # If collector opens user feature, redirect to collector dashboard
    if request.user.is_authenticated and request.user.is_staff:
        return redirect("collector")

    if request.method == "POST":
        form = PickupRequestForm(request.POST, request.FILES)
        if form.is_valid():
            pr = form.save(commit=False)

            # Require user login to create request (forces ownership)
            if not request.user.is_authenticated:
                messages.info(request, "Please login as a user to create a pickup request.")
                return redirect("user_login")

            pr.created_by = request.user
            pr.save()

            messages.success(request, "Pickup request created! You can track it in “My Requests”.")
            return redirect("my_requests")

        messages.error(request, "Please fix the highlighted fields.")
    else:
        form = PickupRequestForm()

    return render(request, "core/request_new.html", {"form": form})


@login_required(login_url="/user/login/")
def my_requests(request):
    # Block collectors from user page
    if request.user.is_staff:
        return redirect("collector")

    requests = PickupRequest.objects.filter(created_by=request.user)[:50]
    return render(request, "core/requests_list.html", {"requests": requests})


def helper(request):
    # Block collectors from user feature
    if request.user.is_authenticated and request.user.is_staff:
        return redirect("collector")

    q = request.GET.get("q", "").strip()
    results = []
    if q:
        results = WasteGuideItem.objects.filter(item_name__icontains=q)[:20]
        if not results:
            messages.info(request, "No exact match found. Try simpler keyword like “battery”, “peel”, “packet”.")
    return render(request, "core/helper.html", {"q": q, "results": results})


# ----------------------------
# USER AUTH
# ----------------------------
def user_register_view(request):
    if request.user.is_authenticated:
        # collector or user: send them to their place
        return redirect("collector" if request.user.is_staff else "request_new")

    if request.method == "POST":
        full_name = request.POST.get("full_name", "").strip()
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()

        if not full_name or not username or not password:
            messages.error(request, "All fields are required.")
            return render(request, "core/user_register.html")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists. Try a different one.")
            return render(request, "core/user_register.html")

        user = User.objects.create_user(username=username, password=password)
        user.first_name = full_name
        user.save()

        login(request, user)
        messages.success(request, "Account created. You are logged in.")
        return redirect("request_new")

    return render(request, "core/user_register.html")


def user_login_view(request):
    if request.user.is_authenticated:
        return redirect("collector" if request.user.is_staff else "request_new")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()

        user = authenticate(request, username=username, password=password)
        if user and not user.is_staff:
            login(request, user)
            messages.success(request, "User logged in.")
            return redirect("request_new")

        messages.error(request, "Invalid user credentials (or this is a collector account).")

    return render(request, "core/user_login.html")


def user_logout_view(request):
    logout(request)
    messages.info(request, "Logged out.")
    return redirect("home")


# ----------------------------
# COLLECTOR AUTH
# ----------------------------
def collector_login_view(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect("collector")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()

        user = authenticate(request, username=username, password=password)
        if user and user.is_staff:
            login(request, user)
            messages.success(request, "Collector logged in.")
            return redirect("collector")

        messages.error(request, "Invalid collector credentials.")

    return render(request, "core/collector_login.html")


def collector_logout_view(request):
    logout(request)
    messages.info(request, "Collector logged out.")
    return redirect("home")


@login_required(login_url="/collector/login/")
def collector_dashboard(request):
    if not request.user.is_staff:
        return HttpResponseForbidden("Collector access only.")

    status = request.GET.get("status", "ALL")
    pickups = PickupRequest.objects.filter(created_by__isnull=False)

    if status in {"REQUESTED", "ASSIGNED", "PICKED"}:
        pickups = pickups.filter(status=status)

    pickups = pickups[:200]

    counts = {
        "requested": PickupRequest.objects.filter(created_by__isnull=False, status="REQUESTED").count(),
        "assigned": PickupRequest.objects.filter(created_by__isnull=False, status="ASSIGNED").count(),
        "picked": PickupRequest.objects.filter(created_by__isnull=False, status="PICKED").count(),
    }

    return render(
        request,
        "core/collector_dashboard.html",
        {"pickups": pickups, "counts": counts, "status": status},
    )


@login_required(login_url="/collector/login/")
def update_status(request, pk):
    if not request.user.is_staff:
        return HttpResponseForbidden("Collector access only.")
    if request.method != "POST":
        return HttpResponseForbidden("POST only")

    pr = get_object_or_404(PickupRequest, pk=pk)

    if pr.created_by is None:
        messages.error(request, "This request is not linked to a user.")
        return redirect("collector")

    new_status = request.POST.get("status")
    allowed = {"REQUESTED", "ASSIGNED", "PICKED"}

    if new_status not in allowed:
        messages.error(request, "Invalid status.")
        return redirect("collector")

    pr.status = new_status
    pr.save()
    messages.success(request, f"Status updated to {pr.get_status_display()}.")
    return redirect("collector")


# Chatbot Views
def chatbot(request):
    """Render chatbot page - accessible without login"""
    return render(request, "core/chatbot.html")


@require_http_methods(["POST"])
def chatbot_message(request):
    """Handle chatbot messages via API"""
    if not GEMINI_AVAILABLE:
        return JsonResponse({"error": "Gemini API not available"}, status=500)
    
    try:
        data = json.loads(request.body)
        user_message = data.get("message", "").strip()
        
        if not user_message:
            return JsonResponse({"error": "Message cannot be empty"}, status=400)
        
        # Get API key from settings
        from django.conf import settings
        api_key = settings.GEMINI_API_KEY
        
        if api_key == "your-api-key-here" or not api_key:
            return JsonResponse({"error": "API key not configured"}, status=500)
        
        # Configure Gemini
        genai.configure(api_key=api_key)
        
        # Create a prompt for waste management guidance
        system_prompt = """You are a helpful waste management assistant for WasteWise, a waste pickup and segregation application. 
You help users with:
1. Waste segregation guidance (Wet, Dry, E-waste, Hazard)
2. How to properly dispose of items
3. Information about waste management
4. How to use the WasteWise app

Always be concise and helpful. If someone asks about non-waste related topics, politely redirect them to waste management topics."""
        
        # Use Gemini Flash 2.5
        model = genai.GenerativeModel("gemini-2.5-flash", 
                                     system_instruction=system_prompt)
        
        response = model.generate_content(user_message)
        bot_reply = response.text
        
        return JsonResponse({"reply": bot_reply})
    
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"error": f"Error: {str(e)}"}, status=500)
