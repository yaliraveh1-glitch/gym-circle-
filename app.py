import math

import folium
import streamlit as st
from streamlit_folium import st_folium

st.set_page_config(page_title="GymCircle", page_icon="🏋️", layout="centered")

try:  # optional: real browser location
    from streamlit_geolocation import streamlit_geolocation
except Exception:  # package missing -> use default location
    streamlit_geolocation = None

# ---------------------------------------------------------------- data
CITY = {
    "Tel Aviv": (32.08, 34.78), "Rishon LeTsiyyon": (31.97, 34.80),
    "Haifa": (32.79, 34.99), "Jerusalem": (31.77, 35.21),
    "Beer Sheva": (31.25, 34.79), "Netanya": (32.33, 34.86),
    "Ashdod": (31.80, 34.65), "Eilat": (29.56, 34.95),
    "Tiberias": (32.79, 35.53), "Herzliya": (32.17, 34.84),
    "Modiin": (31.90, 35.01), "Holon": (32.01, 34.77),
    "Kiryat Shmona": (33.21, 35.57), "Petah Tikva": (32.09, 34.89),
}

# name, age, city, gym, years, level, focus, hours, personal best, bio, active
RAW = [
    ("Maya Cohen", 27, "Tel Aviv", "Iron Haven TLV", 4, "Intermediate", "Powerlifting", "Evenings", "Squat 110 kg", "Coffee first, squats second. Looking for a partner who actually shows up on leg day.", True),
    ("Daniel Levi", 31, "Rishon LeTsiyyon", "Pulse Rishon", 6, "Advanced", "CrossFit", "Early bird", "Clean & jerk 100 kg", "Ex-army fitness instructor. I love early WODs and a good post-workout shakshuka.", True),
    ("Noa Mizrahi", 24, "Haifa", "Carmel Strength", 1, "Beginner", "General fitness", "Mornings", "5 km in 28 min", "New to lifting and happy to learn. Show me the best smoothie spot near the gym.", False),
    ("Yosef Ben-David", 29, "Jerusalem", "Atlas Jerusalem", 5, "Advanced", "Powerlifting", "Evenings", "Deadlift 220 kg", "Chasing a 250 kg pull. Always up to spot or be spotted.", True),
    ("Shira Peretz", 26, "Beer Sheva", "Negev Fit", 2, "Intermediate", "Bodybuilding", "Evenings", "Bench 60 kg", "Prep season is my love language. Let's hit a push day together.", False),
    ("Omer Katz", 33, "Netanya", "Sea Side Gym", 8, "Advanced", "Calisthenics", "Weekends", "12 strict muscle-ups", "Beach workouts on weekends, gym during the week. Always game for a calisthenics session.", True),
    ("Tamar Azoulay", 28, "Ashdod", "Port Fitness", 3, "Intermediate", "HIIT", "Early bird", "10 km in 49 min", "Run, lift, repeat. Looking for someone to keep me accountable at 6am.", False),
    ("Eitan Biton", 35, "Eilat", "Red Sea Gym", 10, "Advanced", "Bodybuilding", "Evenings", "Bench 140 kg", "Training before diving. Visiting Eilat? Come lift with me.", True),
    ("Lior Friedman", 25, "Tiberias", "Galilee Barbell", 1, "Beginner", "Weight loss", "Evenings", "Down 8 kg so far", "Down 8 kg and not stopping. Friendly faces make the best training partners.", False),
    ("Yael Dahan", 30, "Herzliya", "Marina FitHouse", 4, "Intermediate", "Mobility", "Mornings", "Full splits", "Yoga plus lifting. Mobility nerd, happy to swap tips.", True),
    ("Rotem Avraham", 27, "Modiin", "Pulse Modiin", 3, "Intermediate", "General fitness", "Evenings", "15 pull-ups", "Weeknights at the gym, weekends on a trail.", False),
    ("Gal Malka", 32, "Holon", "Iron Holon", 7, "Advanced", "Powerlifting", "Evenings", "Squat 200 kg", "Meet-prep mode. Happy to help newcomers with their form.", True),
    ("Dana Golan", 29, "Kiryat Shmona", "Hermon Strength", 2, "Intermediate", "CrossFit", "Early bird", "Fran in 5:40", "Northern crew. The best views are from the Hermon, then the gym.", False),
    ("Nadav Haim", 26, "Petah Tikva", "Rabin Fit", 2, "Intermediate", "Bodybuilding", "Evenings", "Bench 100 kg", "Chest day every Monday, no excuses. Looking for a spotter.", True),
]


def build_people():
    people = []
    for i, (name, age, city, gym, yrs, lvl, focus, hrs, pr, bio, active) in enumerate(RAW):
        lat, lon = CITY[city]
        people.append(dict(
            id=i, name=name, age=age, city=city, gym=gym, years=yrs, level=lvl,
            focus=focus, hours=hrs, pr=pr, bio=bio, active=active,
            lat=lat + ((i * 37) % 7 - 3) * 0.008, lon=lon + ((i * 53) % 7 - 3) * 0.008,
            hue=(i * 47 + 10) % 360,
            initials="".join(w[0] for w in name.split()),
        ))
    return people


PEOPLE = build_people()

# ---------------------------------------------------------------- state
ss = st.session_state
ss.setdefault("liked", set())
ss.setdefault("passed", set())
ss.setdefault("sel", None)

ME = (31.965, 34.795)  # default: Rishon LeTsiyyon

with st.sidebar:
    st.subheader("📍 Your location")
    if streamlit_geolocation:
        loc = streamlit_geolocation()
        if loc and loc.get("latitude") and loc.get("longitude"):
            ME = (loc["latitude"], loc["longitude"])
            st.success(f"Using your location ({ME[0]:.3f}, {ME[1]:.3f})")
        else:
            st.caption("Click the button and allow location access. Default: Rishon LeTsiyyon.")
    else:
        st.caption("Install streamlit-geolocation to use your exact location.")


