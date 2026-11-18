import json
import math
from collections import Counter

import folium
import streamlit as st
import streamlit.components.v1 as components
from streamlit_folium import st_folium

st.set_page_config(page_title="GymCircle", page_icon="🏋️", layout="centered")
try:
    from streamlit_geolocation import streamlit_geolocation
except Exception:
    streamlit_geolocation = None

st.markdown("""<style>
.block-container{padding-top:1.2rem;max-width:760px}
.brand{font-size:28px;font-weight:800;color:#0f766e;letter-spacing:-.5px}
.tagl{color:#64748b;margin:-4px 0 8px}
.chip{display:inline-block;background:#ecfdf5;color:#0f766e;border-radius:14px;padding:3px 11px;font-size:12.5px;font-weight:600;margin:0 6px 6px 0}
.live{display:inline-block;background:#dcfce7;color:#166534;border-radius:14px;padding:3px 10px;font-size:12.5px;font-weight:600}
.soon{display:inline-block;background:#f1f5f9;color:#475569;border-radius:14px;padding:3px 10px;font-size:12.5px;font-weight:600}
[data-testid="stImage"]{width:100%!important}
[data-testid="stImage"] img{width:100%!important;height:auto;aspect-ratio:1/1;object-fit:cover;border-radius:16px}
div.stButton>button[kind="primary"]{background:#0f766e;border-color:#0f766e;color:#fff}
</style>""", unsafe_allow_html=True)

