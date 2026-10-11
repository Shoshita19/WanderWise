const travelForm = document.getElementById("travelForm");
const planButton = document.getElementById("planButton");
const resultsArea = document.getElementById("resultsArea");
const results = document.getElementById("results");
const resultCount = document.getElementById("resultCount");
const resultSummary = document.getElementById("resultSummary");
const exploreGrid = document.getElementById("exploreGrid");
const favoritesGrid = document.getElementById("favoritesGrid");
const savedPlans = document.getElementById("savedPlans");
const toast = document.getElementById("toast");
let favoriteIds = new Set();
let toastTimer;

function escapeHTML(value) {
    return String(value ?? "").replace(/[&<>"']/g, character => ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;"
    })[character]);
}

function money(value) {
    return "₹" + Number(value || 0).toLocaleString("en-IN");
}

function showToast(message) {
    toast.textContent = message;
    toast.classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toast.classList.remove("show"), 2600);
}

function imageHTML(place) {
    const url = escapeHTML(place.photo_url || "");
    return `<img src="${url}" alt="${escapeHTML(place.name)}" loading="lazy"
        onerror="this.onerror=null;this.src='https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=900&q=80';">`;
}

function placeCard(place, options = {}) {
    const saved = favoriteIds.has(Number(place.id));
    const plannerCard = options.planner === true;
    const tags = (place.interests || []).slice(0, 3).map(tag =>
        `<span class="tag">${escapeHTML(tag)}</span>`).join("");

    let budgetDetails = "";
    if (plannerCard) {
        const status = place.within_budget
            ? `<p class="budget-status">✓ Estimated total is within your budget.</p>`
            : `<p class="budget-status over">Estimated total is ${money(place.estimated_total - place.remaining_budget)}. It may exceed your budget by ${money(Math.abs(place.remaining_budget))}.</p>`;

        budgetDetails = `
            ${status}
            <div class="cost-breakdown">
                <div class="cost-item"><span>Daily expenses</span><strong>${money(place.daily_expenses)}</strong></div>
                <div class="cost-item"><span>Stay estimate</span><strong>${money(place.stay_cost)}</strong></div>
                <div class="cost-item"><span>Transport</span><strong>${money(place.transport_cost)}</strong></div>
                <div class="cost-item"><span>Activities + extras</span><strong>${money(place.activity_cost + place.miscellaneous)}</strong></div>
            </div>
            <details class="itinerary">
                <summary>View ${escapeHTML(place.itinerary.length)}-day sample itinerary</summary>
                <div class="itinerary-list">
                    ${place.itinerary.map(item => `
                        <div class="itinerary-day">
                            <span class="day-chip">DAY ${item.day}</span>
                            <span>${escapeHTML(item.activity)} <strong>· ${money(item.cost)}</strong></span>
                        </div>`).join("")}
                </div>
            </details>`;
    }

    return `
        <article class="destination-card">
            <div class="destination-photo">
                ${imageHTML(place)}
                <span class="photo-gradient"></span>
                <span class="category-pill">${escapeHTML(place.category)}</span>
                <button class="save-button ${saved ? "is-saved" : ""}" type="button"
                    data-action="favorite" data-id="${place.id}"
                    aria-label="${saved ? "Remove" : "Save"} ${escapeHTML(place.name)}"
                    title="${saved ? "Remove from saved places" : "Save place"}">${saved ? "♥" : "♡"}</button>
            </div>
            <div class="destination-content">
                <div class="destination-topline"><span>⌖ ${escapeHTML(place.state)}</span><span class="rating">★ ${Number(place.rating).toFixed(1)}</span></div>
                <h3>${escapeHTML(place.name)}</h3>
                <p>${escapeHTML(place.description)}</p>
                <div class="tag-list">${tags}</div>
                <div class="card-footer">
                    <div class="card-cost"><small>Typical daily estimate</small><strong>${money(place.daily_cost)}</strong></div>
                    <div class="card-season"><small>Best season</small>${escapeHTML(place.best_season)}</div>
                </div>
                ${plannerCard ? `<div class="card-footer"><div class="card-cost"><small>Estimated trip total</small><strong>${money(place.estimated_total)}</strong></div><div class="card-season"><small>Stay idea</small>${escapeHTML(place.stay_name)}</div></div>` : ""}
                <div class="destination-actions">
                    <button class="button button-secondary" type="button" data-action="details" data-id="${place.id}">Quick details</button>
                    <a class="button button-primary" href="#planner" data-action="plan-place" data-interest="${escapeHTML(place.category)}">Plan a visit ↗</a>
                </div>
                ${budgetDetails}
            </div>
        </article>`;
}