def km_from_me(p):
    r = math.pi / 180
    dp, dl = (p["lat"] - ME[0]) * r, (p["lon"] - ME[1]) * r
    a = math.sin(dp / 2) ** 2 + math.cos(ME[0] * r) * math.cos(p["lat"] * r) * math.sin(dl / 2) ** 2
    return 12742 * math.asin(math.sqrt(a))


def dist_text(p):
    d = km_from_me(p)
    return "Less than 2 km away" if d < 1.5 else f"{round(d)} km away"


# ---------------------------------------------------------------- profile UI
def act(i, like):
    if like:
        ss.liked.add(i)
        ss.passed.discard(i)
    else:
        ss.passed.add(i)
        ss.liked.discard(i)


def profile(p, ctx):
    h = p["hue"]
    live = ('<span style="background:rgba(0,0,0,.45);padding:3px 10px;border-radius:12px;'
            'font-size:12px;font-weight:600">● Active now</span><br>') if p["active"] else ""
    st.markdown(
        f"""<div style="height:340px;border-radius:22px;position:relative;overflow:hidden;color:#fff;
        background:linear-gradient(160deg,hsl({h},70%,55%),hsl({(h + 50) % 360},60%,26%))">
        <div style="position:absolute;top:60px;width:100%;text-align:center;font-size:96px;
        font-weight:800;opacity:.28">{p['initials']}</div>
        <div style="position:absolute;left:0;right:0;bottom:0;padding:60px 18px 16px;
        background:linear-gradient(transparent,rgba(0,0,0,.78))">{live}
        <div style="font-size:30px;font-weight:800">{p['name']} <span style="font-weight:500">{p['age']}</span></div>
        <div style="opacity:.92">📍 Lives in {p['city']} · {dist_text(p)}</div></div></div>""",
        unsafe_allow_html=True,
    )
    st.write("")
    st.caption("ABOUT")
    st.write(p["bio"])
    st.caption("TRAINING")
    c1, c2, c3 = st.columns(3)
    yrs = "year" if p["years"] == 1 else "years"
    c1.metric("Training for", f"{p['years']} {yrs}")
    c2.metric("Level", p["level"])
    c3.metric("Focus", p["focus"])
    c4, c5, c6 = st.columns(3)
    c4.metric("Usual hours", p["hours"])
    c5.metric("Home gym", p["gym"])
    c6.metric("Personal best", p["pr"])

    b1, b2 = st.columns(2)
    b1.button("✕ Pass", key=f"pass_{ctx}_{p['id']}", on_click=act, args=(p["id"], False), use_container_width=True)
    b2.button("♥ Like", key=f"like_{ctx}_{p['id']}", on_click=act, args=(p["id"], True), type="primary", use_container_width=True)
    if p["id"] in ss.liked:
        if p["active"]:
            st.success(f"It’s a match! {p['name'].split()[0]} liked you back.")
        else:
            st.info(f"Like sent to {p['name'].split()[0]}.")


# ---------------------------------------------------------------- layout
st.title("🔥 GymCircle")
st.caption("Find training partners at your gym, near you.")
tab_map, tab_disc, tab_likes = st.tabs(["🗺️ Map", "🃏 Discover", f"♥ Likes ({len(ss.liked)})"])

with tab_map:
    only_active = st.toggle("Active now only")
    m = folium.Map(location=ME, zoom_start=10, tiles="OpenStreetMap")
    folium.CircleMarker(
        ME, radius=9, color="#ffffff", weight=3, fill=True,
        fill_color="#3b82f6", fill_opacity=1, tooltip="You",
    ).add_to(m)
    for p in PEOPLE:
        if only_active and not p["active"]:
            continue
        ring = "#22c55e" if p["active"] else "#ffffff"
        html = (f'<div style="width:40px;height:40px;border-radius:50%;border:3px solid {ring};'
                f'background:hsl({p["hue"]},65%,48%);color:#fff;font:700 13px system-ui;'
                f'display:flex;align-items:center;justify-content:center;'
                f'box-shadow:0 2px 8px rgba(0,0,0,.4)">{p["initials"]}</div>')
        folium.Marker(
            [p["lat"], p["lon"]], tooltip=p["name"],
            icon=folium.DivIcon(html=html, icon_size=(40, 40), icon_anchor=(20, 20)),
        ).add_to(m)

    out = st_folium(m, height=460, use_container_width=True,
                    returned_objects=["last_object_clicked_tooltip"])
    clicked = (out or {}).get("last_object_clicked_tooltip")
    for p in PEOPLE:
        if clicked == p["name"]:
            ss.sel = p["id"]
    st.caption("Click a person on the map to open their profile. Green ring = training now. Blue dot = you.")
    if ss.sel is not None:
        st.divider()
        profile(PEOPLE[ss.sel], "map")

with tab_disc:
    remaining = [p for p in PEOPLE if p["id"] not in ss.liked and p["id"] not in ss.passed]
    if remaining:
        profile(remaining[0], "disc")
    else:
        st.success("You’re all caught up!")
        if st.button("Start over"):
            ss.liked.clear()
            ss.passed.clear()
            st.rerun()

with tab_likes:
    liked = [p for p in PEOPLE if p["id"] in ss.liked]
    if not liked:
        st.info("No likes yet. Like people on the map or in Discover.")
    for p in liked:
        status = "It’s a match 🎉" if p["active"] else "Like sent"
        st.markdown(f"**{p['name']}, {p['age']}** · {p['city']} · {p['gym']}  \n{status}")