# ------------------------------------------------------------------ data
GYMS = {
    "Iron Haven": dict(addr="Ibn Gabirol 120, Tel Aviv", ll=(32.0853, 34.7818), price=289, hours="Open 24 hours", rating=4.7, members=1240, peak="17:30 to 20:30", am=["Free weights", "Cardio floor", "Sauna", "Group classes", "Showers"]),
    "Pulse Rishon": dict(addr="Herzl 45, Rishon LeTsiyyon", ll=(31.9714, 34.7893), price=219, hours="05:30 to 23:30", rating=4.5, members=860, peak="18:00 to 21:00", am=["Cardio floor", "Free weights", "Spinning", "Showers"]),
    "Carmel Strength": dict(addr="HaNassi 30, Haifa", ll=(32.7940, 34.9896), price=199, hours="06:00 to 23:00", rating=4.6, members=540, peak="17:00 to 20:00", am=["Free weights", "Functional zone", "Showers"]),
    "Atlas Jerusalem": dict(addr="Jaffa 88, Jerusalem", ll=(31.7842, 35.2137), price=249, hours="05:00 to 24:00", rating=4.8, members=710, peak="18:00 to 21:30", am=["Powerlifting area", "Cardio floor", "Sauna", "Showers"]),
    "Negev Fit": dict(addr="Rager 12, Beer Sheva", ll=(31.2530, 34.7915), price=179, hours="06:00 to 22:30", rating=4.3, members=420, peak="17:30 to 20:00", am=["Free weights", "Cardio floor", "Group classes"]),
    "Red Sea Gym": dict(addr="Hativat HaNegev 5, Eilat", ll=(29.5577, 34.9519), price=229, hours="06:00 to 23:00", rating=4.6, members=380, peak="19:00 to 21:30", am=["Free weights", "Pool access", "Sauna", "Showers"]),
}
# name, age, photo, home, gym, years, level, goal, bio, plan, exercises, min done (None = not started), planned min, when, per week, open to
RAW = [
    ("Maya Cohen", 27, "w44", "Tel Aviv", "Iron Haven", 4, "Intermediate", "Squat 120 kg by spring", "Product designer who trains after work. Prefers a quiet corner of the gym and a good playlist.", "Leg day", ["squat", "deadlift", "plank"], 32, 75, "", 4, "Spotting, Training partner"),
    ("Daniel Levi", 31, "m32", "Rishon LeTsiyyon", "Pulse Rishon", 6, "Advanced", "Run a 10K in under 45 minutes", "Former army fitness instructor. Early riser who likes short, intense sessions.", "Treadmill cardio", ["treadmill", "plank"], 18, 40, "", 5, "Running partner, Tips"),
    ("Noa Mizrahi", 24, "w65", "Haifa", "Carmel Strength", 1, "Beginner", "Learn the basics safely", "Student getting into lifting. Happy to learn and not afraid to ask questions.", "Full body basics", ["squat", "pulldown", "plank"], None, 60, "Tomorrow 07:30", 3, "Beginner buddy"),
    ("Yosef Ben-David", 29, "m75", "Jerusalem", "Atlas Jerusalem", 5, "Advanced", "Deadlift 250 kg", "Software engineer. Powerlifting on weekdays, hiking on weekends.", "Pull day", ["deadlift", "pullup", "pulldown"], 41, 80, "", 4, "Spotting, Form checks"),
    ("Shira Peretz", 26, "w12", "Beer Sheva", "Negev Fit", 2, "Intermediate", "Build upper body strength", "Physiotherapy student. Loves a well planned push session and a coffee afterwards.", "Chest and triceps", ["bench", "pushdown", "ohp"], None, 70, "Today 19:00", 4, "Training partner"),
    ("Omer Katz", 33, "m52", "Netanya", "Iron Haven", 8, "Advanced", "First weighted muscle-up", "Calisthenics coach. Rings on weekends, the gym during the week.", "Back and biceps", ["pullup", "curl", "pulldown"], 27, 65, "", 5, "Tips, Spotting"),
    ("Tamar Azoulay", 28, "w26", "Ashdod", "Pulse Rishon", 3, "Intermediate", "Half marathon in March", "Teacher who runs and lifts. Mornings only.", "Treadmill intervals", ["treadmill", "plank"], None, 45, "Tomorrow 06:00", 4, "Running partner"),
    ("Eitan Biton", 35, "m41", "Eilat", "Red Sea Gym", 10, "Advanced", "Bench press 150 kg", "Dive instructor. Trains hard in the evening when the heat drops.", "Chest day", ["bench", "ohp", "pushdown"], 22, 75, "", 5, "Spotting"),
    ("Lior Friedman", 25, "m18", "Haifa", "Carmel Strength", 1, "Beginner", "Lose 10 kg", "Down 8 kg already. Prefers friendly, no pressure sessions.", "Cardio and core", ["treadmill", "plank"], None, 50, "Tonight 20:00", 3, "Accountability partner"),
    ("Yael Dahan", 30, "w68", "Herzliya", "Iron Haven", 4, "Intermediate", "Hold a handstand for 30 seconds", "Yoga teacher who lifts to stay strong. Always up for swapping mobility tips.", "Shoulders and core", ["ohp", "plank"], 15, 50, "", 4, "Tips, Mobility swaps"),
    ("Rotem Avraham", 27, "m22", "Modiin", "Atlas Jerusalem", 3, "Intermediate", "15 clean pull-ups", "Engineer. Weeknights at the gym, weekends on the trail.", "Back day", ["pullup", "pulldown", "curl"], None, 60, "Today 18:30", 3, "Training partner"),
    ("Gal Malka", 32, "m9", "Holon", "Iron Haven", 7, "Advanced", "Squat 200 kg", "Powerlifting coach in meet prep. Happy to help newcomers with their form.", "Squat focus", ["squat", "deadlift"], 48, 90, "", 5, "Form checks, Coaching"),
    ("Dana Golan", 29, "w90", "Haifa", "Carmel Strength", 2, "Intermediate", "Compete at a local CrossFit event", "Physiotherapist. Mixes lifting with intervals.", "Full body circuit", ["squat", "pullup", "treadmill"], 35, 60, "", 4, "Training partner"),
    ("Nadav Haim", 26, "m64", "Petah Tikva", "Iron Haven", 2, "Intermediate", "Bench press 100 kg", "Accountant. Chest day every Monday, no excuses.", "Chest and triceps", ["bench", "pushdown"], None, 65, "Monday 18:00", 3, "Spotting"),
]
PEOPLE = [dict(id=i, name=t[0], age=t[1], img=f"https://randomuser.me/api/portraits/{'women' if t[2][0] == 'w' else 'men'}/{t[2][1:]}.jpg",
               home=t[3], gym=t[4], yrs=t[5], lvl=t[6], goal=t[7], bio=t[8], plan=t[9], ex=t[10], done=t[11], dur=t[12], when=t[13], wk=t[14], op=t[15])
          for i, t in enumerate(RAW)]