async function fetchJSON(url, options = {}) {
    const response = await fetch(url, {
        headers: { "Content-Type": "application/json" },
        ...options
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Something went wrong. Please try again.");
    return data;
}

async function loadFavorites() {
    try {
        const places = await fetchJSON("/api/favorites");
        favoriteIds = new Set(places.map(place => Number(place.id)));
        document.getElementById("favoriteCount").textContent = places.length;
        document.getElementById("savedPlaceCount").textContent = `${places.length} saved place${places.length === 1 ? "" : "s"}`;
        favoritesGrid.innerHTML = places.length
            ? places.map(place => placeCard(place)).join("")
            : `<div class="empty-state">Your wishlist is waiting. Save a place that catches your eye.</div>`;
        return places;
    } catch (error) {
        showToast(error.message);
        return [];
    }
}

async function loadDestinations() {
    const search = document.getElementById("placeSearch").value.trim();
    const interest = document.getElementById("placeInterest").value;
    const maxBudget = document.getElementById("dailyBudget").value;
    const parameters = new URLSearchParams();
    if (search) parameters.set("search", search);
    if (interest) parameters.set("interest", interest);
    if (maxBudget) parameters.set("max_budget", maxBudget);

    exploreGrid.innerHTML = `<div class="loading-message">Finding places for you...</div>`;
    try {
        const places = await fetchJSON(`/api/destinations?${parameters.toString()}`);
        exploreGrid.innerHTML = places.length
            ? places.map(place => placeCard(place)).join("")
            : `<div class="empty-state">No places match those filters. Try a different interest or budget.</div>`;
    } catch (error) {
        exploreGrid.innerHTML = `<div class="empty-state">${escapeHTML(error.message)}</div>`;
    }
}

async function loadSavedPlans() {
    try {
        const plans = await fetchJSON("/api/saved-plans");
        savedPlans.innerHTML = plans.length ? plans.map(plan => `
            <article class="saved-trip-card">
                ${imageHTML({name: plan.destination_name, photo_url: plan.photo_url})}
                <div>
                    <p class="eyebrow">SAVED TRIP · ${escapeHTML(plan.created_at || "")}</p>
                    <h3>${escapeHTML(plan.destination_name)}, ${escapeHTML(plan.state)}</h3>
                    <p>${escapeHTML(plan.days)} day(s) · Interest: ${escapeHTML(plan.interest)} · Budget: ${money(plan.budget)}</p>
                    <p class="trip-price">Estimated total: ${money(plan.estimated_total)}</p>
                    <button class="button button-secondary" type="button" data-action="delete-plan" data-id="${plan.id}">Delete saved trip</button>
                </div>
            </article>`).join("") : `<div class="empty-state">Your saved trips will appear here after you plan a trip.</div>`;
    } catch (error) {
        savedPlans.innerHTML = `<div class="empty-state">${escapeHTML(error.message)}</div>`;
    }
}

travelForm.addEventListener("submit", async event => {
    event.preventDefault();
    const budget = Number(document.getElementById("budget").value);
    const days = Number(document.getElementById("days").value);
    const interest = document.getElementById("interest").value;

    if (!Number.isFinite(budget) || budget < 1000) {
        showToast("Please enter a budget of at least ₹1,000.");
        return;
    }
    if (!Number.isInteger(days) || days < 1 || days > 30) {
        showToast("Please choose between 1 and 30 days.");
        return;
    }

    planButton.disabled = true;
    planButton.textContent = "Finding ideas...";
    resultsArea.hidden = false;
    results.innerHTML = `<div class="loading-message">Comparing destinations and sample costs...</div>`;

    try {
        const data = await fetchJSON("/api/plan", {
            method: "POST",
            body: JSON.stringify({ budget, days, interest })
        });
        await loadFavorites();
        resultCount.textContent = `${data.suggestions.length} ideas`;
        resultSummary.textContent = `For ${days} day(s), a budget of ${money(budget)} and your interest in ${interest.toLowerCase()}.`;
        results.innerHTML = data.suggestions.length
            ? data.suggestions.map(place => placeCard(place, { planner: true })).join("")
            : `<div class="empty-state">We couldn't find a match. Try another interest.</div>`;
        await loadSavedPlans();
        resultsArea.scrollIntoView({ behavior: "smooth", block: "start" });
    } catch (error) {
        results.innerHTML = `<div class="empty-state">${escapeHTML(error.message)}</div>`;
        showToast(error.message);
    } finally {
        planButton.disabled = false;
        planButton.innerHTML = 'Find my trip <span>↗</span>';
    }
});

document.addEventListener("click", async event => {
    const button = event.target.closest("[data-action]");
    if (!button) return;

    const action = button.dataset.action;
    const id = Number(button.dataset.id);

    if (action === "favorite") {
        const isSaved = favoriteIds.has(id);
        try {
            const result = await fetchJSON(`/api/favorites/${id}`, {
                method: isSaved ? "DELETE" : "POST",
                body: JSON.stringify({})
            });
            showToast(result.message);
            await loadFavorites();
            await loadDestinations();
            // The saved-place list updates immediately. Planner cards update
            // their heart icons the next time a new plan is generated.
        } catch (error) {
            showToast(error.message);
        }
    }

    if (action === "details") {
        const card = button.closest(".destination-card");
        const description = card.querySelector(".destination-content > p");
        const season = card.querySelector(".card-season");
        showToast(`${description.textContent} Best season: ${season.textContent.replace("Best season", "").trim()}`);
    }

    if (action === "plan-place") {
        const interest = button.dataset.interest;
        const interestSelect = document.getElementById("interest");
        const match = [...interestSelect.options].find(option => option.value === interest);
        if (match) interestSelect.value = interest;
    }

    if (action === "delete-plan") {
        if (!confirm("Delete this saved trip?")) return;
        try {
            const result = await fetchJSON(`/api/saved-plans/${id}`, { method: "DELETE" });
            showToast(result.message);
            await loadSavedPlans();
        } catch (error) {
            showToast(error.message);
        }
    }
});

["placeSearch", "placeInterest", "dailyBudget"].forEach(id => {
    document.getElementById(id).addEventListener(id === "placeSearch" ? "input" : "change", loadDestinations);
});

document.getElementById("refreshTrips").addEventListener("click", loadSavedPlans);
document.getElementById("menuToggle").addEventListener("click", () => {
    document.getElementById("mainNav").classList.toggle("open");
});
document.querySelectorAll("#mainNav a").forEach(link => {
    link.addEventListener("click", () => document.getElementById("mainNav").classList.remove("open"));
});

async function startWebsite() {
    await loadFavorites();
    await loadDestinations();
    await loadSavedPlans();
}
startWebsite();