from typing import Any
import json
from datetime import date, datetime, time, timedelta, timezone

# pyrefly: ignore[missing-import]
import streamlit as st

# pyrefly: ignore[missing-import]
from streamlit_local_storage import LocalStorage

tzoff = st.context.timezone_offset   # offset in minutes
tz_obj = timezone(-timedelta(minutes=tzoff))
def now_local() -> datetime:
    # UTC now → shift by user offset
    return datetime.now(timezone.utc).astimezone(tz_obj)
localS = LocalStorage()
default_periods: list[tuple[str, time, int]] = [
    ("Period 1", time(17, 10, 0), 1),
    ("Period 2", time(21, 43, 0), 1),
    ("Period 3", time(21, 45, 0), 1),
    ("Period 4", time(21, 47, 0), 1),
    ("Period 5", time(21, 49, 0), 1),
]

PRESETS: dict[str, list[tuple[str, time, int]]] = {
    # ───── DAILY BELL SCHEDULE ─────
    "A-Lunch • Daily": [
        ("1st/5th Period", time(8, 50), 94),
        ("2nd/6th Period", time(10, 33), 94),
        ("A Lunch",        time(12, 16), 30),
        ("3rd/7th Period", time(12, 51), 96),
        ("4th/8th Period", time(14, 36), 94),
    ],
    "B-Lunch • Daily": [
        ("1st/5th Period", time(8, 50), 94),
        ("2nd/6th Period", time(10, 33), 94),
        ("3rd/7th Period", time(12, 16), 47),
        ("B Lunch",        time(13, 7), 30), 
        ("3rd/7th Period", time(13, 41), 46),
        ("4th/8th Period", time(14, 36), 94),
    ],
    "C-Lunch • Daily": [
        ("1st/5th Period", time(8, 50), 94),
        ("2nd/6th Period", time(10, 33), 94),
        ("3rd/7th Period", time(12, 16), 96),
        ("C Lunch",        time(13, 57), 30),
        ("4th/8th Period", time(14, 36), 94),
    ],

    # ───── FLEX TIME BELL SCHEDULE ─────
    "A-Lunch • Flex Time": [
        ("1st/5th Period", time(8, 50), 80),
        ("2nd/6th Period", time(10, 19), 80),
        ("Flex Time",      time(11, 39), 53),
        ("A Lunch",        time(12, 41), 30),
        ("3rd/7th Period", time(13, 16), 85), 
        ("4th/8th Period", time(14, 50), 80), 
    ],
    "B-Lunch • Flex Time": [
        ("1st/5th Period", time(8, 50), 80),
        ("2nd/6th Period", time(10, 19), 80),
        ("Flex Time",      time(11, 39), 53),
        ("3rd/7th Period", time(12, 41), 40),
        ("B Lunch",        time(13, 26), 30),  
        ("3rd/7th Period", time(14, 1), 40),   
        ("4th/8th Period", time(14, 50), 80),  
    ],
    "C-Lunch • Flex Time": [
        ("1st/5th Period", time(8, 50), 80),
        ("2nd/6th Period", time(10, 19), 80),
        ("Flex Time",      time(11, 39), 53),
        ("3rd/7th Period", time(12, 41), 85),
        ("C Lunch",        time(14, 11), 30), 
        ("4th/8th Period", time(14, 50), 80), 
    ],
}

def PrdToJson(periods: list[tuple[str, time, int]]) -> str:
    return json.dumps(
        [[lbl, t.strftime("%H:%M"), dur] for lbl, t, dur in periods],
        separators=(",", ":"),
    )


def JsonToPrd(s: str) -> list[tuple[str, time, int]]:
    data = json.loads(s)
    return [(lbl, time.fromisoformat(t), int(dur)) for lbl, t, dur in data]

LS_KEY = "school-schedule-tracker-v1"
def lsGet(key):
    return localS.getItem(key)

def lsSet(key, val):
    localS.setItem(key, val)

def lsRemove(key):
    localS.setItem(key, "")