# pose = head, neck, elbow, hand, hip, knee, ankle (x,y each); A = start, B = finish
EX = {
    "bench": dict(name="Bench press", cat="Chest", muscles="Chest, shoulders, triceps", level="Intermediate", sets="3 to 4 sets of 6 to 10",
                  steps=["Lie flat with your eyes under the bar and feet planted.", "Lower the bar to mid chest with elbows at about 45 degrees.", "Press back up until your arms are straight."], tip="Ask a partner to spot you on heavy sets.",
                  A=(55, 124, 72, 128, 74, 102, 75, 76, 122, 128, 158, 128, 160, 180), B=(55, 124, 72, 128, 60, 118, 66, 100, 122, 128, 158, 128, 160, 180), w=1, anc=None,
                  eq='<rect x="40" y="136" width="140" height="8" rx="3"/><line x1="70" y1="144" x2="70" y2="182"/><line x1="165" y1="144" x2="165" y2="182"/>'),
    "squat": dict(name="Barbell squat", cat="Legs", muscles="Quads, glutes, core", level="Intermediate", sets="3 to 5 sets of 5 to 8",
                  steps=["Rest the bar on your upper back, feet shoulder width apart.", "Sit down and back until your thighs are about parallel.", "Drive through the middle of your foot to stand tall."], tip="Keep your chest up and knees in line with your toes.",
                  A=(100, 42, 100, 60, 108, 78, 103, 62, 100, 106, 101, 143, 100, 180), B=(104, 70, 98, 84, 112, 98, 106, 86, 76, 130, 110, 142, 104, 180), w=1, anc=None, eq=""),
    "deadlift": dict(name="Deadlift", cat="Back", muscles="Hamstrings, glutes, lower back", level="Intermediate", sets="3 to 4 sets of 4 to 6",
                     steps=["Stand with the bar over mid foot, hinge and grip just outside your knees.", "Brace your core and push the floor away.", "Lock out your hips, then lower the bar with control."], tip="Keep the bar close to your legs the whole way.",
                     A=(100, 42, 100, 60, 102, 90, 104, 120, 98, 108, 98, 144, 98, 180), B=(124, 72, 110, 80, 111, 115, 112, 150, 70, 100, 100, 132, 94, 180), w=1, anc=None, eq=""),
    "treadmill": dict(name="Treadmill run", cat="Cardio", muscles="Legs, heart and lungs", level="Beginner", sets="20 to 40 minutes",
                      steps=["Start with a 5 minute walk to warm up.", "Raise the speed to a pace where you can still talk.", "Finish with a 3 minute cool down walk."], tip="For intervals, alternate 1 minute fast with 2 minutes easy.",
                      A=(112, 40, 108, 58, 120, 82, 134, 72, 100, 104, 124, 124, 114, 158), B=(112, 40, 108, 58, 92, 82, 84, 94, 100, 104, 80, 134, 58, 152), w=0, anc=None,
                      eq='<rect x="20" y="180" width="180" height="8" rx="4"/><line x1="195" y1="182" x2="195" y2="96"/><line x1="195" y1="96" x2="170" y2="96"/>'),
    "pullup": dict(name="Pull-up", cat="Back", muscles="Lats, biceps, upper back", level="Intermediate", sets="3 sets of 5 to 10",
                   steps=["Hang with hands just wider than your shoulders.", "Pull your elbows down until your chin clears the bar.", "Lower slowly to a full hang."], tip="Use a resistance band until you can do 5 clean reps.",
                   A=(100, 60, 100, 78, 100, 58, 100, 40, 100, 128, 102, 158, 94, 178), B=(100, 30, 100, 48, 86, 60, 100, 40, 100, 98, 102, 128, 94, 148), w=0, anc=None,
                   eq='<line x1="60" y1="40" x2="140" y2="40" stroke-width="5"/><line x1="60" y1="40" x2="60" y2="182"/><line x1="140" y1="40" x2="140" y2="182"/>'),
    "ohp": dict(name="Overhead press", cat="Shoulders", muscles="Shoulders, triceps, core", level="Intermediate", sets="3 sets of 6 to 10",
                steps=["Hold the bar at collarbone height, feet hip width apart.", "Squeeze your glutes and press straight overhead.", "Lower back to your shoulders under control."], tip="Move your head back slightly as the bar passes your face.",
                A=(100, 42, 100, 60, 110, 76, 106, 52, 100, 106, 101, 143, 100, 180), B=(100, 42, 100, 60, 102, 36, 104, 14, 100, 106, 101, 143, 100, 180), w=1, anc=None, eq=""),
    "curl": dict(name="Dumbbell curl", cat="Arms", muscles="Biceps, forearms", level="Beginner", sets="3 sets of 10 to 12",
                 steps=["Stand tall with dumbbells at your sides, palms forward.", "Curl up while keeping your elbows pinned to your ribs.", "Lower slowly over three seconds."], tip="No swinging. Lighter weight and cleaner reps win.",
                 A=(100, 42, 100, 60, 102, 86, 104, 114, 100, 106, 101, 143, 100, 180), B=(100, 42, 100, 60, 106, 88, 124, 66, 100, 106, 101, 143, 100, 180), w=1, anc=None, eq=""),
    "pushdown": dict(name="Triceps pushdown", cat="Arms", muscles="Triceps", level="Beginner", sets="3 sets of 10 to 15",
                     steps=["Face the cable machine with elbows tucked at your sides.", "Press the handle down until your arms are straight.", "Let it rise until your forearms are just past parallel."], tip="Keep your elbows still. Only the forearms move.",
                     A=(104, 42, 102, 60, 106, 86, 126, 76, 100, 106, 101, 143, 100, 180), B=(104, 42, 102, 60, 106, 86, 110, 116, 100, 106, 101, 143, 100, 180), w=0, anc=(146, 12),
                     eq='<line x1="146" y1="10" x2="146" y2="182"/><rect x="138" y="4" width="20" height="8"/>'),
    "pulldown": dict(name="Lat pulldown", cat="Back", muscles="Lats, biceps", level="Beginner", sets="3 sets of 8 to 12",
                     steps=["Sit with your thighs under the pad and a wide grip.", "Pull the bar to your upper chest, leading with your elbows.", "Return slowly until your arms are fully stretched."], tip="Do not lean back far. Keep your chest tall.",
                     A=(108, 76, 108, 92, 102, 60, 96, 26, 110, 132, 142, 128, 144, 180), B=(108, 76, 108, 92, 96, 106, 116, 88, 110, 132, 142, 128, 144, 180), w=0, anc=(100, 8),
                     eq='<rect x="92" y="136" width="36" height="8" rx="3"/><line x1="110" y1="144" x2="110" y2="182"/><rect x="132" y="116" width="26" height="6"/>'),
    "plank": dict(name="Plank", cat="Core", muscles="Abs, glutes, shoulders", level="Beginner", sets="3 holds of 30 to 60 seconds",
                  steps=["Place your forearms on the floor with elbows under shoulders.", "Form a straight line from head to heels.", "Hold and breathe steadily."], tip="Squeeze glutes and abs to stop your hips sagging.",
                  A=(38, 138, 52, 144, 56, 178, 84, 178, 120, 152, 150, 164, 182, 180), B=(38, 138, 52, 144, 56, 178, 84, 178, 120, 146, 150, 160, 182, 180), w=0, anc=None, eq=""),
}
ANIM = """<div style="font-family:system-ui;text-align:center"><svg viewBox="0 0 240 200" style="width:100%;max-width:440px;background:#f1f5f9;border-radius:16px">
<line x1="10" y1="184" x2="230" y2="184" stroke="#cbd5e1" stroke-width="3"/><g stroke="#94a3b8" stroke-width="3" fill="none" stroke-linecap="round">__EQ__</g>
<g id="g" stroke="#0f766e" stroke-width="5" fill="none" stroke-linecap="round" stroke-linejoin="round"></g></svg></div>
<script>const A=__A__,B=__B__,anc=__ANC__,w=__W__,S=document.getElementById('g');
function f(n){const t=(1-Math.cos(n%2600/2600*2*Math.PI))/2,p=A.map((a,i)=>a+(B[i]-a)*t),[hx,hy,nx,ny,ex,ey,wx,wy,px,py,kx,ky,ax,ay]=p;
let s=`<circle cx="${hx}" cy="${hy}" r="9" fill="#0f766e" stroke="none"/><polyline points="${hx},${hy} ${nx},${ny} ${px},${py}"/><polyline points="${px},${py} ${kx},${ky} ${ax},${ay}"/><polyline points="${nx},${ny} ${ex},${ey} ${wx},${wy}"/>`;
if(anc)s+=`<line x1="${anc[0]}" y1="${anc[1]}" x2="${wx}" y2="${wy}" stroke="#94a3b8" stroke-width="2"/>`;
if(w)s+=`<circle cx="${wx}" cy="${wy}" r="8" fill="#334155" stroke="none"/>`;
S.innerHTML=s;requestAnimationFrame(f)}requestAnimationFrame(f);</script>"""


