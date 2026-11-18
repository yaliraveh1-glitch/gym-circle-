import datetime
import json
import math
import random
import urllib.parse
import urllib.request
from collections import Counter

import folium
import pandas as pd
from folium.plugins import MarkerCluster
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


SPORTS = {
    "Focus": ["Gym · חדר כושר", "Running · ריצה"],
    "Individual": ["Athletics · אתלטיקה", "Swimming · שחייה", "Cycling · אופניים", "Triathlon · טריאתלון", "Tennis · טניס", "Gymnastics · התעמלות", "Judo · ג'ודו", "Taekwondo · טאקוונדו", "Karate · קראטה", "Kickboxing · קיק בוקס", "Boxing · אגרוף", "MMA · אומנויות לחימה משולבות", "Sambo · סמבו", "Kendo · קנדו", "Fencing · סיף", "Rowing · חתירה", "Kayak · קיאקים", "Archery · חץ וקשת", "Shooting · קליעה", "Equestrian · רכיבה על סוסים", "Weightlifting · הרמת משקולות", "Powerlifting · הרמת כוח", "Climbing · טיפוס ספורטיבי", "Badminton · בדמינטון", "Table tennis · טניס שולחן", "Squash · סקווש", "Golf · גולף", "Cheerleading · צ'ירלידינג", "Chess · שחמט", "Bridge · ברידג'"],
    "Team": ["Football · כדורגל", "Basketball · כדורסל", "Volleyball · כדורעף", "Handball · כדוריד", "Water polo · כדור מים", "Rugby · רוגבי", "Baseball · בייסבול", "Softball · סופטבול", "Cricket · קריקט", "Ice hockey · הוקי קרח", "Roller hockey · הוקי גלגליות", "Ultimate frisbee · פריסבי", "Lacrosse · לקרוס", "American football · פוטבול", "Tug of war · משיכת חבל"],
}
ALL_SPORTS = [x for v in SPORTS.values() for x in v]
EX["treadmill"]["cat"] = "Running"
EX["run"] = dict(EX["treadmill"], name="Outdoor run", cat="Running", eq="", sets="20 to 60 minutes",
                 steps=["Warm up with 5 minutes of easy jogging and leg swings.", "Run at a conversational pace, landing softly under your hips.", "Finish with 5 minutes of walking and gentle stretching."], tip="Build weekly distance by no more than 10 percent.")
# author id (None = you), sport, text, stats, likes, time
SEED = [
    (0, "Gym · חדר כושר", "Squat PR day. Finally hit 110 kg for three clean reps.", ["110 kg × 3", "Leg day"], 14, "25 min ago"),
    (1, "Running · ריצה", "Easy 10K along the beach before work. Perfect weather.", ["10.2 km", "54 min", "5:18 /km"], 21, "1 hour ago"),
    (6, "Running · ריצה", "Intervals done. Six rounds of 800 m and my legs are shaking.", ["6 × 800 m", "3:35 average"], 17, "3 hours ago"),
    (5, "Gym · חדר כושר", "Ring muscle-up progressions after a pull day.", ["Pull day", "65 min"], 9, "5 hours ago"),
    (7, "Swimming · שחייה", "Open water swim in the Red Sea before the first dive group.", ["1.5 km", "32 min"], 25, "Yesterday"),
    (9, "Gymnastics · התעמלות", "Handstand hold: 12 seconds today, up from 8 last week.", ["12 s hold"], 12, "Yesterday"),
]

# ------------------------------------------------------------------ state and helpers
ss = st.session_state
ss.setdefault("saved", set())
ss.setdefault("hi", set())
ss.setdefault("gym_sel", "Iron Haven")
ss.setdefault("pl", set())
_t = datetime.date.today()
ss.setdefault("log", [dict(d=_t - datetime.timedelta(days=a), sport=b, min=c, km=e) for a, b, c, e in
                      [(1, "Gym · חדר כושר", 60, 0), (2, "Running · ריצה", 45, 7.5), (3, "Gym · חדר כושר", 55, 0), (5, "Running · ריצה", 50, 8.2), (6, "Swimming · שחייה", 40, 1.2)]])
ss.setdefault("up_n", 0)
ss.setdefault("posts", [dict(id=i, uid=a, sport=sp, text=tx, stats=stt, likes=l, t=w, photo=None) for i, (a, sp, tx, stt, l, w) in enumerate(SEED)])
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


