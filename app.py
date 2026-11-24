
from typing import Literal
from typing import Any
# pyrefly: ignore[missing-import]
import streamlit as st
from datetime import datetime
from datetime import timedelta
from datetime import time, date
import json
if "screen" not in st.session_state:
    st.session_state.screen = "tracker"

timeFormat = "%H:%M:%S"
def PrdToJson(periods: list[tuple[str, time, int]]) -> str:
    # [["Label", "HH:MM", minutes], ...]  — compact one-liner
    return json.dumps([[l, t.strftime("%H:%M"), d] for l, t, d in periods], separators=(",", ":"))

def JsonToPrd(s: str) -> list[tuple[str, time, int]]:
    data = json.loads(s)
    return [(l, time.fromisoformat(t), int(d)) for l, t, d in data]
periods: list[tuple[str, time, int]] = [
    ("Period 1", time(10, 00, 0), 1),
    ("Period 2", time(21, 43, 0), 1),
    ("Period 3", time(21, 45, 0), 1),
    ("Period 4", time(21, 47, 0), 1),
    ("Period 5", time(21, 49, 0), 1),
]
if "builderPeriods" not in st.session_state:
    st.session_state.builderPeriods = periods[:]
def handleUpload():
    f = st.session_state["schedule_file"]
    if f is None:
        return
    try:
        loaded = JsonToPrd(f.read().decode())
        st.session_state["periods"] = loaded
        st.session_state["upload_msg"] = ("success", f"Loaded {len(loaded)} periods")
    except Exception as e:
        st.session_state["upload_msg"] = ("error", f"Invalid .sst: {e}")
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
        periods = st.session_state.get("periods", periods)

    st.download_button(
        "Download current schedule",
        PrdToJson(periods),
        file_name=f"Download_{datetime.now().strftime('%Y%m%d-%H%M%S')}.sst",
    )
    st.radio("Mode", ["Countdown", "Schedule Maker"], key = "screen", horizontal = True)
def buildSchedule(periods: list[tuple[str, time, int]]) -> list[tuple[str, time]]:
    schedule: list[tuple[str, time]] = []
    for i, (label, start, length) in enumerate(periods):
        schedule.append((label, start))
        period_end = (datetime.combine(date.today(), start) + timedelta(minutes=length)).time()
        if i + 1 < len(periods):
            next_start = periods[i + 1][1]                     # hard-coded next period start
            break_min = int((datetime.combine(date.today(), next_start) -
                             datetime.combine(date.today(), period_end)).total_seconds() / 60)
            schedule.append((f"Break ({break_min} min)", period_end))
    return schedule

if st.session_state.screen == "Countdown":
    schedule: list[tuple[str, time]] = buildSchedule(periods)
    bar = st.progress(0, text="0%")

    st.title("School Schedule Tracker", text_alignment="center")
    @st.fragment(run_every="1s")
    def showTime():

        nowDt: datetime = datetime.now()
        nowTime: time = nowDt.time()
        
        wantedIndex: int = -1
        for i, (_, t) in enumerate(schedule):
            if t > nowTime:
                wantedIndex = i
                break
        
        if wantedIndex == -1:
            st.write("School day ended")
            return
        
        label, wantedTime = schedule[wantedIndex]
        
        wantedDt: datetime = datetime.combine(nowDt.date(), wantedTime)
        if wantedIndex == 0:
            blockStartDt: datetime = nowDt
        else:
            _, blockStartTime = schedule[wantedIndex - 1]
            blockStartDt = datetime.combine(nowDt.date(), blockStartTime)
        totalSec = (wantedDt - blockStartDt).total_seconds()
        elapsedSec: float = (nowDt - blockStartDt).total_seconds()
        progress: Literal[100] | float   = max(0, min(100, elapsedSec / totalSec)) if totalSec > 0 else 100
        dif: timedelta = wantedDt - nowDt
        totalSeconds: int = int(dif.total_seconds())
        
        hours: int = totalSeconds // 3600
        minutes: int = (totalSeconds % 3600) // 60
        seconds: int = totalSeconds % 60

        bar.progress(progress)
        st.header(f"{progress:.0%}", text_alignment = "center")
        st.write(f"{label}: {hours:02d}:{minutes:02d}:{seconds:02d}")
        st.write(nowDt)
    showTime()
elif st.session_state.screen == "Schedule Maker":
    for i, (label, start, dur) in enumerate(st.session_state.builderPeriods):
        cols = st.columns([3,2,2,1])
        newLabel = cols[0].text_input("Name", label, key = f"lbl_{i}")
        newStart = cols[1].time_input("Start", start, key=f"st_{i}")
        newDur   = cols[2].number_input("Min", 1, 480, dur, key=f"du_{i}")   
        if cols[3].button("Clear", key=f"del_{i}"):
            st.session_state.builderPeriods.pop(i)
            st.rerun()
        st.session_state.builderPeriods[i] = (newLabel, newStart, newDur)
    if st.button("+ Add Period"):
        st.session_state.builderPeriods.append(("New", time(9, 0), 45))
        st.rerun()
    if st.button("Save to Countdown"):
        st.session_state.periods = st.session_state.builderPeriods[:]
        st.session_state.screen = "Countdown"
        st.rerun()