def anim(e):
    return (ANIM.replace("__EQ__", e["eq"]).replace("__A__", json.dumps(e["A"])).replace("__B__", json.dumps(e["B"]))
            .replace("__ANC__", json.dumps(e["anc"])).replace("__W__", str(e["w"])))


# ------------------------------------------------------------------ state and helpers
ss = st.session_state
ss.setdefault("saved", set())
ss.setdefault("hi", set())
ss.setdefault("gym_sel", "Iron Haven")
ME = (31.965, 34.795)
with st.sidebar:
    st.subheader("Your location")
    if streamlit_geolocation:
        loc = streamlit_geolocation()
        if loc and loc.get("latitude") and loc.get("longitude"):
            ME = (loc["latitude"], loc["longitude"])
            st.success("Using your current location")
        else:
            st.caption("Allow location access to see exact distances. Default: Rishon LeTsiyyon.")


def km(ll):
    r = math.pi / 180
    a = math.sin((ll[0] - ME[0]) * r / 2) ** 2 + math.cos(ME[0] * r) * math.cos(ll[0] * r) * math.sin((ll[1] - ME[1]) * r / 2) ** 2
    return 12742 * math.asin(math.sqrt(a))


def dist(ll):
    d = km(ll)
    return "Under 2 km away" if d < 2 else f"{round(d)} km away"