def toggle_like(i):
    ss.pl.symmetric_difference_update({i})


def delete_post(i):
    ss.posts = [p for p in ss.posts if p["id"] != i]


def share():
    up = ss.get(f"p_up{ss.up_n}")
    tx = ss.get("p_text", "").strip()
    if not tx and not up:
        st.toast("Add some text or a photo first")
        return
    stt = []
    if ss.p_sport.startswith("Running") and ss.get("p_km", 0) > 0 and ss.get("p_min", 0) > 0:
        pace = ss.p_min / ss.p_km
        stt = [f"{ss.p_km:.1f} km", f"{ss.p_min} min", f"{int(pace)}:{int(pace % 1 * 60):02d} /km"]
    ss.posts.insert(0, dict(id=max([p["id"] for p in ss.posts], default=-1) + 1, uid=None, sport=ss.p_sport, text=tx, stats=stt,
                            likes=0, t="Just now", photo=up.getvalue() if up else None,
                            gym=None if ss.get("p_gym", "No gym") == "No gym" else ss.p_gym))
    ss.p_text, ss.p_km, ss.p_min = "", 0.0, 0
    ss.up_n += 1
    st.toast("Your post is live")


def post_card(po):
    me = po["uid"] is None
    with st.container(border=True):
        a, b = st.columns([1, 5])
        if me:
            a.markdown("**You**")
        else:
            a.image(PEOPLE[po["uid"]]["img"], width=56)
        b.markdown(f"**{'You' if me else PEOPLE[po['uid']]['name']}** · {po['t']}")
        b.markdown(chips([po["sport"]] + ([f"at {po['gym']}"] if po.get("gym") else [])), unsafe_allow_html=True)
        st.write(po["text"])
        if po["photo"]:
            st.image(po["photo"])
        else:
            h = (po["id"] * 61 + 160) % 360
            st.markdown(f'<div style="height:130px;border-radius:16px;color:#fff;font:700 20px system-ui;display:flex;align-items:flex-end;padding:14px;'
                        f'background:linear-gradient(135deg,hsl({h},62%,46%),hsl({(h + 60) % 360},58%,26%))">{po["sport"].split(" · ")[0]}</div>', unsafe_allow_html=True)
        if po["stats"]:
            st.markdown(chips(po["stats"]), unsafe_allow_html=True)
        liked = po["id"] in ss.pl
        c1, c2 = st.columns([1, 1])
        c1.button(f"{'Liked' if liked else 'Like'} · {po['likes'] + liked}", key=f"pl{po['id']}", on_click=toggle_like, args=(po["id"],))
        if me:
            c2.button("Delete", key=f"pd{po['id']}", on_click=delete_post, args=(po["id"],))


TYP = "Price not listed. Typical Israeli gym range: ₪250 to ₪400 a month (estimate, confirm with the gym)."
CHAINS = [  # keywords, price from (₪/month), note. Prices from Israeli press reports, may change.
    (("space", "ספייס"), 149, "Space: local plan from about ₪149 a month, national multi-club plan about ₪179 to ₪199."),
    (("icon", "אייקון"), 159, "Icon Fitness (Holmes Place budget brand): from about ₪159 a month with a 12 month commitment."),
    (("pro fit", "profit", "פרופיט"), 119, "Pro Fit: off-peak plan from about ₪119 a month."),
    (("holmes", "הולמס"), None, "Holmes Place premium club. " + TYP),
    (("go active", "גו אקטיב", "great shape", "גרייט שייפ", "sporter", "ספורטר", "sher", "שר פיטנס", "swift", "סוויפט"), None, "Major Israeli chain. " + TYP),
]
MIX = ["Chest and triceps", "Leg day", "Back and biceps", "Treadmill cardio", "Full body", "Shoulders and core", "Spinning class", "Yoga and mobility", "Outdoor run prep"]
CURVE = [.05, .03, .02, .02, .03, .2, .5, .7, .6, .45, .35, .35, .45, .4, .35, .4, .55, .85, 1, .95, .75, .45, .2, .1]


def price_info(name, brand):
    t = (name + " " + brand).lower()
    for keys, pr, note in CHAINS:
        if any(k in t for k in keys):
            return pr, note
    return None, TYP


