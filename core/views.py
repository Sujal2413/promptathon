from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from .forms import PickupRequestForm
from .models import PickupRequest, WasteGuideItem


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
