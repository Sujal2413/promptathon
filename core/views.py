from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from .forms import PickupRequestForm
from .models import PickupRequest, WasteGuideItem


def home(request):
    stats = {
        "total": PickupRequest.objects.count(),
        "today": PickupRequest.objects.filter().count(),
        "wet": PickupRequest.objects.filter(waste_type="WET").count(),
        "dry": PickupRequest.objects.filter(waste_type="DRY").count(),
        "ewaste": PickupRequest.objects.filter(waste_type="EWASTE").count(),
        "hazard": PickupRequest.objects.filter(waste_type="HAZARD").count(),
    }
    return render(request, "core/home.html", {"stats": stats})


def request_new(request):
    if request.method == "POST":
        form = PickupRequestForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Pickup request created! You can track it in “My Requests”.")
            return redirect("my_requests")
        messages.error(request, "Please fix the highlighted fields.")
    else:
        form = PickupRequestForm()
    return render(request, "core/request_new.html", {"form": form})


def my_requests(request):
    # MVP: show latest 50 requests
    requests = PickupRequest.objects.all()[:50]
    return render(request, "core/requests_list.html", {"requests": requests})


def helper(request):
    q = request.GET.get("q", "").strip()
    results = []
    if q:
        results = WasteGuideItem.objects.filter(item_name__icontains=q)[:20]
        if not results:
            messages.info(request, "No exact match found. Try simpler keyword like “battery”, “peel”, “packet”.")
    return render(request, "core/helper.html", {"q": q, "results": results})


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()

        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            messages.success(request, "Logged in.")
            return redirect("collector")
        messages.error(request, "Invalid username/password.")
    return render(request, "core/login.html")


def logout_view(request):
    logout(request)
    messages.info(request, "Logged out.")
    return redirect("home")


@login_required
def collector_dashboard(request):
    # Optional strict staff-only:
    # if not request.user.is_staff:
    #     return HttpResponseForbidden("Collector access only")

    status = request.GET.get("status", "ALL")
    pickups = PickupRequest.objects.all()
    if status in {"REQUESTED", "ASSIGNED", "PICKED"}:
        pickups = pickups.filter(status=status)
    pickups = pickups[:200]

    counts = {
        "requested": PickupRequest.objects.filter(status="REQUESTED").count(),
        "assigned": PickupRequest.objects.filter(status="ASSIGNED").count(),
        "picked": PickupRequest.objects.filter(status="PICKED").count(),
    }

    return render(
        request,
        "core/collector_dashboard.html",
        {"pickups": pickups, "counts": counts, "status": status},
    )


@login_required
def update_status(request, pk):
    if request.method != "POST":
        return HttpResponseForbidden("POST only")

    pr = get_object_or_404(PickupRequest, pk=pk)
    new_status = request.POST.get("status")

    allowed = {"REQUESTED", "ASSIGNED", "PICKED"}
    if new_status not in allowed:
        messages.error(request, "Invalid status.")
        return redirect("collector")

    pr.status = new_status
    pr.save()
    messages.success(request, f"Status updated to {pr.get_status_display()}.")
    return redirect("collector")
