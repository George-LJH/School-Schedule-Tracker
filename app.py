# pyrefly: ignore[missing-import]
import streamlit as st
from datetime import datetime
from datetime import timedelta
from datetime import time

st.title("School Schedule Tracker", text_alignment="center")
timeFormat = "%H:%M:%S"
timeList: list[time] = [time(15,28,0), time(15,29,0), time(15,30,0), time(15,31,0), time(15,32,0)]
timeName: list[string] = ["1", "2", "3", "4", "5"]

@st.fragment(run_every="1s")
def show_time():
    now_dt: datetime = datetime.now()
    now_time: time = now_dt.time()
    now_str: str = now_dt.strftime(timeFormat)
    
    # Compare time objects, not strings
    future_times: list[time] = [t for t in timeList if t > now_time]
    
    if not future_times:
        st.write("No upcoming times today")
        return
    
    wanted_time: time = min(future_times)
    
    # Combine today's date with the target time
    wanted_dt: datetime = datetime.combine(now_dt.date(), wanted_time)
    
    # If the time already passed today, it would be negative - but we filtered above
    dif: timedelta = wanted_dt - now_dt
    total_seconds: int = int(dif.total_seconds())
    
    hours: int = total_seconds // 3600
    minutes: int = (total_seconds % 3600) // 60
    seconds: int = total_seconds % 60
    
    st.write(f"{hours:02d}:{minutes:02d}:{seconds:02d}")

show_time()