@st.cache_data(ttl=86400, show_spinner="Loading gyms across Israel...")
def load_osm():
    q = '[out:json][timeout:60];area["ISO3166-1"="IL"][admin_level=2]->.a;(node["leisure"="fitness_centre"](area.a);way["leisure"="fitness_centre"](area.a););out center tags 4000;'
    for url in ("https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter"):
        try:
            req = urllib.request.Request(url, data=urllib.parse.urlencode({"data": q}).encode(), headers={"User-Agent": "GymCircleDemo/1.0"})
            out = []
            for e in json.load(urllib.request.urlopen(req, timeout=70))["elements"]:
                t, c = e.get("tags", {}), e.get("center", {})
                lat, lon = e.get("lat", c.get("lat")), e.get("lon", c.get("lon"))
                name = t.get("name:en") or t.get("name") or t.get("brand")
                if name and lat and lon:
                    out.append(dict(osm=e["id"], name=name, lat=lat, lon=lon, brand=t.get("brand", ""), hours=t.get("opening_hours", "Hours not listed"),
                                    addr=" ".join(x for x in [t.get("addr:street"), t.get("addr:housenumber"), t.get("addr:city")] if x) or "Address not listed",
                                    web=t.get("website") or t.get("contact:website"), phone=t.get("phone") or t.get("contact:phone")))
            if out:
                return out
        except Exception:
            continue
    return []