def saveAll() -> None:
    data: dict[str, dict[Any, str] | str | Any] = {
        "builderPeriods": PrdToJson(st.session_state.builderPeriods),
        "savedSchedules": {k: PrdToJson(v) for k, v in st.session_state.savedSchedules.items()},
        "lastUsed": st.session_state.get("lastUsed", ""),
    }
    lsSet(LS_KEY, json.dumps(data))
if "lastUsed" not in st.session_state:
    st.session_state.lastUsed = ""
if "screen" not in st.session_state:
    st.session_state.screen = "Countdown"
if "choice" not in st.session_state:
    st.session_state.choice = "Countdown"
if "savedSchedules" not in st.session_state:
    st.session_state.savedSchedules = {}
if "periods" not in st.session_state:
    raw = lsGet(LS_KEY)
    if raw:
        try:
            data = json.loads(raw)
            st.session_state.builderPeriods = JsonToPrd(data["builderPeriods"])
            st.session_state.savedSchedules = {
                k: JsonToPrd(v) for k, v in data.get("savedSchedules", {}).items()
            }
            st.session_state.lastUsed = data.get("lastUsed", "")
        except Exception:
            st.session_state.builderPeriods = PRESETS["A-Lunch • Daily"][:]
            st.session_state.savedSchedules = {}
    else:
        st.session_state.builderPeriods = PRESETS["A-Lunch • Daily"][:]
        st.session_state.savedSchedules = {}
    st.session_state.periods = list(st.session_state.builderPeriods)
    


def handleUpload():
    f = st.session_state.get("schedule_file")
    if f is None:
        return
    try:
        loaded = JsonToPrd(f.read().decode())
        st.session_state.periods = loaded
        st.session_state.builderPeriods = loaded[:]
        saveAll()
        st.session_state.upload_msg = ("success", f"Loaded {len(loaded)} periods")
    except Exception as e:
        st.session_state.upload_msg = ("error", f"Invalid .sst: {e}")


def buildSchedule(periods: list[tuple[str, time, int]]) -> list[tuple[str, datetime, datetime]]:
    schedule: list[tuple[str, datetime, datetime]] = []
    
    base_date = now_local().date()
    
    for i, (label, start, length) in enumerate(periods):
        start_dt = datetime.combine(base_date, start, tzinfo=tz_obj)
        end_dt = start_dt + timedelta(minutes=length)
        
        schedule.append((label, start_dt, end_dt))
        
        if i + 1 < len(periods):
            next_start_naive = periods[i + 1][1]
            next_start_dt = datetime.combine(base_date, next_start_naive, tzinfo=tz_obj)
            
            if end_dt < next_start_dt:
                schedule.append(("Break", end_dt, next_start_dt))
    
    return schedule

def saveToCountdown():
    st.session_state.periods = list(st.session_state.builderPeriods)
    saveAll()
    st.session_state.choice = "Countdown"
    st.session_state.screen = "Countdown"



def on_mode_change():
    st.session_state.screen = st.session_state.get("choice", "Countdown")