def status(p):
    if p["done"] is not None:
        return f'<span class="live">Training now · {p["done"]} min in</span>'
    return f'<span class="soon">Next session: {p["when"]}</span>'


def chips(items):
    return "".join(f'<span class="chip">{i}</span>' for i in items)


def active_at(g):
    return [p for p in PEOPLE if p["gym"] == g and p["done"] is not None]


def toggle_save(i):
    ss.saved.symmetric_difference_update({i})


def say_hi(i):
    ss.hi.add(i)
    st.toast(f"Hi sent to {PEOPLE[i]['name'].split()[0]}")


def render_map(m):
    for kw in ({"use_container_width": True}, {"width": "100%"}, {}):
        try:
            return st_folium(m, height=380, returned_objects=["last_object_clicked_tooltip"], **kw)
        except TypeError:
            continue


# ------------------------------------------------------------------ dialogs
@st.dialog("Profile", width="large")
def show_profile(pid):
    p = PEOPLE[pid]
    a, b = st.columns([1, 1.7])
    a.image(p["img"], width=220)
    b.markdown(f"## {p['name']}, {p['age']}")
    b.caption(f"Lives in {p['home']}  \nTrains at {p['gym']} · {dist(GYMS[p['gym']]['ll'])}")
    b.markdown(status(p), unsafe_allow_html=True)
    st.write(p["bio"])
    st.markdown(f"**Today’s session: {p['plan']}**")
    if p["done"] is not None:
        st.progress(min(p["done"] / p["dur"], 1.0), text=f"{p['done']} of {p['dur']} minutes")
    else:
        st.caption(f"Planned {p['dur']} minutes · {p['when']}")
    st.markdown(chips(EX[e]["name"] for e in p["ex"]), unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.metric("Training for", f"{p['yrs']} {'year' if p['yrs'] == 1 else 'years'}")
    c2.metric("Level", p["lvl"])
    c3.metric("Sessions a week", p["wk"])
    st.markdown(f"**Goal:** {p['goal']}")
    st.markdown("**Open to**  \n" + chips(p["op"].split(", ")), unsafe_allow_html=True)
    d1, d2 = st.columns(2)
    d1.button("Say hi", key=f"hi{pid}", type="primary", on_click=say_hi, args=(pid,))
    d2.button("Saved" if pid in ss.saved else "Save", key=f"sv{pid}", on_click=toggle_save, args=(pid,))


@st.dialog("How it’s done", width="large")
def show_exercise(eid):
    e = EX[eid]
    st.markdown(f"### {e['name']}")
    st.caption(f"{e['cat']} · {e['muscles']} · {e['sets']}")
    components.html(anim(e), height=270)
    for i, s in enumerate(e["steps"], 1):
        st.markdown(f"{i}. {s}")
    st.info("Tip: " + e["tip"])
    doing = [p for p in PEOPLE if eid in p["ex"] and p["done"] is not None]
    if doing:
        st.markdown("**Doing this right now**")
        cols = st.columns(len(doing[:5]))
        for c, p in zip(cols, doing[:5]):
            c.image(p["img"], width=80)
            c.caption(p["name"].split()[0])


def person_card(p, k):
    with st.container(border=True):
        st.image(p["img"], width=220)
        st.markdown(f"**{p['name']}, {p['age']}**")
        st.caption(f"{p['plan']} · {p['gym']}")
        st.markdown(status(p), unsafe_allow_html=True)
        if st.button("View profile", key=f"v{k}{p['id']}"):
            show_profile(p["id"])


def grid(lst, k):
    cols = st.columns(2)
    for i, p in enumerate(lst):
        with cols[i % 2]:
            person_card(p, k)


# ------------------------------------------------------------------ layout
st.markdown('<div class="brand">GymCircle</div><div class="tagl">Your gym, your people.</div>', unsafe_allow_html=True)
t_home, t_gyms, t_work, t_saved = st.tabs(["Home", "Gyms", "Workouts", f"Saved ({len(ss.saved | ss.hi)})"])

with t_home:
    live = sorted([p for p in PEOPLE if p["done"] is not None], key=lambda p: km(GYMS[p["gym"]]["ll"]))
    st.markdown(f"### {len(live)} people are training near you right now")
    st.caption("See who is in, what they are working on, and say hi before you head over.")
    grid(live, "l")
    st.markdown("### Planning to train today")
    grid([p for p in PEOPLE if p["done"] is None], "p")

with t_gyms:
    m = folium.Map(tiles="OpenStreetMap")
    lls = [g["ll"] for g in GYMS.values()]
    m.fit_bounds([[min(a for a, b in lls) - .1, min(b for a, b in lls) - .1], [max(a for a, b in lls) + .1, max(b for a, b in lls) + .1]])
    folium.CircleMarker(ME, radius=8, color="#ffffff", weight=3, fill=True, fill_color="#2563eb", fill_opacity=1, tooltip="You").add_to(m)
    for n, g in GYMS.items():
        c = len(active_at(n))
        html = (f'<div style="width:38px;height:38px;border-radius:50%;background:{"#0f766e" if c else "#94a3b8"};color:#fff;border:3px solid #fff;'
                f'font:700 15px system-ui;display:flex;align-items:center;justify-content:center;box-shadow:0 2px 8px rgba(0,0,0,.35)">{c}</div>')
        folium.Marker(g["ll"], tooltip=n, icon=folium.DivIcon(html=html, icon_size=(38, 38), icon_anchor=(19, 19))).add_to(m)
    out = render_map(m)
    clicked = (out or {}).get("last_object_clicked_tooltip")
    if clicked in GYMS and clicked != ss.get("last_click"):
        ss["last_click"] = clicked
        ss["gym_sel"] = clicked
    st.caption("Numbers show how many people are training right now. Tap a gym to see details.")
    name = st.selectbox("Gym", list(GYMS), key="gym_sel")
    g = GYMS[name]
    here = [p for p in PEOPLE if p["gym"] == name]
    st.subheader(name)
    st.caption(f"{g['addr']} · {dist(g['ll'])}")
    c1, c2, c3 = st.columns(3)
    c1.metric("Training now", len(active_at(name)))
    c2.metric("Membership", f"₪{g['price']} a month")
    c3.metric("Rating", f"{g['rating']} / 5")
    st.markdown(f"{g['hours']} · Busiest {g['peak']} · {g['members']:,} members")
    st.markdown(chips(g["am"] + ["Free 7 day trial"]), unsafe_allow_html=True)
    st.markdown("#### Today’s plans at this gym")
    st.markdown(chips(f"{k} ×{v}" for k, v in Counter(p["plan"] for p in here).items()), unsafe_allow_html=True)
    for p in here:
        r1, r2, r3 = st.columns([1, 4, 2])
        r1.image(p["img"], width=64)
        r2.markdown(f"**{p['name']}, {p['age']}**  \n{p['plan']} · {p['dur']} min")
        r2.markdown(status(p), unsafe_allow_html=True)
        if r3.button("View profile", key=f"g{p['id']}"):
            show_profile(p["id"])

with t_work:
    st.markdown("### Workout library")
    st.caption("Tap any exercise to see how it is done.")
    cat = st.radio("Muscle group", ["All"] + sorted({e["cat"] for e in EX.values()}), horizontal=True, label_visibility="collapsed")
    cols = st.columns(2)
    for i, (eid, e) in enumerate([x for x in EX.items() if cat in ("All", x[1]["cat"])]):
        with cols[i % 2], st.container(border=True):
            st.markdown(f"**{e['name']}**")
            st.caption(f"{e['cat']} · {e['level']} · {e['sets']}")
            if st.button("See how it’s done", key=f"ex{eid}"):
                show_exercise(eid)

with t_saved:
    ids = sorted(ss.saved | ss.hi)
    if not ids:
        st.info("People you save or say hi to will appear here.")
    for i in ids:
        p = PEOPLE[i]
        a, b, c = st.columns([1, 4, 2])
        a.image(p["img"], width=72)
        b.markdown(f"**{p['name']}, {p['age']}**  \n{p['plan']} · {p['gym']}")
        b.caption("Hi sent" if i in ss.hi else "Saved")
        if c.button("View profile", key=f"s{i}"):
            show_profile(i)