def build_dir():
    d = [dict(key=f"d{i}", name=n, lat=g["ll"][0], lon=g["ll"][1], addr=g["addr"], hours=g["hours"], price=g["price"], web=None, phone=None, demo=True,
              note="Membership price shown by the gym community.", cap=g["members"] // 18) for i, (n, g) in enumerate(GYMS.items())]
    for o in load_osm():
        pr, note = price_info(o["name"], o["brand"])
        d.append(dict(key=f"o{o['osm']}", name=o["name"], lat=o["lat"], lon=o["lon"], addr=o["addr"], hours=o["hours"], price=pr, web=o["web"], phone=o["phone"],
                      demo=False, note=note, cap=25 + int(random.Random(str(o["osm"])).random() * 50)))
    return d


def hour_now():
    return (datetime.datetime.utcnow().hour + 2) % 24


def sim_active(g, h):
    return int(g["cap"] * CURVE[h] * random.Random(f"{g['key']}{h}").uniform(.6, 1.1))


def mix_for(g, n):
    c = Counter(random.Random(g["key"] + str(hour_now())).choices(MIX, weights=[5, 4, 4, 5, 3, 2, 2, 1, 1], k=max(n, 0)))
    if g["demo"]:
        c.update(p["plan"] for p in active_at(g["name"]))
    return c


def gyms_tab():
    D, h = build_dir(), hour_now()
    for g in D:
        g["act"] = sim_active(g, h) + (len(active_at(g["name"])) if g["demo"] else 0)
    c1, c2 = st.columns([2, 1])
    q = c1.text_input("Search gyms", placeholder="Search by gym name, chain or street", label_visibility="collapsed")
    r = c2.selectbox("Within", [5, 10, 25, 50, 400], index=2, format_func=lambda x: f"Within {x} km" if x < 400 else "All Israel", label_visibility="collapsed")
    sort = st.radio("Sort", ["Closest", "Most active", "Lowest price"], horizontal=True, label_visibility="collapsed")
    res = [g for g in D if km((g["lat"], g["lon"])) <= r and (not q or q.lower() in (g["name"] + " " + g["addr"]).lower())]
    res.sort(key={"Closest": lambda g: km((g["lat"], g["lon"])), "Most active": lambda g: -g["act"], "Lowest price": lambda g: (g["price"] is None, g["price"] or 0)}[sort])
    res = res[:400]
    st.caption(f"{len(res)} gyms shown · {sum(g['act'] for g in res)} people training now (simulated activity)" + ("" if load_osm() else " · Live gym database unavailable, showing featured gyms only"))
    m = folium.Map(location=ME, zoom_start={5: 13, 10: 12, 25: 11, 50: 10, 400: 8}[r], tiles="OpenStreetMap")
    folium.CircleMarker(ME, radius=8, color="#fff", weight=3, fill=True, fill_color="#2563eb", fill_opacity=1, tooltip="You").add_to(m)
    mc = MarkerCluster().add_to(m)
    for g in res:
        b = g["act"] / max(g["cap"], 1)
        col = "#16a34a" if b < .4 else "#f59e0b" if b < .75 else "#dc2626"
        html = (f'<div style="width:30px;height:30px;border-radius:50%;background:{col};color:#fff;border:2px solid #fff;font:700 12px system-ui;'
                f'display:flex;align-items:center;justify-content:center;box-shadow:0 1px 6px rgba(0,0,0,.4)">{g["act"]}</div>')
        folium.Marker((g["lat"], g["lon"]), tooltip=f"{g['name']} · {g['key']}", icon=folium.DivIcon(html=html, icon_size=(30, 30), icon_anchor=(15, 15))).add_to(mc)
    out = render_map(m)
    clicked = ((out or {}).get("last_object_clicked_tooltip") or "").rsplit(" · ", 1)[-1]
    if clicked and clicked != ss.get("last_click") and any(g["key"] == clicked for g in D):
        ss["last_click"], ss["gsel"] = clicked, clicked
    st.caption("Circle number = people training now. Green is quiet, amber moderate, red busy. Tap a pin for details.")
    by = {g["key"]: g for g in D}
    opts = [g["key"] for g in res[:80]]
    if ss.get("gsel") in by and ss["gsel"] not in opts:
        opts.insert(0, ss["gsel"])
    if not opts:
        st.info("No gyms match. Try a wider distance.")
        return
    if ss.get("gsel") not in opts:
        ss["gsel"] = opts[0]
    g = by[st.selectbox("Gym", opts, key="gsel", format_func=lambda k: f"{by[k]['name']} · {by[k]['addr'][:30]}", label_visibility="collapsed")]
    ss["gname"] = g["name"]
    busy = g["act"] / max(g["cap"], 1)
    st.subheader(g["name"])
    st.caption(f"{g['addr']} · {dist((g['lat'], g['lon']))}")
    a, b, c = st.columns(3)
    a.metric("Training now", g["act"])
    b.metric("Busy level", "Quiet" if busy < .4 else "Moderate" if busy < .75 else "Busy")
    c.metric("Membership", f"from ₪{g['price']}" if g["price"] else "Ask the gym")
    st.caption(g["note"])
    st.markdown(f"**Hours:** {g['hours']}" + (f"  \n**Phone:** {g['phone']}" if g["phone"] else ""))
    if g["web"]:
        st.link_button("Visit website", g["web"])
    st.markdown("#### What people are training now")
    mx = mix_for(g, g["act"])
    st.bar_chart(pd.Series(dict(mx)).sort_values()) if mx else st.caption("Nobody is training right now.")
    st.markdown("#### Best times to go")
    st.bar_chart(pd.Series({f"{x:02d}:00": int(g["cap"] * CURVE[x]) for x in range(5, 24)}))
    if g["demo"]:
        st.markdown("#### Members in the community")
        for p in [p for p in PEOPLE if p["gym"] == g["name"]]:
            r1, r2, r3 = st.columns([1, 4, 2])
            r1.image(p["img"], width=64)
            r2.markdown(f"**{p['name']}, {p['age']}**  \n{p['plan']} · {p['dur']} min")
            r2.markdown(status(p), unsafe_allow_html=True)
            if r3.button("View profile", key=f"g{p['id']}"):
                show_profile(p["id"])
    gp = [p for p in ss.posts if p.get("gym") == g["name"]]
    if gp:
        st.markdown("#### Posts from this gym")
        for po in gp[:3]:
            post_card(po)
    else:
        st.caption("No posts yet. Share a workout in the Feed and tag this gym.")
    with st.expander("About this data"):
        st.markdown("Gym locations, addresses and opening hours come live from OpenStreetMap. Chain prices come from Israeli press reports and can change, so confirm with the gym. "
                    "Live activity and workout mix are simulated in this demo and become real once members check in.")


def add_log():
    ss.log.append(dict(d=datetime.date.today(), sport=ss.l_sp, min=ss.l_min, km=ss.l_km))
    st.toast("Workout saved")


def log_section():
    with st.expander("Log a workout"):
        c1, c2, c3 = st.columns(3)
        c1.selectbox("Sport", ALL_SPORTS, key="l_sp")
        c2.number_input("Minutes", min_value=1, max_value=600, value=45, key="l_min")
        c3.number_input("Distance km (optional)", min_value=0.0, max_value=200.0, step=0.1, key="l_km")
        st.button("Save workout", type="primary", on_click=add_log)


def me_tab():
    L, today = ss.log, datetime.date.today()
    days = {x["d"] for x in L}
    d, streak = (today if today in days else today - datetime.timedelta(days=1)), 0
    while d in days:
        streak, d = streak + 1, d - datetime.timedelta(days=1)
    week = {(today - datetime.timedelta(days=i)).strftime("%m-%d"): sum(l["min"] for l in L if l["d"] == today - datetime.timedelta(days=i)) for i in range(6, -1, -1)}
    kmt, sports = sum(l["km"] for l in L), {l["sport"] for l in L}
    a, b, c = st.columns(3)
    a.metric("Streak", f"{streak} days")
    b.metric("This week", f"{sum(week.values())} min")
    c.metric("Workouts", len(L))
    st.bar_chart(pd.Series(week))
    st.markdown("**Badges**")
    st.markdown("".join(f'<span class="{"chip" if ok else "soon"}" style="margin:0 6px 6px 0">{t}</span>' for t, ok in
                        [("First workout", len(L) >= 1), ("3 day streak", streak >= 3), ("Explorer: 3 sports", len(sports) >= 3), ("Century runner: 100 km", kmt >= 100)]), unsafe_allow_html=True)
    st.markdown("**Challenges**")
    for t, v, goal, u in [("Run 100 km", kmt, 100, "km"), ("Complete 12 workouts", len(L), 12, ""), ("Try 3 different sports", len(sports), 3, "")]:
        st.progress(min(v / goal, 1.0), text=f"{t}: {v:g} / {goal} {u}".strip())
    st.markdown("**Distance leaderboard** (demo data)")
    board = sorted([(p["name"], round(random.Random(p["id"]).uniform(20, 140), 1)) for p in PEOPLE] + [("You", round(kmt, 1))], key=lambda x: -x[1])[:8]
    st.markdown("  \n".join(f"{i}. {'**You**' if n == 'You' else n} · {k} km" for i, (n, k) in enumerate(board, 1)))


# ------------------------------------------------------------------ layout
st.markdown('<div class="brand">GymCircle</div><div class="tagl">Your gym, your people.</div>', unsafe_allow_html=True)
t_feed, t_gyms, t_home, t_work, t_me = st.tabs(["Feed", "Gyms", "People", "Train", "Me"])

with t_feed:
    live_p = [p for p in PEOPLE if p["done"] is not None][:6]
    st.caption("Training now")
    for c, p in zip(st.columns(6), live_p):
        c.image(p["img"], width=64)
        c.caption(p["name"].split()[0])
    with st.container(border=True):
        st.markdown("**Share your workout**")
        sp = st.selectbox("Sport", ALL_SPORTS, key="p_sport")
        st.selectbox("Tag a gym (optional)", ["No gym"] + list(GYMS) + ([ss["gname"]] if ss.get("gname") and ss["gname"] not in GYMS else []), key="p_gym")
        st.text_area("What did you do today?", key="p_text", height=80, placeholder="A new personal best, a route you loved, a tip for others...")
        if sp.startswith("Running"):
            r1, r2 = st.columns(2)
            r1.number_input("Distance (km)", min_value=0.0, max_value=100.0, step=0.1, key="p_km")
            r2.number_input("Time (minutes)", min_value=0, max_value=600, step=1, key="p_min")
        st.file_uploader("Add a photo (optional)", type=["jpg", "jpeg", "png"], key=f"p_up{ss.up_n}")
        st.button("Share", type="primary", on_click=share)
    flt = st.radio("Show", ["All", "Gym", "Running", "Other sports"], horizontal=True, label_visibility="collapsed")
    for po in ss.posts:
        k = po["sport"].split(" · ")[0]
        if flt == "All" or (flt == "Gym" and k == "Gym") or (flt == "Running" and k == "Running") or (flt == "Other sports" and k not in ("Gym", "Running")):
            post_card(po)
    with st.expander("All sports on GymCircle"):
        for grp, items in SPORTS.items():
            st.markdown(f"**{grp}**")
            st.markdown(chips(items), unsafe_allow_html=True)

with t_home:
    live = sorted([p for p in PEOPLE if p["done"] is not None], key=lambda p: km(GYMS[p["gym"]]["ll"]))
    st.markdown(f"### {len(live)} people are training near you right now")
    st.caption("See who is in, what they are working on, and say hi before you head over.")
    grid(live, "l")
    st.markdown("### Planning to train today")
    grid([p for p in PEOPLE if p["done"] is None], "p")

with t_gyms:
    gyms_tab()

with t_work:
    log_section()
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

with t_me:
    me_tab()
    st.markdown("**People you saved or said hi to**")
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