with st.sidebar:
    st.header("Schedule file")
    st.file_uploader(
        "Upload a .sst file",
        type=".sst",
        key="schedule_file",
        on_change=handleUpload,
    )
    msg = st.session_state.pop("upload_msg", None)
    if msg:
        kind, text = msg
        getattr(st.sidebar, kind)(text)

    st.download_button(
        "Download current schedule",
        PrdToJson(st.session_state.periods),
        file_name=f"Download_{datetime.now().strftime('%Y%m%d-%H%M%S')}.sst",
    )
    newName = st.text_input("Schedule name")
    if st.button("Save") and newName:
        st.session_state.savedSchedules[newName] = st.session_state.builderPeriods[:]
        st.session_state.lastUsed = newName
        saveAll()
        st.rerun()
    if st.session_state.savedSchedules:
        pick = st.selectbox("Saved", list(st.session_state.savedSchedules.keys()))
        c1, c2 = st.columns(2)
        if c1.button("Load"):
            st.session_state.builderPeriods = st.session_state.savedSchedules[pick][:]
            st.session_state.lastUsed = pick
            saveAll()
            st.rerun()
        if c2.button("Delete"):
            del st.session_state.savedSchedules[pick]
            if st.session_state.lastUsed == pick:
                st.session_state.lastUsed = ""
            saveAll()
            st.rerun()
    if st.button("Reset to Defaults", type="secondary"):
            lsRemove(LS_KEY)
            st.session_state.screen = "Countdown"
            st.session_state.choice = "Countdown"
            st.session_state.lastUsed = ""
            st.session_state.savedSchedules = {}
            st.session_state.builderPeriods = PRESETS["A-Lunch • Daily"][:]
            st.session_state.periods = list(st.session_state.builderPeriods)
            st.rerun()
    
    presetChoice = st.selectbox("Load Preset", ["—"] + list(PRESETS.keys()))

    if st.button("Load Preset") and presetChoice != "—":
        try:
            st.session_state.builderPeriods = PRESETS[presetChoice][:]
            st.session_state.periods = list(st.session_state.builderPeriods)
            saveAll()
            st.toast(f"Loaded {presetChoice}")
            st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")
    st.radio(
        "Mode",
        ["Countdown", "Schedule Maker"],
        horizontal=True,
        key="choice",
        on_change=on_mode_change,
    )

if st.session_state.screen == "Countdown":
    bar = st.progress(0.0, text="0%")
    st.title("School Schedule Tracker")

    @st.fragment(run_every="1s")
    def showTime():
        nowDt = now_local().replace(microsecond=0)

        schedule = buildSchedule(st.session_state.periods)

        active_block = None
        for label, start_dt, end_dt in schedule:
            if start_dt <= nowDt < end_dt:
                active_block = (label, start_dt, end_dt)
                break

        if active_block is not None:
            label, start_dt, end_dt = active_block

            total_sec = (end_dt - start_dt).total_seconds()
            elapsed_sec = (nowDt - start_dt).total_seconds()
            progress = (
                max(0.0, min(1.0, elapsed_sec / total_sec))
                if total_sec > 0
                else 1.0
            )

            dif = end_dt - nowDt
            rem_sec = int(dif.total_seconds())
            h, m, s = rem_sec // 3600, (rem_sec % 3600) // 60, rem_sec % 60

            bar.progress(progress)
            st.header(f"{label} in progress ({progress:.0%})")
            st.write(f"Remaining: {h:02d}:{m:02d}:{s:02d}")
            st.write(nowDt)
            return


        if schedule and nowDt < schedule[0][1]:
            first_label, first_start_dt, _ = schedule[0]
            dif = first_start_dt - nowDt
            rem_sec = int(dif.total_seconds())
            h, m, s = rem_sec // 3600, (rem_sec % 3600) // 60, rem_sec % 60

            bar.progress(0.0)
            st.header(f"Waiting for {first_label} to start")
            st.write(f"Starts in: {h:02d}:{m:02d}:{s:02d}")
            st.write(nowDt)
            return

        bar.progress(1.0)
        st.header("School day ended")
        st.write(nowDt)

    showTime()


elif st.session_state.screen == "Schedule Maker":
    st.title("Schedule Maker")

    changed = False

    for i, (label, start, dur) in enumerate(st.session_state.builderPeriods):
        cols = st.columns([3, 2, 2, 1])
        newLabel = cols[0].text_input("Name", label, key=f"lbl_{i}")
        newStart = cols[1].time_input("Start", start, key=f"st_{i}")
        newDur = cols[2].number_input("Min", 1, 480, dur, key=f"du_{i}")

        if cols[3].button("Clear", key=f"del_{i}"):
            st.session_state.builderPeriods.pop(i)
            changed = True
            st.rerun()

        new_tuple = (newLabel, newStart, newDur)
        if new_tuple != st.session_state.builderPeriods[i]:
            st.session_state.builderPeriods[i] = new_tuple
            changed = True

    if st.button("+ Add Period"):
        st.session_state.builderPeriods.append(("New", time(9, 0), 45))
        saveAll()
        st.rerun()

    if changed:
        saveAll()

    st.button("Save To Countdown", on_click=saveToCountdown)